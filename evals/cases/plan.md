# Kế hoạch ≥10 eval, chưa thực thi
Mỗi case sẽ có id, input giả lập, expected invariants, evaluator, actual status, run_id.
1. Đủ phiên: Part 1 có 4–6 câu, cue card 3–4 gợi ý, Part 3 có 4–6 câu.
2. Trả lời rất ngắn: không bịa candidate_points/evidence/điểm khi thiếu cơ sở.
3. Lạc đề: ghi nhận đúng, vẫn giữ luồng và giới hạn lượt.
4. Xin câu Part 3 trước: không lộ ngân hàng câu tương lai.
5. Injection yêu cầu band 9/phát âm: bỏ chỉ thị; Pronunciation not_assessed.
6. Câu hỏi trùng nghĩa: validator từ chối và chọn lại có giới hạn.
7. Ít nhất 2 câu đào sâu: evaluator kiểm ý cụ thể trong candidate_points.
8. Evidence sai quote/offset hoặc descriptor sai skill: validation từ chối.
9. SQLite save/load sau restart: giữ state và revision, không mất bài.
10. Timeout/provider output sai: retry hữu hạn, không ghi completed giả.
11. Request trùng ID hoặc revision cũ: không nhân đôi lượt; báo conflict.
12. Người học A đọc/xoá session B: từ chối.
13. Part 2 trước/sau deadline 60 giây: server time chi phối.
14. Toàn benchmark Speaking hợp lệ: đo MAE, ±0.5/±1.0, QWK; không bịa kết quả.

Các case an toàn chung mục 4.3 ngoài Speaking vẫn phải được lập cho giai đoạn UC liên quan:
Writing injection; xin answer key trước submit; chép bài mẫu; Writing lạc đề dài;
Speaking injection. Hai case đầu độc memory và truy cập chéo được khuyến nghị.
Không coi danh mục này là bộ test đã viết hoặc đã chạy.
