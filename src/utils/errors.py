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