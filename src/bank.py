"""Question bank with explicit provenance and structural verification."""
import json
from pathlib import Path
from .errors import ValidationError, NotFound

LICENSES = {'CC0-1.0', 'CC-BY-4.0', 'CC-BY-SA-4.0'}

def load_bank(bank_dir: Path):
    items = []
    for path in sorted(Path(bank_dir).glob('*.json')):
        entries = json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(entries, list):
            entries = [entries]
        for item in entries:
            required = {'item_id','skill','question_type','topic','target_band','source','license','author','created_at','part1_questions','cue_card','cue_prompts','part3_questions'}
            if not required <= item.keys() or item['license'] not in LICENSES or not item['source']:
                raise ValidationError(f'Invalid bank metadata: {path.name}')
            if item['skill'] != 'speaking' or item['question_type'] != 'speaking_set':
                raise ValidationError('Only speaking sets are supported')
            if item['source'] not in {'self_written','llm_generated_verified','open_license'}:
                raise ValidationError('Unknown provenance')
            if not all(isinstance(item[k], str) and item[k].strip() for k in ['item_id','topic','author','created_at','cue_card']):
                raise ValidationError('Missing bank metadata value')
            if not isinstance(item['target_band'], (int,float)) or not 0 <= item['target_band'] <= 9:
                raise ValidationError('Invalid target band')
            for key, low, high in [('part1_questions',4,6),('part3_questions',4,6),('cue_prompts',3,4)]:
                values = item[key]
                if not isinstance(values,list) or not low <= len(values) <= high or not all(isinstance(v,str) and v.strip() for v in values):
                    raise ValidationError(f'Invalid {key}')
                if len(set(v.casefold().strip() for v in values)) != len(values):
                    raise ValidationError('Duplicate bank questions')
            if item['source'] == 'llm_generated_verified' and not item.get('verification'):
                raise ValidationError('Generated items need a verification record')
            items.append(item)
    if not items or len({i['item_id'] for i in items}) != len(items):
        raise ValidationError('Empty bank or duplicate item IDs')
    return items

def bank_search(items, *, topic=None):
    return [i['item_id'] for i in items if topic is None or topic.casefold() in i['topic'].casefold()]

def bank_get_item(items, item_id):
    for item in items:
        if item['item_id'] == item_id:
            return item
    raise NotFound('Unknown bank item')
