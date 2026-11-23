# Kliros Manager Vibe

**Status**: Approved
**Created**: 2026-11-09
**Mode**: new

## 1. Project Summary

Build a locally run score-upload and analysis application rooted in `vibe/`. A Python Flask application serves a vanilla HTML/CSS/JavaScript interface and the Import Score wizard. The app persists uploaded score files beneath a configurable local folder and stores application data in `db.json`.

## 2. Requirements & Scope

- Provide a home page with the latest three works and a link to the Import Score wizard.
- Show the latest three uploaded works at the top of home, with thumbnails/titles linking to details; keep upload below that section. Provide a full library listing and a detail view of the original document and metadata.
- Generate and store a 128x128 PNG thumbnail beside each accepted original using a GUID-derived `_128x128.png` filename. Require the logged-in demo user for imports and deletions; the detail page confirms deletion before removing the row and local files.
- Generate a GUID-based stored filename, preserve the original filename as metadata, and delegate upload processing to `service/FileProcessing`.
- Calculate SHA-256 before OCR or pHash; reject exact duplicates with HTTP 409, delete the newly saved file, and do not create a resource row. Store `FileHash` for accepted resources and backfill it for older rows when their source files are available.
- Run OCR, compute perceptual hashes, find possible duplicate scores by pHash Hamming distance, and infer metadata by matching OCR text against metadata field options.
- Return upload details, OCR text and status, possible matches, and inferred metadata as JSON; render those results in the browser.
- Insert each upload into the `resource` table in `db.json`, including its pHash and local file location, so later uploads can compare against it.
- Include a `DataManager` backed by local `db.json` and a `SettingsManager` backed by a local settings file with defaults and an extensible settings structure.
- Initial settings are `storage_folder` and `max_hamming_distance`.
- Include a hard-coded local demo user with instant login and logout; this is not real authentication.
- Provide a signed-in `/profile` page with the user's name, join date, uploads, and owned collections; allow renaming/deleting collections and removing individual items.
- Require a demo login to open the import wizard, process uploads, update metadata, or delete a work; guests can browse but do not see those controls.
- Keep favorites and collection ownership associated with the current demo user. Owners can manage collections regardless of the `Public` flag; cross-user visibility and subscriptions are deferred. New collections default to non-public.
- After metadata review, rank reasonable matches using pHash, title, and composer; ask the user to confirm same/different without merging or changing either resource in this phase. If no reasonable matches exist, state that import is complete.
- Out of scope: Azure resources or SDKs, remote databases or storage, deployment automation, and containerization. Containerization is a later phase.

## 3. Architecture

The Flask process serves the UI and API from one local application. The Import Score wizard submits a candidate as multipart form data to `POST /library/import/check`. Flask validates it, checks the file hash and exact visual hash before saving, then creates a resource for unique uploads. The wizard updates title and metadata through the reusable `PATCH /library/<id>` endpoint.

`UploadService` reads the configured storage folder from `SettingsManager`, creates a GUID-based destination name, validates and hashes the file, and saves it locally. `FileProcessing` performs OCR and pHash generation/comparison, then infers metadata using the metadata definitions and options. `DataManager` reads and writes local JSON records; `SettingsManager` reads local settings and applies sensible defaults when settings are absent.

Keep boundaries between Flask routes, upload handling, file processing, data access, and settings access explicit so later work can replace local persistence or add settings without coupling those concerns to the route or UI.

## 4. Services & API

### Flask backend

- Language/framework: Python and Flask.
- Serve the home page and static frontend assets from Flask.
- Implement `POST /library/import/check` for duplicate preflight and unique resource creation, plus `PATCH /library/<id>` for reusable title/metadata updates.
- Return JSON for success and failure. Success includes the stored upload name, original name, OCR output/status, pHash match results with Hamming distances, and inferred metadata.
- Reject missing or unsupported files with a clear client error. Do not trust a client-supplied filename for a filesystem path; retain it only as original-name metadata.
- Bind local development to loopback by default; no network-facing deployment is part of this phase.

### Browser frontend

- Use plain HTML, CSS, and vanilla JavaScript served by Flask; do not add a frontend framework or build pipeline.
- Provide a file input and duplicate-check step at `/library/import/check` for logged-in users, followed by title/Core/extracted metadata review and expandable additional fields.
- Link exact SHA-256 or exact perceptual-hash duplicates to the existing work detail page without persisting another upload.
- Save title and metadata through the reusable `PATCH /library/<id>` resource update endpoint.
- Allow metadata and title edits from the detail page using the same field layout and reusable update endpoint.
- After saving, show a ranked list of reasonable matches using pHash, title, and composer signals and let the user confirm same/different. Do not start a merge or other workflow after confirmation; show import complete when no reasonable candidates exist.
- Show progress, request errors, and the returned upload, OCR, possible duplicate, inferred-metadata, and debug results.
- Keep the page usable with keyboard navigation and meaningful labels/status announcements.

## 5. Data & Settings

### Local `db.json`

Model the serialized table definitions and rows on `server/db/create_db.sql`, without connecting to MySQL. Preserve the schema concepts and relationships for `user`, `federated_credential`, `resource`, `favorites`, `metadata`, `collection`, and `collection_member`, including resource self-grouping, user/resource favorites with timestamps, metadata JSON/options/flags, defaults, and collection membership ordering/annotations. Seed metadata names, types, options, and flags from the SQL inserts. The resource `FileHash` column stores the SHA-256 file hash for exact duplicate detection. Every non-duplicate upload creates a `resource` row with the exact original client filename in `OriginalName`, a `DisplayName` taken from the first non-empty OCR line or the original filename without its extension, the GUID-based local path in `Source`, SHA-256 in `FileHash`, pHash in `VisualHash`, and OCR/inferred fields in `MetaData`. Initialize a Local Admin for the required `UserID` and associate each upload with it.

