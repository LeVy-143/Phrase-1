# Contract v0.3 — implementation reference
Đây là lựa chọn thiết kế của bản tham khảo, không thay yêu cầu gốc ở requirements.md.
Tên trường ở `src/contracts.py`, JSON schemas ở `schemas/`; JSON payload giữ schema_version="0.1"
vì chưa có thay đổi phá tương thích. Pydantic kiểm kiểu state/result; domain validators
kiểm band/evidence/refs. ID UUID; timestamp UTC ISO-8601; offset Unicode Python.

## State và luồng
`active/part1 → preparing/part2 → active/part2 → active/part3 → awaiting_assessment → completed`.
5 câu Part 1 + 1 cue card (4 gợi ý) + 5 câu Part 3; tối đa 11 lượt answer hợp lệ.
Part 2 có deadline 60 giây do server kiểm; so sánh cùng độ chính xác microsecond.
Reload không reset deadline. elapsed_seconds do code tính từ created_at.
asked_questions giữ question_id, part, text, refers_to_point_ids;
candidate_points giữ point_id, turn_id, summary, quote nguyên văn.
Hiện summary là đoạn đầu tối đa 240 ký tự của answer ≥4 từ, không phải semantic summarizer.
Hai follow-up dựa trên quote có refs; semantic relevance và duplicate paraphrase cần eval rộng hơn.
Duplicate guard hiện dùng word-set Jaccard >0.8, không bảo đảm bắt mọi cách diễn đạt lại.
Lỗi chấm giữ nguyên awaiting_assessment và tất cả answers để retry; không tự báo completed.
`failed` còn là giá trị dự phòng trong schema, không phải trạng thái recovery hiện dùng.

## Facade TV1 ↔ TV2
| Hàm | Input | Output |
|---|---|---|
| ExaminerAgent(storage, provider=None, descriptors=None, clock=time.time) | dependency injection, provider=None là offline | agent |
| start_session | learner_id (demo-1..5), bank_item_id | AgentReply với câu đầu, đã persist |
| submit_answer | context, answer, request_id, expected_revision | AgentReply và checkpoint atomically |
| finish_preparation | context, expected_revision | AgentReply chỉ khi đủ 60 giây |
| resume_session | context | AgentReply từ DB, không sinh lượt mới |
| assess_session | context, expected_revision | AgentReply có assessment hoặc lỗi rõ |
AgentReply={state, examiner_message, assessment|null}. Answer 1–12000 ký tự, không trắng;
request_id dài 1–128. Cùng session+request_id+answer trả reply cũ, đổi answer báo conflict.
ToolContext={learner_id,session_id,run_id} lấy từ actor/phiên phía app, model không được đặt.
MVP chỉ dùng người giả lập, chưa có auth production. UI không gọi SQL/LLM trực tiếp.

## TV2 ↔ TV3
Storage(Path) tự initialize idempotent; SQLite foreign keys ON, transaction đóng connection.
save_session(state, expected_revision, context): create revision=1; update CAS → +1.
commit_reply(reply, expected_revision, context, request_id?, payload_hash?): state/result/
idempotency commit một transaction. Kết quả phải qua schema và evidence/retrieval validation.
load_session/load_assessment/load_traces kiểm learner, session và run. list_sessions chỉ
được app gọi với tài khoản giả lập đang chọn, không phải API auth cho production.
save_assessment(assessment,context) chốt awaiting_assessment thành completed atomically.
checkpoint(context,expected_revision) ghi lại snapshot tin cậy trong DB, không tăng logical revision.
record_retrieval(chunks,context) lưu snapshot rubric đã truy xuất để audit kết quả.
delete_learner_data(learner_id,context) chỉ xoá actor đó, cascade mọi bảng liên quan.
purge(before_iso)/purge_traces(before_iso) là lệnh quản trị local, không expose cho model.

