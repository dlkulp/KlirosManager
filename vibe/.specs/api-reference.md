# Kliros Manager Backend API

Reference for the current Flask PoC in `vibe/app.py`. The dependency-free TypeScript client and request/response DTOs are in [api-client.ts](api-client.ts). Field casing matches the wire format, including `UserID`, collection `UserId`, resource `MetaData`, and update request `metadata`.

## Transport and Authentication

- Base URL: the running app origin, currently `http://127.0.0.1:5004`. Paths below include `/api`; do not append `/api` to the client's `baseUrl`.
- Responses are JSON except file, download, and thumbnail responses, which are binary.
- Login is a demo session for user 1, not real identity-provider authentication. Login/logout take no request body.
- Flask uses a session cookie, not a bearer token. The wrapper sends `credentials: "include"`; a native/mobile client must maintain an equivalent cookie jar through its fetch adapter.
- `/api/*` allows credentialed CORS from the `cors_allowed_origins` array in `settings.json`; the default entries are `http://localhost:5173` and `http://127.0.0.1:5173`. The optional `CORS_ALLOWED_ORIGINS` environment variable overrides the array with a comma-separated list; Flask app config can also override it. Entries must be exact origins (scheme/host/port); wildcard values are ignored or rejected by settings validation. Allowed origins receive GET/POST/PATCH/DELETE/OPTIONS, `Content-Type`/`Authorization` request headers, exposed `Content-Disposition`/`ETag`/`Last-Modified`, and a 600-second preflight cache. Denied origins receive no allow-origin header. `OPTIONS` is handled by Flask's automatic route preflight. Restart Flask after changing settings.
- The TypeScript client sends `credentials: "include"`; cross-origin browser clients must retain/send Flask's session cookie. Different localhost ports work with `SameSite=Lax`. For a cross-site HTTPS frontend, set `SESSION_COOKIE_SAMESITE=None` and `SESSION_COOKIE_SECURE=true`; third-party cookie blocking may still require same-site hosting or a reverse proxy.
- JSON mutations use `Content-Type: application/json`. Import uses multipart form data; let fetch set the multipart boundary.
- IDs are integers. Returned URLs are server-relative, including some legacy URLs in import responses; resolve against the backend origin, not a separately hosted frontend origin.
- DTOs provide compile-time typing, not runtime schema validation. Metadata is flexible JSON, and metadata definitions/options should be read from responses rather than hard-coded.

## Endpoint Index

All successful responses below use HTTP 200. `Auth` means a signed-in cookie session is required.

| Method | Path | Auth | Request | Response DTO |
| --- | --- | --- | --- | --- |
| GET | `/api/session` | No | None | `SessionResponseDto` |
| POST | `/api/login` | No | None | `LoginResponseDto` |
| POST | `/api/logout` | No | None | `LogoutResponseDto` |
| GET | `/api/home` | No | None | `HomeResponseDto` |
| GET | `/api/library` | No | None | `LibraryResponseDto` |
| GET | `/api/search` | No | `SearchRequestDto` as query parameters | `SearchResponseDto` |
| GET | `/api/profile` | Yes | None | `ProfileResponseDto` |
| GET | `/api/library/{id}` | No | Resource ID | `ResourceDetailResponseDto` |
| PATCH | `/api/library/{id}` | Yes | `UpdateResourceRequestDto` JSON | `UpdateResourceResponseDto` |
| DELETE | `/api/library/{id}` | Yes | Resource ID; no body | `DeleteResourceResponseDto` |
| POST | `/api/library/{id}/favorite` | Yes | Resource ID; no body | `FavoriteResponseDto` |
| DELETE | `/api/library/{id}/favorite` | Yes | Resource ID; no body | `UnfavoriteResponseDto` |
| POST | `/api/library/{id}/collections` | Yes | `ResourceCollectionRequestDto` JSON | `ResourceCollectionResponseDto` |
| PATCH | `/api/profile/collections/{collectionId}` | Yes | `RenameCollectionRequestDto` JSON | `RenameCollectionResponseDto` |
| DELETE | `/api/profile/collections/{collectionId}` | Yes | Collection ID; no body | `DeleteCollectionResponseDto` |
| DELETE | `/api/profile/collections/{collectionId}/items/{resourceId}` | Yes | IDs; no body | `RemoveCollectionItemResponseDto` |
| PATCH | `/api/admin/users/{userId}/type` | Admin | `UpdateUserTypeRequestDto` JSON | `UpdateUserTypeResponseDto` |
| POST | `/api/library/import/check` | Yes | `ImportCheckRequestDto` as multipart | `ImportCheckResponseDto` |
| GET | `/api/library/{id}/file` | No | Resource ID | Binary original; `BinaryResponseDto` in wrapper |
| GET | `/api/library/{id}/download` | No | Resource ID | Binary attachment; `BinaryResponseDto` in wrapper |
| GET | `/api/library/{id}/thumbnail` | No | Resource ID | PNG at height 300; `BinaryResponseDto` in wrapper |
| GET | `/api/library/{id}/thumbnail/{height}` | No | Height 300 or 600 | PNG; `BinaryResponseDto` in wrapper |

