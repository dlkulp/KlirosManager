"""Local, extensible application settings with sensible defaults."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any


DEFAULT_SETTINGS: dict[str, Any] = {
    "storage_folder": "uploads",
    "max_hamming_distance": 10,
    "invalid_hamming_distance": 50,
    "reference_image_path": "references",
    "extract_pdf_text": False,
}


class SettingsManager:
    def __init__(self, path: str | Path, project_root: str | Path | None = None):
        self.path = Path(path).resolve()
        self.project_root = Path(project_root or self.path.parent).resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            try:
                loaded = json.loads(self.path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as error:
                raise ValueError(f"Could not read settings file {self.path}: {error}") from error
            if not isinstance(loaded, dict):
                raise ValueError("Settings file must contain a JSON object.")
            self._settings = {**DEFAULT_SETTINGS, **loaded}
        else:
            self._settings = DEFAULT_SETTINGS.copy()
            self._write()
        self._validate()

    def _validate(self) -> None:
        threshold = self._settings["max_hamming_distance"]
        if isinstance(threshold, bool) or not isinstance(threshold, int) or threshold < 0:
            raise ValueError("max_hamming_distance must be a non-negative integer.")
        invalid_threshold = self._settings["invalid_hamming_distance"]
        if (
            isinstance(invalid_threshold, bool)
            or not isinstance(invalid_threshold, int)
            or not 0 <= invalid_threshold <= 64
        ):
            raise ValueError("invalid_hamming_distance must be an integer between 0 and 64.")
        reference_image_path = self._settings["reference_image_path"]
        if not isinstance(reference_image_path, str) or not reference_image_path.strip():
            raise ValueError("reference_image_path must be a non-empty path.")
        if not isinstance(self._settings["extract_pdf_text"], bool):
            raise ValueError("extract_pdf_text must be a boolean.")
        if not isinstance(self._settings["storage_folder"], str) or not self._settings["storage_folder"].strip():
            raise ValueError("storage_folder must be a non-empty path.")

    def _write(self) -> None:
        temporary_path: str | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.path.parent,
                prefix=f".{self.path.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary_file:
                temporary_path = temporary_file.name
                json.dump(self._settings, temporary_file, ensure_ascii=False, indent=2)
                temporary_file.write("\n")
                temporary_file.flush()
                os.fsync(temporary_file.fileno())
            os.replace(temporary_path, self.path)
        finally:
            if temporary_path and os.path.exists(temporary_path):
                os.unlink(temporary_path)

    def get(self, name: str, default: Any = None) -> Any:
        return self._settings.get(name, default)

    def all(self) -> dict[str, Any]:
        return self._settings.copy()

    def set(self, name: str, value: Any) -> None:
        updated = {**self._settings, name: value}
        previous = self._settings
        self._settings = updated
        try:
            self._validate()
            self._write()
        except Exception:
            self._settings = previous
            raise

    def storage_path(self) -> Path:
        configured = Path(self._settings["storage_folder"]).expanduser()
        resolved = (self.project_root / configured).resolve() if not configured.is_absolute() else configured.resolve()
        resolved.mkdir(parents=True, exist_ok=True)
        return resolved

    def reference_image_path(self) -> Path:
        configured = Path(self._settings["reference_image_path"]).expanduser()
        return (self.project_root / configured).resolve() if not configured.is_absolute() else configured.resolve()