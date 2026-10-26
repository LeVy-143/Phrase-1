"""Locally import public official excerpts, preserving Parts and excluding labels.
Not an accuracy dataset: source performance bands are metadata only.
"""
import argparse
from html.parser import HTMLParser
import json
import re
from pathlib import Path
import urllib.request

URL='https://ielts.org/organisations/ielts-for-organisations/understanding-ielts-scoring/resources-for-setting-your-ielts-scores'

class Paragraphs(HTMLParser):
    def __init__(self):super().__init__();self.active=False;self.current=[];self.paragraphs=[]
    def handle_starttag(self,tag,attrs):
        if tag=='p':self.active=True;self.current=[]
    def handle_data(self,data):
        if self.active:self.current.append(data)
    def handle_endtag(self,tag):
        if tag=='p' and self.active:
            self.paragraphs.append(''.join(self.current).strip());self.active=False

def extract_panels(html, metadata):
    panels=re.findall(r'<div class="video-player__transcript-panel"><div>(.*?)</div></div>',html,re.S)
    samples=[s for s in metadata['samples'] if s['source_id']=='S2']
    if len(panels)!=len(samples):raise ValueError('Source layout/sample count changed; review before import')
    output=[]
    for panel,sample in zip(panels,samples):
        parser=Paragraphs();parser.feed(panel);turns=[]
        for paragraph in parser.paragraphs:
            label=re.match(r'^([^:]{1,40}):\s*(.*)',paragraph,re.S)
            if label:
                speaker,text=label.groups()
                if speaker.strip().casefold() in {'examiner','interviewer'}:role='examiner'
                elif speaker.strip().casefold()==sample['speaker_id'].removeprefix('public-source-'):role='candidate'
                else:raise ValueError('Unknown speaker label; refusing to infer turns')
                turns.append({'role':role,'part':f'part{sample["part"]}','text':text})
            elif paragraph:
                if not turns:raise ValueError('Unattributed content before first speaker')
                turns[-1]['text']+='\n'+paragraph
        if not any(t['role']=='candidate' and t['text'].strip() for t in turns):raise ValueError('No candidate text')
        output.append({'sample_id':sample['sample_id'],'part_scope':[f'part{sample["part"]}'],'turns':turns})
    return output

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--html',type=Path,help='Previously downloaded official source HTML; otherwise download official URL')
    p.add_argument('--personal-noncommercial',action='store_true',required=True)
    args=p.parse_args()
    if args.html:html=args.html.read_text()
    else:
        with urllib.request.urlopen(URL,timeout=30) as response:html=response.read().decode('utf-8')
    metadata=json.loads(Path('data/sources/manifest.json').read_text())
    samples=extract_panels(html,metadata)
    root=Path('runtime/sources');root.mkdir(parents=True,exist_ok=True)
    for sample in samples:(root/(sample['sample_id']+'.json')).write_text(json.dumps(sample,ensure_ascii=False,indent=2))
    print(json.dumps({'local_excerpts':len(samples),'output':str(root),'gold_labels_in_model_input':False,'accuracy_eligible':0}))
if __name__=='__main__':main()
