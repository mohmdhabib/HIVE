class HiveError(Exception):
    """Base exception for HIVE."""
    pass

class WorkerNotFoundError(HiveError):
    pass

class WorkerDisabledError(HiveError):
    pass

class LLMError(HiveError):
    pass

class LLMTimeoutError(LLMError):
    pass

class LLMGenerationError(LLMError):
    pass

class KillSwitchActiveError(HiveError):
    pass
