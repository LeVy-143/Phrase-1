"""Evaluate already-produced assessments against legitimate teacher references.
Does NOT invent a dataset or run a provider silently. Null/invalid scores fail.
"""
import json
import math
from pathlib import Path
from statistics import mean
from sklearn.metrics import cohen_kappa_score
from src.errors import ValidationError


def measure(gold_path, predictions_path):
    gold=json.loads(Path(gold_path).read_text())
    predictions=json.loads(Path(predictions_path).read_text())
    if len(gold)<10 or len({g['id'] for g in gold})!=len(gold):
        raise ValidationError('Need at least ten distinct teacher-scored Speaking transcripts')
    if len({p['id'] for p in predictions})!=len(predictions):
        raise ValidationError('Duplicate predictions')
    pred={p['id']:p for p in predictions}
    errors=[];expected=[];actual=[];by_criterion={c:[] for c in ('fluency_coherence','lexical_resource','grammatical_range_accuracy')}
    for g in gold:
        if g.get('reference_source') not in {'teacher_scored','public_examiner_sample'}:
            raise ValidationError('Ground truth must not come from an LLM')
        if not g.get('source_url') and not (g.get('teacher_name') and g.get('scored_at')):
            raise ValidationError('Reference provenance missing')
        if not g.get('license') or not g.get('transcript_ref'):
            raise ValidationError('Reference transcript/license missing')
        p=pred.get(g['id'])
        if p is None or not all(p.get(k) for k in ('run_id','model','prompt_version','data_version','descriptor_version')):
            raise ValidationError('Missing prediction or run provenance')
        from src.tools import compute_band
        g_band=compute_band({**g['criteria'],'pronunciation':None})
        p_band=compute_band({**p['criteria'],'pronunciation':None})
        if g_band is None or p_band is None:
            raise ValidationError('Missing reference or prediction text criterion score')
        errors.append(abs(g_band-p_band));expected.append(int(g_band*2));actual.append(int(p_band*2))
        for c in by_criterion:
            by_criterion[c].append(abs(g['criteria'][c]-p['criteria'][c]))
    qwk=cohen_kappa_score(expected,actual,labels=list(range(19)),weights='quadratic') if len(set(expected+actual))>1 else None
    if qwk is not None and not math.isfinite(qwk):
        qwk=None
    return {'count':len(errors),'mae':mean(errors),'within_0_5':mean(e<=.5 for e in errors),
      'within_1_0':mean(e<=1 for e in errors),'qwk':qwk,
      'mae_by_criterion':{c:mean(v) for c,v in by_criterion.items()},
      'uc03_accuracy_threshold_met':mean(e<=1 for e in errors)>=.8}
