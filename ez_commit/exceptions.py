"""
Custom exceptions for ez-commit
"""

class EzCommitError(Exception):
    """Base exception for all ez-commit errors."""
    def __init__(self, message, exit_code=1):
        super().__init__(message)
        self.exit_code = exit_code

class GitError(EzCommitError):
    """Raised when a git operation fails."""
    def __init__(self, message):
        super().__init__(message, exit_code=2)

class APIError(EzCommitError):
    """Raised when an API operation fails."""
    def __init__(self, message):
        super().__init__(message, exit_code=3)

class ConfigError(EzCommitError):
    """Raised when a configuration operation fails."""
    def __init__(self, message):
        super().__init__(message, exit_code=4)

class EditorError(EzCommitError):
    """Raised when an editor operation fails."""
    def __init__(self, message):
        super().__init__(message, exit_code=5)
