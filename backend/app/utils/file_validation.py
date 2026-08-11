"""
Validates uploaded resume files against three independent signals — extension,
declared size, and actual file content (magic bytes) — rather than trusting
any single one. A renamed .exe with a .pdf extension fails the magic-byte
check even though the extension and size look fine.
"""

from app.config.settings import settings
from app.utils.exceptions import AppException

PDF_MAGIC = b"%PDF-"
DOCX_MAGIC = b"PK\x03\x04"  # DOCX is a ZIP container


class UnsupportedFileTypeException(AppException):
    status_code = 415
    message = "Only PDF and DOCX files are supported"


class FileTooLargeException(AppException):
    status_code = 413
    message = "File exceeds the maximum upload size"


class CorruptFileException(AppException):
    status_code = 422
    message = "The file's content doesn't match its extension — it may be corrupted or mislabeled"


def get_extension(filename: str) -> str:
    if "." not in filename:
        return ""
    return filename.rsplit(".", 1)[-1].lower()


def validate_upload(filename: str, content: bytes) -> str:
    """Returns the validated extension, or raises."""
    extension = get_extension(filename)
    if extension not in settings.allowed_upload_extensions_list:
        raise UnsupportedFileTypeException(
            f"'.{extension}' is not supported. Allowed: {', '.join(settings.allowed_upload_extensions_list)}"
        )

    if len(content) == 0:
        raise CorruptFileException("The uploaded file is empty")
    if len(content) > settings.max_upload_size_bytes:
        raise FileTooLargeException(f"File exceeds the {settings.MAX_UPLOAD_SIZE_MB}MB limit")

    if extension == "pdf" and not content.startswith(PDF_MAGIC):
        raise CorruptFileException()
    if extension == "docx" and not content.startswith(DOCX_MAGIC):
        raise CorruptFileException()

    return extension
