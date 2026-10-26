# Bàn giao cho nhóm 4 người
Người dùng đã xác nhận giảng viên đồng ý nhóm 4. Không cần người thứ 5 cho Phase 1
này; các yêu cầu rubric khác vẫn giữ nguyên. Nhóm điền tên và người sở hữu UC khi nộp.

1. **TV3** review storage/bank: 10 bộ có provenance, schema SQLite, CAS/idempotency,
   restart và delete. Review bằng người nội dung AI-generated và quyết định license.
2. **TV2** review agent/tools/provider/rag và hai skills. Nạp official descriptors,
   cấu hình key mới qua secret manager, kiểm native tool calling với model thật;
   đo câu trùng nghĩa, follow-up và chất lượng chấm. Không dùng rubric giả để mở Live.
3. **TV1** review UI: luồng 3 phần, timer server, resume, errors, evidence/disclaimer.
   UX hiện là reference; thêm auth trước khi dùng người thật.
4. **TV4** review tests/eval/CI; chạy CI trên GitHub sau khi diff được duyệt;
   chuẩn bị ≥10 transcript được giáo viên chấm, chạy benchmark và regression chất lượng;
   viết báo cáo, phân công, video ≤15 phút, trace mẫu đúng loại chạy.

## Đã có và chưa thể tuyên bố hoàn tất
Offline app→agent→SQLite và ≥10 eval thực đã chạy; 2 skill có contract và được gọi,
traces lưu run/node/tool/retrieval/model/error với refs. CI đã cấu hình, chưa chạy remote.
Live adapter có native tool loop nhưng chưa chứng minh provider thật hỗ trợ.
RAG engine có, official corpus chưa có. Chưa có teacher benchmark nên chưa công bố
accuracy hay kết luận đạt U3 toàn bộ. Đây là blocker bên ngoài, không test pass thay thế.
Toàn đồ án còn cần UC phủ K1–K8 và các sản phẩm trong requirements.md.

## Duyệt Git
Người dùng đã yêu cầu tạo pull request, cho phép commit/push nhánh review. Không merge.
Không tự đưa key vào Git hay tự cấu hình secret giá trị trong GitHub.
