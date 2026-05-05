from typing import Optional, Dict

class MedSightException(Exception):
    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"
    message: str = "An unexpected error occurred"
    
    def __init__(self, message: Optional[str] = None, details: Optional[Dict] = None):
        self.message = message or self.__class__.message
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> dict:
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details
        }

# 401 / 403 Authentication Exceptions
class AuthenticationError(MedSightException):
    status_code = 401
    error_code = "AUTH_REQUIRED"
    message = "Authentication required"

class InvalidTokenError(MedSightException):
    status_code = 401
    error_code = "INVALID_TOKEN"
    message = "Token is invalid or expired"

class ExpiredTokenError(MedSightException):
    status_code = 401
    error_code = "TOKEN_EXPIRED"
    message = "Token has expired"

class BlacklistedTokenError(MedSightException):
    status_code = 401
    error_code = "TOKEN_REVOKED"
    message = "Token has been revoked"

class InsufficientPermissionsError(MedSightException):
    status_code = 403
    error_code = "FORBIDDEN"
    message = "Insufficient permissions"

class AccountInactiveError(MedSightException):
    status_code = 403
    error_code = "ACCOUNT_INACTIVE"
    message = "Account not yet verified"

class AccountLockedError(MedSightException):
    status_code = 429
    error_code = "ACCOUNT_LOCKED"
    message = "Account temporarily locked"

# 404 / 409 Resource Exceptions
class NotFoundError(MedSightException):
    status_code = 404
    error_code = "NOT_FOUND"
    message = "Resource not found"

class UserNotFoundError(NotFoundError):
    error_code = "USER_NOT_FOUND"
    message = "User not found"

class SessionNotFoundError(NotFoundError):
    error_code = "SESSION_NOT_FOUND"
    message = "Analysis session not found"

class TaskNotFoundError(NotFoundError):
    error_code = "TASK_NOT_FOUND"
    message = "Analysis task not found"

class DuplicateError(MedSightException):
    status_code = 409
    error_code = "DUPLICATE"
    message = "Resource already exists"

class EmailAlreadyExistsError(DuplicateError):
    error_code = "EMAIL_EXISTS"
    message = "Email already registered"

# 400 Validation Exceptions
class ValidationError(MedSightException):
    status_code = 422
    error_code = "VALIDATION_ERROR"
    message = "Request validation failed"

class FileTooLargeError(MedSightException):
    status_code = 413
    error_code = "FILE_TOO_LARGE"
    message = "File exceeds maximum size"

class InvalidFileTypeError(MedSightException):
    status_code = 415
    error_code = "INVALID_FILE_TYPE"
    message = "File type not supported"

class InvalidFileError(MedSightException):
    status_code = 400
    error_code = "INVALID_FILE"
    message = "File is corrupted or unreadable"

class PromptInjectionError(MedSightException):
    status_code = 400
    error_code = "PROMPT_INJECTION"
    message = "Input contains disallowed content"

# 503 ML Exceptions
class ModelNotLoadedError(MedSightException):
    status_code = 503
    error_code = "MODEL_UNAVAILABLE"
    message = "AI model not available"

class InferenceError(MedSightException):
    status_code = 503
    error_code = "INFERENCE_FAILED"
    message = "AI processing failed"

class InferenceTimeoutError(MedSightException):
    status_code = 503
    error_code = "INFERENCE_TIMEOUT"
    message = "AI processing timed out"

class CircuitOpenError(MedSightException):
    status_code = 503
    error_code = "CIRCUIT_OPEN"
    message = "Service temporarily unavailable"

class VRAMError(MedSightException):
    status_code = 503
    error_code = "GPU_MEMORY_FULL"
    message = "GPU memory insufficient"

# 403 Authorization Exceptions
class SessionAccessDeniedError(MedSightException):
    status_code = 403
    error_code = "SESSION_ACCESS_DENIED"
    message = "You don't own this session"

class APIKeyAccessDeniedError(MedSightException):
    status_code = 403
    error_code = "API_KEY_ACCESS_DENIED"
    message = "API key lacks permission"

# 429 Rate Limit Exception
class RateLimitExceededError(MedSightException):
    status_code = 429
    error_code = "RATE_LIMIT_EXCEEDED"
    message = "Too many requests"
    
    def __init__(self, message: Optional[str] = None, retry_after_seconds: int = 60):
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds

# 400 Security Exceptions
class SecurityError(MedSightException):
    status_code = 400
    error_code = "SECURITY_VIOLATION"
    message = "Security check failed"

class PathTraversalError(SecurityError):
    error_code = "PATH_TRAVERSAL"
    message = "Invalid file path"