## Response Models

Full TypeScript declarations are in [api-client.ts](api-client.ts).

| DTO | Fields / Meaning |
| --- | --- |
| `UserDto` | `UserID`, `Name`, `Email`, `JoinedAt` (local date/time string, no timezone), `UserType` (`regular`, `moderator`, `admin`) |
| `SessionResponseDto` | `{logged_in: true, user: UserDto}` or `{logged_in: false, user: null}` |
| `ResourceDto` | Visible resource fields `id`, `DisplayName`, `OriginalName`, `MetaData`, `GroupID`, `Source`, `UserID`, `Reviewed`, `Public`, `Hidden` (false/null), `VisualHash`, `FileHash`; optional `DownloadCount`; derived `title`, `thumbnail_url`, `thumbnail_srcset`, `thumbnail_sizes`, `detail_url`, `api_url` |
| `HomeResponseDto` | `recent_works: ResourceDto[]`, latest three resource IDs first |
| `LibraryResponseDto` | `works: ResourceDto[]`, all resources, descending ID |
| `SearchResponseDto` | `results`, `total`, `page`, `page_size`, `page_count`, `facets`; result resources add `uploaded_at` and `popularity` |
| `CollectionDto` | `id`, `Name`, `Public`, `UserId` |
| `ProfileResponseDto` | `user`, `initials`, `uploads`, `favorites`, `collections`; each collection adds `items: ResourceDto[]` |
| `MetadataDefinitionDto` | `id`, `Name`, `Type`, `Options`, `Core`, `Extracted`, `Searchable`, optional `Required` |
| `MetadataFieldDto` | Metadata definition plus current or inferred `value` |
| `ResourceDetailResponseDto` | `resource`, `original_name`, `uploader`, `uploader_initials`, `uploader_resource_count`, `is_favorite`, `is_logged_in`, `user_collections`, `resource_collection_ids`, `ocr`, `metadata_details`, `metadata_fields`, `metadata_summary`, `is_pdf`, `file_url`, `download_url` |
| `OcrDto` | `status` (`success`, `unavailable`, `error`), `text`, `message`; detail's `ocr` may be empty when absent |
| `RankedMatchDto` | `resource_id`, `title`, `original_name`, `composer`, nullable `hamming_distance`, `title_similarity`, `composer_similarity`, numeric `confidence`, `detail_url`, `preview_url` |
| `BinaryResponseDto` | Client-side envelope: `body: Blob`, `content_type`, `content_disposition`; these are not server JSON fields |

