"""Explicit live capability probe. Requires a key and makes billable API calls.
Force the first call to isolate capability from the model's automatic tool choice.
A required argument avoids ambiguous empty-object behavior in some providers.
"""
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from openai import OpenAIError
from src.provider import ChatProvider, function_tool
from src.errors import ProviderError


def probe(provider):
    messages=[{'role':'user','content':'Call capability_probe with probe_id="uc03-check". Then return a JSON object containing the exact marker returned by the tool.'}]
    tool=function_tool('capability_probe','Look up a server test marker',
                       {'probe_id':{'type':'string','enum':['uc03-check']}},['probe_id'])
    try:
        response=provider.client.chat.completions.create(model=provider.model,messages=messages,tools=[tool],
            tool_choice={'type':'function','function':{'name':'capability_probe'}},temperature=0)
        message=response.choices[0].message
        if not message.tool_calls:
            raise ProviderError('Provider did not issue a native tool call')
        messages.append(message.model_dump(exclude_none=True))
        marker=uuid.uuid4().hex
        for call in message.tool_calls:
            if call.function.name!='capability_probe' or json.loads(call.function.arguments)!={'probe_id':'uc03-check'}:
                raise ProviderError('Provider returned an invalid tool name or arguments')
            messages.append({'role':'tool','tool_call_id':call.id,'content':json.dumps({'marker':marker})})
        followup=provider.client.chat.completions.create(model=provider.model,messages=messages,temperature=0)
        if marker not in (followup.choices[0].message.content or ''):
            raise ProviderError('Provider did not return the actual tool result marker')
    except (OpenAIError,ValueError,IndexError,AttributeError):
        raise ProviderError('Native tool probe failed; no credential or provider response body logged') from None
    return {'status':'passed','model':provider.model,'timestamp':datetime.now(timezone.utc).isoformat(),
            'forced_tool_choice':True,'native_tool_result_roundtrip':True,
            'limitations':['Does not prove reliable automatic tool selection or IELTS assessment quality.']}


def main():
    result=probe(ChatProvider())
    dest=Path('runtime/provider-probe.json');dest.parent.mkdir(exist_ok=True)
    dest.write_text(json.dumps(result,indent=2))
    print(json.dumps(result))

if __name__=='__main__':
    main()
