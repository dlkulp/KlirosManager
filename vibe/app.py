"""Local Flask application for uploading and analyzing score files."""

from __future__ import annotations

import os
import json
import io
import mimetypes
import hashlib
import tempfile
from pathlib import Path
from typing import Any

from flask import Flask, abort, jsonify, redirect, request, send_file, session, url_for
from werkzeug.utils import secure_filename

from data_manager import DataManager
from service.UploadService import UploadService, UploadValidationError
from service.FileProcessing import FileProcessing
from settings_manager import SettingsManager


PROJECT_ROOT = Path(__file__).resolve().parent


def create_app(test_config: dict[str, Any] | None = None) -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_mapping(
        DATABASE_PATH=PROJECT_ROOT / "db.json",
        SETTINGS_PATH=PROJECT_ROOT / "settings.json",
        MAX_CONTENT_LENGTH=25 * 1024 * 1024,
        SECRET_KEY=os.environ.get("FLASK_SECRET_KEY", "local-kliros-poc-secret"),
        CORS_ALLOWED_ORIGINS=os.environ.get("CORS_ALLOWED_ORIGINS"),
        SESSION_COOKIE_SAMESITE=os.environ.get("SESSION_COOKIE_SAMESITE", "Lax"),
        SESSION_COOKIE_SECURE=os.environ.get("SESSION_COOKIE_SECURE", "false").casefold() in {"1", "true", "yes"},
    )
    if test_config:
        app.config.update(test_config)

    settings = SettingsManager(app.config["SETTINGS_PATH"], project_root=PROJECT_ROOT)
    configured_origins = app.config["CORS_ALLOWED_ORIGINS"]
    if configured_origins is None:
        configured_origins = settings.get("cors_allowed_origins")
    if isinstance(configured_origins, str):
        configured_origins = configured_origins.split(",")
    if not isinstance(configured_origins, (list, tuple, set)):
        raise ValueError("CORS_ALLOWED_ORIGINS must be a list or comma-separated string.")
    app.config["CORS_ALLOWED_ORIGINS"] = {
        origin.strip().rstrip("/")
        for origin in configured_origins
        if isinstance(origin, str) and origin.strip() and origin.strip() != "*"
    }

    data_manager = DataManager(app.config["DATABASE_PATH"])
    file_processing = FileProcessing()
    app.extensions["settings_manager"] = settings
    app.extensions["data_manager"] = data_manager
    app.extensions["file_processing"] = file_processing

    @app.after_request
    def add_api_cors_headers(response):
        if request.path.startswith("/api/"):
            response.vary.add("Origin")
            origin = request.headers.get("Origin", "").rstrip("/")
            if origin in app.config["CORS_ALLOWED_ORIGINS"]:
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Credentials"] = "true"
                response.headers["Access-Control-Allow-Methods"] = "GET, POST, PATCH, DELETE, OPTIONS"
                response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
                response.headers["Access-Control-Expose-Headers"] = "Content-Disposition, ETag, Last-Modified"
                response.headers["Access-Control-Max-Age"] = "600"
        return response

    @app.context_processor
    def inject_current_user():
        user_id = session.get("user_id")
        return {"current_user": data_manager.get_user(user_id) if isinstance(user_id, int) else None}

    def is_logged_in() -> bool:
        user_id = session.get("user_id")
        return isinstance(user_id, int) and data_manager.get_user(user_id) is not None

    def is_admin() -> bool:
        user_id = session.get("user_id")
        user = data_manager.get_user(user_id) if isinstance(user_id, int) else None
        return user is not None and user.get("UserType") == "admin"

    @app.post("/login")
    def demo_login():
        demo_user = data_manager.get_user(1)
        if demo_user is None:
            abort(500)
        session["user_id"] = demo_user["UserID"]
        return redirect(request.referrer or url_for("home"))

    @app.post("/logout")
    def demo_logout():
        session.pop("user_id", None)
        return redirect(request.referrer or url_for("home"))

    @app.get("/api/session")
    def api_session():
        user_id = session.get("user_id")
        user = data_manager.get_user(user_id) if isinstance(user_id, int) else None
        return jsonify({"logged_in": user is not None, "user": user})

    @app.post("/api/login")
    def api_login():
        demo_user = data_manager.get_user(1)
        if demo_user is None:
            abort(500)
        session["user_id"] = demo_user["UserID"]
        return jsonify({"logged_in": True, "user": demo_user})

    @app.post("/api/logout")
    def api_logout():
        session.pop("user_id", None)
        return jsonify({"logged_in": False, "user": None})

    @app.patch("/api/admin/users/<int:user_id>/type")
    def api_update_user_type(user_id: int):
        if not is_logged_in():
            return jsonify({"error": "Log in to manage user types."}), 401
        if not is_admin():
            return jsonify({"error": "Admin access is required."}), 403
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return jsonify({"error": "Send a JSON object."}), 400
        user_type = payload.get("user_type")
        if not isinstance(user_type, str) or user_type not in {"regular", "moderator"}:
            return jsonify({"error": "UserType must be regular or moderator."}), 400
        try:
            user = data_manager.update_user_type(user_id, user_type)
        except ValueError as error:
            return jsonify({"error": str(error)}), 400
        if user is None:
            return jsonify({"error": "User not found."}), 404
        return jsonify({"user_id": user["UserID"], "user_type": user["UserType"]})

    @app.get("/")
    def home():
        return send_file(PROJECT_ROOT / "templates" / "index.html", mimetype="text/html")

    @app.get("/api/latest")
    @app.get("/api/latest/<int:count>")
    def latest_data(count: int = 3):
        resources = sorted(data_manager.visible_resources(), key=lambda row: row["id"], reverse=True)
        recent_works = [_resource_view(row, url_for) for row in resources[:min(count, 10)]]
        return jsonify({"recent_works": recent_works})

    @app.get("/import")
    def import_score():
        return send_file(PROJECT_ROOT / "templates" / "import.html", mimetype="text/html")

    @app.get("/library")
    def library():
        return send_file(PROJECT_ROOT / "templates" / "library.html", mimetype="text/html")

    @app.get("/api/library")
    def library_data():
        resources = sorted(data_manager.visible_resources(), key=lambda row: row["id"], reverse=True)
        return jsonify({"works": [_resource_view(row, url_for) for row in resources]})

    @app.get("/search")
    def search():
        return send_file(PROJECT_ROOT / "templates" / "search.html", mimetype="text/html")

    @app.get("/api/search")
    def search_api():
        try:
            filters = json.loads(request.args.get("filters", "{}"))
        except json.JSONDecodeError:
            return jsonify({"error": "Filters must be a JSON object."}), 400
        if not isinstance(filters, dict):
            return jsonify({"error": "Filters must be a JSON object."}), 400
        try:
            page = int(request.args.get("page", "1"))
            page_size = int(request.args.get("page_size", "24"))
        except ValueError:
            page, page_size = 1, 24

        search_result = data_manager.search_resources(
            query=request.args.get("q", ""),
            filters=filters,
            sort=request.args.get("sort", "uploaded"),
            page=page,
            page_size=page_size,
        )
        return jsonify({
            **search_result,
            "results": [
                {
                    **_resource_view(row["resource"], url_for),
                    "metadata": _resource_metadata_view(row["resource"]),
                    "uploaded_at": row["uploaded_at"],
                    "popularity": row["popularity"],
                }
                for row in search_result["results"]
            ],
        })

    @app.get("/api/search/facets")
    def search_facets_api():
        return jsonify({"facets": data_manager.search_facets()})

    @app.get("/api/site/metadata")
    def site_metadata():
        return jsonify({
            "metadata_fields": [
                {
                    **definition,
                }
                for definition in data_manager.metadata_definitions()
            ],
        })

    @app.get("/profile")
    @app.get("/profile/<int:user_id>")
    def profile(user_id: int | None = None):
        return send_file(PROJECT_ROOT / "templates" / "profile.html", mimetype="text/html")

    @app.get("/api/profile")
    @app.get("/api/profile/<int:user_id>")
    def profile_data(user_id: int | None = None):
        logged_in = is_logged_in()
        if user_id is None:
            current_user_id = session.get("user_id")
            if not logged_in or not isinstance(current_user_id, int):
                return jsonify({"error": "Log in to view your profile."}), 401
            user_id = current_user_id
        user = data_manager.get_user(user_id)
        if user is None:
            return jsonify({"error": "User not found."}), 404
        is_owner = logged_in and user_id == session["user_id"]
        resources = {
            row["id"]: _resource_view(row, url_for)
            for row in data_manager.visible_resources()
        }
        uploads = sorted(
            (resource for resource in resources.values() if resource.get("UserID") == user_id),
            key=lambda resource: resource["id"],
            reverse=True,
        )
        profile_payload = {
            "user": user if is_owner else {
                key: user[key] for key in ("UserID", "Name", "JoinedAt", "UserType")
            },
            "initials": "".join(word[0] for word in user["Name"].split()[:2]).upper(),
            "uploads": uploads,
        }
        if not is_owner:
            return jsonify(profile_payload)
        collections = data_manager.collections_for_user(user_id)
        favorites = [
            resources[row["ResourceID"]]
            for row in sorted(data_manager.rows("favorites"), key=lambda row: row["FavoritedAt"], reverse=True)
            if row["UserID"] == user_id and row["ResourceID"] in resources
        ]
        memberships = data_manager.rows("collection_member")
        for collection in collections:
            members = sorted(
                (member for member in memberships if member["CollectionID"] == collection["id"]),
                key=lambda member: member["id"],
            )
            collection["items"] = [
                resources[member["ResourceID"]]
                for member in members
                if member["ResourceID"] in resources
            ]
        return jsonify({
            **profile_payload,
            "favorites": favorites,
            "collections": collections,
        })

    @app.patch("/api/profile")
    def api_update_profile():
        if not is_logged_in():
            return jsonify({"error": "Log in to update your profile."}), 401
        payload = request.get_json(silent=True) or {}
        
        try:
            user = data_manager.update_user_name(session["user_id"], payload.get("name", ""))
        except ValueError as error:
            return jsonify({"error": str(error)}), 400
        if user is None:
            return jsonify({"error": "User not found."}), 404
        return jsonify({"user": user})

    @app.post("/profile/collections/<int:collection_id>/rename")
    def rename_profile_collection(collection_id: int):
        if not is_logged_in():
            abort(401)
        try:
            collection = data_manager.rename_collection(
                session["user_id"], collection_id, request.form.get("name", "")
            )
        except ValueError as error:
            return str(error), 400
        if collection is None:
            abort(404)
        return redirect(url_for("profile"))

    @app.patch("/api/profile/collections/<int:collection_id>")
    def api_rename_profile_collection(collection_id: int):
        if not is_logged_in():
            return jsonify({"error": "Log in to manage collections."}), 401
        payload = request.get_json(silent=True) or {}
        try:
            collection = data_manager.rename_collection(
                session["user_id"], collection_id, payload.get("name", "")
            )
        except ValueError as error:
            return jsonify({"error": str(error)}), 400
        if collection is None:
            return jsonify({"error": "Collection not found."}), 404
        return jsonify({"collection": collection})

    @app.post("/profile/collections/<int:collection_id>/delete")
    def delete_profile_collection(collection_id: int):
        if not is_logged_in():
            abort(401)
        if not data_manager.delete_collection(session["user_id"], collection_id):
            abort(404)
        return redirect(url_for("profile"))

    @app.delete("/api/profile/collections/<int:collection_id>")
    def api_delete_profile_collection(collection_id: int):
        if not is_logged_in():
            return jsonify({"error": "Log in to manage collections."}), 401
        if not data_manager.delete_collection(session["user_id"], collection_id):
            return jsonify({"error": "Collection not found."}), 404
        return jsonify({"deleted": True, "collection_id": collection_id})

    @app.post("/profile/collections/<int:collection_id>/items/<int:resource_id>/delete")
    def remove_profile_collection_item(collection_id: int, resource_id: int):
        if not is_logged_in():
            abort(401)
        try:
            data_manager.remove_collection_item(session["user_id"], collection_id, resource_id)
        except ValueError:
            abort(404)
        return redirect(url_for("profile"))

    @app.delete("/api/profile/collections/<int:collection_id>/items/<int:resource_id>")
    def api_remove_profile_collection_item(collection_id: int, resource_id: int):
        if not is_logged_in():
            return jsonify({"error": "Log in to manage collections."}), 401
        try:
            removed = data_manager.remove_collection_item(session["user_id"], collection_id, resource_id)
        except ValueError:
            return jsonify({"error": "Collection not found."}), 404
        return jsonify({"removed": removed, "resource_id": resource_id})

    @app.get("/library/<int:resource_id>")
    def library_detail(resource_id: int):
        if _get_resource(data_manager, resource_id) is None:
            abort(404)
        return send_file(PROJECT_ROOT / "templates" / "detail.html", mimetype="text/html")

    @app.get("/api/library/<int:resource_id>")
    def library_detail_data(resource_id: int):
        resource = _get_resource(data_manager, resource_id)
        if resource is None:
            abort(404)
        source_value = resource.get("Source")
        source_path = Path(source_value) if source_value else Path(resource.get("OriginalName") or "")
        metadata = resource.get("MetaData") or {}
        uploader = data_manager.get_user(resource["UserID"])
        if uploader is not None:
            uploader = {
                key: uploader[key]
                for key in ("UserID", "Name", "JoinedAt", "UserType")
            }
        uploader = uploader or {"Name": "Unknown user", "JoinedAt": ""}
        uploader_initials = "".join(word[0] for word in uploader["Name"].split()[:2]).upper()
        signed_in_user_id = session.get("user_id")
        return jsonify({
            "resource": _resource_view(resource, url_for),
            "original_name": resource.get("OriginalName") or source_path.name,
            "uploader": uploader,
            "uploader_initials": uploader_initials,
            "is_favorite": data_manager.is_favorite(signed_in_user_id, resource_id) if isinstance(signed_in_user_id, int) else False,
            "ocr": metadata.get("OCR") or {},
            "metadata": _resource_metadata_view(resource),
            "file_url": f"/api/library/{resource_id}/file",
            "download_url": f"/api/library/{resource_id}/download",
        })

    @app.post("/api/library/<int:resource_id>/favorite")
    @app.delete("/api/library/<int:resource_id>/favorite")
    @app.post("/library/<int:resource_id>/favorite")
    def toggle_resource_favorite(resource_id: int):
        if _get_resource(data_manager, resource_id) is None:
            abort(404)
        user_id = session.get("user_id")
        if not isinstance(user_id, int):
            return jsonify({"error": "Log in to save favorites."}), 401
        try:
            if request.method == "DELETE":
                data_manager.remove_favorite(user_id, resource_id)
                is_favorite = False
            else:
                is_favorite = data_manager.toggle_favorite(user_id, resource_id)
        except ValueError as error:
            return jsonify({"error": str(error)}), 400
        return jsonify({"is_favorite": is_favorite})

    @app.post("/api/library/<int:resource_id>/collections")
    @app.post("/library/<int:resource_id>/collections")
    def add_resource_to_collection(resource_id: int):
        if _get_resource(data_manager, resource_id) is None:
            abort(404)
        user_id = session.get("user_id")
        if not isinstance(user_id, int):
            return jsonify({"error": "Log in to manage collections."}), 401
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return jsonify({"error": "Send a JSON object."}), 400
        try:
            new_name = payload.get("new_collection_name", "")
            action = payload.get("action", "add")
            if action not in {"add", "remove"}:
                return jsonify({"error": "Collection action must be add or remove."}), 400
            if action == "remove" and new_name:
                return jsonify({"error": "A new collection cannot be removed."}), 400
            if isinstance(new_name, str) and new_name.strip():
                collection = data_manager.create_collection(user_id, new_name)
            else:
                collection_id = payload.get("collection_id")
                collection = next((
                    item for item in data_manager.collections_for_user(user_id)
                    if item["id"] == collection_id
                ), None)
                if collection is None:
                    return jsonify({"error": "Choose one of your collections or enter a new name."}), 400
            if action == "remove":
                added = False
                changed = data_manager.remove_collection_item(user_id, collection["id"], resource_id)
            else:
                added = data_manager.add_resource_to_collection(user_id, collection["id"], resource_id)
                changed = added
        except ValueError as error:
            return jsonify({"error": str(error)}), 400
        return jsonify({
            "collection": collection["Name"],
            "collection_id": collection["id"],
            "is_public": bool(collection.get("Public")),
            "added": added,
            "changed": changed,
        })

    @app.get("/api/library/<int:resource_id>/file")
    @app.get("/library/<int:resource_id>/file")
    def library_file(resource_id: int):
        resource = _get_resource(data_manager, resource_id)
        if resource is None:
            abort(404)
        source_value = resource.get("Source")
        if not source_value:
            abort(404)
        source_path = Path(source_value).resolve()
        if not source_path.is_file():
            abort(404)
        mimetype = mimetypes.guess_type(resource.get("OriginalName") or source_path.name)[0]
        return send_file(
            io.BytesIO(source_path.read_bytes()),
            mimetype=mimetype or "application/octet-stream",
            as_attachment=False,
            download_name=resource.get("OriginalName"),
            conditional=True,
        )

    @app.get("/api/library/<int:resource_id>/download")
    @app.get("/library/<int:resource_id>/download")
    def download_library_file(resource_id: int):
        resource = _get_resource(data_manager, resource_id)
        if resource is None:
            abort(404)
        source_value = resource.get("Source")
        if not source_value:
            abort(404)
        source_path = Path(source_value).resolve()
        if not source_path.is_file():
            abort(404)

        # Increment the download count
        data_manager.track_download(resource_id)
        original_name = resource.get("OriginalName") or source_path.name
        title = str(resource.get("DisplayName") or Path(original_name).stem).strip()
        metadata = _resource_metadata_view(resource)

        extension = Path(original_name).suffix or source_path.suffix
        if extension and title.casefold().endswith(extension.casefold()):
            title = title[:-len(extension)].rstrip()

        # Create the basename from title - metadata.get("Tone") - attribution (only the non-blank parts)
        attribution = metadata.get("Composer", "") or metadata.get("Arranger", "") or metadata.get("Tradition", "") or "Unknown"
        parts = [str(part).strip() for part in (title, metadata.get("Tone", ""), attribution) if part and str(part).strip()]
        basename = secure_filename("-".join(parts)) or "score"
        download_name = f"{basename}{extension}"
        mimetype = mimetypes.guess_type(original_name)[0] or "application/octet-stream"
        return send_file(
            io.BytesIO(source_path.read_bytes()),
            mimetype=mimetype,
            as_attachment=True,
            download_name=download_name,
        )

    @app.get("/api/library/<int:resource_id>/thumbnail")
    @app.get("/library/<int:resource_id>/thumbnail")
    def library_thumbnail(resource_id: int):
        return serve_library_thumbnail(resource_id, 300)

    @app.get("/api/library/<int:resource_id>/thumbnail/<int:height>")
    @app.get("/library/<int:resource_id>/thumbnail/<int:height>")
    def library_thumbnail_size(resource_id: int, height: int):
        return serve_library_thumbnail(resource_id, height)

    def serve_library_thumbnail(resource_id: int, height: int):
        if height not in (300, 600):
            abort(404)
        resource = _get_resource(data_manager, resource_id)
        if resource is None:
            abort(404)
        source_value = resource.get("Source")
        if not source_value:
            abort(404)
        source_path = Path(source_value).resolve()
        if not source_path.is_file():
            abort(404)
        thumbnail_path = source_path.with_name(f"{source_path.stem}_{height}px.png")
        if not thumbnail_path.is_file():
            _, error = FileProcessing._generate_thumbnails(
                FileProcessing._first_page_image(source_path)[0], source_path
            )
            if error or not thumbnail_path.is_file():
                abort(404)
        return send_file(io.BytesIO(thumbnail_path.read_bytes()), mimetype="image/png", conditional=True)

    @app.post("/library/<int:resource_id>/delete")
    def delete_library_resource(resource_id: int):
        if not is_logged_in():
            abort(401)
        try:
            resource = data_manager.delete_resource(resource_id, session["user_id"])
        except PermissionError:
            abort(403)
        if resource is None:
            abort(404)
        return redirect(url_for("home"), code=303)

    @app.delete("/api/library/<int:resource_id>")
    def api_delete_library_resource(resource_id: int):
        if not is_logged_in():
            return jsonify({"error": "Log in to delete this work."}), 401
        try:
            resource = data_manager.delete_resource(resource_id, session["user_id"])
        except PermissionError:
            return jsonify({"error": "You may only delete resources you uploaded."}), 403
        if resource is None:
            return jsonify({"error": "Work not found."}), 404
        return jsonify({"deleted": True, "resource_id": resource_id})

    @app.post("/api/library/import/check")
    @app.post("/library/import/check")
    def check_import_upload():
        if not is_logged_in():
            return jsonify({"status": "error", "error": "Log in to import a score."}), 401
        uploaded_file = request.files.get("file")
        if uploaded_file is None:
            return jsonify({"status": "error", "error": "Choose a file to upload."}), 400
        try:
            UploadService.validate(uploaded_file)
        except UploadValidationError as error:
            return jsonify({"status": "error", "error": str(error)}), error.status_code

        original_name = uploaded_file.filename or ""
        uploaded_file.stream.seek(0)
        file_bytes = uploaded_file.stream.read()
        uploaded_file.stream.seek(0)
        file_hash = hashlib.sha256(file_bytes).hexdigest()

        storage_folder = settings.storage_path()
        visible_resources = data_manager.visible_resources()
        for resource_row in visible_resources:
            if data_manager.resource_file_hash(resource_row):
                continue
            source_path = resource_row.get("Source")
            if not source_path or not Path(source_path).is_file():
                continue
            try:
                legacy_hash = UploadService.calculate_file_hash(source_path)
                data_manager.update_resource_file_hash(resource_row["id"], legacy_hash)
            except OSError:
                continue

        duplicate = data_manager.find_resource_by_file_hash(file_hash)
        if duplicate:
            return _duplicate_response(duplicate, "sha256", url_for, file_hash=file_hash)

        with tempfile.TemporaryDirectory(prefix="kliros-import-") as temporary_folder:
            candidate_path = Path(temporary_folder) / f"candidate{Path(original_name).suffix.lower()}"
            candidate_path.write_bytes(file_bytes)
            try:
                candidate_image, render_error = file_processing._first_page_image(candidate_path)
                visual_hash = file_processing._perceptual_hash(candidate_image)
            except Exception as error:
                return jsonify({"status": "error", "error": f"First-page analysis failed: {error}"}), 500

            if visual_hash:
                duplicate = next((
                    candidate_resource for candidate_resource in visible_resources
                    if candidate_resource.get("VisualHash") and candidate_resource["VisualHash"].casefold() == visual_hash.casefold()
                ), None)
                if duplicate:
                    return _duplicate_response(duplicate, "phash", url_for, file_hash=file_hash, visual_hash=visual_hash)

                reference_hashes, reference_error = file_processing.reference_image_hashes(
                    settings.reference_image_path()
                )
                if reference_error:
                    return jsonify({
                        "status": "error",
                        "error": reference_error,
                    }), 500
                distances = [
                    (distance, reference["name"])
                    for reference in reference_hashes
                    if (distance := FileProcessing.hamming_distance(visual_hash, reference["visual_hash"])) is not None
                ]
                if not distances:
                    return jsonify({
                        "status": "error",
                        "error": "The uploaded page could not be compared with the reference images.",
                    }), 500
                reference_distance, closest_reference = min(distances)
                invalid_threshold = settings.get("invalid_hamming_distance")
                if reference_distance > invalid_threshold:
                    return jsonify({
                        "status": "rejected",
                        "reason": "not_sheet_music",
                        "error": (
                            "This page does not appear to be sheet music "
                            f"(closest dHash distance {reference_distance} to {closest_reference}, "
                            f"limit {invalid_threshold})."
                        ),
                        "debug": {
                            "file_hash": file_hash,
                            "visual_hash": visual_hash,
                            "ocr_text": "",
                        },
                        "reference_check": {
                            "hamming_distance": reference_distance,
                            "reference_image": closest_reference,
                            "threshold": invalid_threshold,
                        },
                    }), 422

            try:
                result = file_processing.process_image(
                    candidate_image,
                    visible_resources,
                    data_manager.metadata_definitions(),
                    settings.get("max_hamming_distance"),
                    candidate_path,
                    render_error,
                    visual_hash,
                    settings.get("extract_pdf_text"),
                )
            except Exception as error:
                return jsonify({"status": "error", "error": f"Score processing failed: {error}"}), 500

            thumbnail_data = {}
            for height, thumbnail_name in (result.get("thumbnail_names") or {}).items():
                temporary_thumbnail = Path(temporary_folder) / thumbnail_name
                if temporary_thumbnail.is_file():
                    thumbnail_data[int(height)] = temporary_thumbnail.read_bytes()

        inferred_metadata = result.get("inferred_metadata", {})
        stored_metadata = {
            **inferred_metadata,
        }
        uploaded_file.stream.seek(0)
        try:
            saved_upload = UploadService(settings.storage_path()).save(uploaded_file)
        except UploadValidationError as error:
            return jsonify({"status": "error", "error": str(error)}), error.status_code

        saved_path = saved_upload["path"]
        thumbnail_paths = []
        for height, image_data in thumbnail_data.items():
            thumbnail_path = saved_path.with_name(f"{saved_path.stem}_{height}px.png")
            try:
                thumbnail_path.write_bytes(image_data)
                thumbnail_paths.append(thumbnail_path)
            except OSError as error:
                result.setdefault("errors", []).append(f"Thumbnail could not be saved: {error}")

        stored_metadata["FileHash"] = file_hash
        ocr_text = result.get("ocr", {}).get("text", "")
        display_name = next((line.strip() for line in ocr_text.splitlines() if line.strip()), "")
        if not display_name:
            display_name = Path(saved_upload["original_name"]).stem
        try:
            created_resource = data_manager.insert_resource({
                "OriginalName": saved_upload["original_name"],
                "DisplayName": display_name[:255],
                "MetaData": stored_metadata,
                "Source": str(saved_upload["path"].resolve()),
                "UserID": session.get("user_id", 1),
                "VisualHash": result.get("visual_hash"),
                "FileHash": saved_upload["file_hash"],
            })
        except Exception as error:
            saved_path.unlink(missing_ok=True)
            for thumbnail_path in thumbnail_paths:
                thumbnail_path.unlink(missing_ok=True)
            return jsonify({"status": "error", "error": f"Upload was saved, but its local database row could not be written: {error}"}), 500

        response = {
            "status": "created",
            "upload": {
                "resource_id": created_resource["id"],
                "stored_name": saved_upload["stored_name"],
                "original_name": saved_upload["original_name"],
                "title": created_resource["DisplayName"],
                "source": created_resource["Source"],
                "thumbnail_url": url_for("library_thumbnail", resource_id=created_resource["id"]),
                "thumbnail_600_url": url_for("library_thumbnail_size", resource_id=created_resource["id"], height=600),
                "thumbnail_srcset": (
                    f"{url_for('library_thumbnail_size', resource_id=created_resource['id'], height=300)} 232w, "
                    f"{url_for('library_thumbnail_size', resource_id=created_resource['id'], height=600)} 464w"
                ),
                "detail_url": url_for("library_detail", resource_id=created_resource["id"]),
            },
            "ocr": result.get("ocr", {"status": "unavailable", "text": "", "message": "OCR was not run."}),
            "visual_hash": created_resource["VisualHash"],
            "matches": result.get("matches", []),
            "inferred_metadata": inferred_metadata,
            "debug": {
                "file_hash": file_hash,
                "visual_hash": result.get("visual_hash"),
                "ocr_text": result.get("ocr", {}).get("text", ""),
            },
            "errors": result.get("errors", []),
        }
        return jsonify(response), 200

    @app.patch("/api/library/<int:resource_id>")
    @app.patch("/library/<int:resource_id>")
    def update_library_resource(resource_id: int):
        if not is_logged_in():
            return jsonify({"status": "error", "error": "Log in to edit this work."}), 401
        if _get_resource(data_manager, resource_id) is None:
            abort(404)
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return jsonify({"status": "error", "error": "Send a JSON object."}), 400
        display_name = payload.get("DisplayName")
        metadata_values = payload.get("metadata", {})
        if not isinstance(display_name, str) or not display_name.strip():
            return jsonify({"status": "error", "error": "Title is required."}), 400
        if len(display_name.strip()) > 255:
            return jsonify({"status": "error", "error": "Title must be 255 characters or fewer."}), 400
        if not isinstance(metadata_values, dict):
            return jsonify({"status": "error", "error": "Metadata must be an object."}), 400
        allowed_fields = {definition["Name"] for definition in data_manager.metadata_definitions()}
        unknown_fields = set(metadata_values) - allowed_fields
        if unknown_fields:
            return jsonify({"status": "error", "error": f"Unknown metadata fields: {', '.join(sorted(unknown_fields))}"}), 400
        resource = data_manager.update_resource_metadata(resource_id, display_name.strip(), metadata_values)
        if resource is None:
            abort(404)
        matches = FileProcessing.rank_similar_resources(
            resource,
            data_manager.visible_resources(),
            settings.get("max_hamming_distance"),
        )
        for match in matches:
            match["detail_url"] = url_for("library_detail", resource_id=match["resource_id"])
            match["preview_url"] = url_for(
                "library_thumbnail_size", resource_id=match["resource_id"], height=600
            )
        return jsonify({
            "status": "updated",
            "resource_id": resource["id"],
            "title": resource["DisplayName"],
            "detail_url": url_for("library_detail", resource_id=resource_id),
            "matches": matches,
            "import_complete": not matches,
        })

    @app.errorhandler(413)
    def request_too_large(_error):
        return jsonify({"status": "error", "error": "File is too large. Maximum upload size is 25 MB."}), 413

    return app


