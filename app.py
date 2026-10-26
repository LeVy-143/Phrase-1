"""TV1 Streamlit reference UI. Run: streamlit run app.py."""
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
import streamlit as st
from src.bank import bank_search, bank_get_item
from src.storage import Storage
from src.examiner_agent import ExaminerAgent, context_for
from src.errors import IELTSException
from src.tools import DISCLAIMER

st.set_page_config(page_title='Speaking Practice — UC-03', page_icon='💬')
st.title('Speaking Mock Test · text')
st.caption('Bản tham khảo đồ án, không phải sản phẩm IELTS chính thức. Chỉ dùng tài khoản giả lập.')
st.info(DISCLAIMER)

storage=Storage(Path(os.environ.get('IELTS_DB_PATH','runtime/ielts.sqlite3')))
mode=st.sidebar.radio('Chế độ', ['Offline — kiểm tra luồng, không chấm band','Live — model và descriptors thật'])
provider=index=None
try:
    if mode.startswith('Live'):
        from src.provider import ChatProvider
        from src.rag import DescriptorIndex
        provider=ChatProvider()
        index=DescriptorIndex(os.environ.get('IELTS_DESCRIPTORS_PATH','runtime/descriptors/chunks.json'))
except IELTSException as exc:
    st.error(str(exc)); st.stop()
agent=ExaminerAgent(storage,provider=provider,descriptors=index)
learner=st.sidebar.selectbox('Người học giả lập', [f'demo-{i}' for i in range(1,6)])
if st.session_state.get('actor')!=learner or st.session_state.get('mode')!=mode:
    st.session_state.update(actor=learner,mode=mode,session_id=None)
items=agent.items
item_id=st.sidebar.selectbox('Chủ đề',bank_search(items),format_func=lambda key: bank_get_item(items,key)['topic'])
if st.sidebar.button('Bắt đầu phiên mới'):
    reply=agent.start_session(learner_id=learner,bank_item_id=item_id)
    st.session_state.session_id=reply['state']['session_id']
    st.rerun()
sessions=storage.list_sessions(learner)
if sessions:
    selected=st.sidebar.selectbox('Phiên đã lưu',[s['session_id'] for s in sessions])
    if st.sidebar.button('Tiếp tục phiên đã lưu'):
        st.session_state.session_id=selected; st.rerun()
if st.sidebar.checkbox('Xác nhận xoá toàn bộ dữ liệu giả lập của tài khoản này'):
    if st.sidebar.button('Xoá dữ liệu'):
        storage.delete_learner_data(learner,context={'learner_id':learner})
        st.session_state.session_id=None; st.rerun()
current=next((s for s in sessions if s['session_id']==st.session_state.get('session_id')),None)
if current is None:
    st.write('Chọn chủ đề và bắt đầu. Offline lưu phiên thật nhưng không tạo điểm AI.')
    st.stop()
context=context_for(current)
reply=agent.resume_session(context=context); state=reply['state']
st.caption(f"Session: {state['session_id']} · Run: {state['run_id']}")
st.subheader(f"{state['part'].upper()} · {state['status']}")
st.progress(min(len([t for t in state['turns'] if t['role']=='candidate'])/11,1.0))
for turn in state['turns']:
    with st.chat_message('assistant' if turn['role']=='examiner' else 'user'):
        st.text(turn['text'])
try:
    if state['status']=='preparing':
        remaining=max(0,int((datetime.fromisoformat(state['preparation_deadline_at'])-datetime.now(timezone.utc)).total_seconds()))
        st.warning(f'Part 2: chuẩn bị 60 giây. Còn khoảng {remaining} giây khi cập nhật.')
        st.caption('Nhấn cập nhật khi hết giờ; máy chủ kiểm thời hạn, reload không reset đồng hồ.')
        if st.button('Cập nhật / Bắt đầu trả lời Part 2'):
            agent.finish_preparation(context=context,expected_revision=state['revision']); st.rerun()
    elif state['status']=='active':
        with st.form('answer_form',clear_on_submit=True):
            answer=st.text_area('Câu trả lời',max_chars=12000)
            send=st.form_submit_button('Gửi câu trả lời')
        if send:
            agent.submit_answer(context=context,answer=answer,request_id=str(uuid.uuid4()),expected_revision=state['revision'])
            st.rerun()
    elif state['status']=='awaiting_assessment':
        st.info('Đã lưu đủ câu trả lời. Nếu chấm lỗi, bài vẫn còn ở SQLite; có thể thử lại.')
        if st.button('Hoàn tất / Chấm phiên'):
            with st.spinner('Agent đang xử lý rubric và kiểm tra kết quả…'):
                agent.assess_session(context=context,expected_revision=state['revision'])
            st.rerun()
except IELTSException as exc:
    st.error(str(exc))
assessment=reply['assessment']
if assessment:
    st.subheader('Kết quả luyện tập')
    st.info(assessment['disclaimer'])
    if assessment['overall_band'] is None:
        st.warning('Không có band: chế độ offline hoặc chưa đủ cơ sở đánh giá.')
    else:
        st.metric('Band ước lượng — chỉ 3 tiêu chí text',assessment['overall_band'])
    for criterion in assessment['criteria']:
        st.write(f"{criterion['criterion']}: {criterion['band'] if criterion['band'] is not None else criterion['status']}")
        st.text(criterion['comment'])
        for evidence in criterion['evidence']:
            st.text(f"{evidence['turn_id']} [{evidence['start_char']}:{evidence['end_char']}]: {evidence['quote']}")
        if criterion['descriptor_refs']:
            st.caption('Descriptor refs: '+', '.join(criterion['descriptor_refs']))
    for limitation in assessment['limitations']:
        st.caption(limitation)
    for suggestion in assessment['suggestions']:
        st.write('• '+suggestion)
with st.expander('Tiến trình agent — log không chứa transcript'):
    st.json(storage.load_traces(context=context))
