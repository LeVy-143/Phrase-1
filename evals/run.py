"""One-command behavioral evaluation. Preserves pytest's exit status."""
import argparse
from datetime import datetime,timezone
import json
import csv
from pathlib import Path
import subprocess
import sys
import uuid
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--all',action='store_true',help='Run all offline behavioral and UI evaluations')
    p.add_argument('--label',default='current')
    p.add_argument('--gold',type=Path)
    p.add_argument('--predictions',type=Path)
    args=p.parse_args()
    run_id=str(uuid.uuid4());out=ROOT/'runtime/evals'/run_id;out.mkdir(parents=True)
    completed=subprocess.run([sys.executable,'-m','pytest','-q','tests' if args.all else 'tests/test_evals.py',f'--junitxml={out / "junit.xml"}'],cwd=ROOT)
    tree=ET.parse(out/'junit.xml')
    cases=[]
    for case in tree.findall('.//testcase'):
        status='failed' if case.find('failure') is not None else 'error' if case.find('error') is not None else 'skipped' if case.find('skipped') is not None else 'passed'
        cases.append({'id':case.attrib.get('classname','')+'::'+case.attrib['name'],'status':status,'seconds':float(case.attrib.get('time',0))})
    benchmark={'status':'unrun','reason':'No legitimate teacher-scored gold and predictions supplied; offline tests are not accuracy benchmarks.'}
    exit_code=completed.returncode
    if bool(args.gold)!=bool(args.predictions):
        p.error('--gold and --predictions must be provided together')
    if args.gold:
        try:
            from .benchmark import measure
            benchmark={'status':'completed','metrics':measure(args.gold,args.predictions)}
            if not benchmark['metrics']['uc03_accuracy_threshold_met']:
                exit_code=1
        except Exception as exc:
            benchmark={'status':'failed','reason':type(exc).__name__+': '+str(exc)}
            exit_code=1
    report={'run_id':run_id,'label':args.label,'timestamp':datetime.now(timezone.utc).isoformat(),
      'mode':'offline-behavioral','model':'none; providers in tests are explicitly synthetic fixtures',
      'prompt_version':'speaking-v1','data_version':'bank-v1','descriptor_version':'synthetic-test-only in retrieval tests',
      'counts':{s:sum(c['status']==s for c in cases) for s in ('passed','failed','error','skipped')},
      'cases':cases,'benchmark':benchmark,'exit_code':exit_code}
    (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    with (out/'cases.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=['id','status','seconds']);writer.writeheader();writer.writerows(cases)
    print(json.dumps({'report':str(out/'report.json'),'counts':report['counts'],'benchmark':benchmark},ensure_ascii=False))
    return exit_code
if __name__=='__main__':
    sys.exit(main())
