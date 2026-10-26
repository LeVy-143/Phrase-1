# RAG official descriptors — dữ liệu runtime chưa có
Nguồn đề xuất: https://ielts.org/cdn/Guides/ielts-speaking-band-descriptors.pdf
Chưa tải được: proxy trả 403. Không lưu bản PDF hoặc nội dung descriptors trong Git.
Nhóm cần tự kiểm điều khoản trước khi tải/sử dụng; công khai không có nghĩa được tái phân phối.

`python -m scripts.ingest_descriptors --download` tải PDF bằng HTTPS có TLS verification;
kiểm magic PDF, giới hạn kích thước, ghi SHA256 để truy vết bản đã tải.
SHA256 này là provenance sau tải, không phải checksum do nhà phát hành cung cấp.
Chunking hiện **cần review thủ công**, không đoán cột bảng PDF hoặc cắt theo ký tự.
Tạo JSON array, mỗi phần tử gồm:
- chunk_id (duy nhất), test_part="speaking";
- criterion: fluency_coherence / lexical_resource / grammatical_range_accuracy;
- band: số nguyên 1..9; version: phiên bản/ngày của tài liệu;
- source_url: URL HTTPS chính thức; text: nguyên văn ô tiêu chí×band đã kiểm;
- license_note: ghi điều khoản/giới hạn sử dụng đã review.

Importer yêu cầu đủ band 1–9 cho 3 tiêu chí text và cờ --permissions-reviewed.
Có thể thêm Pronunciation để mở rộng sau, nhưng text không truy xuất để cho điểm phát âm.
Không có đoạn descriptor giả trong repo. Tests tự tạo fixture ghi rõ SYNTHETIC.
`DescriptorIndex` ingestion JSON → hashing embedding 4096 chiều/ngram → sparse vector store
trong bộ nhớ → metadata filter criterion/version/test_part → cosine retrieval.
Mỗi retrieval lưu chunk snapshot ở SQLite, refs trong trace; không gọi embedding API.
Cần benchmark retrieval trước khi kết luận chất lượng, có thể nâng cấp backend qua contract.