Nullable resource fields follow the local database schema; thumbnail URLs/srcset are null when the source file is absent. `Source` exposes a backend-local path, not a URL clients should fetch. `MetaData` may contain primitives, arrays, `{value, source, reviewed}` objects, OCR, and hash data. Detail `metadata_details` is an array of `[name, value]` pairs; object/array values are JSON-encoded strings. `metadata_summary` contains `{name, value}` strings for defined nonempty metadata fields. Unknown uploaders fall back to `{Name: "Unknown user", JoinedAt: ""}`.

## Search

| Query Parameter | Default | Behavior |
| --- | --- | --- |
| `q` | Empty | Trimmed, case-insensitive substring match across derived title, original filename, and all metadata values, including non-searchable fields |
| `filters` | `{}` | JSON-encoded object, e.g. `{"Service":"Vespers","Language":"English"}`; selected fields combine with AND; values use case-insensitive exact matching |
| `page` | `1` | Minimum 1; clamped to the last available page; empty results still return page 1 |
| `page_size` | `24` | Allowed values: 24, 48, 96; other values fall back to 24 |
| `sort` | `uploaded` | `uploaded`, `popularity`, or `name`; unknown values fall back to `uploaded` |

Malformed/non-object `filters` returns 400. Unknown/non-searchable filter names, non-string values, and blank values are ignored. If either numeric pagination parameter is not an integer, both reset to their defaults. Facets include only definitions with `Searchable: true`; options retain definition order and append distinct stored values. Facets cover the whole library, not just the filtered page; some can be empty.

Upload sorting uses source-file modification time in epoch seconds, falling back to resource ID. Popularity uses numeric download count when present, otherwise favorites count. Name sorting is ascending/case-insensitive; popularity/upload sorts are descending. An empty result has `total: 0`, `page_count: 0`, `page: 1`, and `results: []`.

## Profile, Favorites, and Collections

`GET /api/profile` returns only the current user's uploads, favorites, and owned collections. Favorites sort by `FavoritedAt` descending; collections sort by name; collection items sort by membership ID. The profile payload omits favorite timestamps and collection-member order/annotation fields.

- Favorite POST toggles and returns `{is_favorite: boolean}`. It is not safe to blindly retry.
- Favorite DELETE is idempotent and returns `{is_favorite: false}`. It removes only the current user's favorite, not the score or other users' favorites.
- Collection POST either uses `{collection_id, action?: "add" | "remove"}` or creates and populates a new collection with `{new_collection_name, action?: "add"}`. Default action is `add`; new collections are private.
- Collection POST returns `{collection, collection_id, is_public, added, changed}`. Re-adding an existing member yields `added: false, changed: false`. Removal always has `added: false`; `changed` indicates an actual removal. Invalid action/collection/new-name combinations return 400.
- Rename uses `{name}` and returns `{collection: CollectionDto}`. A trimmed nonempty name of at most 255 characters is required. Invalid names return 400; unowned/missing collections return 404.
- Delete collection returns `{deleted: true, collection_id}` and removes memberships, not scores. Unowned/missing collections return 404.
- Delete collection item returns `{removed: boolean, resource_id}`. Missing membership is not an error (`removed: false`); unowned/missing collection returns 404.

Collection authorization is ownership-based regardless of `Public`. There are no standalone create/list collection APIs: use profile to list, and resource collection POST to create and add a work.

## User Types

The SQL and JSON schemas use a `UserType` enum with `regular`, `moderator`, and `admin`; new database users default to `regular`, while the seeded `Local Owner` is `admin`. Existing JSON database schema-version-7 accounts migrate to `regular`, except user ID 1, which remains/becomes `admin`.

`PATCH /api/admin/users/{userId}/type` accepts `{"user_type":"moderator"}` or `{"user_type":"regular"}` and returns `{ "user_id": number, "user_type": "regular" | "moderator" }`. Only a signed-in admin can call it. Anonymous requests return 401, signed-in non-admin requests return 403, unknown users return 404, and invalid input returns 400. Admin users cannot be demoted through this endpoint, and the endpoint cannot grant admin status.

