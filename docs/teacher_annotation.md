# Hoàn thiện gold text hợp lệ
Phần này cần người chấm đủ điều kiện, không thể thay bằng một lần gọi LLM.
1. Chuẩn bị ≥10 transcript có quyền dùng, ưu tiên nhóm tự đóng vai. Giữ một tập chưa
   dùng chỉnh prompt. Không đưa bài làm người thật/phiếu consent vào Git.
2. Người chấm đánh giá riêng fluency_coherence (nêu giới hạn text), lexical_resource,
   grammatical_range_accuracy; không bắt chấm Pronunciation khi không có audio.
3. Ghi người chấm, ngày, phạm vi text/audio, nguồn/quyền sử dụng. Điểm chưa chấm để null,
   không dùng published performance band để điền cả ba ô.
4. Gold JSON theo evals/README.md; predictions phải từ model thật có run/trace/version.
   Label/nhận xét người chấm tuyệt đối không đưa vào input model đang eval.
5. Chạy `python -m evals.run --all --gold /private/gold.json --predictions /private/predictions.json`;
   chỉ khi ≥10 mẫu hợp lệ mới báo MAE, ±band, QWK và ngưỡng UC-03. Không bỏ mẫu khó để pass.
