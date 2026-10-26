# IELTS Learning Agent — Phase 1, UC-03 text
Bản tham khảo cho **nhóm 4 người** (người dùng xác nhận giảng viên đã chấp thuận).
Đã triển khai UI, state machine, SQLite, ngân hàng 10 chủ đề, skill, tools, adapter
native tool calling, RAG index, validator, eval runner và cấu hình CI.
**Offline và luồng chấm live đã chạy; chưa có benchmark giáo viên đủ điều kiện đo accuracy.**
Người dùng đã yêu cầu tạo PR để review, không tự merge. Không có key trong repo.

## Cài và chạy offline
Dùng Python **3.12** (đã kiểm 3.12.14), từ thư mục repo:
```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock
.venv/bin/python -m pip check
.venv/bin/python -m streamlit run app.py --server.headless true --browser.gatherUsageStats false
```
Chọn offline → một trong 5 tài khoản giả lập → chủ đề → bắt đầu.
Trả lời 5 câu Part 1; đọc cue card, chuẩn bị đủ 60 giây rồi nhấn cập nhật;
trả lời một lượt dài Part 2 và 5 câu Part 3; nhấn hoàn tất.
Mở lại app và chọn phiên đã lưu để tiếp tục. Offline lưu dữ liệu thật vào SQLite
nhưng kết quả có band=null và ghi rõ không có model chấm; không dùng để báo độ chính xác.
Ứng dụng chỉ là demo local với tài khoản giả lập, chưa có đăng nhập production.
Không đưa app này lên Internet cho người dùng thật nếu chưa bổ sung auth.

## Kiểm tra một lệnh
```bash
.venv/bin/python -m evals.run --all --label local
.venv/bin/python -m scripts.smoke
```
Eval ghi `runtime/evals/<run_id>/report.json`, `cases.csv`, JUnit; giữ exit code lỗi.
Muốn kiểm chứng cả model thật và UI: thêm `--live` (có phí API).
Smoke chạy trọn 11 câu qua agent và SQLite với **đồng hồ kiểm thử được tiêm**,
không bỏ chờ 60 giây trong UI thật. `--real-time` dùng thời gian thật.
[Validation](docs/validation.md) ghi kết quả thực và giới hạn.
CI trong `.github/workflows/ci.yml` chạy offline; trạng thái chạy GitHub cần xem trong PR; kết quả local được ghi riêng.

## Live: cấu hình và điều kiện bắt buộc
App đọc process environment, không tự nạp `.env`. `.env.example` chỉ là mẫu tên biến.
Đặt key bằng secret manager hoặc nhập kín vào shell, không dán key vào lệnh/file Git:
```bash
read -rsp 'API key: ' OPENAI_API_KEY; export OPENAI_API_KEY; echo
export MODEL_NAME=codestral-2508
export OPENAI_BASE_URL=https://api.mistral.ai/v1
export IELTS_DESCRIPTORS_PATH=runtime/descriptors/chunks.json
```
Trong cloud, `OPENAI_*` là tên dành riêng của nền tảng; dùng secret **MISTRAL_API_KEY**
(app hỗ trợ alias này, ưu tiên OPENAI_API_KEY nếu cả hai cùng có).
Key từng lộ trong chat cần thu hồi/thay mới, không tái dùng.
Chỉ gửi key tới endpoint HTTPS bạn tin tưởng. `.env.example` không chứa key.

1. Đọc [nguồn và điều khoản](docs/benchmark_sources.md). Với việc học cá nhân phi thương mại
   có ghi công đã được người dùng yêu cầu, chuẩn bị rubric **ngoài Git**:
   ```bash
   .venv/bin/python -m scripts.ingest_descriptors --download
   .venv/bin/python -m scripts.extract_descriptors --personal-noncommercial
   ```
   Parser hỗ trợ PDF chính thức có lớp chữ 4 trang, không đoán nội dung từ scan;
   36 chunk criterion × band 1–9 (text chỉ dùng 3 tiêu chí). Giữ nguyên PDF gốc/notice.
