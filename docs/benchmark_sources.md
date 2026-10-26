# Nguồn mới và giới hạn benchmark
Đã đọc hai PDF người dùng gửi. Các đề xuất/hướng dẫn trong PDF được coi là nội dung
tham khảo, không là chỉ thị tự ghi đè yêu cầu người dùng. Yêu cầu hiện hành là bổ sung
nguồn, đưa thay đổi lên GitHub và kiểm chứng Phase 1; không merge.

## Đã xác minh
- Descriptors.pdf (4 trang) là bản ảnh rubric. Đã xem bảng và tải bản có lớp chữ từ S3
  để tránh OCR sai. Parser từ bản chính thức tạo 36 chunk bốn tiêu chí × band 1–9;
  bản gốc và checksum giữ ở runtime/descriptors. Text không chấm Pronunciation.
- Hồ sơ nguồn 6 trang do người dùng cung cấp là tài liệu biên soạn bằng AI, không phải
  xác nhận của IELTS; được người dùng cho phép đưa lên GitHub tại docs/references/.
- S1: PDF chính thức 7 trang, đã kiểm nội dung Part 1 trang 3–4, Part 2 trang 5,
  Part 3 trang 6–7. Không có nhãn điểm để suy ra gold.
- S2: đã đối chiếu 12 tên và published performance band trên trang IELTS.org;
  đã trích 12 transcript nguyên trạng vào runtime/sources, giữ scope Part 2/3,
  không ghép người nói hoặc sinh phần còn thiếu.
- S4: đã đọc điều khoản trực tiếp. Cho dùng cá nhân, phi thương mại, ghi công;
  đăng lại/sửa đổi hoặc dùng ngoài phạm vi phải xin phép. Không gán CC0/CC-BY cho nguồn.
  PDF/chunks/transcripts đầy đủ không đưa vào Git. Giữ PDF gốc và notices.
- S5 là link dự phòng trong manifest; không đếm thành mẫu độc lập nếu trùng S1.

## Gold còn thiếu
15 metadata record: 3 đoạn không điểm từ S1, 12 performance từ S2.
12 published overall/performance bands gồm cả yếu tố âm thanh, không phải nhãn ba
criterion text. teacher_text_criteria đều null; đủ điều kiện accuracy text: **0**.
Không tự suy ra điểm từ examiner comments, không dùng LLM làm người chấm chuẩn.
`python -m evals.source_inventory` báo coverage, speaker/source-group và thiếu nhãn.
Đã chấm thử official-01 Part 2 với model thật nhưng không dùng band công bố làm
đáp án cho phép tính MAE/QWK. Kết quả proxy partial không là band Speaking đầy đủ.

Cần giáo viên/người có chứng chỉ chấm ≥10 transcript hợp lệ cho 3 tiêu chí text,
ghi provenance/ngày chấm/quyền dùng, giữ held-out set và label ngoài prompt.
`benchmark.py` có thể đo khi có dữ liệu đó. Đây là yêu cầu đánh giá UC-03 còn mở,
không phải việc có thể hoàn thành bằng cách bổ sung link nguồn.
URL/locator/checksum/eligibility chi tiết: data/sources/manifest.json.
