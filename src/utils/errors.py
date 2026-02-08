class UserError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)

class IvalidFileTypeError(UserError):
    """Error for when an unsupported file type is provided."""

class IncompatibleDataError(UserError):
    """Error for invalid dataset values or """