## Import and Metadata Update

Import-check is a **write operation**, not a preview. It validates and compares the file, then stores a resource immediately if no duplicate/rejection is found. Review/save is a subsequent PATCH; there is no transaction spanning both requests.

Send multipart field `file` with its original filename. Extensions: `.pdf`, `.png`, `.jpg`, `.jpeg`, `.tif`, `.tiff`, `.bmp`, `.webp`, `.gif`. Filename must be at most 255 characters; content must match the extension. Maximum request body is 25 MiB (the server error text calls it 25 MB).

| Status | HTTP | Response |
| --- | --- | --- |
| `created` | 200 | `ImportCreatedResponseDto`: `upload`, `ocr`, nullable `visual_hash`, initial `matches`, `inferred_metadata`, `debug`, `metadata_fields`, `errors` |
| `duplicate` | 200 | `ImportDuplicateResponseDto`: `match_type` (`sha256` exact file or `phash` identical first-page perceptual hash), `duplicate`, `debug`; no new copy stored |
| `rejected` | 422 | `ImportRejectedResponseDto`: `reason: "not_sheet_music"`, `error`, `debug`, `reference_check` (distance, reference image, threshold); no new resource stored |
| `error` | 400/401/413/415/500/503 | `{status: "error", error: string}`; thrown as `ApiError` by the client |

`upload` contains `resource_id`, `stored_name`, `original_name`, `title`, `source`, thumbnail URLs/srcset, and `detail_url`. `debug` contains `file_hash`, nullable `visual_hash`, and `ocr_text`. Initial import matches have only `resource_id`, `original_name`, `visual_hash`, and `hamming_distance`; they are **not** `RankedMatchDto` and do not contain preview/detail URLs. Inferred metadata values have `value`, `source: "ocr"`, and `reviewed: false`. A created response may contain non-fatal OCR/thumbnail errors; do not treat `errors.length > 0` as a failed import.

PATCH `/api/library/{id}` accepts:

```json
{
  "DisplayName": "Evening Hymn",
  "metadata": {"Service": "Vespers", "Language": "English", "Composer": ""}
}
```

Title is required, trimmed, and limited to 255 characters. `metadata` is optional (default `{}`); keys must be defined metadata fields. Only submitted metadata keys change; empty string/null clears a field. Other values are stored as `{value, source: "user", reviewed: true}`. The backend does not enforce metadata type/option choices. Response: `{status: "updated", resource_id, title, detail_url, matches: RankedMatchDto[], import_complete}`. `import_complete` is true when no ranked matches exist. Match confirmation is currently browser-only; there is no merge/confirmation endpoint.

## Files, Thumbnails, and Soft Deletion

- `/file` returns the original inline with its detected media type (fallback `application/octet-stream`).
- `/download` returns the original attachment. `Content-Disposition` provides a sanitized title/composer filename (arranger fallback), preserving the original extension. Download counts are not incremented.
- `/thumbnail` and `/thumbnail/{height}` return PNGs at height 300 or 600, with approximate widths 232 or 464. Missing thumbnails may be generated lazily. Unsupported height, missing record/source, or generation failure returns 404.
- Resource lists, search results/facets, profile uploads/favorites/collection items, duplicate checks, match candidates, detail pages/APIs, and media endpoints omit or return 404 for hidden resources.
- DELETE resource soft-deletes by setting `Hidden: true` and returns `{deleted: true, hidden: true, resource_id}`. It keeps the row, source and thumbnails, group references, favorites, and collection memberships. Repeating DELETE returns 404. Hidden resources can still be inspected in the local database but are not returned by public resource endpoints.
- File/thumbnail routes can return conditional HTTP 304; the wrapper does not send conditional headers by default. A custom fetch that returns an uncached 304 will be treated as an error.

