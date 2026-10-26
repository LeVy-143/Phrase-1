"""Explicit billable AppTest: UI -> native model tools -> RAG -> SQLite.
Uses fictional answers and an injected clock for the 60-second preparation only.
"""
import json
import os
import time
import uuid
from pathlib import Path
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
from src.examiner_agent import ExaminerAgent,context_for
from src.storage import Storage
from src.tools import DISCLAIMER
from scripts.live_smoke import ANSWERS


def main():
    root=Path(__file__).resolve().parents[1];clock=[time.time()]
    run_id=str(uuid.uuid4());db=root/'runtime'/f'live-ui-{run_id}.sqlite3'
    os.environ['IELTS_DB_PATH']=str(db)
    os.environ['IELTS_DESCRIPTORS_PATH']=str(root/'runtime/descriptors/chunks.json')
    original=ExaminerAgent.__init__
    def initialize(self,*args,**kwargs):
        kwargs['clock']=lambda:clock[0]
        original(self,*args,**kwargs)
    with patch.object(ExaminerAgent,'__init__',initialize):
        app=AppTest.from_file(str(root/'app.py'),default_timeout=90).run()
        app.sidebar.radio[0].set_value('Live — model và descriptors thật').run()
        assert not app.exception and not app.error,'Live UI initialization failed'
        next(b for b in app.sidebar.button if b.label=='Bắt đầu phiên mới').click().run()
        for index,answer in enumerate(ANSWERS):
            if index==5:
                clock[0]+=60
                next(b for b in app.button if b.label=='Cập nhật / Bắt đầu trả lời Part 2').click().run()
            app.text_area[0].set_value(answer)
            next(b for b in app.button if b.label=='Gửi câu trả lời').click().run()
            assert not app.exception and not app.error,'UI answer submission failed'
        next(b for b in app.button if b.label=='Hoàn tất / Chấm phiên').click().run(timeout=90)
        assert not app.exception and not app.error,'Live assessment failed'
        assert any('completed' in h.value for h in app.subheader)
        assert len(app.metric)==1,'Expected a real model text proxy band'
    storage=Storage(db);state=storage.list_sessions('demo-1')[0]
    trace=storage.load_traces(context=context_for(state))
    report={'status':'passed','run_id':state['run_id'],'mode':'live-UI','questions':len(state['asked_questions']),
      'overall_proxy':storage.load_assessment(state['session_id'],context=context_for(state))['overall_band'],
      'model_calls':sum(e['event_type']=='model' for e in trace),'accuracy_benchmark':False,'disclaimer':DISCLAIMER,
      'limitations':['Fictional candidate; injected Part 2 clock; real model/RAG/SQLite.']}
    dest=root/'runtime/live-ui-report.json';dest.write_text(json.dumps(report,indent=2));print(json.dumps(report))
if __name__=='__main__':main()
