# Kiến trúc tham khảo
```mermaid
flowchart TD
    UI[TV1: Streamlit app] --> Controller[TV2: session controller]
    Controller --> Bank[TV3: licensed Speaking bank]
    Controller --> DB[(TV3: SQLite checkpoints / results / traces)]
    Controller --> Mode{Assessment mode}
    Mode -->|offline| Null[No model score / bands null]
    Mode -->|live| Provider[OpenAI-compatible native tool loop]
    Provider --> Retrieval[retrieve_descriptors]
    Retrieval --> Index[Hash embeddings / sparse index / metadata filter]
    Index --> Official[Reviewed official chunks in runtime]
    Provider --> Checkpoint[save_attempt: trusted SQLite checkpoint]
    Checkpoint --> DB
    Provider --> Validate[rubric-verifier + compute_band in code]
    Validate --> DB
    Null --> DB
    Eval[TV4: tests / eval runner / CI] --> UI
    Eval --> Controller
```
Điều phối câu hỏi/phần/thời gian bằng code để model không tự nhảy part.
Model chịu trách nhiệm bản chấm live có tool calling; follow-up hiện dùng template
tham chiếu quote có thật. Hai skill là speaking-examiner và rubric-verifier,
không có multi-agent/MCP trong UC-03 này. Các UC K6 thuộc backlog toàn đồ án.
