import copy
import json
from pathlib import Path
import pytest
from evals.source_inventory import inventory
from src.errors import ValidationError
from src.examiner_agent import context_for


def test_source_catalog_is_not_fake_gold():
    data=json.loads((Path(__file__).resolve().parents[1]/'data/sources/manifest.json').read_text())
    report=inventory(data)
    assert report['sample_count']==15
    assert set(report['part_counts'])=={'1','2','3'}
    assert report['published_performance_labels']==12
    assert report['eligible_text_accuracy_samples']==0
    assert not report['minimum_ten_text_gold_met']
    assert all(s['teacher_text_criteria'] is None for s in data['samples'])


def test_published_overall_cannot_be_laundered_into_criteria():
    sample={'sample_id':'test-only','part':2,'source_group':'test','speaker_id':'test',
      'source_url':'https://example.invalid','transcript_ref':'local-test','license_status':'permission_confirmed',
      'reference_source':'published_performance_only','published_performance_band':8,
      'teacher_text_criteria':dict.fromkeys(['fluency_coherence','lexical_resource','grammatical_range_accuracy'],8)}
    assert inventory({'samples':[sample]})['eligible_text_accuracy_samples']==0


def test_partial_transcript_preserves_scope_and_content(agent):
    turns=[{'role':'examiner','part':'part2','text':'Describe a journey.'},
           {'role':'candidate','part':'part2','text':'I took a bus to a community workshop.'}]
    reply=agent.import_transcript(learner_id='demo-1',turns=turns,part_scope=['part2'],source_sample_id='synthetic-unit-fixture')
    state=reply['state']
    assert len(state['turns'])==2 and state['part_scope']==['part2']
    assert [{k:t[k] for k in ['role','part','text']} for t in state['turns']]==turns
    assert len(state['asked_questions'])==1
    result=agent.assess_session(context=context_for(state),expected_revision=state['revision'])['assessment']
    assert result['overall_band'] is None
    assert any('part2' in limitation for limitation in result['limitations'])


def test_partial_transcript_rejects_scope_mismatch(agent):
    with pytest.raises(ValidationError):
        agent.import_transcript(learner_id='demo-1',turns=[{'role':'candidate','part':'part1','text':'A fictional answer'}],part_scope=['part3'],source_sample_id='synthetic-unit-fixture')


def test_importer_does_not_leak_comments_or_published_band():
    from scripts.import_official_samples import extract_panels
    html='<div class="video-player__transcript-panel"><div><p><strong>Examiner:</strong> A test question?</p><p><strong>Fictional:</strong> An unchanged fictional answer.</p></div></div><p>Examiner comments: Band 9</p>'
    metadata={'samples':[{'source_id':'S2','sample_id':'synthetic-source-fixture','speaker_id':'public-source-fictional','part':2,'published_performance_band':9}]}
    payload=extract_panels(html,metadata)[0]
    assert set(payload)=={'sample_id','part_scope','turns'}
    assert len(payload['turns'])==2
    assert payload['turns'][1]['text']=='An unchanged fictional answer.'
    assert 'Band 9' not in json.dumps(payload)


def test_scan_like_pdf_rejected_instead_of_invented_chunks(tmp_path):
    from pypdf import PdfWriter
    from scripts.extract_descriptors import extract
    writer=PdfWriter()
    for _ in range(4):writer.add_blank_page(width=960,height=540)
    path=tmp_path/'synthetic-blank.pdf'
    with path.open('wb') as file:writer.write(file)
    with pytest.raises(ValueError,match='text layer|headers'):
        extract(path)
