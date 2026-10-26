import json
from pathlib import Path
import pytest
from src.storage import Storage
from src.examiner_agent import ExaminerAgent

@pytest.fixture
def clock():
    class Clock:
        value=1_800_000_000.0
        def __call__(self):
            return self.value
        def advance(self,seconds):
            self.value+=seconds
    return Clock()

@pytest.fixture
def storage(tmp_path):
    return Storage(tmp_path/'test.sqlite3')

@pytest.fixture
def agent(storage,clock):
    return ExaminerAgent(storage,clock=clock)

@pytest.fixture
def started(agent):
    return agent.start_session(learner_id='demo-1',bank_item_id='sp-public_transport')

@pytest.fixture
def finish_interview(agent,clock):
    from src.examiner_agent import context_for
    def finish(reply, answer='I use the bus because it is affordable and I enjoy talking to my neighbours.'):
        for index in range(11):
            state=reply['state']; context=context_for(state)
            if state['status']=='preparing':
                clock.advance(60)
                reply=agent.finish_preparation(context=context,expected_revision=state['revision'])
                state=reply['state']
            reply=agent.submit_answer(context=context_for(state),answer=answer,request_id=f'answer-{index}',expected_revision=state['revision'])
        return reply
    return finish

@pytest.fixture
def descriptor_fixture(tmp_path):
    # SYNTHETIC retrieval fixture. These texts/bands are NOT official rubrics
    # or teacher scores; never used by the production index unless explicitly supplied.
    from src.rag import DescriptorIndex
    chunks=[{'chunk_id':f'test-{c}-{band}','test_part':'speaking','criterion':c,'band':band,
      'version':'synthetic-test-only','source_url':'https://example.invalid/test-fixture',
      'license_note':'Synthetic test fixture, not IELTS descriptors',
      'text':f'SYNTHETIC TEST ONLY: {c} test band {band}'}
      for c in ('fluency_coherence','lexical_resource','grammatical_range_accuracy') for band in range(1,10)]
    path=tmp_path/'chunks.json';path.write_text(json.dumps(chunks))
    return DescriptorIndex(path)
