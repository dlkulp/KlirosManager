# Moderation

Early thinking on how uploaded scores get reviewed before they are public. This is a companion to [newScoreFlow.md](newScoreFlow.md). Score-approval changes below remain proposals; user flag reporting is implemented as described in its own section.

## Roles

Users already have a `UserType` of `regular`, `moderator` or `admin`. An admin can switch a user between regular and moderator.


|                                        | Regular                      | Moderator             | Admin                 |
| ---------------------------------------- | ------------------------------ | ----------------------- | ----------------------- |
| Upload                                 | Yes                          | Yes                   | Yes                   |
| See own private uploads                | Yes (tagged **Unmoderated**) | Yes                   | Yes                   |
| See others' private uploads            | No                           | Yes                   | Yes                   |
| Approve, reject, replace, manage works | No                           | Yes                   | Yes                   |
| Delete own upload                      | Yes                          | Yes                   | Yes                   |
| Delete anyone's upload                 | No                           | Yes (already allowed) | Yes (already allowed) |
| Change user roles                      | No                           | No                    | Yes                   |
| Restore a rejected or deleted upload   | No                           | ?                     | Yes                   |

## Resource states

The `resource` table already has `Public`, `Reviewed`, `ReviewerId`, `ReviewedAt` and `Deleted`. Today only `Deleted` is enforced.


| State                    | Public      | Reviewed | Deleted                      | Who sees it                                                                                                                  |
| -------------------------- | ------------- | ---------- | ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------ |
| Unmoderated (new upload) | false       | false    | false                        | Uploader, moderators, admins                                                                                                 |
| Approved                 | true        | true     | false                        | Everyone                                                                                                                     |
| Rejected                 | false       | true     | true                         | Moderators and admins only (for audit and undo). Uploader needs some view of thumbnail and "rejected", but not details page. |
| Deleted by owner         | any         | any      | true                         | Moderators and admins only                                                                                                   |
| Replaced                 | (unchanged) | true     | false, with `ReplacedBy` set | Nobody directly. Links redirect to the replacement                                                                           |

The booleans allow combinations that make no sense, such as `Public = true` with `Reviewed = false`. A single `Status` column (`unmoderated`, `approved`, `rejected`, `deleted`) would be clearer. Keep `Deleted` until the migration is done.

TODO: Switch to `Status` column. Consider a status for "replaced" when a better copy is found and linked. Replaced items cannot be searched or viewed (viewing redirects). Uploader still sees their thumbnail but a message like "this has been replaced." Similarly, for "rejected", uploader can see thumbnail with message "this upload has been rejected." Need to determine how long rejected/replaced thumbnails appear and if they can be dismissed from uploader's view somehow.

## Actions


