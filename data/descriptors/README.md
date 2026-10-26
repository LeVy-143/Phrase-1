# Official Speaking descriptor runtime index
Đã tải được PDF có lớp chữ chính thức (4 trang), parser tạo 36 chunk theo criterion × band.
URL: https://ielts.org/cdn/ielts-downloadable-assets/ielts-guidance-and-support/ielts-guides/ielts-speaking-band-descriptors.pdf

```bash
.venv/bin/python -m scripts.ingest_descriptors --download
.venv/bin/python -m scripts.extract_descriptors --personal-noncommercial
```
Parser chỉ hỗ trợ layout 960×540 đã kiểm, xác nhận headers và band rows, reject scan/
layout lạ/ô thiếu thay vì bịa chữ. Tài liệu bản ảnh người dùng gửi đã được đối chiếu
bằng hình với nguồn chính thức có lớp chữ. Giữ nguyên PDF gốc và notices.
Chỉ dùng cá nhân phi thương mại có ghi công theo điều khoản S4; không tái phân phối
PDF/chunks lên GitHub. Corpus và originals ở runtime/descriptors/ (gitignored).
Metadata: chunk_id, test_part, criterion, band, version, source_url, source_page,
source_sha256, license_note. Checksum trong data/sources/manifest.json.
Text không chấm Pronunciation; 3 tiêu chí text có band 1–9 để retrieval.
Index dùng HashingVectorizer 4096 chiều/ngram, sparse store trong bộ nhớ, lọc criterion/
version trước cosine search; snapshot retrieval ở SQLite để audit. Chưa benchmark
chất lượng retrieval độc lập, không nhầm fixture tests với official descriptors.
Có thể import JSON đã review qua scripts.ingest_descriptors --input và cờ permissions.
Xem docs/benchmark_sources.md để phân biệt rubric, transcript và benchmark.
