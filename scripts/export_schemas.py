"""Export JSON schemas from the shared Python contract types."""
import json
from pathlib import Path
from pydantic import TypeAdapter
from src.contracts import SessionState,SpeakingAssessment,BankItem
if __name__=='__main__':
    dest=Path('schemas');dest.mkdir(exist_ok=True)
    for contract in (SessionState,SpeakingAssessment,BankItem):
        (dest/(contract.__name__+'.schema.json')).write_text(json.dumps(TypeAdapter(contract).json_schema(),ensure_ascii=False,indent=2)+'\n')
