from pathlib import Path
from streamlit.testing.v1 import AppTest

def test_app_to_agent_sqlite(tmp_path,monkeypatch):
    path=tmp_path/'ui.sqlite3'
    monkeypatch.setenv('IELTS_DB_PATH',str(path))
    app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/'app.py'),default_timeout=15).run()
    assert not app.exception
    next(b for b in app.sidebar.button if b.label=='Bắt đầu phiên mới').click().run()
    assert not app.exception
    assert any('PART1' in s.value for s in app.subheader)
    app.text_area[0].set_value('I take the bus because it is affordable.')
    next(b for b in app.button if b.label=='Gửi câu trả lời').click().run()
    assert not app.exception
    from src.storage import Storage
    sessions=Storage(path).list_sessions('demo-1')
    assert len(sessions)==1
    assert len([t for t in sessions[0]['turns'] if t['role']=='candidate'])==1
    assert len(sessions[0]['asked_questions'])==2


def test_complete_ui_interview(tmp_path,monkeypatch):
    from src.examiner_agent import ExaminerAgent
    clock=[1_800_000_000.0]
    original=ExaminerAgent.__init__
    def initialize(self,*args,**kwargs):
        kwargs['clock']=lambda:clock[0]
        original(self,*args,**kwargs)
    monkeypatch.setattr(ExaminerAgent,'__init__',initialize)
    monkeypatch.setenv('IELTS_DB_PATH',str(tmp_path/'full-ui.sqlite3'))
    app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/'app.py'),default_timeout=15).run()
    next(b for b in app.sidebar.button if b.label=='Bắt đầu phiên mới').click().run()
    for index in range(11):
        if index==5:
            clock[0]+=60
            next(b for b in app.button if b.label=='Cập nhật / Bắt đầu trả lời Part 2').click().run()
        app.text_area[0].set_value('I use public transport because it is affordable and practical for my family.')
        next(b for b in app.button if b.label=='Gửi câu trả lời').click().run()
        assert not app.exception
    next(b for b in app.button if b.label=='Hoàn tất / Chấm phiên').click().run()
    assert not app.exception
    assert any('completed' in h.value for h in app.subheader)
    assert any('Không có band' in w.value for w in app.warning)
    assert len(app.metric)==0
