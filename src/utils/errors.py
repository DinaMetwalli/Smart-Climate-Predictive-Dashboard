"""Module for handling custom error types."""

class UserError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


# -- File upload errors --
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


# -- Registration errors --
class PasswordTooShortError(UserError):
    """Error for when the password used for registration is less than 8 characters."""

class PasswordDoesNotMatchError(UserError):
    """Error for when the password entered again on registration does not match the first one."""

class UsernameTooShortError(UserError):
    """Error for when the username used for registration is less than 4 characters."""

class UsernameAlreadyExistsError(UserError):
    """Error for when a user already exists with the same username used for registraton."""


# -- Login errors --
class UserDoesNotExistError(UserError):
    """Error for when a requested user cannot be found."""


# -- Prediction errors --
class NotEnoughDataError(UserError):
    """Error for when the uploaded custom analysis file doesn't have enough history to perform the prediction."""

class APIConnectionError(UserError):
    """Error for when connections to the live data API(s) fails (due to network or API issues)."""