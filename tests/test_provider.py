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


def test_scheduled_native_call_uses_forced_choice():
    class ScheduledMessage(ToolMessage):
        def __init__(self):
            super().__init__('lookup')
            self.tool_calls[0].function.arguments='{"criterion":"lexical_resource"}'
        def model_dump(self,**kwargs):
            data=super().model_dump(**kwargs)
            data['tool_calls'][0]['function']['arguments']=self.tool_calls[0].function.arguments
            return data
    p,calls=provider_for([ScheduledMessage(),NS(tool_calls=None,content='{"ok":true}')])
    invoked=[]
    result,used=p.run({'tool_sequence':[{'name':'lookup','arguments':{'criterion':'lexical_resource'}}]},
        tools=[{'type':'function'}],handlers={'lookup':lambda criterion:invoked.append(criterion) or {'chunks':[]}})
    assert invoked==['lexical_resource'] and result=={'ok':True}
    assert calls[0]['tool_choice']=={'type':'function','function':{'name':'lookup'}}
    assert calls[1]['response_format']=={'type':'json_object'}
    assert 'tools' not in calls[1]


def test_required_tools_cannot_be_skipped_by_json_answer():
    p,_=provider_for([NS(tool_calls=None,content='{"ok":true}')])
    with pytest.raises(OutputValidationError):
        p.run({'tool_sequence':[{'name':'lookup','arguments':{}}]},tools=[{'type':'function'}],handlers={'lookup':lambda:{}})


def test_tool_trace_records_safe_arguments_and_result_refs():
    p,_=provider_for([ToolMessage(),NS(tool_calls=None,content='{"ok":true}')])
    events=[]
    p.run({},tools=[{'type':'function'}],handlers={'lookup':lambda:[{'chunk_id':'test-ref-only'}]},
          on_event=lambda kind,name,**metrics:events.append((kind,name,metrics)))
    tool=next(e[2] for e in events if e[0]=='tool')
    assert tool['arguments']=={} and tool['output_refs']==['test-ref-only']
    assert tool['succeeded'] and tool['duration_ms']>=0