def _get_resource(data_manager: DataManager, resource_id: int) -> dict[str, Any] | None:
    return next((row for row in data_manager.visible_resources() if row["id"] == resource_id), None)


def _resource_metadata_view(resource: dict[str, Any]) -> dict[str, str]:
    metadata_values: dict[str, str] = {}
    for name, value in (resource.get("MetaData") or {}).items():
        if name in ("OCR", "FileHash"):
            continue
        if isinstance(value, dict) and "value" in value:
            metadata_values[name] = str(value["value"])
        elif isinstance(value, list):
            metadata_values[name] = json.dumps(value)
        elif value is None:
            metadata_values[name] = ""
        else:
            metadata_values[name] = str(value)
    return metadata_values


def _resource_view(resource: dict[str, Any], url_builder) -> dict[str, Any]:
    source_value = resource.get("Source")
    has_source = bool(source_value and Path(source_value).is_file())
    thumbnail_url = f"/api/library/{resource['id']}/thumbnail" if has_source else None
    thumbnail_srcset = (
        f"/api/library/{resource['id']}/thumbnail/300 232w, "
        f"/api/library/{resource['id']}/thumbnail/600 464w"
        if has_source else None
    )
    return {
         # resource minus the metadata property
        **{key: value for key, value in resource.items() if key != "MetaData"},
        "title": resource.get("DisplayName") or Path(resource.get("OriginalName") or "Untitled").stem,
        "thumbnail_url": thumbnail_url,
        "thumbnail_srcset": thumbnail_srcset,
        "thumbnail_sizes": "(max-width: 600px) 48px, (max-width: 900px) 30vw, 300px",
        "detail_url": url_builder("library_detail", resource_id=resource["id"]),
        "api_url": f"/api/library/{resource['id']}",
    }


def _duplicate_response(
    resource: dict[str, Any],
    match_type: str,
    url_builder,
    *,
    file_hash: str | None = None,
    visual_hash: str | None = None,
) -> Any:
    return jsonify({
        "status": "duplicate",
        "match_type": match_type,
        "debug": {"file_hash": file_hash, "visual_hash": visual_hash, "ocr_text": ""},
        "duplicate": {
            "resource_id": resource["id"],
            "title": resource.get("DisplayName") or Path(resource.get("OriginalName") or "Untitled").stem,
            "original_name": resource.get("OriginalName"),
            "detail_url": url_builder("library_detail", resource_id=resource["id"]),
        },
    })


if __name__ == "__main__":
    app = create_app()
    host = os.environ.get("FLASK_HOST", "127.0.0.1")
    app.run(host=host, port=int(os.environ.get("PORT", "5000")), debug=False)