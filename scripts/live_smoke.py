"""Billable full-session verification with fictional answers, NOT accuracy gold."""
import argparse
import json
import time
import uuid
from pathlib import Path
from src.storage import Storage
from src.examiner_agent import ExaminerAgent,context_for
from src.provider import ChatProvider
from src.rag import DescriptorIndex
from src.tools import validate_assessment, DISCLAIMER

ANSWERS=[
'I usually travel between my home, the university library and a small supermarket. Most destinations are close enough for a bus journey. I try to combine shopping with my trip home so I do not need to travel twice.',
'I walk if the destination is nearby and the weather is comfortable. For a longer journey I take the bus because the fare is affordable. Walking gives me some exercise, although it is inconvenient when I carry heavy books.',
'The roads near my home are busiest just before morning classes begin. Parents drive their children to school while office workers are commuting. If I leave fifteen minutes earlier, the bus is noticeably less crowded.',
'I normally travel alone, but I sometimes meet a classmate at the bus stop. We discuss our assignments during the journey. Travelling together makes delays less frustrating, although we also enjoy a quiet trip when we are tired.',
'More reliable information about arrival times would make my journey easier. I would rather wait at home than stand beside a busy road. Covered bus stops would also help passengers during heavy rain.',
'Last month I took a local bus to a community workshop with a classmate. We wanted to learn how to repair small household objects instead of throwing them away. I checked the route the evening before, but I underestimated how crowded the bus would be. At first we had to stand, and I worried that we would miss our stop. An older passenger explained where we should get off, which made the journey much less stressful. The trip took about forty minutes and cost much less than a taxi. What I remember most is that people who had never met were willing to help one another. Since then, I have used the bus more often. However, I would not say it is suitable for every journey, especially late at night when services are limited.',
'Other passengers may value convenience more than price. For example, a parent with two young children might prefer a direct car journey even when it costs more. I think transport policy needs to recognise those practical differences rather than assume everybody has the same priorities.',
'In the future I might work from home for part of the week, so I would need fewer daily journeys. Better live information could also make buses easier to use. Nevertheless, people will still need transport for social activities and essential services.',
'Cheaper tickets could help people with low incomes reach jobs and education. However, the discount needs stable funding. A targeted pass may be more practical than lowering every fare, provided applying for it is simple and respectful.',
'Remote work could spread demand across the day instead of concentrating it during rush hour. Some routes might become less busy, while local neighbourhood services become more important. Planners should use recent travel data rather than assume commuting patterns will stay the same.',
'Passengers should leave priority seats available, keep noise at a reasonable level and give others room to board. Drivers also need clear rules and support. A welcoming system depends on both considerate behaviour and good service design.'
]

def run(label='regular', *, answers=None, provider=None):
    answers=answers or ANSWERS
    clock=[time.time()]
    storage=Storage(Path('runtime/live-smoke.sqlite3'))
    index=DescriptorIndex('runtime/descriptors/chunks.json')
    provider=provider or ChatProvider()
    agent=ExaminerAgent(storage,provider=provider,descriptors=index,clock=lambda:clock[0])
    reply=agent.start_session(learner_id='demo-1',bank_item_id='sp-public_transport')
    started=time.monotonic()
    for number,answer in enumerate(answers):
        state=reply['state']
        if state['status']=='preparing':
            clock[0]+=60
            reply=agent.finish_preparation(context=context_for(state),expected_revision=state['revision'])
            state=reply['state']
        reply=agent.submit_answer(context=context_for(state),answer=answer,request_id=str(uuid.uuid4()),expected_revision=state['revision'])
    state=reply['state'];context=context_for(state)
    reply=agent.assess_session(context=context,expected_revision=state['revision'])
    result=reply['assessment'];events=storage.load_traces(context=context)
    with storage.connect() as db:
        snapshots=[json.loads(r[0]) for r in db.execute('SELECT chunk_json FROM retrievals WHERE session_id=?',(state['session_id'],))]
    validate_assessment(result,state=state,retrieved=snapshots)
    report={'run_id':state['run_id'],'session_id':state['session_id'],'label':label,
      'status':reply['state']['status'],'model':provider.model,'prompt_version':'speaking-v2','data_version':'fictional-live-smoke-v1',
      'descriptor_version':index.chunks[0]['version'],'questions':len(state['asked_questions']),
      'native_tool_names':sorted({e['name'] for e in events if e['event_type']=='tool'}),
      'model_calls':sum(e['event_type']=='model' for e in events),
      'tokens':sum(e['token_count'] or 0 for e in events),'estimated_cost':None,
      'latency_seconds':round(time.monotonic()-started,3),'overall_band':result['overall_band'],
      'pronunciation':next(c for c in result['criteria'] if c['criterion']=='pronunciation'),
      'disclaimer':DISCLAIMER,'accuracy_benchmark':False,'clock':'injected for Part 2 only; live model calls are real'}
    dest=Path('runtime/live')/state['run_id'];dest.mkdir(parents=True)
    (dest/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    (dest/'assessment.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    (dest/'trace.json').write_text(json.dumps(events,ensure_ascii=False,indent=2))
    print(json.dumps(report,ensure_ascii=False),flush=True)
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--label',default='regular');args=p.parse_args()
    run(args.label)
if __name__=='__main__':main()
