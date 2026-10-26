# CI
ci.yml: Python 3.12 → cài requirements.lock → pip check → eval offline → upload reports.
Không có secret và không gọi live API trên push/PR. Cấu hình đã tạo nhưng chưa chạy
trên GitHub vì chưa commit/push. Không có badge pass giả. Chạy live capability riêng
sau khi chủ repo cấu hình key an toàn và xác nhận chi phí.