Bảng: sessions, assessments, requests, retrievals, traces. Dữ liệu dưới runtime/.
Trace ở SQLite, không còn thiết kế JSONL ban đầu; scripts.smoke xuất JSON giả lập riêng.
load_bank(Path) trả BankItem list hoặc ValidationError; bank_search trả ID;
bank_get_item trả item hoặc NotFound. Thiếu source/license bị từ chối.
BankItem metadata và verification ghi rõ AI review, human review pending.

## Native tools và RAG
Model assessment có hai tool allowlisted:
- retrieve_descriptors(criterion,top_k=8): chỉ 3 tiêu chí text Speaking, top_k 1–8;
  DescriptorIndex lọc metadata trước cosine retrieval, lưu snapshots/ref IDs.
- save_attempt(expected_revision): native tool chỉ nhận revision đúng với checkpoint hiện tại, không nhận state từ model; ghi checkpoint tin cậy qua SQLite,
  trả persisted/revision/session_id chỉ khi write thành công.
Ngoài ra compute_band và validate_assessment luôn chạy bằng code sau model output,
model không được tự tính overall hoặc nộp band Pronunciation.
`src.tools.retrieve_descriptors` là adapter công khai dùng index đã import.
ChatProvider.run(task,tools,handlers,on_event) thực hiện native tool-call → handler →
message role=tool → model tiếp tục, tối đa 8 model calls/attempt. Output sai schema được
sửa tối đa 2 lần (tối đa 24 model calls; SDK retry transport transient tối đa 2).
Lỗi credentials/capability được báo ProviderError, không fallback sang model giả.
Task tool_sequence là lịch prerequisite do code tin cậy tạo: ba lượt retrieval (mỗi tiêu chí),
một checkpoint rồi một final JSON. Mỗi prerequisite dùng forced native tool choice;
model không được bỏ qua hoặc tự đổi arguments. Không suy ra auto tool selection đáng tin cậy.

## SpeakingAssessment
Exactly 4 criterion: fluency_coherence, lexical_resource, grammatical_range_accuracy,
pronunciation. Ba tiêu chí text có status assessed + band hữu hạn 0..9 bước .5,
evidence và descriptor_refs; hoặc insufficient_evidence + band=null.
Pronunciation luôn not_assessed, band=null, evidence=[], descriptor_refs=[].
Overall do code: trung bình 3 tiêu chí, Decimal half-up đến .5;
thiếu bất kỳ điểm nào → null. overall_basis=three_text_criteria, không là điểm thi chính thức.
Evidence={turn_id,quote,start_char,end_char}, phải trỏ candidate turn và đúng
Turn.text[start_char:end_char], 0<=start<end<=len(text). Model trả turn_id/quote; code tính
offset bằng lần xuất hiện đầu tiên, không sửa quote sai để cho qua. Refs thuộc retrieval của run,
test_part=speaking, criterion đúng. Disclaimer bắt buộc, limitations phải nêu giới hạn text.
Offline trả mọi band null và nêu không chấm model; fixture chỉ ở tests.

## Trace và lỗi
TraceEvent lưu run/session/event IDs, timestamp, loại, tên, input_refs/output_refs,
duration_ms, token_count, estimated_cost/currency, error_code và version metadata.
Không raw transcript, prompt hoặc key; input/output nhạy cảm được đại diện bằng refs.
Provider có token usage thì ghi thật, thiếu để null; chi phí chưa có giá xác minh để null.
Tool trace còn ghi arguments hợp lệ, output_refs, succeeded và duration_ms; không sao chép
raw transcript/rubric vào log. Chi phí chưa có bảng giá xác minh vẫn là null.

Standalone: import_transcript(learner_id, turns, part_scope, source_sample_id) nhận đúng
turns với role/part/text và lưu awaiting_assessment; không yêu cầu hay tự sinh đủ 11 câu.
part_scope và source_sample_id là trường optional mới của state. Kết quả có limitation
nêu scope, không là band đầy đủ; CLI reject field gold/comment để tránh leakage.

Lỗi: ValidationError, OutputValidationError, NotFound, AccessDenied,
RevisionConflict, IdempotencyConflict, DescriptorUnavailable, ProviderError, StorageError.
UI bắt domain errors, hiển thị thông báo không chứa response body/key; không báo pass giả.
