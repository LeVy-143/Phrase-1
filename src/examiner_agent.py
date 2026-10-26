"""Deterministic session controller with a native-tool-calling assessment agent.
Offline mode exercises the harness and persists state but never assigns bands.
"""
import copy
import hashlib
import json
import re
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from .bank import load_bank, bank_get_item
from .errors import ValidationError, RevisionConflict, OutputValidationError
from .provider import function_tool
from .tools import CRITERIA, DISCLAIMER, compute_band, validate_assessment

ROOT=Path(__file__).resolve().parents[1]

def uid():
    return str(uuid.uuid4())

def iso(seconds=None):
    return datetime.fromtimestamp(time.time() if seconds is None else seconds,timezone.utc).isoformat()

def context_for(state):
    return {k:state[k] for k in ('learner_id','session_id','run_id')}

def normalized(text):
    return set(re.findall(r'\w+',text.casefold()))

def similar(a,b):
    x,y=normalized(a),normalized(b)
    return bool(x and y) and len(x&y)/len(x|y) > .8

class ExaminerAgent:
    def __init__(self, storage, *, provider=None, descriptors=None, clock=time.time):
        self.storage=storage
        self.provider=provider
        self.descriptors=descriptors
        self.clock=clock
        self.items=load_bank(ROOT/'data/bank')

    def _trace(self,state,event_type,name,**metrics):
        event={'event_id':uid(),'run_id':state['run_id'],'session_id':state['session_id'],
          'timestamp':iso(self.clock()),'event_type':event_type,'name':name,
          'input_refs':metrics.get('input_refs',[]),'output_refs':metrics.get('output_refs',[]),'duration_ms':metrics.get('duration_ms',0),
          'token_count':metrics.get('token_count'),'estimated_cost':None,'currency':None,
          'error_code':metrics.get('error_code'),'model':getattr(self.provider,'model','offline-no-grading'),
          'prompt_version':'speaking-v1','data_version':'bank-v1',
          'descriptor_version':','.join(sorted({c['version'] for c in self.descriptors.chunks})) if self.descriptors else 'unavailable'}
        self.storage.trace(event,context=context_for(state))

    def _ask(self,state,text,*,refs=None):
        if any(similar(text,q['text']) for q in state['asked_questions']):
            raise ValidationError('Duplicate question rejected')
        qid=uid()
        state['asked_questions'].append({'question_id':qid,'part':state['part'],'text':text,'refers_to_point_ids':refs or []})
        state['turns'].append({'turn_id':qid,'role':'examiner','part':state['part'],'text':text})

    def _reply(self,state,assessment=None):
        last=next((t['text'] for t in reversed(state['turns']) if t['role']=='examiner'),'')
        if state['status']=='awaiting_assessment':
            last='The interview is complete. Assessment is pending; retry assessment when dependencies are available.'
        if state['status']=='completed':
            last='Mock test complete. Review the practice feedback below.'
        return {'state':state,'examiner_message':last,'assessment':assessment}

    def start_session(self,*,learner_id,bank_item_id):
        if not re.fullmatch(r'demo-[1-5]',learner_id):
            raise ValidationError('Reference app accepts only five fictional demo learners')
        item=bank_get_item(self.items,bank_item_id)
        now=iso(self.clock())
        state={'schema_version':'0.1','session_id':uid(),'learner_id':learner_id,'run_id':uid(),'revision':0,
          'mode':'text','status':'active','part':'part1','bank_item_id':bank_item_id,'asked_questions':[],
          'candidate_points':[],'turns':[],'elapsed_seconds':0,'preparation_started_at':None,
          'preparation_deadline_at':None,'created_at':now,'updated_at':now}
        self._ask(state,item['part1_questions'][0])
        reply=self.storage.commit_reply(self._reply(state),expected_revision=None,context=context_for(state))
        self._trace(reply['state'],'skill','speaking-examiner')
        self._trace(reply['state'],'tool','save_attempt')
        return reply

    def resume_session(self,*,context):
        state=self.storage.load_session(context['session_id'],context=context)
        return self._reply(state,self.storage.load_assessment(context['session_id'],context=context))

    def finish_preparation(self,*,context,expected_revision):
        state=self.storage.load_session(context['session_id'],context=context)
        if state['revision']!=expected_revision:
            raise RevisionConflict('Reload session')
        if state['status']!='preparing' or datetime.fromtimestamp(self.clock(),timezone.utc)<datetime.fromisoformat(state['preparation_deadline_at']):
            raise ValidationError('Part 2 preparation lasts 60 seconds; please wait')
        state['status']='active'; state['updated_at']=iso(self.clock())
        state['elapsed_seconds']=max(0,int(self.clock()-datetime.fromisoformat(state['created_at']).timestamp()))
        reply=self.storage.commit_reply(self._reply(state),expected_revision=expected_revision,context=context)
        self._trace(reply['state'],'node','part2_prepared')
        return reply

    def submit_answer(self,*,context,answer,request_id,expected_revision):
        if not isinstance(answer,str) or not answer.strip() or len(answer)>12000 or not isinstance(request_id,str) or not 1<=len(request_id)<=128:
            raise ValidationError('Answer must contain 1–12000 characters; request ID is required')
        digest=hashlib.sha256(answer.encode()).hexdigest()
        cached=self.storage.cached_reply(context,request_id,digest)
        if cached:
            return cached
        state=self.storage.load_session(context['session_id'],context=context)
        if state['revision']!=expected_revision:
            raise RevisionConflict('Reload before submitting')
        if state['status']!='active':
            raise ValidationError('Session is not accepting answers')
        item=bank_get_item(self.items,state['bank_item_id'])
        turn={'turn_id':uid(),'role':'candidate','part':state['part'],'text':answer}
        state['turns'].append(turn)
        # Untrusted literal point. It is never inserted into instructions or executed.
        if len(answer.split())>=4:
            state['candidate_points'].append({'point_id':uid(),'turn_id':turn['turn_id'],
              'summary':answer[:240],'quote':answer[:240]})
        count=sum(q['part']==state['part'] for q in state['asked_questions'])
        if state['part']=='part1':
            if count<5:
                self._ask(state,item['part1_questions'][count])
            else:
                state['part']='part2'; state['status']='preparing'
                state['preparation_started_at']=iso(self.clock())
                state['preparation_deadline_at']=iso(self.clock()+60)
                self._ask(state,item['cue_card']+'\n'+'\n'.join('- '+p for p in item['cue_prompts']))
        elif state['part']=='part2':
            state['part']='part3'
            text,refs=self._followup(state,0,item)
            self._ask(state,text,refs=refs)
        elif count<5:
            text,refs=self._followup(state,count,item)
            self._ask(state,text,refs=refs)
        else:
            state['status']='awaiting_assessment'
        state['updated_at']=iso(self.clock())
        state['elapsed_seconds']=max(0,int(self.clock()-datetime.fromisoformat(state['created_at']).timestamp()))
        reply=self.storage.commit_reply(self._reply(state),expected_revision=expected_revision,context=context,request_id=request_id,payload_hash=digest)
        self._trace(reply['state'],'node','accept_answer')
        self._trace(reply['state'],'tool','save_attempt')
        return reply

    def _followup(self,state,index,item):
        points=state['candidate_points']
        if index in (0,1) and points:
            point=points[-1] if index==0 else points[0]
            # A bounded reference question is safe even without an LLM. Semantic
            # quality is an evaluation target, not a claimed benchmark result.
            text=(f'You mentioned “{point["quote"]}”. Why might other people have a different view?'
                  if index==0 else f'Earlier you said “{point["quote"]}”. How could this change in the future?')
            return text,[point['point_id']]
        return item['part3_questions'][index],[]

    def assess_session(self,*,context,expected_revision):
        state=self.storage.load_session(context['session_id'],context=context)
        if state['status']=='completed':
            return self.resume_session(context=context)
        if state['status']!='awaiting_assessment' or state['revision']!=expected_revision:
            raise ValidationError('Finish all three parts before assessment')
        self._trace(state,'skill','speaking-examiner')
        self._trace(state,'skill','rubric-verifier')
        start=time.monotonic()
        try:
            result=self._assessment(state)
        except Exception as exc:
            self._trace(state,'error','assessment',error_code=type(exc).__name__,duration_ms=int((time.monotonic()-start)*1000))
            raise
        state['status']='completed'; state['updated_at']=iso(self.clock())
        reply=self.storage.commit_reply(self._reply(state,result),expected_revision=expected_revision,context=context)
        self._trace(reply['state'],'node','assessment_complete',duration_ms=int((time.monotonic()-start)*1000))
        return reply

    def _assessment(self,state):
        base={'schema_version':'0.1','assessment_id':uid(),'session_id':state['session_id'],
          'run_id':state['run_id'],'overall_basis':'three_text_criteria','disclaimer':DISCLAIMER,
          'limitations':['Text cannot assess pronunciation or acoustic fluency.','Three-criterion overall is a practice proxy, not an official IELTS Speaking score.'],
          'suggestions':[]}
        if self.provider is None:
            base.update(criteria=[{'criterion':c,'status':'not_assessed' if c=='pronunciation' else 'insufficient_evidence',
              'band':None,'evidence':[],'descriptor_refs':[],
              'comment':'Offline harness mode: no model assessment was performed.'} for c in CRITERIA],overall_band=None)
            base['limitations'].append('OFFLINE: no scoring model or official descriptor retrieval executed.')
            validate_assessment(base,state=state,retrieved=[])
            return base
        if self.descriptors is None:
            from .errors import DescriptorUnavailable
            raise DescriptorUnavailable('Official descriptors are required for live assessment')
        retrieved={}; saved=False
        def retrieve_descriptors(criterion,top_k=8):
            chunks=self.descriptors.retrieve(criterion=criterion,top_k=top_k,query=' '.join(t['text'] for t in state['turns'] if t['role']=='candidate')[:4000])
            self.storage.record_retrieval(chunks,context=context_for(state))
            retrieved.update({c['chunk_id']:c for c in chunks})
            self._trace(state,'retrieval','speaking_descriptors',output_refs=[c['chunk_id'] for c in chunks])
            return chunks
        def save_attempt():
            nonlocal saved
            # The final answer was committed before assessment; verify the real
            # database checkpoint as the model's read/write tool boundary.
            result=self.storage.checkpoint(context=context_for(state),expected_revision=state['revision'])
            saved=True
            return result
        tools=[function_tool('retrieve_descriptors','Retrieve official Speaking band descriptors before scoring',
                 {'criterion':{'type':'string','enum':list(CRITERIA[:3])},'top_k':{'type':'integer','minimum':1,'maximum':8}},['criterion']),
               function_tool('save_attempt','Persist the current trusted attempt checkpoint to SQLite; no model-supplied state is accepted',{},[])]
        task={'operation':'assess_text_speaking','required_tools':['retrieve_descriptors for each text criterion','save_attempt'],
          'candidate_data':state['turns'],'output_contract':{'criteria':[{'criterion':'one of fluency_coherence, lexical_resource, grammatical_range_accuracy',
          'status':'assessed or insufficient_evidence','band':'0..9 step .5 or null','evidence':[{'turn_id':'candidate turn ID','quote':'verbatim','start_char':0,'end_char':1}],
          'descriptor_refs':['retrieved chunk ID'],'comment':'specific feedback'}],'suggestions':['actionable advice']},
          'rules':'Return exactly three text criteria. Insufficient data means null, never invented evidence. Never assess pronunciation.'}
        last_error=None
        for attempt in range(3):
            try:
                output,used=self.provider.run(task,tools=tools,handlers={'retrieve_descriptors':retrieve_descriptors,'save_attempt':save_attempt},
                    on_event=lambda kind,name,**kw:self._trace(state,kind,name,**kw))
                if not saved or 'retrieve_descriptors' not in used:
                    raise OutputValidationError('Required native tool calls were not executed')
                if len(output.get('criteria',[]))!=3:
                    raise OutputValidationError('Expected three text criteria')
                base['criteria']=output['criteria']+[{'criterion':'pronunciation','status':'not_assessed','band':None,'evidence':[],
                  'descriptor_refs':[],'comment':'Not assessed: no audio in text mode.'}]
                base['suggestions']=output.get('suggestions',[])
                base['overall_band']=compute_band({c['criterion']:c['band'] for c in base['criteria']})
                validate_assessment(base,state=state,retrieved=list(retrieved.values()))
                return base
            except (OutputValidationError,KeyError,TypeError) as exc:
                last_error=exc
                task['repair_instruction']='Previous output failed schema/evidence validation. Re-read original candidate data and retrieved descriptors. Correct the output without inventing quotes.'
                self._trace(state,'error','schema_repair',error_code='OutputValidationError')
        raise OutputValidationError('Assessment output invalid after two repair attempts') from last_error
