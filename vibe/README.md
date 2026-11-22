# Kliros Manager Vibe PoC

A local Flask app for importing scores, extracting text from their first page, comparing hashes, and suggesting metadata. The browser UI uses vanilla JavaScript and locally served Pico CSS. The home page shows recent works, `/library` lists the collection, and detail pages show the original, metadata, uploader profile, favorites, and collection actions. Login is a fake local demo session only; no external identity provider is used. No Azure service, remote database, container configuration, or deployment tooling is included.

## Run locally

From this directory, create a virtual environment and install the Python packages:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Then launch the app with the root script:

```powershell
.\run.ps1
```

The script locates Tesseract (including standard per-user and system-wide Windows installs), sets `TESSERACT_CMD`, and starts Flask. Open `http://127.0.0.1:5000`. On macOS or Linux, activate with `source .venv/bin/activate` and run `python app.py` instead.

## Cross-origin API access

The API allows credentialed CORS requests from the exact origins in `settings.json` under `cors_allowed_origins` (an array of scheme/host/port strings). The default Vite development origins are `http://localhost:5173` and `http://127.0.0.1:5173`. Edit the array, for example to `["https://web.example.com", "http://localhost:5174"]`, then restart Flask. The optional `CORS_ALLOWED_ORIGINS` environment variable overrides the file with a comma-separated list. Origins not on the allowlist receive no `Access-Control-Allow-Origin` header; wildcard origins are not supported with credentials. CORS headers apply to `/api/*`, including API media routes and preflight requests.

The frontend must send cookies (`credentials: "include"` in fetch). A different port on `localhost` is cross-origin but same-site and works with the default `SameSite=Lax` session cookie. For a truly cross-site HTTPS frontend, set `SESSION_COOKIE_SAMESITE=None` and `SESSION_COOKIE_SECURE=true`; browser third-party-cookie restrictions may still block the session, so a same-site deployment or reverse proxy is more reliable. CORS is not authentication or CSRF protection; the local demo login is not suitable for production.

## Local prerequisites

- Python 3.10 or later.
- The packages in `requirements.txt`. PyMuPDF renders PDF pages locally, so Poppler is not required.
- PDFs exported by recognized notation software are read by a program-specific extractor in `service/ScoreExtractors.py` instead of OCR. Currently MuseScore, Sibelius and LilyPond are recognized. It returns the printed title, credits and lyrics, joining hyphenated syllables back into words, and it does not use Tesseract. Other PDFs with an embedded text layer use page body text only when `extract_pdf_text` is enabled, and PDF document metadata is ignored. All remaining PDFs fall back to Tesseract OCR.
- The Tesseract OCR executable installed separately. `run.ps1` finds standard per-user and system-wide Windows installations or a `PATH` installation; set `TESSERACT_CMD` if it is elsewhere.
  `winget install UB-Mannheim.TesseractOCR`
- Permission to write the configured upload folder, `settings.json`, and `db.json`.

If Tesseract is missing or cannot run, the upload is still stored and recorded, and its response reports OCR as unavailable or failed. The app does not claim text was extracted in that case.

## Local data and settings

The first app start creates `settings.json` and a schema-shaped `db.json` in this directory. The default settings are:

```json
{
  "storage_folder": "uploads",
  "max_hamming_distance": 10,
  "invalid_hamming_distance": 50,
  "reference_image_path": "references",
  "extract_pdf_text": false
}
```

Relative paths resolve from this project directory; absolute paths are also accepted. `reference_image_path` points to a folder of sheet-music examples. An upload passes if its dHash is within the 0–64 `invalid_hamming_distance` threshold of at least one supported image or PDF in that folder. Reference hashes are cached in memory until a file is added, removed, or changed. `extract_pdf_text` enables PDF page-text extraction before OCR; when false, PDFs go directly to Tesseract. Additional settings can be stored in the same JSON object. The database seeds the SQL-defined metadata options and a `Local Owner` with `JoinedAt`. “Log in (demo)” signs in as this hard-coded user; logout clears the session. This demo session is not a security boundary.

`db.json` and each settings update use atomic file replacement. This store is intended for one local Flask process, not concurrent writers or multiple app instances. Back up `db.json` and the upload folder together if the local library matters.

## API

Browser routes `/`, `/library`, `/search`, `/profile`, `/profile/<id>`, `/import`, and `/library/<id>` serve static HTML shells. Page data is provided by JSON APIs: `GET /api/session`, `/api/home`, `/api/library`, `/api/library/<id>`, `/api/profile`, `/api/search` (query, `filters`, `page`, `page_size`, and `sort`), and `/api/search/facets` (metadata filter choices). Authentication is exposed through `POST /api/login` and `/api/logout`.

Import, metadata updates, favorites, collections, and deletes are API operations. `POST /api/library/import/check` accepts multipart file data and returns the upload, OCR, and metadata-review payload; `PATCH /api/library/<id>` updates metadata and returns possible matches. `POST /api/library/<id>/favorite` and `/collections` manage the signed-in user's data, while `DELETE /api/library/<id>` soft-deletes a work by setting `Hidden`. Hidden works are omitted from lists, search, profile collections, detail pages, and media endpoints; their files and relationships are retained. The `/import` shell checks `/api/session` and hides its form for guests; write APIs enforce login. Collection management is owner-scoped regardless of `Public`; public visibility and subscriptions are future work.