| Action           | Effect                                                                                                                                                                                 |
| ------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Approve**      | `Public = true`, `Reviewed = true`, sets `ReviewerId` and `ReviewedAt`. The moderator can fix the title and metadata at the same time.                                                 |
| **Reject**       | `Deleted = true`, `Reviewed = true`, with a required reason (see below). The file stays on disk until it is purged.                                                                    |
| **Replace**      | Confirms an "is a better copy of" proposal. Sets `ReplacedBy` and moves favorites and collection entries. See [newScoreFlow.md](newScoreFlow.md#replacing-a-score-with-a-better-copy). |
| **Link to work** | Confirms or changes `WorkID`, adds aliases, or merges two works.                                                                                                                       |
| **Undo**         | Reverses any of the above, using the action log.                                                                                                                                       |

Rejection reasons, a fixed list plus free text:

- Not sheet music.
- Duplicate of an existing score (link it).
- Copyrighted, or not allowed to be shared.
- Unreadable or poor quality.
- Inappropriate.
- Other.

## Queue

Moderators work from a queue of unmoderated uploads, oldest first by default. Each item shows:

- the thumbnail, title, metadata and uploader;
- the flags from import: `not_sheet_music`, `near_duplicate`, `no_text` and `title_match` (see [newScoreFlow.md](newScoreFlow.md#proposed-flow));
- the uploader's proposals: "same work as…" and "better copy of…", shown side by side for comparison.

Filters by flag let a moderator handle the easy cases quickly. For example, approve everything with no flags, then work through `near_duplicate` with side-by-side previews.

## Visibility rules

Once `Public` is enforced, every place that lists or serves resources must apply the same check: *public, or owned by the current user, or the current user is a moderator or admin*. The places that need it:

- Search, search facets and `/api/latest`. Most likely public only, even for the owner, so that unmoderated scores don't appear in shared lists. Owners see theirs on their profile instead.
- The detail page, file, download and thumbnail endpoints.
- Profiles: another user's profile shows only their public uploads.
- Collections and favorites. A public collection may contain a private resource. Hide those items from other viewers rather than showing broken entries.
- Duplicate checks. These look at *all* rows, but must not reveal another user's private resource (see [newScoreFlow.md](newScoreFlow.md#proposed-flow)).

Put the rule in one helper in `DataManager`, for example `resources_visible_to(user)`, instead of repeating it in each route.

## User flag reports (implemented)

The Flask PoC stores one report per submission in `flag_reports`: `id`, `ResourceID`, nullable reporter `UserID`, `ReasonCode`, `Notes`, `CreationDate`, nullable `ResolutionDate`, `IsSustained`, nullable `ResolutionUserID`, and `ResolutionNotes`.

`flag_report_reasons` maps `Code` to `DisplayMessage`. Starter codes are `copyright`, `inappropriate`, `not_church_music`, `metadata_mismatch`, and `other`. These user reports are separate from automatic import flags and from the proposed upload-approval queue.

- Guests and signed-in users can report a non-deleted score through `POST /api/library/{id}/flags`. The reporter comes from the session or is null for an anonymous report. The existing **Report to Moderator** dialog loads reasons from `GET /api/flag-report-reasons` and now sends the report.
- Admins, not moderators, fetch unresolved reports through `GET /api/admin/flag-reports`, oldest creation date first with report ID breaking ties. Reported scores that are subsequently deleted remain reviewable in this API queue.
- Admins resolve through `PATCH /api/admin/flag-reports/{id}/resolve` with a boolean `is_sustained` and optional `resolution_notes`. Both notes fields are limited to 2000 characters.
- Sustaining a report records the decision only; it does not change the score. Resolved reports remain stored, leave the pending queue, and cannot have their resolution overwritten.

The SQL reference schema and automatic JSON schema-version-10 migration include both tables. Contracts and client methods are in [the API reference](../vibe/.specs/api-reference.md#flag-reports). No admin review screen is implemented yet.

TODO: A flag history endpoint/page would allow admins to review flags that have already been resolved.

## Audit log

Add a `moderation_action` table: `id`, `ResourceID`, `ModeratorID`, `Action`, `Reason`, `Details` (JSON, for example the moved favorite and collection rows for a replacement), `CreatedAt`. This gives a history per resource, makes Undo possible, and lets an admin review what moderators have done.

## Notifying uploaders

Uploaders should learn what happened to their upload. In order of effort:

1. The status and rejection reason on the user's own profile.
2. In-app notifications.
3. Email.

Starting with the first is enough.

## Open questions

- Q: Do uploads by moderators and admins skip the queue, or does someone else still have to review them?
  A: These should skip the queue.
- Q: Can a user withdraw an unmoderated upload, or choose to keep it private for good?
  A: They can delete their own upload regardless of status. We do not allow private scores.
- Q: How long are rejected files kept before they are purged from disk?
  A: TBD
- Q: Can trusted regular users have their uploads approved automatically after a number of approvals?
  A: TBD
- Q: Who can edit the metadata of an approved, public score? The owner only, moderators, or anyone through a suggestion that is then moderated?
  A: Owner, moderator, admin. Another user could flag the score and choose a reason indicating metadata mismatch.
- Q: Copyright: do we need a takedown request process separate from moderation?
  A: This should be one of the reasons for flagging.
- Q: What happens when a flag is sustained (found to be valid)?
  A: This should probably lead to the item being soft-deleted, but also removed from favorites and collections. Or, like YouTube, collections sometimes contain items which are no longer available. TBD

[<- Back](README.md)
