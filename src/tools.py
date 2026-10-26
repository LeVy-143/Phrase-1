"""Code-owned scoring and evidence checks. No model can override these rules."""
from decimal import Decimal, ROUND_HALF_UP
import math
from pydantic import TypeAdapter, ValidationError as SchemaError
from .contracts import SpeakingAssessment
from .errors import OutputValidationError

CRITERIA = ('fluency_coherence','lexical_resource','grammatical_range_accuracy','pronunciation')
DISCLAIMER = 'Điểm ước lượng do AI chấm, chỉ dùng để luyện tập, không thay thế điểm thi chính thức'

def compute_band(criteria):
    if criteria.get('pronunciation') is not None:
        raise OutputValidationError('Pronunciation cannot be assessed in text mode')
    values = [criteria.get(c) for c in CRITERIA[:3]]
    if any(v is None for v in values):
        return None
    if not all(type(v) in (int,float) and math.isfinite(v) and 0 <= v <= 9 and v*2 == int(v*2) for v in values):
        raise OutputValidationError('Invalid criterion band')
    average = sum(Decimal(str(v)) for v in values) / 3
    return float((average * 2).quantize(Decimal('1'), rounding=ROUND_HALF_UP) / 2)

def save_attempt(storage, state, *, expected_revision, context):
    return storage.save_session(state, expected_revision=expected_revision, context=context)

def validate_assessment(assessment, *, state, retrieved):
    try:
        TypeAdapter(SpeakingAssessment).validate_python(assessment, strict=True)
        if assessment['session_id'] != state['session_id'] or assessment['run_id'] != state['run_id']:
            raise ValueError('Context mismatch')
        criteria = assessment['criteria']
        if len(criteria) != 4 or {c['criterion'] for c in criteria} != set(CRITERIA):
            raise ValueError('Exactly four unique criteria required')
        turns = {t['turn_id']: t['text'] for t in state['turns'] if t['role']=='candidate'}
        refs = {c['chunk_id']: c for c in retrieved}
        for c in criteria:
            if c['criterion'] == 'pronunciation':
                if c['status'] != 'not_assessed' or c['band'] is not None or c['evidence'] or c['descriptor_refs']:
                    raise ValueError('No pronunciation score in text mode')
            elif c['status'] == 'assessed':
                band = c['band']
                if type(band) not in (int,float) or not math.isfinite(band) or not 0<=band<=9 or band*2 != int(band*2):
                    raise ValueError('Invalid band')
                if not c['evidence'] or not c['descriptor_refs']:
                    raise ValueError('Assessed criterion requires evidence and retrieval')
            elif c['status'] != 'insufficient_evidence' or c['band'] is not None:
                raise ValueError('Invalid assessment status')
            if not isinstance(c['comment'],str) or not c['comment'].strip():
                raise ValueError('Comment required')
            for e in c['evidence']:
                text = turns[e['turn_id']]
                a,b = e['start_char'],e['end_char']
                if type(a) is not int or type(b) is not int or not 0<=a<b<=len(text) or text[a:b] != e['quote']:
                    raise ValueError('Evidence does not match the candidate turn')
            for ref in c['descriptor_refs']:
                chunk = refs[ref]
                if chunk['test_part'] != 'speaking' or chunk['criterion'] != c['criterion']:
                    raise ValueError('Descriptor provenance mismatch')
        expected = compute_band({c['criterion']:c['band'] for c in criteria})
        if assessment['overall_band'] != expected or assessment['overall_basis'] != 'three_text_criteria':
            raise ValueError('Overall band must be calculated by code')
        if assessment['disclaimer'] != DISCLAIMER or not assessment['limitations']:
            raise ValueError('Disclaimer/limitations missing')
        if not isinstance(assessment['suggestions'],list) or not all(isinstance(s,str) for s in assessment['suggestions']):
            raise ValueError('Invalid suggestions')
    except (KeyError, TypeError, ValueError, SchemaError) as exc:
        raise OutputValidationError('Invalid assessment schema, evidence, references or band calculation') from None


def retrieve_descriptors(*, criterion, top_k, version=None, index=None):
    """Public tool adapter; live use requires an imported descriptor index."""
    if index is None:
        import os
        from .rag import DescriptorIndex
        index=DescriptorIndex(os.environ.get('IELTS_DESCRIPTORS_PATH','runtime/descriptors/chunks.json'))
    return index.retrieve(criterion=criterion,top_k=top_k,version=version)
