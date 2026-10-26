"""Offline full session smoke: writes real SQLite and trace, no bands or API calls."""
import argparse
import json
import time
from pathlib import Path
from src.storage import Storage
from src.examiner_agent import ExaminerAgent,context_for

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--real-time',action='store_true',help='Actually wait 60 seconds in Part 2 instead of injecting a test clock')
    args=p.parse_args()
    class DemoClock:
        value=time.time()
        def __call__(self):
            return time.time() if args.real_time else self.value
    clock=DemoClock()
    storage=Storage(Path('runtime/smoke.sqlite3'));agent=ExaminerAgent(storage,clock=clock)
    reply=agent.start_session(learner_id='demo-1',bank_item_id='sp-public_transport')
    for index in range(11):
        state=reply['state']
        if state['status']=='preparing':
            if args.real_time:
                time.sleep(60)
            else:
                clock.value+=60
            reply=agent.finish_preparation(context=context_for(state),expected_revision=state['revision'])
            state=reply['state']
        reply=agent.submit_answer(context=context_for(state),answer='I take the local bus because it is affordable and lets me meet my neighbours.',request_id=f'smoke-{index}',expected_revision=state['revision'])
    state=reply['state']
    reply=agent.assess_session(context=context_for(state),expected_revision=state['revision'])
    assert reply['assessment']['overall_band'] is None
    output=Path('runtime/smoke');output.mkdir(exist_ok=True)
    (output/'trace.json').write_text(json.dumps(storage.load_traces(context=context_for(state)),indent=2))
    print(json.dumps({'session_id':state['session_id'],'status':reply['state']['status'],'questions':len(state['asked_questions']),
      'band':None,'clock':'real' if args.real_time else 'injected test clock','trace':str(output/'trace.json')}))
if __name__=='__main__':
    main()
