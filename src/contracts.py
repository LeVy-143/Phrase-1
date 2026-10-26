"""Contract v0.2. TypedDict JSON; runtime uses Pydantic plus domain validators."""
from typing import Literal, TypedDict, NotRequired

Part = Literal["part1", "part2", "part3"]
Status = Literal["active", "preparing", "awaiting_assessment", "completed", "failed"]
Criterion = Literal["fluency_coherence", "lexical_resource", "grammatical_range_accuracy", "pronunciation"]

class Turn(TypedDict):
    turn_id: str
    role: Literal["examiner", "candidate"]
    part: Part
    text: str

class AskedQuestion(TypedDict):
    question_id: str
    part: Part
    text: str
    refers_to_point_ids: list[str]

class CandidatePoint(TypedDict):
    point_id: str
    turn_id: str
    summary: str
    quote: str

class SessionState(TypedDict):
    schema_version: str
    session_id: str
    learner_id: str
    run_id: str
    revision: int
    mode: Literal["text"]
    status: Status
    part: Part
    bank_item_id: str
    asked_questions: list[AskedQuestion]
    candidate_points: list[CandidatePoint]
    turns: list[Turn]
    elapsed_seconds: int
    preparation_started_at: str | None
    preparation_deadline_at: str | None
    created_at: str
    updated_at: str

class Evidence(TypedDict):
    turn_id: str
    quote: str
    start_char: int
    end_char: int

class CriterionAssessment(TypedDict):
    criterion: Criterion
    status: Literal["assessed", "not_assessed", "insufficient_evidence"]
    band: float | None
    evidence: list[Evidence]
    descriptor_refs: list[str]
    comment: str

class SpeakingAssessment(TypedDict):
    schema_version: str
    assessment_id: str
    session_id: str
    run_id: str
    criteria: list[CriterionAssessment]
    overall_band: float | None
    overall_basis: Literal["three_text_criteria"]
    limitations: list[str]
    suggestions: list[str]
    disclaimer: str

class DescriptorChunk(TypedDict):
    chunk_id: str
    test_part: Literal["speaking"]
    criterion: Criterion
    band: float
    version: str
    source_url: str
    text: str
    license_note: str

class BankItem(TypedDict):
    item_id: str
    skill: Literal["speaking"]
    question_type: Literal["speaking_set"]
    topic: str
    target_band: float
    source: Literal["self_written", "llm_generated_verified", "open_license"]
    license: str
    author: str
    created_at: str
    part1_questions: list[str]
    cue_card: str
    cue_prompts: list[str]
    part3_questions: list[str]
    verification: NotRequired[dict[str, str]]

class AgentReply(TypedDict):
    state: SessionState
    examiner_message: str
    assessment: SpeakingAssessment | None

class ToolContext(TypedDict):
    learner_id: str
    session_id: str
    run_id: str

class TraceEvent(TypedDict):
    run_id: str
    session_id: str
    event_id: str
    timestamp: str
    event_type: Literal["node", "tool", "skill", "retrieval", "model", "error", "confirmation"]
    name: str
    input_refs: list[str]
    output_refs: list[str]
    duration_ms: int
    token_count: int | None
    estimated_cost: float | None
    currency: str | None
    error_code: str | None
