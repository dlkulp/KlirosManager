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
- PDFs with an embedded text layer use page body text only; PDF document metadata is ignored. Image-only PDFs fall back to Tesseract OCR.
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

Browser routes `/`, `/library`, `/search`, `/profile`, `/import`, and `/library/<id>` serve static HTML shells. Page data is provided by JSON APIs: `GET /api/session`, `/api/home`, `/api/library`, `/api/library/<id>`, `/api/profile`, `/api/search` (query, `filters`, `page`, `page_size`, and `sort`), and `/api/search/facets` (metadata filter choices). Authentication is exposed through `POST /api/login` and `/api/logout`.

Import, metadata updates, favorites, collections, and deletes are API operations. `POST /api/library/import/check` accepts multipart file data and returns the upload, OCR, and metadata-review payload; `PATCH /api/library/<id>` updates metadata and returns possible matches. `POST /api/library/<id>/favorite` and `/collections` manage the signed-in user's data, while `DELETE /api/library/<id>` soft-deletes a work by setting `Hidden`. Hidden works are omitted from lists, search, profile collections, detail pages, and media endpoints; their files and relationships are retained. The `/import` shell checks `/api/session` and hides its form for guests; write APIs enforce login. Collection management is owner-scoped regardless of `Public`; public visibility and subscriptions are future work.

Users have a `UserType` of `regular`, `moderator`, or `admin`. New users default to `regular`; the seeded `Local Owner` is `admin`. An admin can switch a non-admin user between regular and moderator with `PATCH /api/admin/users/<id>/type` and a JSON body such as `{"user_type":"moderator"}`. The endpoint cannot grant admin or demote an admin.

`GET /library/<id>/download` lets any visitor download the original document. The attachment name uses the work title, appends the composer when present, and preserves the original extension. Download counts are deferred.

Signed-in users can visit `/profile` to see their name, join date, uploads, favorites, and owned collections. `GET /api/profile` includes full score-card data in `uploads`, `favorites`, and each collection's `items`. `DELETE /api/library/<id>/favorite` removes the signed-in user's favorite without toggling it back on when repeated. From the profile users can unfavorite scores, rename or delete a collection, and remove individual items. All score lists share a vanilla JavaScript card renderer in `static/site.js`, with no frontend build step. Collection management follows ownership regardless of the `Public` flag; cross-user visibility and subscriptions are future features.

`/search` displays all scores initially, with live text and metadata filters, 24/48/96-item pages, and upload-date, popularity, or name sorting. Text search covers titles and metadata values. Popularity uses favorites until download counts are available.

On detail pages, **Add to Collection** opens a selector where owners can save or remove the work from their collections or create a new collection. **Report to Moderator** currently displays a thank-you only; reasons and details are not sent or stored.

## Tests

Run the focused tests from this directory:

```powershell
python -m unittest discover -s tests -v
```

The upload-route test uses a controlled processing result and does not require Tesseract. It still validates multipart handling, GUID storage, prior-row input, and database persistence.
