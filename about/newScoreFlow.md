# New score flow

How a score gets into the library today (in the `vibe/` proof of concept) and how we want it to work. The proposals here are ideas to discuss, not decisions. Moderation is covered in [moderation.md](moderation.md).

## How it works today

The import page is a three-step wizard: **Upload**, **Review details**, **Possible related works**.

### 1. Upload: `POST /api/library/import/check`

The user must be logged in. The server runs these checks in order and stops at the first one that fails:

1. **Validate the file.** It checks the type (PDF or image) and the size (25 MB at most).
2. **Backfill old file hashes.** Every resource that has no `FileHash` is hashed from disk and updated. This runs on *every* upload.
3. **Exact file duplicate.** If the file's SHA-256 matches a non-deleted resource, the server returns `status: "duplicate"` (`match_type: "sha256"`) and stores nothing.
4. **Render the first page** and compute its 64-bit perceptual hash (dHash).
5. **Exact visual duplicate.** If another resource has the *same* visual hash, it returns `status: "duplicate"` (`match_type: "phash"`) and stores nothing.
6. **Is it sheet music?** The visual hash is compared with a folder of reference score images. If the closest reference is farther than `invalid_hamming_distance` (default 50), the server returns HTTP 422 with `status: "rejected"` and `reason: "not_sheet_music"`, and stores nothing.
7. **Process the page.** The server:
   - makes thumbnails;
   - extracts the text: from the PDF's text layer for MuseScore, Sibelius or LilyPond PDFs, otherwise with OCR;
   - finds visual matches within `max_hamming_distance` (default 10);
   - infers metadata (for example Tone or Style) from the text.
8. **Save.** It stores the file and thumbnails and inserts a `resource` row. The title is the first line of text, or the file name if there is none. The response is `status: "created"`, with `inferred_metadata`, OCR text and matches.

### 2. Review details: `PATCH /api/library/<id>`

The user corrects the title and metadata. The server saves them, then ranks similar resources by:

- visual hash distance (≤ `max_hamming_distance`);
- title similarity (≥ 72%);
- title (≥ 50%) plus composer (≥ 85%).

### 3. Possible related works

The user can mark each match as **Same work** or **Different work**, but this is only shown on screen. Nothing is saved and neither record changes.

### What the resource looks like afterwards

The new row has `Public = false` and `Reviewed = false`. However, nothing reads those columns. `visible_resources()` only filters out `Deleted`, so a new upload shows up straight away in search, latest and detail pages for everyone.

### Problems with the current flow

- **False rejections.** A score that is far from every reference image may still be real music, such as an unusual layout, handwritten chant or a style we have no reference for. Today the user is turned away and the file is lost.
- **Exact visual-hash match isn't proof of a duplicate.** The same edition may have been scanned at a different quality, and we can't tell which copy is better, so this shouldn't silently block the upload.
- **There's no way to act on a match.** "Same work" is thrown away. Better copies can't replace worse ones, and different versions of the same hymn can't be linked.
- **There's no review.** Anything uploaded is public straight away.
- **The backfill loop runs on every upload.** It reads every un-hashed file from disk. This should be a one-time migration.
- **Duplicate checks only see non-deleted rows.** Once there are private uploads, they must also check private rows from other users, without revealing those rows.

## Proposed flow

Accept almost everything, keep it private, and let people sort it out afterwards.

1. **Validate** the type and size. Unchanged.
2. **Exact file duplicate (SHA-256).** This is still a hard stop, because there is nothing to gain from storing the same bytes twice.
   - If the match is public or belongs to the uploader, link to it.
   - If it is someone else's private upload, say only "This file has already been uploaded and is waiting for review." Don't reveal the title or the owner.