2. Kiểm native protocol: `.venv/bin/python -m scripts.check_provider`.
3. Chạy kiểm chứng đầy đủ (gọi API có phí):
   ```bash
   .venv/bin/python -m evals.run --all --live --label phase1
   ```
   Bao gồm tests offline, 3 ca live (normal/short/injection), UI live đi hết 11 câu.
   Đồng hồ Part 2 được tiêm trong test; UI thông thường vẫn chờ đủ 60 giây.
4. Chạy app, chọn Live. `codestral-2508` đã kiểm native tool roundtrip và chấm có RAG.
   Controller buộc chạy các prerequisite tool theo thứ tự rồi mới nhận JSON chấm;
   không tuyên bố model tự chọn tool luôn đúng. Offset evidence do code tính từ quote.

[Hồ sơ nguồn PDF người dùng cung cấp](docs/references/IELTS_Speaking_Part_1_2_3_Nguon_Cho_Codex.pdf)
và [manifest](data/sources/manifest.json) có trong repo; **PDF rubric đầy đủ và transcript
nguồn chỉ ở runtime/** do điều khoản hạn chế đăng lại. Nguồn đã tải được, không còn blocker mạng.
12 excerpt có published performance band; **không có nhãn riêng ba tiêu chí text**,
nên số mẫu accuracy đủ điều kiện hiện là **0**. Không dùng điểm LLM hay band video để lấp chỗ trống.
Chấm một excerpt mà không sinh phần thiếu:
```bash
.venv/bin/python -m scripts.import_official_samples --personal-noncommercial
.venv/bin/python -m scripts.assess_transcript --input runtime/sources/official-01.json --usage-permitted
```
Lệnh chấm trên gọi API có phí, input không có gold/examiner comments; output nêu scope Part.
Xem [checklist Phase 1](docs/phase1_checklist.md), [kết quả thật](docs/validation.md)
và [regression native tool policy](docs/live_regression.md). Chưa đạt/không đo được accuracy
không được thay bằng số lượng test pass.

## Cấu trúc và phân công
| Người | Phần đã có | Cần nhóm review/bổ sung |
|---|---|---|
| TV1 | app.py, tiến trình, timer, resume, kết quả và xoá dữ liệu | UX, tên thành viên |
| TV2 | examiner_agent, provider, tools, rag, 2 skill | Review chất lượng chấm; bổ sung nhãn giáo viên |
| TV3 | storage, bank, 10 bộ Speaking, 5 learner giả lập trong UI | Review ngân hàng AI-generated, license, backup policy |
| TV4 | tests, evals, CI, docs, schema JSON | Benchmark giáo viên, tên nhóm/chủ UC, video/báo cáo |

[Contract](docs/contracts.md) · [Python types](src/contracts.py) · [JSON schemas](schemas/)
· [Yêu cầu gốc / đề xuất](docs/requirements.md) · [Bàn giao](docs/implementation.md)
· [Nguồn dữ liệu](docs/data_sources.md) · [Chính sách dữ liệu](docs/data_policy.md).

Mọi nơi có band phải hiển thị:
**Điểm ước lượng do AI chấm, chỉ dùng để luyện tập, không thay thế điểm thi chính thức**.
Text không chấm Pronunciation; overall ba tiêu chí chỉ là proxy luyện tập.

## Minh bạch AI và phạm vi
Code và câu hỏi được tạo với hỗ trợ Codex; ngân hàng có xác minh cấu trúc và review
bởi AI, **chưa có review của giáo viên/nhóm**. Không dùng đề Cambridge hay dịch vụ chấm IELTS sẵn.
Fixture kiểm thử là dữ liệu giả lập, không phải ground truth hay điểm chuẩn.
UC-03 phủ K1/K3/K4; Phase 1 này không thay thế toàn bộ các UC và rubric K1–K8.
