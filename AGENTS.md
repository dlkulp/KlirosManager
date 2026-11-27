# Notes for contributors and AI agents

This file holds durable repository knowledge. It is checked in so every contributor and coding agent sees it. Keep each note short and put details in the relevant README; when you learn something that would help the next person, add it here or to that README instead of keeping it in personal or tool-specific memory.

- This is not a Flash/Elosity project; do not use Flash/Elosity-specific skills or tools here.

## Layout

- `vibe/`: Python Flask proof of concept (score import, OCR, hashing, metadata). Setup, settings and API are in [vibe/README.md](vibe/README.md).
- `client/`, `frontend/`, `server/`: JavaScript UI and Node server; see [README.md](README.md).
- `about/`: design docs. `prototypes/`: experiments and sample files.

## vibe

- Run tests from `vibe/` with `.venv\Scripts\python.exe -m unittest discover -s tests`. Modules are imported as `from service.X import ...`.
- PyMuPDF is imported as `fitz`; recent versions print a deprecation warning on import, which can be ignored.
- Score PDF text extraction (MuseScore, Sibelius, LilyPond, and how to add more) is documented in the "Score PDF extraction" section of [vibe/README.md](vibe/README.md). Key rules:
  - Layout logic lives in the shared `LyricLayoutExtractor`; program subclasses only handle detection, music fonts and spacing tweaks.
  - Footers are optional and not tied to a program or website: on each page the footer is the lowest block of text under the music. Don't match specific taglines (for example Mutopia's).
  - Test with synthetic PDFs built with `fitz`. Commit real samples only if they are public domain or freely licensed.
