import io
import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app import create_app
from data_manager import DataManager
from service.FileProcessing import FileProcessing


class UploadRouteTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)
        settings_path = self.root / "settings.json"
        reference_folder = self.root / "references"
        reference_folder.mkdir()
        from PIL import Image

        Image.new("RGB", (64, 64), "white").save(reference_folder / "reference.png")
        settings_path.write_text(json.dumps({
            "storage_folder": str(self.root / "uploads"),
            "reference_image_path": str(reference_folder),
        }), encoding="utf-8")
        self.app = create_app({
            "TESTING": True,
            "DATABASE_PATH": self.root / "db.json",
            "SETTINGS_PATH": settings_path,
        })
        self.client = self.app.test_client()

    @staticmethod
    def pdf_bytes():
        return b"%PDF-1.4\n% controlled route test\n"

    def login_demo(self):
        return self.client.post("/login")

    def test_api_cors_allows_configured_frontends_with_credentials_and_preflight(self):
        origin = "http://localhost:5173"
        response = self.client.get("/api/session", headers={"Origin": origin})
        self.assertEqual(response.headers["Access-Control-Allow-Origin"], origin)
        self.assertEqual(response.headers["Access-Control-Allow-Credentials"], "true")
        self.assertIn("Origin", response.headers["Vary"])

        preflight = self.client.options(
            "/api/library/1/favorite",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "DELETE",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        self.assertEqual(preflight.status_code, 200)
        self.assertEqual(preflight.headers["Access-Control-Allow-Origin"], origin)
        self.assertIn("DELETE", preflight.headers["Access-Control-Allow-Methods"])
        self.assertIn("Content-Type", preflight.headers["Access-Control-Allow-Headers"])

        denied = self.client.get("/api/session", headers={"Origin": "https://unlisted.example"})
        self.assertNotIn("Access-Control-Allow-Origin", denied.headers)
        self.assertEqual(
            self.client.get("/search", headers={"Origin": origin}).headers.get("Access-Control-Allow-Origin"),
            None,
        )

    def test_api_cors_allowlist_can_be_configured_in_settings_json(self):
        settings_path = self.root / "settings.json"
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
        settings["cors_allowed_origins"] = ["https://frontend.example"]
        settings_path.write_text(json.dumps(settings), encoding="utf-8")
        app = create_app({
            "TESTING": True,
            "DATABASE_PATH": self.root / "settings-cors-db.json",
            "SETTINGS_PATH": settings_path,
        })

        response = app.test_client().get(
            "/api/session",
            headers={"Origin": "https://frontend.example"},
        )
        self.assertEqual(response.headers["Access-Control-Allow-Origin"], "https://frontend.example")

    def test_admin_can_switch_regular_and_moderator_but_cannot_assign_admin(self):
        data_manager = self.app.extensions["data_manager"]
        database = json.loads((self.root / "db.json").read_text(encoding="utf-8"))
        database["tables"]["user"]["rows"].append({
            "UserID": 2,
            "Name": "Choir member",
            "Email": "member@example.test",
            "JoinedAt": "2026-01-01 00:00:00",
            "UserType": "regular",
        })
        data_manager._write(database)
        endpoint = "/api/admin/users/2/type"

        self.assertEqual(self.client.patch(endpoint, json={"user_type": "moderator"}).status_code, 401)
        self.login_demo()
        self.assertEqual(self.client.patch("/api/admin/users/1/type", json={"user_type": "regular"}).status_code, 400)
        self.assertEqual(self.client.patch(endpoint, json={"user_type": "admin"}).status_code, 400)
        self.assertEqual(self.client.patch(endpoint, json={"user_type": "unknown"}).status_code, 400)
        self.assertEqual(self.client.patch("/api/admin/users/999/type", json={"user_type": "regular"}).status_code, 404)

        moderator = self.client.patch(endpoint, json={"user_type": "moderator"})
        self.assertEqual(moderator.status_code, 200)
        self.assertEqual(moderator.get_json(), {"user_id": 2, "user_type": "moderator"})
        regular = self.client.patch(endpoint, json={"user_type": "regular"})
        self.assertEqual(regular.status_code, 200)
        self.assertEqual(data_manager.get_user(2)["UserType"], "regular")

        with self.client.session_transaction() as session_data:
            session_data["user_id"] = 2
        forbidden = self.client.patch(endpoint, json={"user_type": "moderator"})
        self.assertEqual(forbidden.status_code, 403)
        self.assertEqual(data_manager.get_user(2)["UserType"], "regular")

    def test_session_cookie_sets_configured_samesite_and_secure_flags(self):
        local_cookie = self.client.post("/api/login").headers["Set-Cookie"]
        self.assertIn("SameSite=Lax", local_cookie)
        self.assertNotIn("; Secure", local_cookie)

        with patch.dict(os.environ, {
            "SESSION_COOKIE_SAMESITE": "None",
            "SESSION_COOKIE_SECURE": "true",
            "CORS_ALLOWED_ORIGINS": "https://frontend.example",
        }):
            app = create_app({
                "TESTING": True,
                "DATABASE_PATH": self.root / "secure-db.json",
                "SETTINGS_PATH": self.root / "settings.json",
            })
            response = app.test_client().post(
                "/api/login",
                headers={"Origin": "https://frontend.example"},
            )

        secure_cookie = response.headers["Set-Cookie"]
        self.assertIn("SameSite=None", secure_cookie)
        self.assertIn("; Secure", secure_cookie)
        self.assertEqual(response.headers["Access-Control-Allow-Credentials"], "true")
        self.assertEqual(
            response.headers["Access-Control-Allow-Origin"],
            "https://frontend.example",
        )

    def test_upload_saves_guid_file_compares_previous_rows_and_persists_result(self):
        self.login_demo()
        fake_result = {
            "status": "success",
            "ocr": {"status": "success", "text": "Byzantine Tone 4", "message": ""},
            "visual_hash": "aabbccdd",
            "matches": [],
            "inferred_metadata": {"Tone Set": {"value": "Byzantine", "source": "ocr", "reviewed": False}},
            "errors": [],
        }
        processor = self.app.extensions["file_processing"]
        with patch.object(processor, "_first_page_image", return_value=(object(), None)), \
             patch.object(processor, "_perceptual_hash", return_value="aabbccdd"), \
             patch.object(processor, "process_image", return_value=fake_result) as process:
            response = self.client.post(
                "/library/import/check",
                data={"file": (io.BytesIO(self.pdf_bytes()), "my score.pdf")},
                content_type="multipart/form-data",
            )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["upload"]["original_name"], "my score.pdf")
        self.assertTrue(payload["upload"]["stored_name"].endswith(".pdf"))
        self.assertNotEqual(payload["upload"]["stored_name"], "my score.pdf")
        self.assertTrue((self.root / "uploads" / payload["upload"]["stored_name"]).exists())
        self.assertIn("/thumbnail/300 232w", payload["upload"]["thumbnail_srcset"])
        self.assertIn("/thumbnail/600 464w", payload["upload"]["thumbnail_srcset"])
        process.assert_called_once()
        self.assertEqual(process.call_args.args[1], [])
        self.assertFalse(process.call_args.args[7])
        rows = self.app.extensions["data_manager"].rows("resource")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["VisualHash"], "aabbccdd")
        self.assertEqual(rows[0]["OriginalName"], "my score.pdf")
        self.assertEqual(rows[0]["DisplayName"], "Byzantine Tone 4")
        self.assertEqual(rows[0]["UserID"], 1)
        self.assertEqual(rows[0]["FileHash"], hashlib.sha256(self.pdf_bytes()).hexdigest())
        self.assertFalse(rows[0]["MetaData"]["Tone Set"]["reviewed"])
        self.assertEqual(payload["debug"]["ocr_text"], "Byzantine Tone 4")
        self.assertEqual(payload["debug"]["file_hash"], rows[0]["FileHash"])

    def test_display_name_falls_back_to_original_filename_without_extension(self):
        self.login_demo()
        fake_result = {
            "status": "partial",
            "ocr": {"status": "unavailable", "text": "  \n\t", "message": "OCR unavailable"},
            "visual_hash": "aabbccdd",
            "matches": [],
            "inferred_metadata": {},
            "errors": ["OCR unavailable"],
        }
        processor = self.app.extensions["file_processing"]
        with patch.object(processor, "_first_page_image", return_value=(object(), None)), \
             patch.object(processor, "_perceptual_hash", return_value="aabbccdd"), \
             patch.object(processor, "process_image", return_value=fake_result):
            response = self.client.post(
                "/library/import/check",
                data={"file": (io.BytesIO(self.pdf_bytes()), "my score.pdf")},
                content_type="multipart/form-data",
            )

        self.assertEqual(response.status_code, 200)
        resource = self.app.extensions["data_manager"].rows("resource")[0]
        self.assertEqual(resource["OriginalName"], "my score.pdf")
        self.assertEqual(resource["DisplayName"], "my score")

    def test_exact_duplicate_is_removed_and_rejected_before_processing(self):
        self.login_demo()
        fake_result = {
            "status": "success",
            "ocr": {"status": "success", "text": "score", "message": ""},
            "visual_hash": "aabbccdd",
            "matches": [],
            "inferred_metadata": {},
            "errors": [],
        }
        processor = self.app.extensions["file_processing"]
        with patch.object(processor, "_first_page_image", return_value=(object(), None)), \
             patch.object(processor, "_perceptual_hash", return_value="aabbccdd"), \
             patch.object(processor, "process_image", return_value=fake_result) as process:
            first = self.client.post(
                "/library/import/check",
                data={"file": (io.BytesIO(self.pdf_bytes()), "first.pdf")},
                content_type="multipart/form-data",
            )
            duplicate = self.client.post(
                "/library/import/check",
                data={"file": (io.BytesIO(self.pdf_bytes()), "renamed-copy.pdf")},
                content_type="multipart/form-data",
            )

        self.assertEqual(first.status_code, 200)
        self.assertEqual(duplicate.status_code, 200)
        self.assertEqual(duplicate.get_json()["status"], "duplicate")
        self.assertEqual(duplicate.get_json()["duplicate"]["resource_id"], 1)
        self.assertEqual(duplicate.get_json()["debug"]["file_hash"], hashlib.sha256(self.pdf_bytes()).hexdigest())
        self.assertIsNone(duplicate.get_json()["debug"]["visual_hash"])
        self.assertEqual(process.call_count, 1)
        self.assertEqual(len(self.app.extensions["data_manager"].rows("resource")), 1)
        self.assertEqual(len(list((self.root / "uploads").iterdir())), 1)

    def test_exact_duplicate_of_legacy_resource_is_backfilled_and_rejected(self):
        self.login_demo()
        existing_path = self.root / "existing-score.pdf"
        existing_path.write_bytes(self.pdf_bytes())
        data_manager = self.app.extensions["data_manager"]
        data_manager.insert_resource({
            "OriginalName": "existing-score.pdf",
            "Source": str(existing_path),
            "UserID": 1,
        })
        processor = self.app.extensions["file_processing"]

        with patch.object(processor, "_first_page_image") as first_page, \
             patch.object(processor, "process_image") as process:
            response = self.client.post(
                "/library/import/check",
                data={"file": (io.BytesIO(self.pdf_bytes()), "reupload.pdf")},
                content_type="multipart/form-data",
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["match_type"], "sha256")
        first_page.assert_not_called()
        process.assert_not_called()
        self.assertTrue(existing_path.exists())
        self.assertEqual(len(list((self.root / "uploads").iterdir())), 0)
        self.assertEqual(len(data_manager.rows("resource")), 1)
        self.assertEqual(data_manager.rows("resource")[0]["FileHash"], hashlib.sha256(self.pdf_bytes()).hexdigest())

    def test_exact_phash_duplicate_is_detected_before_ocr_or_saving(self):
        self.login_demo()
        unique_bytes = b"%PDF-1.4\nfirst version"
        second_bytes = b"%PDF-1.4\nsecond byte-distinct version"
        fake_result = {
            "status": "success",
            "ocr": {"status": "success", "text": "Title", "message": ""},
            "visual_hash": "aabbccdd",
            "matches": [],
            "inferred_metadata": {},
            "errors": [],
        }
        processor = self.app.extensions["file_processing"]
        with patch.object(processor, "_first_page_image", return_value=(object(), None)), \
             patch.object(processor, "_perceptual_hash", return_value="aabbccdd"), \
             patch.object(processor, "process_image", return_value=fake_result) as process:
            first = self.client.post(
                "/library/import/check",
                data={"file": (io.BytesIO(unique_bytes), "first.pdf")},
                content_type="multipart/form-data",
            )
            process.reset_mock()
            second = self.client.post(
                "/library/import/check",
                data={"file": (io.BytesIO(second_bytes), "second.pdf")},
                content_type="multipart/form-data",
            )

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(second.get_json()["match_type"], "phash")
        self.assertEqual(second.get_json()["duplicate"]["resource_id"], 1)
        self.assertEqual(second.get_json()["debug"]["visual_hash"], "aabbccdd")
        self.assertEqual(second.get_json()["debug"]["ocr_text"], "")
        process.assert_not_called()
        self.assertEqual(len(self.app.extensions["data_manager"].rows("resource")), 1)
        self.assertEqual(len(list((self.root / "uploads").iterdir())), 1)

    def test_import_rejects_page_far_from_configured_sheet_music_reference(self):
        self.login_demo()
        settings = self.app.extensions["settings_manager"]
        settings.set("invalid_hamming_distance", 0)
        candidate_hash = "f" * 16
        references = [
            {"name": "first.png", "visual_hash": "0" * 16},
            {"name": "second.png", "visual_hash": "1" * 16},
        ]
        expected_distance = min(
            FileProcessing.hamming_distance(candidate_hash, reference["visual_hash"])
            for reference in references
        )
        self.assertGreater(expected_distance, 0)

        processor = self.app.extensions["file_processing"]
        with patch.object(processor, "_first_page_image", return_value=(object(), None)), \
             patch.object(processor, "_perceptual_hash", return_value=candidate_hash), \
             patch.object(processor, "reference_image_hashes", return_value=(references, None)), \
             patch.object(processor, "process_image") as process:
            response = self.client.post(
                "/library/import/check",
                data={"file": (io.BytesIO(b"%PDF-1.4\nnot sheet music"), "not-music.pdf")},
                content_type="multipart/form-data",
            )

        payload = response.get_json()
        self.assertEqual(response.status_code, 422)
        self.assertEqual(payload["status"], "rejected")
        self.assertEqual(payload["reason"], "not_sheet_music")
        self.assertEqual(payload["reference_check"]["hamming_distance"], expected_distance)
        self.assertIn("does not appear to be sheet music", payload["error"])
        self.assertIn(str(payload["reference_check"]["hamming_distance"]), payload["error"])
        process.assert_not_called()
        self.assertFalse(self.app.extensions["data_manager"].rows("resource"))
        self.assertFalse(list((self.root / "uploads").glob("*")))

    def test_missing_and_invalid_uploads_return_json_errors(self):
        self.login_demo()
        missing = self.client.post("/library/import/check", data={})
        invalid = self.client.post(
            "/library/import/check",
            data={"file": (io.BytesIO(b"not an image"), "bad.png")},
            content_type="multipart/form-data",
        )

        self.assertEqual(missing.status_code, 400)
        self.assertIn("error", missing.get_json())
        self.assertEqual(invalid.status_code, 400)
        self.assertIn("error", invalid.get_json())

    def test_import_page_and_metadata_patch_endpoint(self):
        self.login_demo()
        resource = self.app.extensions["data_manager"].insert_resource({
            "OriginalName": "score.pdf",
            "DisplayName": "Detected title",
            "UserID": 1,
            "MetaData": {"OCR": {"text": "Detected title"}},
            "FileHash": "a" * 64,
        })
        candidate = self.app.extensions["data_manager"].insert_resource({
            "OriginalName": "candidate.pdf",
            "DisplayName": "Reviewed title",
            "UserID": 1,
            "MetaData": {"Composer": {"value": "Test Composer"}},
        })
        unrelated = self.app.extensions["data_manager"].insert_resource({
            "OriginalName": "unrelated.pdf",
            "DisplayName": "Unrelated work",
            "UserID": 1,
            "MetaData": {"Composer": {"value": "Different Composer"}},
        })

        page = self.client.get("/import")
        updated = self.client.patch(
            f"/library/{resource['id']}",
            json={"DisplayName": "Reviewed title", "metadata": {"Composer": "Test Composer"}},
        )

        self.assertEqual(page.status_code, 200)
        self.assertIn(b"Import score", page.data)
        self.assertIn(b"Additional fields", page.data)
        self.assertIn(b'id="import-debug-panel"', page.data)
        self.assertIn(b'id="matches-step"', page.data)
        self.assertIn(b'id="duplicate-preview-dialog"', page.data)
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.get_json()["detail_url"], f"/library/{resource['id']}")
        self.assertEqual(updated.get_json()["matches"][0]["resource_id"], candidate["id"])
        self.assertEqual(updated.get_json()["matches"][0]["preview_url"], f"/library/{candidate['id']}/thumbnail/600")
        self.assertFalse(updated.get_json()["import_complete"])
        updated_resource = self.app.extensions["data_manager"].rows("resource")[0]
        self.assertEqual(updated_resource["DisplayName"], "Reviewed title")
        self.assertEqual(updated_resource["MetaData"]["Composer"]["value"], "Test Composer")
        self.assertEqual(updated_resource["FileHash"], "a" * 64)
        detail = self.client.get(f"/library/{resource['id']}").get_data(as_text=True)
        detail_payload = self.client.get(f"/api/library/{resource['id']}").get_json()
        self.assertIn('id="edit-metadata-button"', detail)
        self.assertIn('id="metadata-edit-form"', detail)
        self.assertEqual(detail_payload["resource"]["title"], "Reviewed title")
        self.assertEqual(detail_payload["metadata"]["Composer"], "Test Composer")

        completion = self.client.patch(
            f"/library/{unrelated['id']}",
            json={"DisplayName": "Distinct repertoire", "metadata": {"Composer": "Another composer"}},
        )
        self.assertEqual(completion.status_code, 200)
        self.assertEqual(completion.get_json()["matches"], [])
        self.assertTrue(completion.get_json()["import_complete"])

    def test_demo_login_favorites_collections_and_uploader_profile(self):
        data_manager = self.app.extensions["data_manager"]
        resource = data_manager.insert_resource({
            "OriginalName": "score.pdf",
            "DisplayName": "Service Hymn",
            "UserID": 1,
            "MetaData": {"OCR": {"text": "Service Hymn"}},
        })

        detail = self.client.get(f"/library/{resource['id']}").get_data(as_text=True)
        payload = self.client.get(f"/api/library/{resource['id']}").get_json()
        self.assertIn('id="detail-title"', detail)
        self.assertIn('id="open-report-dialog"', detail)
        self.assertIn('id="report-dialog"', detail)
        self.assertIn("Not sheet music", detail)
        self.assertIn("Questionable", detail)
        self.assertIn("Copyright", detail)
        self.assertEqual(payload["uploader"]["Name"], "Local Owner")
        self.assertEqual(payload["metadata"], {})
        self.assertEqual(self.client.post(f"/library/{resource['id']}/favorite").status_code, 401)

        login = self.client.post("/login")
        self.assertEqual(login.status_code, 302)
        favorite = self.client.post(f"/library/{resource['id']}/favorite")
        self.assertEqual(favorite.status_code, 200)
        self.assertTrue(favorite.get_json()["is_favorite"])

        collection_response = self.client.post(
            f"/library/{resource['id']}/collections",
            json={"new_collection_name": "Vespers"},
        )
        self.assertEqual(collection_response.status_code, 200)
        self.assertTrue(collection_response.get_json()["added"])
        self.assertTrue(collection_response.get_json()["changed"])
        self.assertEqual(collection_response.get_json()["collection_id"], data_manager.collections_for_user(1)[0]["id"])
        collection = data_manager.collections_for_user(1)[0]
        self.assertFalse(collection["Public"])
        removed = self.client.post(
            f"/library/{resource['id']}/collections",
            json={"collection_id": collection["id"], "action": "remove"},
        )
        self.assertEqual(removed.status_code, 200)
        self.assertFalse(removed.get_json()["added"])
        self.assertTrue(removed.get_json()["changed"])
        self.assertFalse(data_manager.rows("collection_member"))
        added_again = self.client.post(
            f"/library/{resource['id']}/collections",
            json={"collection_id": collection["id"], "action": "add"},
        )
        self.assertTrue(added_again.get_json()["added"])
        member = data_manager.rows("collection_member")[0]
        self.assertIsNone(member["Order"])
        self.assertIsNone(member["Annotation"])

        logout = self.client.post("/logout")
        self.assertEqual(logout.status_code, 302)
        self.assertEqual(self.client.post(f"/library/{resource['id']}/favorite").status_code, 401)

    def test_profile_lists_uploads_and_manages_owned_collections(self):
        data_manager = self.app.extensions["data_manager"]
        resource = data_manager.insert_resource({
            "OriginalName": "score.pdf",
            "DisplayName": "Evening Hymn",
            "UserID": 1,
        })
        collection = data_manager.create_collection(1, "Vespers")
        data_manager.add_resource_to_collection(1, collection["id"], resource["id"])

        guest_page = self.client.get("/profile")
        self.assertEqual(guest_page.status_code, 200)
        self.assertEqual(self.client.get("/api/profile").status_code, 401)
        self.assertEqual(
            self.client.post(f"/profile/collections/{collection['id']}/rename", data={"name": "Evening"}).status_code,
            401,
        )

        self.login_demo()
        page = self.client.get("/profile")
        page_html = page.get_data(as_text=True)
        profile_payload = self.client.get("/api/profile").get_json()
        self.assertEqual(page.status_code, 200)
        self.assertIn('id="profile-content"', page_html)
        self.assertEqual(profile_payload["user"]["Name"], "Local Owner")
        self.assertEqual(profile_payload["uploads"][0]["title"], "Evening Hymn")
        self.assertEqual(profile_payload["collections"][0]["Name"], "Vespers")

        renamed = self.client.post(
            f"/profile/collections/{collection['id']}/rename",
            data={"name": "Evening services"},
        )
        self.assertEqual(renamed.status_code, 302)
        self.assertEqual(data_manager.collections_for_user(1)[0]["Name"], "Evening services")
        removed = self.client.post(
            f"/profile/collections/{collection['id']}/items/{resource['id']}/delete"
        )
        self.assertEqual(removed.status_code, 302)
        self.assertFalse(data_manager.rows("collection_member"))
        data_manager.add_resource_to_collection(1, collection["id"], resource["id"])
        deleted = self.client.post(f"/profile/collections/{collection['id']}/delete")
        self.assertEqual(deleted.status_code, 302)
        self.assertFalse(data_manager.rows("collection"))
        self.assertFalse(data_manager.rows("collection_member"))

    def test_profile_favorites_are_owner_scoped_and_unfavorite_is_idempotent(self):
        data_manager = self.app.extensions["data_manager"]
        database_path = self.root / "db.json"
        database = json.loads(database_path.read_text(encoding="utf-8"))
        other_user = dict(database["tables"]["user"]["rows"][0])
        other_user.update({"UserID": 2, "Name": "Other user", "Email": "other@example.test", "ProfileID": "other"})
        database["tables"]["user"]["rows"].append(other_user)
        database_path.write_text(json.dumps(database), encoding="utf-8")
        resource = data_manager.insert_resource({
            "OriginalName": "favorite.pdf", "DisplayName": "Favorite Hymn", "UserID": 1,
        })
        other_resource = data_manager.insert_resource({"OriginalName": "other.pdf", "UserID": 2})
        data_manager.toggle_favorite(1, resource["id"])
        data_manager.toggle_favorite(2, resource["id"])
        data_manager.toggle_favorite(2, other_resource["id"])
        endpoint = f"/api/library/{resource['id']}/favorite"
        self.assertEqual(self.client.delete(endpoint).status_code, 401)

        self.login_demo()
        payload = self.client.get("/api/profile").get_json()
        self.assertEqual([work["id"] for work in payload["favorites"]], [resource["id"]])
        self.assertEqual(payload["favorites"][0]["title"], "Favorite Hymn")
        self.assertEqual(payload["favorites"][0]["detail_url"], f"/library/{resource['id']}")
        with self.client.get("/profile") as page:
            self.assertIn(b'id="profile-favorites"', page.data)
            self.assertIn(b'id="profile-no-favorites"', page.data)
        for _ in range(2):
            response = self.client.delete(endpoint)
            self.assertEqual(response.status_code, 200)
            self.assertFalse(response.get_json()["is_favorite"])
        self.assertEqual(self.client.get("/api/profile").get_json()["favorites"], [])
        self.assertTrue(data_manager.is_favorite(2, resource["id"]))
        self.assertTrue(data_manager.is_favorite(2, other_resource["id"]))
        self.assertIsNotNone(data_manager.get_user(1))
        self.assertEqual(len(data_manager.rows("resource")), 2)
        self.assertEqual(self.client.delete("/api/library/9999/favorite").status_code, 404)

    def test_search_page_shows_all_works_and_metadata_filter_data(self):
        data_manager = self.app.extensions["data_manager"]
        data_manager.insert_resource({
            "OriginalName": "vespers.pdf",
            "DisplayName": "Evening Hymn",
            "UserID": 1,
            "MetaData": {
                "Service": {"value": "Vespers", "source": "user", "reviewed": True},
                "Composer": {"value": "John Doe", "source": "user", "reviewed": True},
            },
        })

        response = self.client.get("/search")
        page = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn('id="search-query"', page)
        self.assertNotIn('"works"', page)
        self.assertNotIn('"Name": "Composer"', page)
        self.assertIn('id="search-pagination"', page)
        initial = self.client.get("/api/search", query_string={"page_size": 24}).get_json()
        self.assertEqual(initial["total"], 1)
        self.assertEqual(len(initial["results"]), 1)
        self.assertIn("Service", initial["facets"])
        self.assertNotIn("Composer", initial["facets"])
        text_match = self.client.get("/api/search", query_string={"q": "John Doe"}).get_json()
        self.assertEqual(text_match["total"], 1)
        self.assertEqual(text_match["results"][0]["title"], "Evening Hymn")
        metadata_match = self.client.get(
            "/api/search",
            query_string={"filters": json.dumps({"Service": "Vespers"})},
        ).get_json()
        self.assertEqual(metadata_match["total"], 1)
        ignored_filter = self.client.get(
            "/api/search",
            query_string={"filters": json.dumps({"Composer": "John Doe"})},
        ).get_json()
        self.assertEqual(ignored_filter["total"], 1)

        for number in range(25):
            data_manager.insert_resource({
                "OriginalName": f"other-{number}.pdf",
                "DisplayName": f"Other Hymn {number:02d}",
                "UserID": 1,
            })
        first_page = self.client.get("/api/search", query_string={"page_size": 24}).get_json()
        second_page = self.client.get("/api/search", query_string={"page_size": 24, "page": 2}).get_json()
        self.assertEqual(first_page["total"], 26)
        self.assertEqual(len(first_page["results"]), 24)
        self.assertEqual(len(second_page["results"]), 2)

    def test_page_routes_are_static_and_data_is_available_from_json_apis(self):
        for path in ("/", "/library", "/search", "/profile", "/import"):
            with self.subTest(path=path):
                response = self.client.get(path)
                page = response.get_data(as_text=True)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.mimetype, "text/html")
                self.assertNotIn("{{", page)
                self.assertNotIn("{%", page)
                response.close()

        self.assertFalse(self.client.get("/api/session").get_json()["logged_in"])
        self.assertIn("recent_works", self.client.get("/api/home").get_json())
        self.assertIn("works", self.client.get("/api/library").get_json())
        self.assertIn("results", self.client.get("/api/search").get_json())
        self.assertEqual(self.client.get("/api/profile").status_code, 401)
        self.assertEqual(self.client.get("/api/library/987").status_code, 404)

        self.assertEqual(self.client.post("/api/login").status_code, 200)
        self.assertEqual(self.client.get("/api/profile").status_code, 200)
        self.assertEqual(self.client.post("/api/logout").status_code, 200)
        self.assertFalse(self.client.get("/api/session").get_json()["logged_in"])

    def test_home_and_pico_stylesheet_are_served_locally(self):
        page = self.client.get("/")
        stylesheet = self.client.get("/static/pico.min.css")

        self.assertEqual(page.status_code, 200)
        self.assertIn(b'href="/import"', page.data)
        self.assertNotIn(b'id="upload-form"', page.data)
        self.login_demo()
        signed_in_page = self.client.get("/")
        self.assertIn(b'id="account-controls"', signed_in_page.data)
        self.assertEqual(stylesheet.status_code, 200)
        self.assertIn(b"Pico CSS", stylesheet.data)
        stylesheet.close()
        page.close()
        signed_in_page.close()

    def test_home_library_detail_thumbnail_and_delete_flow(self):
        self.login_demo()
        from PIL import Image

        upload_folder = self.root / "uploads"
        upload_folder.mkdir(exist_ok=True)
        data_manager = self.app.extensions["data_manager"]
        resources = []
        for number in range(1, 5):
            source = upload_folder / f"score-{number}.pdf"
            source.write_bytes(b"%PDF-1.4\nscore")
            Image.new("RGB", (232, 300), (number * 20, 50, 70)).save(
                source.with_name(f"{source.stem}_300px.png")
            )
            Image.new("RGB", (464, 600), (number * 20, 50, 70)).save(
                source.with_name(f"{source.stem}_600px.png")
            )
            resources.append(data_manager.insert_resource({
                "OriginalName": f"score-{number}.pdf",
                "DisplayName": f"Work {number}",
                "Source": str(source),
                "UserID": 1,
                "MetaData": {"Style": {"value": "Byzantine", "source": "ocr", "reviewed": False}},
            }))

        home = self.client.get("/")
        home_html = home.get_data(as_text=True)
        recent_works = self.client.get("/api/home").get_json()["recent_works"]
        self.assertIn('id="recent-works"', home_html)
        self.assertEqual([work["title"] for work in recent_works], ["Work 4", "Work 3", "Work 2"])
        self.assertIn("thumbnail/300 232w", recent_works[0]["thumbnail_srcset"])
        self.assertIn("thumbnail/600 464w", recent_works[0]["thumbnail_srcset"])
        self.assertIn('href="/library"', home_html)
        self.assertEqual(self.client.get("/library/987").status_code, 404)

        library = self.client.get("/library")
        library_html = library.get_data(as_text=True)
        library_works = self.client.get("/api/library").get_json()["works"]
        self.assertIn('id="library-grid"', library_html)
        self.assertEqual(len(library_works), 4)

        resource_id = resources[1]["id"]
        detail = self.client.get(f"/library/{resource_id}")
        detail_html = detail.get_data(as_text=True)
        detail_payload = self.client.get(f"/api/library/{resource_id}").get_json()
        self.assertIn('id="original-score"', detail_html)
        self.assertEqual(detail_payload["resource"]["title"], "Work 2")
        self.assertEqual(detail_payload["metadata"]["Style"], "Byzantine")
        self.assertEqual(detail_payload["file_url"], f"/api/library/{resource_id}/file")

        original = self.client.get(f"/library/{resource_id}/file")
        download = self.client.get(f"/library/{resource_id}/download")
        thumbnail_response = self.client.get(f"/library/{resource_id}/thumbnail")
        thumbnail_600_response = self.client.get(f"/library/{resource_id}/thumbnail/600")
        self.assertEqual(original.mimetype, "application/pdf")
        self.assertIn("inline", original.headers["Content-Disposition"])
        byte_range = self.client.get(f"/library/{resource_id}/file", headers={"Range": "bytes=0-4"})
        self.assertEqual(byte_range.status_code, 206)
        self.assertEqual(byte_range.data, b"%PDF-")
        self.assertIn("filename=Work_2.pdf", download.headers["Content-Disposition"])
        self.assertEqual(download.data, b"%PDF-1.4\nscore")
        self.assertEqual(thumbnail_response.mimetype, "image/png")
        with Image.open(io.BytesIO(thumbnail_response.data)) as thumbnail_image:
            self.assertEqual(thumbnail_image.size, (232, 300))
        with Image.open(io.BytesIO(thumbnail_600_response.data)) as thumbnail_image:
            self.assertEqual(thumbnail_image.size, (464, 600))
        original.close()
        byte_range.close()
        download.close()
        thumbnail_response.close()
        thumbnail_600_response.close()

        deleted_source = Path(resources[1]["Source"])
        deleted_thumbnails = [
            deleted_source.with_name(f"{deleted_source.stem}_{height}px.png")
            for height in (300, 600)
        ]
        deleted = self.client.post(f"/library/{resource_id}/delete")
        self.assertEqual(deleted.status_code, 303)
        self.assertEqual(deleted.headers["Location"], "/")
        self.assertTrue(deleted_source.exists())
        self.assertTrue(all(path.exists() for path in deleted_thumbnails))
        deleted_row = next(
            row for row in self.app.extensions["data_manager"].rows("resource")
            if row["id"] == resource_id
        )
        self.assertTrue(deleted_row["Hidden"])
        self.assertIsNone(self.app.extensions["data_manager"].delete_resource(resource_id))

    def test_hidden_resources_are_omitted_from_reads_but_keep_relationships(self):
        self.login_demo()
        data_manager = self.app.extensions["data_manager"]
        upload_folder = self.root / "uploads"
        upload_folder.mkdir(exist_ok=True)
        source = upload_folder / "hidden-score.pdf"
        source.write_bytes(self.pdf_bytes())
        hidden = data_manager.insert_resource({
            "OriginalName": source.name,
            "DisplayName": "Hidden score title",
            "Source": str(source),
            "UserID": 1,
            "FileHash": "hidden-file-hash",
            "MetaData": {"Language": {"value": "Hidden-only language"}},
        })
        visible = data_manager.insert_resource({
            "OriginalName": "visible-score.pdf",
            "DisplayName": "Visible score title",
            "UserID": 1,
            "MetaData": {"Language": {"value": "English"}},
        })
        data_manager.toggle_favorite(1, hidden["id"])
        collection = data_manager.create_collection(1, "Saved")
        data_manager.add_resource_to_collection(1, collection["id"], hidden["id"])
        data_manager.add_resource_to_collection(1, collection["id"], visible["id"])

        deleted = self.client.delete(f"/api/library/{hidden['id']}")

        self.assertEqual(deleted.status_code, 200)
        self.assertEqual(deleted.get_json(), {"deleted": True, "hidden": True, "resource_id": hidden["id"]})
        self.assertTrue(source.exists())
        self.assertEqual(self.client.get(f"/library/{hidden['id']}").status_code, 404)
        self.assertEqual(data_manager.find_resource_by_file_hash("hidden-file-hash"), None)
        self.assertEqual(
            [(row["ResourceID"], row["UserID"]) for row in data_manager.rows("favorites")],
            [(hidden["id"], 1)],
        )
        self.assertEqual(
            [row["ResourceID"] for row in data_manager.rows("collection_member")],
            [hidden["id"], visible["id"]],
        )

        home = self.client.get("/api/home").get_json()["recent_works"]
        library = self.client.get("/api/library").get_json()["works"]
        search = self.client.get("/api/search", query_string={"q": "Hidden score title"}).get_json()
        self.assertNotIn(hidden["id"], [row["id"] for row in home])
        self.assertEqual([row["id"] for row in library], [visible["id"]])
        self.assertEqual(search["total"], 0)
        self.assertNotIn("Hidden-only language", self.client.get("/api/search").get_json()["facets"]["Language"])

        profile = self.client.get("/api/profile").get_json()
        self.assertEqual([row["id"] for row in profile["uploads"]], [visible["id"]])
        self.assertEqual(profile["favorites"], [])
        self.assertEqual([row["id"] for row in profile["collections"][0]["items"]], [visible["id"]])

        hidden_resource_paths = [
            f"/api/library/{hidden['id']}",
            f"/api/library/{hidden['id']}/file",
            f"/api/library/{hidden['id']}/download",
            f"/api/library/{hidden['id']}/thumbnail",
            f"/api/library/{hidden['id']}/thumbnail/600",
        ]
        for path in hidden_resource_paths:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 404)
        self.assertEqual(self.client.patch(
            f"/api/library/{hidden['id']}",
            json={"DisplayName": "No longer visible", "metadata": {}},
        ).status_code, 404)
        self.assertEqual(self.client.post(
            f"/api/library/{hidden['id']}/favorite",
        ).status_code, 404)
        self.assertEqual(self.client.post(
            f"/api/library/{hidden['id']}/collections",
            json={"collection_id": collection["id"]},
        ).status_code, 404)
        self.assertEqual(self.client.delete(f"/api/library/{hidden['id']}").status_code, 404)

    def test_import_delete_and_metadata_updates_require_demo_login(self):
        upload_folder = self.root / "uploads"
        upload_folder.mkdir(exist_ok=True)
        source = upload_folder / "protected-score.pdf"
        source.write_bytes(self.pdf_bytes())
        resource = self.app.extensions["data_manager"].insert_resource({
            "OriginalName": source.name,
            "DisplayName": "Protected score",
            "Source": str(source),
            "UserID": 1,
            "MetaData": {"Composer": {"value": "Some Composer"}},
        })

        import_page = self.client.get("/import")
        import_post = self.client.post("/library/import/check", data={})
        download = self.client.get(f"/library/{resource['id']}/download")
        metadata_update = self.client.patch(
            f"/library/{resource['id']}",
            json={"DisplayName": "Changed title", "metadata": {}},
        )
        delete = self.client.post(f"/library/{resource['id']}/delete")
        detail = self.client.get(f"/library/{resource['id']}").get_data(as_text=True)

        self.assertEqual(import_page.status_code, 200)
        self.assertIn(b'id="import-form"', import_page.data)
        self.assertEqual(import_post.status_code, 401)
        self.assertEqual(download.status_code, 200)
        self.assertEqual(download.mimetype, "application/pdf")
        self.assertIn('filename=Protected_score-Some_Composer.pdf', download.headers["Content-Disposition"])
        self.assertEqual(download.data, self.pdf_bytes())
        self.assertEqual(metadata_update.status_code, 401)
        self.assertEqual(delete.status_code, 401)
        self.assertTrue(source.exists())
        self.assertTrue(any(
            row["id"] == resource["id"]
            for row in self.app.extensions["data_manager"].rows("resource")
        ))
        self.assertIn('id="delete-resource-form"', detail)
        self.assertIn('id="edit-metadata-button"', detail)
        session_response = self.client.get("/api/session").get_json()
        self.assertFalse(session_response["logged_in"])
        detail_payload = self.client.get(f"/api/library/{resource['id']}").get_json()
        self.assertEqual(detail_payload["download_url"], f"/api/library/{resource['id']}/download")

        self.login_demo()
        self.assertEqual(self.client.get("/import").status_code, 200)
        signed_in_detail = self.client.get(f"/library/{resource['id']}").get_data(as_text=True)
        self.assertIn('id="delete-resource-form"', signed_in_detail)
        self.assertIn('id="edit-metadata-button"', signed_in_detail)


