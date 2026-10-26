# Yêu cầu và quyết định thiết kế
## Nguồn đã đọc
- D1: `2026-10-06_de_tai_06_ielts_learning_agent.docx` do người dùng cung cấp,
  đọc nội dung thân tài liệu, gồm bảng. Không phân phối lại DOCX trong repo.
- P1: ảnh “PHASE 1 — Bootstrap dự án”, 07/10–27/10, 3 tuần,
  hạn cuối tuần 7, kiến thức buổi 1–5; do người dùng gửi trong chat.
- U: yêu cầu người dùng: ban đầu scaffold, sau đó yêu cầu triển khai toàn bộ Phase 1, 4 thành viên được giảng viên chấp thuận;
  commit phải chờ duyệt, không tự push, không key trong repo.
Repo ban đầu rỗng, không có tài liệu Phase 1 để đối chiếu thêm.
Nhận xét xen trong D1 như “bỏ”, “khó quá” không hủy yêu cầu chính thức.

## Truy vết bắt buộc (trạng thái lúc scaffold; cập nhật thực thi cuối file)
| Nguồn | Yêu cầu | Nơi dự kiến / trạng thái hiện tại |
|---|---|---|
| P1 | Đăng ký nhóm 5 SV, đề tài, use case, người sở hữu | Người dùng xác nhận giảng viên chấp thuận nhóm 4; danh sách tên/UC owner chờ nhóm điền |
| P1 | Repo, CI, codebase app và agent | Có scaffold; CI và runtime chưa triển khai |
| P1 | Agent loop ≥2 tool, ≥1 skill, log từng bước | tools/skill/trace có contract, chưa chạy |
| P1 | 1 UC từ app đến agent, ≥10 eval case | Chọn UC-03; chỉ có kế hoạch eval, chưa đạt |
| D1 UC-03 | Part 1: 4–6 câu; Part 2: 1 phút chuẩn bị, lượt dài; Part 3: 4–6 câu | State/contract; chưa runtime |
| D1 UC-03 | Cue card 3–4 gợi ý, đúng thứ tự, giới hạn lượt do nhóm đặt | Contract đề xuất 11 câu hỏi chính tối đa |
| D1 UC-03 | ≥80% phiên có ≥2 câu đào sâu theo candidate_points; không trùng nghĩa | Cần evaluator ngữ nghĩa, không chỉ so string |
| D1 UC-03 | State có part, asked_questions, candidate_points, elapsed_seconds | src/contracts.py |
| D1 UC-03 | 4 tiêu chí; Pronunciation text not_assessed; evidence từ transcript, refs Speaking | Contract kết quả; chưa validator |
| D1 UC-03, 2.3, 6.2 | ≥10 transcript giáo viên chấm; ≥80% lệch tổng ≤1 band; MAE, ±0.5/1, QWK, evidence/refs, đào sâu | Benchmark chưa có, không tạo nhãn giả |
| D1 2.1 | ≥10 bộ Speaking, source/license và metadata | data/bank/ chưa có nội dung |
| D1 2.2 | RAG descriptors, chunk tiêu chí × band, metadata; ghi chú ngữ pháp tự viết có mã | data/descriptors/ cần ingestion và nguồn hợp lệ |
| D1 4.1 | Tool có scope; ≥1 tool ngoài thật (SQLite được chấp nhận) | save_attempt → Storage dự kiến tool thật |
| D1 4.2 | Toàn hệ thống ≥2 skill có contract | Phase 1 làm speaking-examiner trước; skill thứ hai chưa chọn, vẫn còn yêu cầu |
| D1 4.3–4.4 | ≥5 attack case chung; run ID, trace từng bước, token/chi phí/lỗi | Kế hoạch tại evals/, TraceEvent; chưa có trace |
| D1 1.5, 5 | Không sao chép đề cấm; điểm có nhãn; không dịch vụ chấm sẵn; bảo vệ dữ liệu | data_sources/policy; chờ thực thi |
| D1 6.1–6.3 | Eval một lệnh, xuất cấu trúc; regression ≥2 lần, model/prompt/data version | TV4 tương lai; chưa có kết quả |
| D1 7 | README, .env.example, AGENTS, skills, bank, evals, docs, báo cáo, phân công, video ≤15 phút, trace mẫu | Scaffold không thay thế sản phẩm nộp |

