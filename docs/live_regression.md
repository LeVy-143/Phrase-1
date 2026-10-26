# Regression native tool policy — chạy API thật
So sánh **hành vi harness**, không là benchmark chấm band. Model codestral-2508;
rubric version official-sha256:eab717cea3230c2bc9a0888655518bd8f4fd9ca7f8b2f4bdef231e42229cb6c9;
dataset fictional-live-smoke-v1. Ba case cố định: regular, short, injection.
Regular là development case; short/injection không được dùng để chỉnh prompt sau khi xem kết quả.
Không có ground truth band để tuyên bố tăng accuracy. Tập ba ca là nhỏ.

- Auto baseline: model thấy toàn bộ intended tool arguments qua required_tool_requests,
  dùng tool_choice=auto. 1/3 case hoàn tất: short; regular/injection fail OutputValidationError.
- Scheduled: controller yêu cầu lần lượt retrieve từng tiêu chí và checkpoint, rồi mới
  nhận JSON. 3/3 hoàn tất; mỗi case có 5 model calls.
- Hai phía cùng dữ liệu/contract/scoring/validator; sự khác biệt là chính sách bắt buộc
  prerequisite tools. Quote offsets do code tính nguyên văn, không đoán vị trí bằng LLM.
- Một vòng debug auto trước đó bỏ mất cả args checkpoint đã bị loại khỏi so sánh;
  kết quả dùng ở đây là vòng đã giữ nguyên intended arguments cho model.

| Case | Auto kết quả / latency | Scheduled kết quả / latency |
|---|---|---|
| regular | fail / 56.840s | pass / 27.650s |
| short | pass / 4.102s, 2 calls, 12,161 tokens | pass / 5.481s, 5 calls, 33,971 tokens |
| injection | fail / 47.538s | pass / 18.276s |

Scheduled dùng thêm token ở case ngắn để bảo đảm prerequisite workflow; không tuyên bố
rẻ hơn hoặc nhanh hơn trong mọi trường hợp. Tổng token scheduled regular 39,735;
injection 38,943. Cost USD để null vì chưa xác minh bảng giá, không gán số giả.
Normal và injection cùng trả proxy band 7.0 trong lần chạy này; Pronunciation null,
short overall null. Đây là điểm model thật cho dữ liệu giả lập, không là điểm chuẩn.
Mọi band là điểm ước lượng do AI chấm, chỉ dùng luyện tập, không thay thế điểm thi chính thức.
Kết quả/IDs thực: docs/evidence/live-auto.json và live-scheduled.json; trace có trong DB runtime.

Lệnh tái chạy có phí API:
`python -m scripts.live_regression --policy auto` (exit 1 khi case fail) và
`python -m scripts.live_regression --policy scheduled`.
Không retry vô hạn hoặc đổi expected output để khiến baseline hay cải tiến pass.