3. **Render, hash and extract text.** Same as today.
4. **Save** as `Public = false` and `Reviewed = false`, which appears as "Unmoderated" in the UI. The uploader can see and use it right away (favorite it, add it to a collection, download it), and it shows a clear **Unmoderated** tag.
5. **Record flags instead of rejecting.** Store the signals moderators need:
   - `not_sheet_music`: the reference distance is above `invalid_hamming_distance`;
   - `near_duplicate`: the visual distance is ≤ `max_hamming_distance`, or the visual hash is exactly the same;
   - `no_text`: OCR or text extraction found nothing;
   - `title_match`: the title or alias matches an existing work (see [Works](#works-grouping-different-versions-of-the-same-piece)).

   The thresholds become *priority hints*, not gates.
6. **Review details.** Same as today, plus two new questions for the uploader:
   - *Is this the same piece as an existing work?* This links it to a work.
   - *Is this a better copy of an existing score?* This proposes a replacement.

   Both are saved as proposals for a moderator to confirm.
7. **Moderation.** A moderator approves the upload (it becomes public), rejects it (it is set as deleted) or confirms or edits the proposals. See [moderation.md](moderation.md).

The response states reduce to `created` (with flags), `duplicate` (SHA-256 only) and `error`. The `rejected` / `not_sheet_music` state goes away.

Open questions:

- Should a user be able to keep an upload private on purpose (for example a personal or copyrighted copy) without asking for moderation? If so, add a "Keep private" choice that skips the queue.
- Do we still want *any* hard limit? For example, a blank page or a photo of a cat at distance 60 or more. We could keep a much higher `invalid_hamming_distance` as an anti-spam limit, or rely on rate limits and moderation.

## Replacing a score with a better copy

When two files are the *same edition* (same engraving, same page) and one is cleaner, we want the better one to take over without breaking anyone's favorites, collections or links.

### Model

Add a `ReplacedBy` column to `resource` (nullable, pointing to `resource.id`).

- The replaced resource stays in the database with its file. It is hidden from search and latest.
- Requests for `/library/<old>` redirect to `/library/<new>` (HTTP 301 from the API, or a banner saying "This score was replaced by a better copy").
- A chain (A replaced by B, then B replaced by C) is followed to the end. A replacement must not form a loop.

### Favorites and collections

There are two options:

| | Rewrite at replace time | Resolve at read time |
|---|---|---|
| How | Change `favorites.ResourceID` and `collection_member.ResourceID` from old to new | Leave the rows alone. When reading, follow `ReplacedBy` |
| Pros | Simple queries. Old rows can be cleaned up later | Fully reversible. Keeps history |
| Cons | Undo needs a log of what was moved | Every read has to follow the chain |

Recommendation: **rewrite at replace time and log it** in a `moderation_action` entry (see [moderation.md](moderation.md)), so an undo can move the rows back. Edge cases:

- A user who favorited *both* ends up with one favorite. Keep the earlier `FavoritedAt`.
- A collection that holds both keeps the new one at the position of whichever came first, plus its `Annotation`. If both had an annotation, join them.
- Copy `DownloadCount` and any metadata the new resource is missing from the old one, but don't overwrite values the new one already has.

### Who can replace

- The uploader *proposes* the replacement during import (question 6 above) or from the detail page.
- A moderator *confirms* it. Replacing public content changes other people's collections, so a regular user can't do it alone.

## Works: grouping different versions of the same piece

Choir directors want "all the Our Fathers", even when they are titled "The Lord's Prayer", "Our Father", "Отче наш" or "Pater Noster", and come in Byzantine, Znamenny and Kievan settings. That isn't something title similarity can find reliably.

### Model

- `work` (`id`, `Name`, `Description`, optional liturgical fields such as hymn type or feast). This is the *piece of music*, independent of any setting.
- `work_alias` (`WorkID`, `Name`, `Language`). These are the alternative titles. Store them normalized for matching, as `rank_similar_resources` already does.
- `resource.WorkID` (nullable). This is a resource's link to its work. A resource can belong to only one work.

This is separate from the existing `resource.GroupID`, which links *one* score to its parts, MIDI and lyrics files. Keep `GroupID` for that, and consider renaming it to `ParentID` so the two don't get confused.

### Matching

- On import, compare the title and OCR text with **all aliases**, not just other resources' titles. An exact alias match is strong evidence. A fuzzy match is a suggestion.
- Show the matched work, not individual scores, as the first choice: "Is this *The Lord's Prayer*?" Then show near-identical scores below it as possible replacements.
- When a user chooses "Same work", the resource is linked to that work as a proposal. A moderator confirms it, adds an alias if the title was new, or merges two works that turn out to be the same.

### Non-literal matches

Aliases are maintained by people, not inferred. Liturgical texts have many translations, and only someone who knows the services will know that "Gladsome Light" and "O Joyful Light" are the same hymn. We can seed aliases for the common texts and let moderators add the rest. Later, metadata such as hymn type, feast and tone can narrow the suggestions, for example "Exapostilarion for Nativity".

## Summary of proposed changes

- Remove the `not_sheet_music` rejection and the exact-visual-hash block. Store them as flags.
- New uploads start private and unmoderated. Enforce `Public` everywhere resources are listed or served.
- Make the old file-hash backfill a one-time migration.
- Add `ReplacedBy` and a replacement action that moves favorites and collection entries, with a log.
- Add `work` and `work_alias`, and `resource.WorkID`. Turn the "Same work" button into a saved proposal.

[<- Back](README.md)
