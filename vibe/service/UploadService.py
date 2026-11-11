"""Validated local upload storage."""

from __future__ import annotations

import hashlib
import uuid
from pathlib import Path
from typing import Any

from werkzeug.datastructures import FileStorage


IMAGE_FORMATS = {
    ".png": "PNG",
    ".jpg": "JPEG",
    ".jpeg": "JPEG",
    ".tif": "TIFF",
    ".tiff": "TIFF",
    ".bmp": "BMP",
    ".webp": "WEBP",
    ".gif": "GIF",
}
SUPPORTED_EXTENSIONS = {".pdf", *IMAGE_FORMATS}


class UploadValidationError(ValueError):
    def __init__(self, message: str, status_code: int = 415):
        super().__init__(message)
        self.status_code = status_code


class UploadService:
    def __init__(self, storage_folder: str | Path):
        self.storage_folder = Path(storage_folder).resolve()
        self.storage_folder.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def validate(file_storage: FileStorage) -> str:
        original_name = file_storage.filename or ""
        if not original_name.strip():
            raise UploadValidationError("Choose a file to upload.", 400)
        return UploadService._validate(file_storage, original_name)

    @staticmethod
    def _validate(file_storage: FileStorage, original_name: str) -> str:
        extension = Path(original_name).suffix.lower()
        if extension not in SUPPORTED_EXTENSIONS:
            raise UploadValidationError("Unsupported file type. Upload a PDF or a supported image.")
        if len(original_name) > 255:
            raise UploadValidationError("Filename must be 255 characters or fewer.", 400)

        stream = file_storage.stream
        stream.seek(0)
        header = stream.read(8)
        stream.seek(0)
        if not header:
            raise UploadValidationError("The uploaded file is empty.", 400)
        if extension == ".pdf":
            if not header.startswith(b"%PDF-"):
                raise UploadValidationError("The file contents do not match a PDF document.")
            return extension

        try:
            from PIL import Image

            with Image.open(stream) as image:
                actual_format = image.format
                image.verify()
        except ImportError as error:
            raise UploadValidationError("Image support is unavailable; install the listed Python dependencies.", 503) from error
        except Exception as error:
            raise UploadValidationError("The uploaded image is invalid or could not be decoded.", 400) from error
        finally:
            stream.seek(0)
        if actual_format != IMAGE_FORMATS[extension]:
            raise UploadValidationError("The file contents do not match the filename extension.")
        return extension

    def save(self, file_storage: FileStorage) -> dict[str, Any]:
        original_name = file_storage.filename or ""
        extension = self.validate(file_storage)
        stored_name = f"{uuid.uuid4()}{extension}"
        destination = self.storage_folder / stored_name
        file_digest = hashlib.sha256()
        file_storage.stream.seek(0)
        try:
            with destination.open("xb") as output:
                while chunk := file_storage.stream.read(1024 * 1024):
                    output.write(chunk)
                    file_digest.update(chunk)
        except Exception:
            destination.unlink(missing_ok=True)
            raise
        return {
            "stored_name": stored_name,
            "original_name": original_name,
            "path": destination,
            "file_hash": file_digest.hexdigest(),
        }

    @staticmethod
    def calculate_file_hash(path: str | Path) -> str:
        file_digest = hashlib.sha256()
        with Path(path).open("rb") as source:
            while chunk := source.read(1024 * 1024):
                file_digest.update(chunk)
        return file_digest.hexdigest()