## Errors and PoC Limits

Most API errors contain `{error: string}` with optional `status: "error"`, but Flask `abort()` responses and unexpected exceptions can be HTML. Common codes are 400 (invalid input), 401 (login required), 404 (missing/unowned resource or collection), 413 (request too large), 415 (unsupported/mismatched upload), 422 (not sheet music), 500 (processing/internal failure), and 503 (image validation dependency unavailable).

`KlirosApi` throws `ApiError` with `status` and the parsed error JSON or raw response text in `body`. Recognized import 422 rejections are returned as the discriminated union instead. Network failures and aborts propagate fetch's native errors. The wrapper does not retry mutations. Any injected fetch adapter must also avoid blind retries of POST/PATCH operations.

Current authorization limits: metadata update and resource deletion require login but **not uploader ownership**; all signed-in users can edit/delete a work. Public read APIs filter hidden resources but do not filter by `Public`. The local JSON store supports one process, not concurrent multi-instance writers. CORS is an origin-sharing policy, not authentication or CSRF protection; the demo login and other production security controls remain unsuitable for production.

## Legacy and Static Routes

These routes are not used by the typed client:

| Route | Behavior |
| --- | --- |
| GET `/`, `/library`, `/search`, `/profile`, `/import` | Static HTML shells |
| GET `/library/{id}` | Detail HTML shell for a visible resource; hidden/missing resources return 404 |
| POST `/login`, `/logout` | Demo session actions followed by 302 redirect |
| POST `/library/import/check`, PATCH `/library/{id}` | Aliases of the API import/update routes |
| POST `/library/{id}/favorite`, `/library/{id}/collections` | Aliases of API mutations; no legacy DELETE favorite alias |
| GET `/library/{id}/file`, `/download`, `/thumbnail`, `/thumbnail/{height}` | Under `/library/{id}`; aliases of the corresponding API media routes |
| POST `/library/{id}/delete` | Soft-delete work, then 303 redirect to home |
| POST `/profile/collections/{id}/rename` | Form field `name`, then 302 redirect to profile |
| POST `/profile/collections/{id}/delete` | Delete owned collection, then 302 redirect |
| POST `/profile/collections/{id}/items/{resourceId}/delete` | Remove owned collection member, then 302 redirect |
| GET `/static/{path}` | Flask static CSS/JS/assets; not a data API |

## TypeScript Usage

```ts
import { ApiError, KlirosApi } from "./api-client";

const api = new KlirosApi({ baseUrl: "http://127.0.0.1:5004" });
await api.login();
const page = await api.search({ q: "hymn", filters: { Service: "Vespers" }, page_size: 24 });
const profile = await api.getProfile();
if (profile.favorites.length) await api.unfavorite(profile.favorites[0].id);

async function importScore(file: File) {
  try {
    const result = await api.checkImport({ file, filename: file.name });
    if (result.status === "created") {
      return api.updateResource(result.upload.resource_id, {
        DisplayName: result.upload.title,
        metadata: { Language: "English" },
      });
    }
    if (result.status === "duplicate") return result.duplicate;
    return result.error;
  } catch (error) {
    if (error instanceof ApiError) console.error(error.status, error.message, error.body);
    throw error;
  }
}

const download = await api.downloadResource(1);
const objectUrl = URL.createObjectURL(download.body);
// Use the blob URL, then release it when no longer needed.
URL.revokeObjectURL(objectUrl);
```

The wrapper requires standard fetch, FormData, Blob, URLSearchParams, and AbortSignal APIs (modern browsers or a compatible native/Node adapter). Pass an `AbortSignal` as the method's options argument for cancellation. The TypeScript source is a handoff artifact for another frontend; the existing vanilla-JS PoC does not import it and still has no frontend build step. Validate with TypeScript using `--strict --noEmit --target ES2022 --module ES2022 --lib ES2022,DOM api-client.ts`.