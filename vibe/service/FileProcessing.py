"""First-page OCR, perceptual hashing, matching, and metadata inference."""

from __future__ import annotations

import os
import re
import shutil
import threading
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any


class FileProcessing:
    _REFERENCE_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".webp"}

    def __init__(self):
        self._reference_hash_cache: dict[
            Path,
            tuple[tuple[tuple[str, int, int], ...], list[dict[str, str]]],
        ] = {}
        self._reference_hash_lock = threading.Lock()

    def reference_image_hashes(self, folder: str | Path) -> tuple[list[dict[str, str]], str | None]:
        reference_folder = Path(folder).resolve()
        if not reference_folder.is_dir():
            return [], f"Sheet-music reference folder was not found: {reference_folder}"
        try:
            files = sorted(
                (
                    path for path in reference_folder.iterdir()
                    if path.is_file() and path.suffix.casefold() in self._REFERENCE_EXTENSIONS
                ),
                key=lambda path: path.name.casefold(),
            )
            signature = tuple(
                (str(path), path.stat().st_size, path.stat().st_mtime_ns)
                for path in files
            )
        except OSError as error:
            return [], f"Reference folder could not be read: {error}"
        if not files:
            return [], f"No supported reference images were found in: {reference_folder}"

        with self._reference_hash_lock:
            cached = self._reference_hash_cache.get(reference_folder)
            if cached and cached[0] == signature:
                return list(cached[1]), None

            hashes = []
            for path in files:
                try:
                    image, error = self._first_page_image(path)
                    if error or image is None:
                        continue
                    visual_hash = self._perceptual_hash(image)
                except Exception:
                    continue
                if visual_hash:
                    hashes.append({"name": path.name, "visual_hash": visual_hash})

            if not hashes:
                return [], f"No usable sheet-music reference images were found in: {reference_folder}"
            self._reference_hash_cache[reference_folder] = (signature, hashes)
            return list(hashes), None

    def process(
        self,
        stored_filename: str,
        storage_folder: str | Path,
        previous_resources: list[dict[str, Any]],
        metadata_definitions: list[dict[str, Any]],
        max_hamming_distance: int,
        extract_pdf_text: bool = False,
    ) -> dict[str, Any]:
        stored_path = Path(storage_folder).resolve() / Path(stored_filename).name
        image, render_error = self._first_page_image(stored_path)
        visual_hash = self._perceptual_hash(image)
        return self.process_image(
            image,
            previous_resources,
            metadata_definitions,
            max_hamming_distance,
            stored_path,
            render_error,
            visual_hash,
            extract_pdf_text,
        )

    def process_image(
        self,
        image,
        previous_resources: list[dict[str, Any]],
        metadata_definitions: list[dict[str, Any]],
        max_hamming_distance: int,
        stored_path: Path,
        render_error: str | None = None,
        visual_hash: str | None = None,
        extract_pdf_text: bool = False,
    ) -> dict[str, Any]:
        errors: list[str] = []
        if render_error:
            errors.append(render_error)
        thumbnail_names, thumbnail_error = self._generate_thumbnails(image, stored_path)
        if thumbnail_error:
            errors.append(thumbnail_error)

        visual_hash = self._perceptual_hash(image)
        if image is not None and visual_hash is None:
            errors.append("Perceptual hashing is unavailable; install the listed Python dependencies.")

        ocr = (
            self._extract_pdf_text(stored_path)
            if extract_pdf_text and stored_path.suffix.lower() == ".pdf"
            else None
        )
        if ocr is None:
            ocr = self._extract_ocr(image)
        if ocr["status"] != "success" and ocr.get("message"):
            errors.append(ocr["message"])

        matches = self._find_matches(visual_hash, previous_resources, stored_path, max_hamming_distance)
        inferred_metadata = self._infer_metadata(ocr["text"], metadata_definitions)
        status = "success" if visual_hash is not None and ocr["status"] == "success" else "partial"
        return {
            "status": status,
            "ocr": ocr,
            "visual_hash": visual_hash,
            "thumbnail_names": thumbnail_names,
            "matches": matches,
            "inferred_metadata": inferred_metadata,
            "errors": errors,
        }

    @staticmethod
    def _first_page_image(path: Path):
        if path.suffix.lower() == ".pdf":
            try:
                import fitz
                from PIL import Image
                from io import BytesIO

                with fitz.open(path) as document:
                    if not document.page_count:
                        return None, "The PDF has no pages to process."
                    pixmap = document.load_page(0).get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
                return Image.open(BytesIO(pixmap.tobytes("png"))), None
            except ImportError:
                return None, "PDF rendering is unavailable; install the listed Python dependencies."
            except Exception as error:
                return None, f"The first PDF page could not be rendered: {error}"
        try:
            from PIL import Image

            with Image.open(path) as source:
                source.seek(0)
                return source.copy(), None
        except ImportError:
            return None, "Image processing is unavailable; install the listed Python dependencies."
        except Exception as error:
            return None, f"The image could not be opened for processing: {error}"

    @staticmethod
    def _perceptual_hash(image) -> str | None:
        if image is None:
            return None
        try:
            import imagehash

            return str(imagehash.dhash(image))
        except ImportError:
            return None
        except Exception:
            return None

    @staticmethod
    def _generate_thumbnails(image, stored_path: Path) -> tuple[dict[int, str], str | None]:
        if image is None:
            return {}, None
        try:
            from PIL import Image, ImageOps

            thumbnails = {}
            for height in (300, 600):
                width = round(height * 8.5 / 11)
                dimensions = (width, height)
                fitted_image = ImageOps.contain(
                    image.convert("RGB"),
                    dimensions,
                    method=Image.Resampling.LANCZOS,
                )
                canvas = Image.new("RGB", dimensions, "white")
                canvas.paste(
                    fitted_image,
                    ((width - fitted_image.width) // 2, (height - fitted_image.height) // 2),
                )
                thumbnail_name = f"{stored_path.stem}_{height}px.png"
                canvas.save(stored_path.with_name(thumbnail_name), format="PNG")
                thumbnails[height] = thumbnail_name
            return thumbnails, None
        except Exception as error:
            return {}, f"Thumbnail generation failed: {error}"

    @staticmethod
    def _extract_ocr(image) -> dict[str, str]:
        if image is None:
            return {"status": "unavailable", "text": "", "message": "OCR could not run because no page image was available."}
        try:
            import pytesseract
        except ImportError:
            return {"status": "unavailable", "text": "", "message": "OCR is unavailable; install pytesseract and the Tesseract executable."}

        configured_command = os.environ.get("TESSERACT_CMD")
        if configured_command:
            pytesseract.pytesseract.tesseract_cmd = configured_command
        elif not shutil.which(pytesseract.pytesseract.tesseract_cmd):
            local_app_data = os.environ.get("LOCALAPPDATA")
            if local_app_data:
                local_install = Path(local_app_data) / "Programs" / "Tesseract-OCR" / "tesseract.exe"
                if local_install.is_file():
                    pytesseract.pytesseract.tesseract_cmd = str(local_install)
            if not shutil.which(pytesseract.pytesseract.tesseract_cmd):
                program_files = os.environ.get("ProgramFiles")
                if program_files:
                    system_install = Path(program_files) / "Tesseract-OCR" / "tesseract.exe"
                    if system_install.is_file():
                        pytesseract.pytesseract.tesseract_cmd = str(system_install)
        if not shutil.which(pytesseract.pytesseract.tesseract_cmd):
            return {"status": "unavailable", "text": "", "message": "Tesseract OCR was not found. Install it and add it to PATH, or set TESSERACT_CMD."}
        try:
            text = pytesseract.image_to_string(image)
            text = FileProcessing._clean_ocr_text(text)
            return {"status": "success", "text": text, "message": ""}
        except Exception as error:
            return {"status": "error", "text": "", "message": f"Tesseract OCR failed: {error}"}

    @staticmethod
    def _extract_pdf_text(path: Path) -> dict[str, str] | None:
        try:
            import fitz

            with fitz.open(path) as document:
                page_text = [
                    extracted
                    for page in document
                    if isinstance((extracted := page.get_text("text", sort=True)), str)
                ]
                text = "\n".join(page_text).strip()
            if text:
                return {"status": "success", "text": text, "message": ""}
        except Exception:
            pass
        return None

    @staticmethod
    def _clean_ocr_text(text: str) -> str:
        text = text.strip()
        text = re.sub(r"_+", " ", text)
        return re.sub(r" *[-–—]+ *", "", text)

    @staticmethod
    def hamming_distance(first_hash: str | None, second_hash: str | None) -> int | None:
        if not isinstance(first_hash, str) or not isinstance(second_hash, str):
            return None
        try:
            return (int(first_hash, 16) ^ int(second_hash, 16)).bit_count()
        except ValueError:
            return None

    @staticmethod
    def _find_matches(
        visual_hash: str | None,
        resources: list[dict[str, Any]],
        stored_path: Path,
        threshold: int,
    ) -> list[dict[str, Any]]:
        if visual_hash is None:
            return []
        current_path = str(stored_path.resolve())
        matches = []
        for resource in resources:
            candidate_hash = resource.get("VisualHash")
            if not candidate_hash or resource.get("Source") == current_path:
                continue
            distance = FileProcessing.hamming_distance(visual_hash, candidate_hash)
            if distance is None:
                continue
            if distance <= threshold:
                matches.append({
                    "resource_id": resource.get("id"),
                    "original_name": resource.get("OriginalName"),
                    "visual_hash": candidate_hash,
                    "hamming_distance": distance,
                })
        return sorted(matches, key=lambda match: (match["hamming_distance"], match["resource_id"] or 0))

    @staticmethod
    def rank_similar_resources(
        resource: dict[str, Any],
        resources: list[dict[str, Any]],
        max_hamming_distance: int,
    ) -> list[dict[str, Any]]:
        def metadata_value(row: dict[str, Any], name: str) -> str:
            value = (row.get("MetaData") or {}).get(name)
            if isinstance(value, dict):
                value = value.get("value")
            return str(value).strip() if value is not None else ""

        def normalize(value: str) -> str:
            return " ".join(re.sub(r"[^\w\s]", " ", value.casefold()).split())

        current_title = normalize(str(resource.get("DisplayName") or ""))
        current_composer = normalize(metadata_value(resource, "Composer"))
        current_hash = resource.get("VisualHash")
        matches = []

        for candidate in resources:
            if candidate.get("id") == resource.get("id"):
                continue
            candidate_title = normalize(str(candidate.get("DisplayName") or ""))
            candidate_composer = normalize(metadata_value(candidate, "Composer"))
            title_similarity = (
                SequenceMatcher(None, current_title, candidate_title).ratio()
                if current_title and candidate_title else None
            )
            composer_similarity = (
                SequenceMatcher(None, current_composer, candidate_composer).ratio()
                if current_composer and candidate_composer else None
            )
            hamming_distance = None
            hash_similarity = None
            candidate_hash = candidate.get("VisualHash")
            if current_hash and candidate_hash:
                try:
                    current_bits = int(current_hash, 16)
                    candidate_bits = int(candidate_hash, 16)
                    hamming_distance = (current_bits ^ candidate_bits).bit_count()
                    bit_width = max(len(current_hash), len(candidate_hash)) * 4
                    hash_similarity = 1 - hamming_distance / max(bit_width, 1)
                except (TypeError, ValueError):
                    hamming_distance = None

            reasonable = (
                (hamming_distance is not None and hamming_distance <= max_hamming_distance)
                or (title_similarity is not None and title_similarity >= 0.72)
                or (
                    title_similarity is not None
                    and title_similarity >= 0.50
                    and composer_similarity is not None
                    and composer_similarity >= 0.85
                )
            )
            if not reasonable:
                continue

            weighted_signals = []
            if hash_similarity is not None:
                weighted_signals.append((0.55, hash_similarity))
            if title_similarity is not None:
                weighted_signals.append((0.30, title_similarity))
            if composer_similarity is not None:
                weighted_signals.append((0.15, composer_similarity))
            confidence = sum(weight * score for weight, score in weighted_signals) / sum(
                weight for weight, _ in weighted_signals
            )
            matches.append({
                "resource_id": candidate.get("id"),
                "title": candidate.get("DisplayName") or candidate.get("OriginalName"),
                "original_name": candidate.get("OriginalName"),
                "composer": metadata_value(candidate, "Composer") or None,
                "hamming_distance": hamming_distance,
                "title_similarity": title_similarity,
                "composer_similarity": composer_similarity,
                "confidence": confidence,
            })

        return sorted(
            matches,
            key=lambda match: (
                -match["confidence"],
                match["hamming_distance"] if match["hamming_distance"] is not None else float("inf"),
                (match["title"] or "").casefold(),
            ),
        )

    @staticmethod
    def _infer_metadata(ocr_text: str, definitions: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        normalized_text = " ".join(ocr_text.casefold().split())
        inferred = {}
        for definition in definitions:
            options = definition.get("Options")
            if not options:
                continue
            for option in options:
                option_text = str(option).casefold()
                if definition.get("Type") == "number":
                    found = re.search(rf"(?<!\w){re.escape(option_text)}(?!\w)", normalized_text)
                else:
                    found = re.search(rf"(?<!\w){re.escape(option_text)}(?!\w)", normalized_text)
                if found:
                    inferred[definition["Name"]] = {"value": option, "source": "ocr", "reviewed": False}
                    break
        return inferred