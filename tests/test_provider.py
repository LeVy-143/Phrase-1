"""Native protocol unit tests: no external network or invented live results."""
import json
from types import SimpleNamespace as NS
import pytest
from src.provider import ChatProvider
from src.errors import ProviderError, OutputValidationError

class ToolMessage:
    content=None
    def __init__(self,name='lookup'):
        self.tool_calls=[NS(id='call-1',function=NS(name=name,arguments='{}'))]
    def model_dump(self,**kwargs):
        return {'role':'assistant','content':None,'tool_calls':[{'id':'call-1','type':'function','function':{'name':self.tool_calls[0].function.name,'arguments':'{}'}}]}


def provider_for(messages):
    provider=object.__new__(ChatProvider);provider.model='unit-test'
    observed=[]
    def create(**kwargs):
        observed.append(json.loads(json.dumps(kwargs)))
        return NS(choices=[NS(message=messages.pop(0))],usage=NS(total_tokens=12))
    provider.client=NS(chat=NS(completions=NS(create=create)))
    return provider,observed


def test_native_tool_result_roundtrip():
    p,calls=provider_for([ToolMessage(),NS(tool_calls=None,content='{"ok":true}')])
    invoked=[]
    result,used=p.run({'test':'fixture'},tools=[{'type':'function'}],handlers={'lookup':lambda:invoked.append(True) or {'found':1}})
    assert result=={'ok':True} and used=={'lookup'} and invoked==[True]
    assert calls[1]['messages'][-1]=={'role':'tool','tool_call_id':'call-1','content':'{"found": 1}'}


def test_unknown_tool_rejected():
    p,_=provider_for([ToolMessage('run_shell')])
    with pytest.raises(ProviderError):
        p.run({},tools=[{'type':'function'}],handlers={})


def test_malformed_json_rejected():
    p,_=provider_for([NS(tool_calls=None,content='not json')])
    with pytest.raises(OutputValidationError):
        p.run({})
