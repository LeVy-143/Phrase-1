# Checklist Phase 1 — nhóm 4 người
Nguồn Phase 1: ảnh người dùng gửi, không suy từ toàn bộ rubric của cả đồ án.
Ngoại lệ nhóm 4 người đã được người dùng xác nhận là giảng viên chấp thuận.

| Yêu cầu Phase 1 | Bằng chứng | Trạng thái |
|---|---|---|
| Đề tài/use case/người sở hữu và nhóm | IELTS Learning Agent; UC-03; bảng team.md | Vai trò có, tên/owner chính thức chờ nhóm cung cấp |
| Repo, codebase app và agent | app.py; src/examiner_agent.py và src/provider.py | Có |
| CI | .github/workflows/ci.yml; link checks ở PR | Bản trước CI xanh; bản bổ sung phải xem check commit mới |
| Agent loop ≥2 tool | live trace có retrieve_descriptors và save_attempt; vòng native model→tool→model | Đã chạy thật |
| ≥1 skill | speaking-examiner + rubric-verifier; skill events trong trace | Có hai, đã gọi |
| Log từng bước | docs/traces/live-speaking.json, run/node/tool/model/retrieval refs | Đã chạy, không raw transcript/key |
| Một UC từ app tới agent | scripts/live_ui_check, docs/evidence/live-ui.json | UI đủ 11 câu, RAG chính thức, SQLite thật, model thật |
| ≥10 eval case | tests/test_evals.py ≥20 case; tổng offline mới 34; eval runner JSON/CSV/JUnit | Đã chạy, không dùng test count thay accuracy |

## Các tiêu chí UC-03 / cả đồ án vẫn phải phân biệt
- Text không chấm phát âm; code tính band, evidence/refs được validate. Đã kiểm live.
- Part 1/3 chọn 5 câu, cue 4 gợi ý, Part 2 60 giây server. Có tests cho deadline/resume.
- Hai follow-up có point refs; duplicate lexical guard có test. Chưa có evaluator ngữ nghĩa
  đủ rộng để chứng minh không có câu trùng nghĩa hoặc tỷ lệ ≥80% trên nhiều phiên độc lập.
- Chưa có ≥10 gold text phù hợp; chưa đo được accuracy/QWK/MAE hay ngưỡng UC-03 ≥80%.
- Chưa có giá token được kiểm chứng để tính chi phí USD; trace ghi token/latency thật,
  estimated_cost=null. Không tạo số chi phí giả.
- 5 attack case chung của toàn đồ án gồm các UC Writing/answer-key chưa triển khai;
  các case ngoài UC-03 giữ trong backlog, không khai báo pass.
- Bộ ngân hàng Writing/Reading/Listening, các UC khác/K1–K8, báo cáo/video và rubric
  toàn đồ án không tự trở thành yêu cầu triển khai hết trong bootstrap Phase 1 này.

Không coi tài liệu nguồn là benchmark giáo viên. Không nói đã đăng ký nhóm lên hệ thống
của trường; repo chỉ cung cấp bảng để nhóm điền/nộp.