Initialize one local demo user with a `JoinedAt` timestamp and associate uploaded resources and owned collections with it. Keep federated credentials empty; the demo login is not real authentication. The `Public` flag does not change ownership or management rights; public visibility and subscriptions are future work. Use stable integer IDs and validate local references in `DataManager`. Write updates atomically through a temporary file and replace so an interrupted write does not leave malformed JSON; document that this single-process JSON store is for local use, not concurrent multi-instance access.

### `SettingsManager`

- Load settings from a local settings file and provide defaults when it does not yet exist.
- `storage_folder`: configurable local directory for GUID-named uploaded files. Resolve it consistently and create it when needed.
- `max_hamming_distance`: non-negative threshold used to classify pHash results as possible matches.
- Keep settings lookup/default handling extensible so later settings can be added without changing upload routes or processing callers.
- Do not add cloud configuration, secrets, or remote settings storage.

## 6. Design System & UI

**Component Library**: Pico.css, stored/served locally with the app; no CDN dependency. Use semantic HTML elements and small project-owned CSS additions rather than a JavaScript component framework.

The first screen leads with the latest three score uploads, each showing its thumbnail and title linking to details, plus a link to the full library. The detail page shows the original score, metadata, an uploader profile square with work count/join date, a favorite star, collection actions, and a delete action. The import wizard has an expandable Debug panel with raw OCR and hashes. Present processing state and upload results in a compact, readable layout. Ensure responsive layout, visible focus, sufficient contrast, and accessible form labels.

## 7. Processing Flow

1. The browser submits a score file to `POST /library/import/check`.
2. Flask validates the file and calculates SHA-256; a match returns the existing resource link without saving or creating a row.
3. If SHA-256 is unique, render the first page and compute its perceptual hash. An exact visual-hash match returns the existing resource link, without OCR or persistent storage.
4. If both checks are unique, run OCR and infer metadata, assign a GUID filename, save the original and thumbnail, and insert a resource row.
5. Show the title, Core fields, OCR-extracted values, and expandable additional fields for review.
6. Save edits using `PATCH /library/<id>`, which updates the resource's title and metadata and can be reused by other editing pages.
7. Rank reasonable existing resources using visual hash, title, and composer; show match candidates for same/different confirmation without merging or changing records. If none are reasonable, show import complete.
8. The frontend shows progress, duplicate links, raw Debug values, match results, and processing/update errors at the appropriate wizard step.

## 8. Implementation & Verification

Implement in this order: local configuration and settings defaults; schema-shaped JSON initialization and `DataManager`; upload and processing service boundaries; Flask route and response/error contract; then the served upload/results page.

Acceptance checks:

- The app starts locally with Python and Flask and serves the upload page without an external service.
- A valid supported score file is saved under the configured folder with a GUID-based name, and the original filename remains available in the result.
- Each analyzable upload generates a 128x128 PNG thumbnail beside the original; latest three appear on home, and `/library` lists all works with links to detail pages.
- Detail pages display the full-size image or embedded PDF and metadata; the delete action removes the resource and local original/thumbnail files and redirects home.
- Detail-page Edit mode presents the title, core metadata, and expandable additional fields to logged-in users; saving persists values through `PATCH /library/<id>`.
- Guests cannot import, edit metadata, or delete works; signed-in deletion requires browser confirmation and remains server-protected.
- Any visitor can download the original document from its detail page using a title-based filename, appending composer when present and retaining the original extension; download counts are deferred.
- The signed-in profile page shows account details, uploads, and all owned collections; collection rename, delete, and item removal are owner-scoped even when `Public=true`.
- Every successful upload is persisted as a `resource` row with its pHash and local file location; a subsequent upload compares against that row.
- An exact byte-for-byte re-upload is rejected before OCR/pHash, returns HTTP 409, removes only the newly uploaded copy, and leaves resource row counts unchanged.
- `/library/submit` returns the documented success payload, including OCR status/text, pHash match details, and inferred metadata; invalid or missing files produce a clear JSON error.
- The configured Hamming-distance threshold changes which candidates are returned as possible matches.
- After metadata save, ranked reasonable matches show title/composer and hash distance for review; confirming same/different does not merge resources or start another workflow. With no candidates, the UI states that import is complete.
- `db.json` preserves the reference table definitions and relationships across reads/writes, including metadata options and the Local Admin association.
- Settings defaults work when no settings file exists; changing the storage folder or threshold affects subsequent processing, and additional settings can be represented without redesigning the manager.
- The browser presents success, no-match, in-progress, and failure states and remains usable at narrow viewport widths and with keyboard navigation.

## 9. Local Run & Prerequisites

Use Python 3.x in a virtual environment and install the chosen pip packages for Flask, OCR integration, PDF rendering, and image hashing. Install the Tesseract executable separately and make it available on `PATH`; install Poppler or the selected PDF renderer's equivalent if required. Ensure the process can write to the configured upload folder, settings file, and `db.json` location.

Run the Flask application locally from the `vibe/` project root. Keep generated uploads, settings, and database data local; do not require Azure credentials, network storage, a remote database, or container tooling.

## 10. Deferred Work

Containerization, deployment, remote persistence, real authentication, and concurrent operation require a later approved phase. The fake demo login is only for exercising user-owned favorites and collections locally.