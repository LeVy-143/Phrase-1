"""Safe domain errors: messages must never include credentials/provider payloads."""
class IELTSException(Exception):
    pass
class ValidationError(IELTSException):
    pass
class AccessDenied(IELTSException):
    pass
class NotFound(IELTSException):
    pass
class RevisionConflict(IELTSException):
    pass
class IdempotencyConflict(IELTSException):
    pass
class DescriptorUnavailable(IELTSException):
    pass
class ProviderError(IELTSException):
    pass
class OutputValidationError(ValidationError):
    pass

class StorageError(IELTSException):
    pass
