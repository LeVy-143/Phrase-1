# Chính sách dữ liệu tham khảo
MVP chỉ chấp nhận demo-1..demo-5, UI ghi rõ giả lập; chưa có auth production.
SQLite chứa transcript, state, kết quả, request idempotency và retrieval snapshot
trong runtime/ (gitignored). Trace ở SQLite chỉ chứa mã tham chiếu/metrics, không raw
candidate content, prompt hoặc key. Xoá learner cascade xoá sessions/results/requests/
retrievals/traces; UI có xác nhận trước khi xoá.

Đề xuất retention: session/memory 30 ngày kể từ updated_at, trace 7 ngày.
`python -m scripts.purge` thực hiện xoá các mục quá hạn; chưa có scheduler,
người vận hành phải cấu hình chạy hằng ngày. Không có memory dài hạn ngoài session.
File export smoke dùng dữ liệu giả lập và không tự bị SQLite cascade xoá; không bật
export này cho dữ liệu thật. Cần policy backup/export nếu triển khai production.

Nếu dùng người thật: cần consent văn bản, scan ngoài repo, chỉ mã consent được lưu;
không commit transcript/audio/bài làm/PII. Audio không thuộc MVP; mở rộng STT phải xoá
sau chuyển transcript trừ khi có đồng ý giữ. Memory tương lai phải có evidence và owner.
Key chỉ ở process environment/secret manager, không log. Thu hồi key từng lộ trong chat.
