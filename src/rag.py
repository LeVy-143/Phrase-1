"""Local embedding index: HashingVectorizer avoids an additional embedding API.
Chunks must be imported from reviewed, official speaking descriptors.
"""
import json
from pathlib import Path
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .errors import DescriptorUnavailable, ValidationError
from .tools import CRITERIA

class DescriptorIndex:
    def __init__(self, path):
        path = Path(path)
        if not path.exists():
            raise DescriptorUnavailable('Import official descriptors first: python -m scripts.ingest_descriptors --help')
        self.chunks = json.loads(path.read_text(encoding='utf-8'))
        if not self.chunks:
            raise DescriptorUnavailable('Descriptor index is empty')
        for chunk in self.chunks:
            required = {'chunk_id','test_part','criterion','band','version','source_url','text','license_note'}
            if not required <= chunk.keys() or chunk['test_part'] != 'speaking' or chunk['criterion'] not in CRITERIA:
                raise ValidationError('Invalid descriptor metadata')
            if not chunk['source_url'].startswith('https://') or not chunk['text'].strip() or not chunk['license_note'].strip():
                raise ValidationError('Descriptor source and permissions are required')
        if len({c['chunk_id'] for c in self.chunks}) != len(self.chunks):
            raise ValidationError('Duplicate descriptor chunk IDs')
        self.embedder = HashingVectorizer(n_features=4096, alternate_sign=False, norm='l2', ngram_range=(1,2))
        self.vectors = self.embedder.transform([c['text'] for c in self.chunks])

    def retrieve(self, *, criterion, top_k=4, version=None, query=''):
        if criterion not in CRITERIA or type(top_k) is not int or not 1<=top_k<=8:
            raise ValidationError('Invalid descriptor filter')
        indices = [i for i,c in enumerate(self.chunks) if c['criterion']==criterion and (version is None or c['version']==version)]
        if not indices:
            raise DescriptorUnavailable('No descriptors match the requested criterion/version')
        scores = cosine_similarity(self.embedder.transform([query or criterion.replace('_',' ')]), self.vectors[indices])[0]
        return [self.chunks[indices[i]] for i in sorted(range(len(indices)), key=lambda i: float(scores[i]), reverse=True)[:top_k]]
