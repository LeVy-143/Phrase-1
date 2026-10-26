"""Explicit live capability probe. Requires a key and makes billable API calls."""
from src.provider import ChatProvider,function_tool
from src.errors import ProviderError

def main():
    provider=ChatProvider()
    result,used=provider.run({'task':'Call capability_probe with no arguments, then return a JSON object with its returned marker.'},
      tools=[function_tool('capability_probe','Return a harmless test marker',{},[])],
      handlers={'capability_probe':lambda:{'marker':'native-tool-roundtrip'}})
    if 'capability_probe' not in used or 'native-tool-roundtrip' not in str(result):
        raise ProviderError('Native tool roundtrip was not demonstrated by this model')
    print('Verified native tool-call roundtrip for model:',provider.model)
if __name__=='__main__':
    main()