## Phạm vi toàn đồ án còn giữ nguyên
D1 không chỉ có UC-03: mỗi SV sở hữu ≥1 UC; tập UC phủ K1–K8;
UC-03 chỉ phủ K1/K3/K4. Cần chọn thêm UC cho toàn đồ án, không tuyên bố
UC-03 đã đáp ứng toàn bộ rubric.
Ngân hàng toàn đề tài còn có Writing Task 1 ≥10, Task 2 ≥10, Reading ≥6
(600–900 từ, 8–13 câu, ≥3 dạng), Listening ≥4 (400–700 từ, 8–10 câu).
Benchmark toàn đề tài còn có ≥30 Writing band 4–8, ≥10 hồ sơ placement,
≥40 câu Reading/Listening có đáp án người kiểm, dữ liệu tấn công;
≥5 tài khoản giả lập có lịch sử. Các mục này chưa làm, không bị xóa khỏi backlog.
Chi tiết UC khác giữ theo D1 khi chọn triển khai; không diễn giải scaffold này
thành đặc tả thay thế toàn bộ đề tài.

## Đề xuất, không phải yêu cầu gốc
Python 3.11+, Streamlit cho app.py, SQLite, JSONL trace, adapter OpenAI Chat
Completions; RAG engine sẽ chốt khi triển khai. Không bắt buộc LangGraph từ D1
(vốn là khuyến nghị); nếu không dùng phải giải thích workflow tương đương.
Part 1 chọn 5 câu, Part 3 chọn 5 (≥2 follow-up), Part 2 một cue card:
11 câu chính, mỗi câu chỉ nhận một answer được chấp nhận; không tăng vô hạn
vì retry. Tối đa 8 model calls/interaction và 2 lần sửa schema, timeout 30s/call,
retry transient tối đa 2; đạt giới hạn lưu lỗi có thể phục hồi, không bịa kết quả.
Các giới hạn là đề xuất v0.1, cần kiểm thực nghiệm trước khi chốt.

## Cập nhật sau yêu cầu “chạy hết”
Người dùng cho phép triển khai toàn bộ Phase 1, xác nhận nhóm 4 được giảng viên đồng ý.
Bảng phía trên ghi trạng thái lúc scaffold (lịch sử), không phải trạng thái cuối.
Trạng thái hiện tại: UI/state/SQLite/10 bộ bank/2 skills/tools/validators/eval runner/CI
đã được triển khai; kiểm offline đạt. Live key, official descriptors, teacher benchmark,
review ngân hàng bởi nhóm và CI remote còn chờ, xem validation.md.
Ngân hàng/benchmark các UC khác vẫn là backlog toàn đồ án, không ngầm xóa yêu cầu.
Python đã chốt 3.12 cho lockfile kiểm thực tế. Model calls tối đa 8 mỗi lần sinh output,
cho phép tối đa 2 lần sửa schema (tối đa 24 calls trước retry transport); SDK retry tối đa 2
cho lỗi transport/status transient. Không có tool shell hoặc quyền model ghi state tùy ý.

## Cập nhật nguồn và kiểm chứng live
Đã tích hợp hai PDF người dùng bổ sung: hồ sơ nguồn được publish theo yêu cầu; rubric
đầy đủ giữ runtime do điều khoản S4. Official PDF/native corpus, API key, native tool loop,
UI live và regression hành vi đã chạy. Không còn blocker key/mạng/descriptors.
Vẫn thiếu teacher text labels: 15 metadata/12 published performance bands nhưng 0 gold
text đủ điều kiện. Checklist Phase 1 và ranh giới với toàn rubric tại phase1_checklist.md.