class FileProcessingTests(unittest.TestCase):
    def test_tesseract_uses_standard_windows_install_when_env_is_unset(self):
        import os
        from PIL import Image

        local_install = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Tesseract-OCR" / "tesseract.exe"
        if not local_install.is_file():
            self.skipTest("Standard per-user Tesseract install is not available.")
        with patch.dict(os.environ, {"TESSERACT_CMD": ""}):
            result = FileProcessing._extract_ocr(Image.new("RGB", (160, 80), "white"))

        self.assertEqual(result["status"], "success")

    def test_pdf_body_text_is_used_without_reading_file_metadata_or_running_ocr(self):
        import fitz

        pdf_path = Path(tempfile.gettempdir()) / "body-text-score.pdf"
        with fitz.open() as document:
            page = document.new_page()
            page.insert_text((72, 72), "Printable score body")
            document.set_metadata({"title": "Metadata title only", "author": "Metadata author"})
            document.save(pdf_path)

        with patch.object(FileProcessing, "_generate_thumbnails", return_value=({}, None)), \
             patch.object(FileProcessing, "_perceptual_hash", return_value="0" * 16), \
             patch.object(FileProcessing, "_extract_ocr") as ocr:
            result = FileProcessing().process_image(object(), [], [], 10, pdf_path, extract_pdf_text=True)

        self.assertEqual(result["ocr"]["status"], "success")
        self.assertIn("Printable score body", result["ocr"]["text"])
        self.assertNotIn("Metadata title only", result["ocr"]["text"])
        self.assertNotIn("Metadata author", result["ocr"]["text"])
        ocr.assert_not_called()
        pdf_path.unlink(missing_ok=True)

    def test_image_only_pdf_falls_back_to_tesseract(self):
        import fitz

        pdf_path = Path(tempfile.gettempdir()) / "image-only-score.pdf"
        with fitz.open() as document:
            document.new_page()
            document.save(pdf_path)

        tesseract_result = {"status": "success", "text": "OCR score text", "message": ""}
        with patch.object(FileProcessing, "_generate_thumbnails", return_value=({}, None)), \
             patch.object(FileProcessing, "_perceptual_hash", return_value="0" * 16), \
             patch.object(FileProcessing, "_extract_ocr", return_value=tesseract_result) as ocr:
            result = FileProcessing().process_image(object(), [], [], 10, pdf_path)

        self.assertEqual(result["ocr"], tesseract_result)
        ocr.assert_called_once()
        pdf_path.unlink(missing_ok=True)

    def test_pdf_text_layer_can_be_disabled(self):
        import fitz

        pdf_path = Path(tempfile.gettempdir()) / "disabled-text-score.pdf"
        with fitz.open() as document:
            page = document.new_page()
            page.insert_text((72, 72), "Embedded text is disabled")
            document.save(pdf_path)

        tesseract_result = {"status": "success", "text": "Tesseract fallback", "message": ""}
        with patch.object(FileProcessing, "_generate_thumbnails", return_value=({}, None)), \
             patch.object(FileProcessing, "_perceptual_hash", return_value="0" * 16), \
             patch.object(FileProcessing, "_extract_ocr", return_value=tesseract_result) as ocr:
            result = FileProcessing().process_image(object(), [], [], 10, pdf_path, extract_pdf_text=False)

        self.assertEqual(result["ocr"], tesseract_result)
        ocr.assert_called_once()
        pdf_path.unlink(missing_ok=True)

    def test_hamming_distance_requires_matching_hex_hashes(self):
        self.assertEqual(FileProcessing.hamming_distance("0000", "0001"), 1)
        self.assertEqual(FileProcessing.hamming_distance("ffff", "0000"), 16)
        self.assertEqual(FileProcessing.hamming_distance("0000", "00001"), 1)
        self.assertIsNone(FileProcessing.hamming_distance("nope", "0000"))

    def test_reference_hashes_are_cached_until_folder_contents_change(self):
        reference_folder = Path(tempfile.gettempdir()) / "kliros-reference-cache-test"
        reference_folder.mkdir(exist_ok=True)
        reference_file = reference_folder / "reference.png"
        reference_file.write_bytes(b"first reference")
        processor = FileProcessing()
        with patch.object(processor, "_first_page_image", return_value=(object(), None)) as load_image, \
             patch.object(processor, "_perceptual_hash", return_value="a" * 16) as hash_image:
            first_hashes, first_error = processor.reference_image_hashes(reference_folder)
            cached_hashes, cached_error = processor.reference_image_hashes(reference_folder)
            reference_file.write_bytes(b"updated reference file")
            updated_hashes, updated_error = processor.reference_image_hashes(reference_folder)

        self.assertIsNone(first_error)
        self.assertIsNone(cached_error)
        self.assertIsNone(updated_error)
        self.assertEqual(first_hashes, cached_hashes)
        self.assertEqual(updated_hashes, first_hashes)
        self.assertEqual(load_image.call_count, 2)
        self.assertEqual(hash_image.call_count, 2)
        reference_file.unlink()
        reference_folder.rmdir()

    def test_ranks_reasonable_matches_by_hash_title_and_composer(self):
        resource = {
            "id": 10,
            "DisplayName": "Our Father",
            "VisualHash": "0000",
            "MetaData": {"Composer": {"value": "Strochnoi"}},
        }
        candidates = [
            {
                "id": 1,
                "OriginalName": "our-father-a.pdf",
                "DisplayName": "Our Father",
                "VisualHash": "0001",
                "MetaData": {"Composer": {"value": "Strochnoi"}},
            },
            {"id": 2, "OriginalName": "our-father-b.pdf", "DisplayName": "Our Father", "VisualHash": "ffff", "MetaData": {}},
            {
                "id": 3,
                "OriginalName": "unrelated.pdf",
                "DisplayName": "Unrelated Chant",
                "VisualHash": "ffff",
                "MetaData": {"Composer": {"value": "Strochnoi"}},
            },
        ]

        matches = FileProcessing.rank_similar_resources(resource, candidates, max_hamming_distance=2)

        self.assertEqual([match["resource_id"] for match in matches], [1, 2])
        self.assertEqual(matches[0]["hamming_distance"], 1)
        self.assertEqual(matches[0]["composer_similarity"], 1.0)
        self.assertIsNone(matches[1]["composer_similarity"])

    def test_process_image_generates_300_and_600px_letter_portrait_thumbnails(self):
        from PIL import Image

        source_path = Path(tempfile.gettempdir()) / "score-upload.pdf"
        image = Image.new("RGB", (600, 900), "black")
        ocr = {"status": "success", "text": "Score", "message": ""}
        processor = FileProcessing()
        with patch.object(processor, "_perceptual_hash", return_value="0" * 16), \
             patch.object(processor, "_extract_ocr", return_value=ocr):
            result = processor.process_image(image, [], [], 10, source_path)

        thumbnail_names = result["thumbnail_names"]
        self.assertEqual(thumbnail_names, {300: "score-upload_300px.png", 600: "score-upload_600px.png"})
        for height, width in ((300, 232), (600, 464)):
            thumbnail_path = source_path.with_name(thumbnail_names[height])
            with Image.open(thumbnail_path) as thumbnail:
                self.assertEqual(thumbnail.size, (width, height))
            thumbnail_path.unlink()

    def test_ocr_cleanup_replaces_underscore_runs_and_removes_spaced_dashes(self):
        cleaned = FileProcessing._clean_ocr_text("  Psalm__Tone_4 - Feast–Rank _Name  ")

        self.assertEqual(cleaned, "Psalm Tone 4FeastRank  Name")

    def test_matches_respect_hamming_threshold_and_exclude_current_file(self):
        current_path = Path("C:/library/current.pdf")
        resources = [
            {"id": 1, "OriginalName": "near-a.pdf", "VisualHash": "0001", "Source": "C:/library/a.pdf"},
            {"id": 2, "OriginalName": "near-b.pdf", "VisualHash": "0010", "Source": "C:/library/b.pdf"},
            {"id": 3, "OriginalName": "far.pdf", "VisualHash": "ffff", "Source": "C:/library/far.pdf"},
            {"id": 4, "OriginalName": "current.pdf", "VisualHash": "0000", "Source": str(current_path)},
        ]

        matches = FileProcessing._find_matches("0000", resources, current_path, 1)

        self.assertEqual([match["resource_id"] for match in matches], [1, 2])
        self.assertEqual([match["hamming_distance"] for match in matches], [1, 1])
        inferred = FileProcessing._infer_metadata(
            "A Byzantine service in tone 4",
            [{"Name": "Tone Set", "Type": "string", "Options": ["Byzantine"]},
             {"Name": "Tone", "Type": "number", "Options": [1, 2, 3, 4]}],
        )
        self.assertEqual(inferred["Tone"]["value"], "4")
        self.assertFalse(inferred["Tone"]["reviewed"])


if __name__ == "__main__":
    unittest.main()