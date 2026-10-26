"""Billable assessment of an explicitly scoped transcript, without gold leakage.
Input JSON contains ONLY sample_id, part_scope and turns [{role,part,text}].
Keep permissioned transcripts under runtime/ or outside the repository.
"""
import argparse
import json
from pathlib import Path
from src.examiner_agent import ExaminerAgent,context_for
from src.storage import Storage
from src.provider import ChatProvider
from src.rag import DescriptorIndex
from src.errors import ValidationError
from src.tools import DISCLAIMER


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,required=True)
    p.add_argument('--usage-permitted',action='store_true',required=True)
    args=p.parse_args();payload=json.loads(args.input.read_text())
    if set(payload)!={'sample_id','part_scope','turns'}:
        raise ValidationError('Only sample_id, part_scope and turns allowed; gold labels/comments must stay in evaluator')
    storage=Storage(Path('runtime/transcript-assessment.sqlite3'))
    agent=ExaminerAgent(storage,provider=ChatProvider(),descriptors=DescriptorIndex('runtime/descriptors/chunks.json'))
    reply=agent.import_transcript(learner_id='demo-1',turns=payload['turns'],part_scope=payload['part_scope'],source_sample_id=payload['sample_id'])
    state=reply['state'];reply=agent.assess_session(context=context_for(state),expected_revision=state['revision'])
    dest=Path('runtime/transcripts')/state['run_id'];dest.mkdir(parents=True)
    (dest/'assessment.json').write_text(json.dumps(reply['assessment'],ensure_ascii=False,indent=2))
    (dest/'trace.json').write_text(json.dumps(storage.load_traces(context=context_for(state)),indent=2))
    print(json.dumps({'run_id':state['run_id'],'sample_id':payload['sample_id'],'part_scope':payload['part_scope'],
        'status':reply['state']['status'],'overall_proxy':reply['assessment']['overall_band'],'accuracy_benchmark':False,'disclaimer':DISCLAIMER,'output':str(dest)}))
if __name__=='__main__':main()