Users have a `UserType` of `regular`, `moderator`, or `admin`. New users default to `regular`; the seeded `Local Owner` is `admin`. An admin can switch a non-admin user between regular and moderator with `PATCH /api/admin/users/<id>/type` and a JSON body such as `{"user_type":"moderator"}`. The endpoint cannot grant admin or demote an admin.

`GET /library/<id>/download` lets any visitor download the original document. The attachment name uses the work title, appends the composer when present, and preserves the original extension. Download counts are deferred.

Signed-in users can visit `/profile` to see their name, join date, uploads, favorites, and owned collections. `GET /api/profile` includes full score-card data in `uploads`, `favorites`, and each collection's `items`; it returns 401 for guests. Anyone can visit `/profile/<id>` to see another user's name, join date, and uploads; the score detail page links the uploader name there. `GET /api/profile/<id>` is also available to guests, but omits email, favorites, and collections unless the signed-in user owns the requested profile. `DELETE /api/library/<id>/favorite` removes the signed-in user's favorite without toggling it back on when repeated. From the profile users can unfavorite scores, rename or delete a collection, and remove individual items. All score lists share a vanilla JavaScript card renderer in `static/site.js`, with no frontend build step. Collection management follows ownership regardless of the `Public` flag; cross-user collection visibility and subscriptions are future features.

`/search` displays all scores initially, with live text and metadata filters, 24/48/96-item pages, and upload-date, popularity, or name sorting. Text search covers titles and metadata values. Popularity uses favorites until download counts are available.

On detail pages, **Add to Collection** opens a selector where owners can save or remove the work from their collections or create a new collection. **Report to Moderator** currently displays a thank-you only; reasons and details are not sent or stored.

## Score PDF extraction

`service/ScoreExtractors.py` reads PDFs exported by notation software, where a plain text extraction mixes lyrics with garbage from music-font glyphs. `extract_score_text` tries each extractor in `SCORE_EXTRACTORS` and returns `None` when none claims the file, so `FileProcessing.process_image` falls back to the text layer or OCR.

### How the shared engine works

`LyricLayoutExtractor` holds all layout logic; each program's subclass only says how to recognize its PDFs, which fonts are music, and any join-spacing tweak.

- **Systems** are groups of five long horizontal staff lines, merged into one system when a tall vertical line (barline or bracket) spans them.
- **Lyric rows** are text rows inside a system or stacked below it, each within `max_row_gap` (40pt) of the row above. The lyric style is the most common font and size on the first (topmost) text row of each system, counting every style on that baseline. Text in other styles (tempo, dynamics, chords, measure numbers, staff names) is ignored.
- **Words** are rebuilt from syllables. Syllables are joined when a hyphen lies between them on the same row: either a `-` text glyph on the baseline or a short vector dash 1–5pt above it. Extender lines sit on the baseline and are ignored. Leading verse numbers (`1.`, `2)`) are removed. Verses continue across systems and pages.
- **Header**: on page 1, above the first system, the largest text is the title. Text centered under it is the subtitle, and text at the left or right edge is credits (composer, arranger, translator, instrument).
- **Footer**: footers are optional and do not depend on the program or the source website. On each page, the text under the last system, excluding lyric rows, is split into blocks wherever there is a gap of more than about two line heights. The lowest block is the footer; any blocks above it (such as extra stanzas printed under the music) go to other text. Don't add rules that match a specific publisher's tagline.

### Program notes

| Program | Recognized by | Music fonts (excluded) | Hyphens and quirks |
| --- | --- | --- | --- |
| MuseScore | Creator `MuseScore Studio…` or XMP `CreatorTool` | Leland, Bravura, MScore, Petaluma, MuseJazz (Private Use Area glyphs) | Vector dashes about 2pt above the baseline; lyrics usually Edwin |
| Sibelius | Creator contains `Sibelius`, or an `Opus*` font | Opus, Helsinki, Inkpen2, Reprise, Norfolk (mapped to ordinary Latin letters, so excluded by name) | `-` text on the baseline, sometimes smaller; verse number glued to the first syllable (`1.Twin`) |
| LilyPond | Creator `LilyPond …` (usually via Ghostscript), or an Emmentaler/feta font | Emmentaler, feta, parmesan, LilyJAZZ | Vector dashes; leaves out the hyphen when syllables are squeezed together, so gaps under 0.1 em also join (`tight_join_ratio`); verse numbers are separate bold spans |

Font names in PDFs often carry a subset prefix (`ABCDEF+Name`); the engine strips it before matching.

### Adding a program

1. Inspect real exports with PyMuPDF: `document.metadata`, `page.get_fonts()`, `page.get_text("rawdict")` spans, and `page.get_drawings()` near the lyric rows to see how hyphens are drawn.
2. Subclass `LyricLayoutExtractor` and set `source`, `matches()`, `music_font_prefixes` and, only if needed, `tight_join_ratio`. Keep layout fixes in the shared engine, not the subclass.
3. Register it in `SCORE_EXTRACTORS`. Re-run every sample you have from the other programs to confirm their output does not change.
4. Add a test in `tests/test_upload_processing.py` that builds a small synthetic PDF with `fitz`. Commit a real sample as a fixture only if it is public domain or freely licensed; never commit copyrighted downloads.

Known gaps: tempo markings above the first system can appear among the credits, and Sibelius lyrics sometimes lose the space between two words (`it'snearly`).

## Tests

Run the focused tests from this directory:

```powershell
python -m unittest discover -s tests -v
```

The upload-route test uses a controlled processing result and does not require Tesseract. It still validates multipart handling, GUID storage, prior-row input, and database persistence.
