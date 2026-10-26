# IELTS Learning Agent — Phase 1, UC-03 text
Bản tham khảo cho **nhóm 4 người** (người dùng xác nhận giảng viên đã chấp thuận).
Đã triển khai UI, state machine, SQLite, ngân hàng 10 chủ đề, skill, tools, adapter
native tool calling, RAG index, validator, eval runner và cấu hình CI.
**Offline chạy được; live scoring và benchmark giáo viên chưa được xác minh.**
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

1. Kiểm điều khoản nguồn chính thức, tải PDF nếu được phép:
   `.venv/bin/python -m scripts.ingest_descriptors --download`.
2. Chunk thủ công theo **criterion × band** từ PDF chính thức, review nội dung;
   tạo JSON như [hướng dẫn RAG](data/descriptors/README.md), không tự bịa descriptors.
3. Import cục bộ: `.venv/bin/python -m scripts.ingest_descriptors --input /path/to/reviewed.json --permissions-reviewed`.
4. Kiểm native tool calling (lệnh này gọi API có phí):
   `.venv/bin/python -m scripts.check_provider`.
5. Chạy app, chọn Live và làm phiên mới. Không suy ra model có tool calling chỉ từ tên.

Hiện tải `ielts.org` bị proxy trả 403; cấu hình domain đã lưu draft, chưa chứng minh
đã áp dụng. Thiếu official chunks hoặc key thì Live báo lỗi, không dùng rubric giả thay thế.
RAG dùng hashing embeddings/ngram + sparse vector index trong bộ nhớ,
metadata filter trước cosine search; đây là thiết kế đơn giản, chất lượng retrieval chưa benchmark.
Tham khảo benchmark trong [evals](evals/README.md). Không lấy fixture làm điểm giáo viên.

## Cấu trúc và phân công
| Người | Phần đã có | Cần nhóm review/bổ sung |
|---|---|---|
| TV1 | app.py, tiến trình, timer, resume, kết quả và xoá dữ liệu | UX, tên thành viên |
| TV2 | examiner_agent, provider, tools, rag, 2 skill | Model thật, official descriptors, chất lượng câu hỏi/chấm |
| TV3 | storage, bank, 10 bộ Speaking, 5 learner giả lập trong UI | Review ngân hàng AI-generated, license, backup policy |
| TV4 | tests, evals, CI, docs, schema JSON | Benchmark giáo viên, live integration, CI trên GitHub, video/báo cáo |

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
