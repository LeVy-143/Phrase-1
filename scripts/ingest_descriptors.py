"""Permission-aware import. Never publish third-party descriptor text in Git.
Input JSON is one reviewed criterion x band chunk per entry; see --help.
The PDF downloader deliberately does not guess table boundaries or invent chunks.
"""
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request
from urllib.parse import urlparse

OFFICIAL_URL = 'https://ielts.org/cdn/ielts-downloadable-assets/ielts-guidance-and-support/ielts-guides/ielts-speaking-band-descriptors.pdf'

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--download', action='store_true', help='Download official PDF to ignored runtime/; terms must be reviewed separately')
    p.add_argument('--input', type=Path, help='Reviewed JSON chunks: chunk_id,test_part,criterion,band,version,source_url,text,license_note')
    p.add_argument('--output', type=Path, default=Path('runtime/descriptors/chunks.json'))
    p.add_argument('--permissions-reviewed', action='store_true', help='Confirm permitted local use; does not imply redistribution rights')
    args=p.parse_args()
    if args.download:
        dest=Path('runtime/descriptors/speaking.pdf'); dest.parent.mkdir(parents=True,exist_ok=True)
        with urllib.request.urlopen(OFFICIAL_URL, timeout=30) as response:
            if urlparse(response.url).scheme != 'https' or urlparse(response.url).hostname not in {'ielts.org','www.ielts.org'}:
                p.error('Unexpected download destination')
            data=response.read(10_000_001)
        if len(data)>10_000_000 or not data.startswith(b'%PDF'):
            p.error('Not a valid PDF download')
        dest.write_bytes(data)
        print(json.dumps({'file':str(dest),'sha256':hashlib.sha256(data).hexdigest()}))
    if args.input:
        if not args.permissions_reviewed:
            p.error('Review source terms, then pass --permissions-reviewed for local import')
        from src.rag import DescriptorIndex
        index=DescriptorIndex(args.input)
        for criterion in ('fluency_coherence','lexical_resource','grammatical_range_accuracy'):
            bands={c['band'] for c in index.chunks if c['criterion']==criterion}
            if not set(range(1,10)) <= bands:
                p.error('Import must cover bands 1–9 for all three text criteria')
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(index.chunks,ensure_ascii=False,indent=2),encoding='utf-8')
        print(f'Imported {len(index.chunks)} reviewed chunks to {args.output}')
    if not args.download and not args.input:
        p.print_help()
if __name__=='__main__':
    main()
