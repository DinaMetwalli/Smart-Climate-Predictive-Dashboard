"""Module for handling custom error types."""

class UserError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)

class InvalidFileTypeError(UserError):
    """Error for when an unsupported file type is provided."""

class IncompatibleDataError(UserError):
    """Error for invalid dataset structure."""

class FileProcessingError(UserError):
    """
    Error for when an exception occurs on file processing.
    
    E.g. unable to open the file.
    """

class FileTypeMismatchError(UserError):
    """Error for when different (supported) file types are uploaded."""

class PasswordTooShortError(UserError):
    """Error for when the password used for registration is less than 8 characters."""

class UsernameTooShortError(UserError):
    """Error for when the username used for registration is less than 4 characters."""

class InvalidUsername(UserError):
    """Error for when the username used for registration is invalid."""

class UsernameAlreadyExistsError(UserError):
    """Error for when a user already exists with the same username used for registraton."""

class UserDoesNotExist(UserError):
    """Error for when a requested user cannot be found."""