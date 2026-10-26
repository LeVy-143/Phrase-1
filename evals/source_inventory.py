"""Report source coverage without laundering published bands into text gold."""
import argparse
import json
from collections import Counter
from pathlib import Path

TEXT_CRITERIA={'fluency_coherence','lexical_resource','grammatical_range_accuracy'}

def inventory(manifest):
    samples=manifest['samples'];eligible=[]
    for sample in samples:
        criteria=sample.get('teacher_text_criteria')
        scored=(sample.get('reference_source') in {'teacher_scored','public_examiner_sample'} and
                isinstance(criteria,dict) and set(criteria)==TEXT_CRITERIA and
                all(type(v) in (int,float) and 0<=v<=9 and v*2==int(v*2) for v in criteria.values()))
        permission=sample.get('license_status') in {'personal_noncommercial_only_no_redistribution','permission_confirmed','open_license'}
        provenance=bool(sample.get('source_url') or (sample.get('teacher_name') and sample.get('scored_at')))
        if scored and permission and provenance and sample.get('transcript_ref'):
            eligible.append(sample['sample_id'])
    return {'sample_count':len(samples),'part_counts':dict(Counter(str(s['part']) for s in samples)),
      'source_groups':len({s['source_group'] for s in samples}),
      'speaker_ids':len({s['speaker_id'] for s in samples if not s['speaker_id'].endswith('not-yet-resolved')}),
      'published_performance_labels':sum(s.get('published_performance_band') is not None for s in samples),
      'missing_text_criterion_labels':sum(s.get('teacher_text_criteria') is None for s in samples),
      'eligible_text_accuracy_samples':len(eligible),'eligible_sample_ids':eligible,
      'minimum_ten_text_gold_met':len(eligible)>=10,
      'warning':'Performance bands include audio pronunciation and are not text-only criterion ground truth.'}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--manifest',type=Path,default=Path('data/sources/manifest.json'));args=p.parse_args()
    print(json.dumps(inventory(json.loads(args.manifest.read_text())),ensure_ascii=False,indent=2))
if __name__=='__main__':main()
