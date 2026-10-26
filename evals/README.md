# Evaluation
```bash
.venv/bin/python -m evals.run --all --label local
```
Chạy toàn bộ behavioral/UI/protocol tests; không có --all thì chỉ behavioral UC-03.
Kết quả hiện hành ở runtime/evals/<run_id>/; không commit DB/trace người thật.
Bộ test có ≥10 case thực: đúng thứ tự, đáp ngắn/lạc đề, xin câu trước, injection,
no duplicate, follow-up grounding, persistence/ownership, idempotency, timer,
privacy/delete, rounding, stop condition, evidence/refs, model lỗi, thiếu RAG,
ngân hàng metadata, retrieval filter, bounded repair; UI đi hết 3 phần.
Unit fixtures về model/descriptors được gắn nhãn synthetic, không chứng minh model live.

## Benchmark Speaking — chưa có dữ liệu hợp lệ
Cần ≥10 transcript giáo viên chấm, không dùng LLM gán ground truth.
File gold JSON array: id, transcript_ref, reference_source (teacher_scored hoặc
public_examiner_sample), source_url hoặc teacher_name+scored_at, license,
criteria {fluency_coherence, lexical_resource, grammatical_range_accuracy}.
Dùng transcript giả lập được giáo viên chấm, hoặc consent và lưu dữ liệu thật ngoài repo.
Predictions JSON array: id, run_id, model, prompt_version, data_version,
descriptor_version, criteria cùng 3 trường (điểm model thật, có trace tương ứng).
Không gửi teacher scores vào prompt model. Chấm qua Live trước, xuất điểm đã validate;
đã có scripts.assess_transcript cho input theo scope Part, không tự sinh phần thiếu.
```bash
.venv/bin/python -m evals.run --all --gold /private/gold.json --predictions /private/predictions.json --label live-benchmark
```
Tính MAE tổng/từng tiêu chí, tỉ lệ ±0.5/±1.0, QWK; overall do code từ 3 tiêu chí text.
Thiếu dữ liệu báo unrun; dữ liệu không hợp lệ/thấp ngưỡng ≥80% trong ±1 band báo lỗi.
Không cung cấp gold giả để làm lệnh pass. Chi phí/token/latency thật lấy từ trace;
chi phí không có giá đã xác minh để null. Cần evaluator ngữ nghĩa riêng để xác nhận
không trùng nghĩa và chất lượng follow-up ở nhiều phiên (≥80%), không suy ra từ 1 test.

## Regression
docs/validation.md ghi các lần chạy thật và bản sửa timer. Đây là regression hành vi;
đã có live regression native tool policy tại docs/live_regression.md; chưa có so sánh accuracy
model vì thiếu teacher gold, dù key và official descriptors đã hoạt động.
Yêu cầu regression chất lượng theo đề tài vẫn còn, không thay bằng số liệu offline.

## Live kiểm chứng (có phí)
`python -m evals.run --all --live` chạy offline tests rồi 3 scenario model thật và full UI.
Raw source transcripts và rubric không vào Git. docs/evidence và docs/traces chứa kết quả/refs
được phép chia sẻ, không có key hay raw transcript người thật.
`python -m evals.source_inventory` kiểm số mẫu đủ nhãn, hiện là 0, không có gold giả.
