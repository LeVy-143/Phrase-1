"""Extract criterion x band cells from the official 960x540 four-page PDF.
This is a format-specific parser: reject scans/changed layouts rather than guess.
Full rubric text is local-only. Original PDF and copyright notices are preserved.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path
from pypdf import PdfReader

SOURCE_URL='https://ielts.org/cdn/ielts-downloadable-assets/ielts-guidance-and-support/ielts-guides/ielts-speaking-band-descriptors.pdf'
TERMS_URL='https://ielts.org/legal/ielts-copyright-and-trade-mark-statement'
CRITERIA=('fluency_coherence','lexical_resource','grammatical_range_accuracy','pronunciation')
ROWS=[[(9,285,430),(8,170,285),(7,30,170)],[(6,265,440),(5,125,265),(4,0,125)],[(3,330,440),(2,185,330),(1,90,185)]]
COLUMNS=[(49,273),(273,496),(496,720),(720,951)]

def extract(path):
    path=Path(path);reader=PdfReader(path)
    if len(reader.pages)!=4:
        raise ValueError('Expected the official four-page descriptor PDF')
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    chunks=[]
    for page_no,(page,rows) in enumerate(zip(reader.pages[1:],ROWS),start=2):
        if abs(float(page.mediabox.width)-960)>1 or abs(float(page.mediabox.height)-540)>1:
            raise ValueError('Unexpected page dimensions; layout needs review')
        spans=[]
        def visitor(text,cm,tm,font,size):
            if text.strip():spans.append((float(tm[4]),float(tm[5]),text.strip()))
        page.extract_text(visitor_text=visitor)
        for header in ('Fluency and coherence','Lexical resource','Grammatical range and','Pronunciation'):
            if not any(header in s[2] for s in spans):
                raise ValueError('PDF has no supported text layer or headers differ')
        for band,low,high in rows:
            if not any(x<45 and text==str(band) and low<y<high for x,y,text in spans):
                raise ValueError(f'Band row {band} does not match expected layout')
            for criterion,(left,right) in zip(CRITERIA,COLUMNS):
                parts=sorted((s for s in spans if left<=s[0]<right and low<s[1]<high),key=lambda s:(-round(s[1],1),s[0]))
                text=' '.join(s[2].replace('\n',' ') for s in parts)
                text=re.sub(r'\s*-\s*','-',re.sub(r'\s+',' ',text)).strip()
                if len(text)<15:
                    raise ValueError(f'Empty/suspicious cell: {band}/{criterion}')
                chunks.append({'chunk_id':f'speaking-{digest[:12]}-{criterion}-b{band}','test_part':'speaking',
                  'criterion':criterion,'band':band,'version':'official-sha256:'+digest,'source_url':SOURCE_URL,
                  'text':text,'source_page':page_no,'source_sha256':digest,
                  'license_note':'Copyright IELTS Partners. Attributed personal/non-commercial local study only; no public redistribution. Original PDF retained with notices. Terms: '+TERMS_URL})
    if len(chunks)!=36:
        raise ValueError('Incomplete descriptor matrix')
    return chunks

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pdf',type=Path,default=Path('runtime/descriptors/speaking.pdf'))
    p.add_argument('--output',type=Path,default=Path('runtime/descriptors/chunks.json'))
    p.add_argument('--personal-noncommercial',action='store_true',required=True,
                   help='Acknowledge local attributed personal/non-commercial use; not redistribution permission')
    args=p.parse_args();chunks=extract(args.pdf)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(chunks,ensure_ascii=False,indent=2))
    print(json.dumps({'chunks':len(chunks),'criteria':4,'bands':'1-9','output':str(args.output)}))
if __name__=='__main__':main()
