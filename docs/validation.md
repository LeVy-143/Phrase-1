# Kết quả thực thi — 2026-10-26
Môi trường: Python 3.12.14, Linux; requirements.lock là phiên bản dependencies
thực tế đã cài. Chạy từ /workspace/Phrase-1. Không có API key trong process khi kiểm tra.

## Kết quả hiện tại
- `python -m evals.run --all --label final-reference`: **25 passed, 0 failed/error/skipped**.
- Report: `runtime/evals/16e73cf5-5fe0-4cf1-b310-13f03668347e/report.json` và cases.csv/JUnit.
- Bao gồm **20 behavioral eval case** test_evals.py, 3 native-protocol unit tests,
  2 Streamlit AppTest (một case đi hết 11 lượt, ba phần và hoàn tất offline).
- `python -m scripts.smoke`: SQLite thật, 11 câu, completed, band=null;
  đồng hồ tiêm để vượt 60 giây trong smoke, UI vẫn dùng deadline thật.
- Trace mẫu thực tế ở docs/traces/offline-smoke.json, chỉ dữ liệu giả lập;
  không gọi model hoặc retrieval official, không phải trace thành công của live scoring.
- `python -m pip check`: không xung đột dependencies.
- Cài lặp từ requirements.lock: thành công, log runtime/install-repeat.log.
- `python -m compileall -q app.py src scripts evals`: thành công.
- Streamlit đã khởi động; local health endpoint trả `ok`; AppTest xác minh hành vi UI.
- `python -m scripts.purge`: chạy được; lần chạy này 0 session/trace quá hạn,
  không tuyên bố đây là bằng chứng purge dữ liệu hết hạn (chưa có fixture hết hạn).
- Git: tất cả file mới chưa stage/commit, không push. Runtime/venv/.env được ignore.

## Regression hành vi có thật
| Nhãn / run_id | Kết quả | Thay đổi |
|---|---|---|
| first-integrated / ec27dad8-537b-4d7c-8cfa-4aa11ddf5542 | 22 passed | Integration đầu |
| timer-precision-fix / 3a15db01-8cd5-4c1c-b2bf-3ff396ce2984 | 23 passed | Sửa precision deadline; thêm ca hồi quy |
| persistence-and-full-ui / f9340697-2a06-44c2-bde6-0de695733c04 | 24 passed | Lưu snapshot retrieval, đóng connection, UI full session |
| final-reference / 16e73cf5-5fe0-4cf1-b310-13f03668347e | 25 passed | Thêm kiểm sửa malformed output tối đa 2 lần |
Smoke đầu phát hiện lỗi ISO timestamp làm tròn microsecond khiến đúng 60 giây có thể
bị từ chối; sửa bằng so sánh datetime cùng precision, rồi smoke và regression pass.
Các run có số case khác nhau; không dùng tỉ lệ pass này làm bằng chứng tăng accuracy model.

## Chưa chạy / chưa có bằng chứng
- Live provider và native tool calling với codestral-2508: **unrun**, thiếu key an toàn.
  Native protocol chỉ mới được kiểm với mock, không chứng minh provider thật hỗ trợ.
- Official descriptors: download HTTPS bị proxy 403; chưa có corpus được review quyền.
  RAG retrieval hiện chỉ được kiểm bằng fixture SYNTHETIC, không là descriptor thật.
- Benchmark giáo viên ≥10 transcript: **unrun**, chưa có dataset hợp lệ.
  Chưa có MAE/QWK/±band, follow-up rate toàn benchmark hoặc chất lượng chấm thực tế.
- Không trùng nghĩa trên toàn tập và ≥80% phiên có ≥2 follow-up phù hợp:
  unit test kiểm grounding/cấu trúc; evaluator ngữ nghĩa đa phiên vẫn cần thực hiện.
- Regression chất lượng theo model/prompt/data: chưa chạy, không thay bằng regression hành vi.
- GitHub Actions: đã viết workflow, **chưa chạy remote** vì chưa commit/push.
- Ngân hàng AI-generated: validator và AI editorial review đã có; human review còn pending.

## Cấu hình cloud đã lưu, chưa áp dụng/publish được xác nhận
install_script, start_skill; biến MODEL_NAME/IELTS_DESCRIPTORS_PATH; yêu cầu secret
MISTRAL_API_KEY (không giá trị); domain ielts.org, www.ielts.org, api.mistral.ai.
Nền tảng dành riêng tên OPENAI_* nên dùng alias MISTRAL_API_KEY trong cloud;
app vẫn hỗ trợ OPENAI_API_KEY ở môi trường local.
Người dùng review/lưu trong environment settings, nhập key **mới** an toàn rồi publish
khi sẵn sàng. Lưu draft không chứng minh domain đã áp dụng hoặc live API chạy được.
Sau cập nhật, retry đúng bước bị chặn, chạy capability probe và benchmark hợp lệ.
Không gọi bản tham khảo này đạt toàn bộ rubric UC-03 khi các bước trên chưa xác minh.
