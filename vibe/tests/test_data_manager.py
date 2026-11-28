import json
import tempfile
import unittest
from pathlib import Path

from data_manager import DataManager, METADATA_SEED


def _downgrade_to_schema_8(database):
    for name in ("flag_reports", "flag_report_reasons"):
        database["tables"].pop(name, None)
        database["next_ids"].pop(name, None)
    resource = database["tables"]["resource"]
    resource["columns"] = [
        column for column in resource["columns"]
        if column["name"] not in {"ReviewerId", "ReviewedAt"}
    ]
    for column in resource["columns"]:
        if column["name"] == "Deleted":
            column["name"] = "Hidden"
    for row in resource["rows"]:
        row["Hidden"] = row.pop("Deleted", False)
        row.pop("ReviewerId", None)
        row.pop("ReviewedAt", None)

    collection = database["tables"]["collection"]
    collection["columns"] = [
        column for column in collection["columns"]
        if column["name"] != "CreationDate"
    ]
    for row in collection["rows"]:
        row.pop("CreationDate", None)


class DataManagerTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.tmp_path = Path(self.temporary_directory.name)

    def test_initializes_schema_owner_and_metadata_seeds(self):
        database_path = self.tmp_path / "db.json"

        manager = DataManager(database_path)

        self.assertEqual(manager.table("resource")["columns"][0]["name"], "id")
        owner = manager.rows("user")[0]
        self.assertEqual(owner["UserID"], 1)
        self.assertEqual(owner["Name"], "Local Admin")
        self.assertEqual(owner["Email"], "admin@kliros.invalid")
        self.assertTrue(owner["JoinedAt"])
        self.assertEqual(owner["UserType"], "admin")
        self.assertEqual(
            [(user["Name"], user["UserType"]) for user in manager.rows("user")],
            [("Local Admin", "admin"), ("Local Moderator", "moderator"), ("Local User", "regular")],
        )
        self.assertEqual(len(manager.metadata_definitions()), len(METADATA_SEED))
        tradition = next(row for row in manager.metadata_definitions() if row["Name"] == "Tradition")
        self.assertIn("Byzantine", tradition["Options"])
        self.assertTrue(manager.metadata_definitions()[0]["Core"])
        self.assertEqual(manager.metadata_definitions()[2]["Type"], "string")
        database = json.loads(database_path.read_text(encoding="utf-8"))
        self.assertEqual(database["schema_version"], 10)
        self.assertIn("FileHash", [column["name"] for column in manager.table("resource")["columns"]])
        self.assertIn("ReviewerId", [column["name"] for column in manager.table("resource")["columns"]])
        self.assertIn("CreationDate", [column["name"] for column in manager.table("collection")["columns"]])
        self.assertEqual(manager.rows("favorites"), [])

    def test_resource_rows_persist_with_stable_ids_and_valid_references(self):
        database_path = self.tmp_path / "db.json"
        manager = DataManager(database_path)
        resource = {
            "OriginalName": "service.pdf",
            "Source": "uploads/score.pdf",
            "UserID": 1,
            "VisualHash": "ff00",
            "FileHash": "a" * 64,
            "MetaData": {"Language": {"value": "Greek", "source": "ocr", "reviewed": False}},
        }

        inserted = manager.insert_resource(resource)
        reopened = DataManager(database_path)
        next_inserted = reopened.insert_resource({**resource, "OriginalName": "service-copy.pdf"})

        self.assertEqual(inserted["id"], 1)
        self.assertEqual(next_inserted["id"], 2)
        self.assertEqual([row["VisualHash"] for row in reopened.rows("resource")], ["ff00", "ff00"])
        self.assertEqual(reopened.find_resource_by_file_hash("A" * 64)["id"], 1)

    def test_rejects_resource_with_missing_owner(self):
        manager = DataManager(self.tmp_path / "db.json")

        with self.assertRaisesRegex(ValueError, "UserID"):
            manager.insert_resource({"OriginalName": "score.png", "UserID": 999})

    def test_soft_deletes_resource_and_preserves_group_relationships(self):
        manager = DataManager(self.tmp_path / "db.json")
        first = manager.insert_resource({"OriginalName": "score.png", "UserID": 1})
        second = manager.insert_resource({"OriginalName": "part.png", "UserID": 1, "GroupID": first["id"]})

        deleted = manager.delete_resource(first["id"], 1)

        self.assertEqual(deleted["OriginalName"], "score.png")
        self.assertTrue(deleted["Deleted"])
        self.assertEqual([row["id"] for row in manager.rows("resource")], [first["id"], second["id"]])
        self.assertEqual([row["id"] for row in manager.visible_resources()], [second["id"]])
        self.assertEqual(manager.rows("resource")[1]["GroupID"], first["id"])
        self.assertIsNone(manager.delete_resource(first["id"], 1))

    def test_regular_users_can_delete_only_their_own_resources(self):
        manager = DataManager(self.tmp_path / "db.json")
        own = manager.insert_resource({"OriginalName": "own.pdf", "UserID": 3})
        someone_elses = manager.insert_resource({"OriginalName": "other.pdf", "UserID": 1})

        with self.assertRaisesRegex(PermissionError, "only delete resources they uploaded"):
            manager.delete_resource(someone_elses["id"], 3)

        self.assertTrue(manager.delete_resource(own["id"], 3)["Deleted"])
        self.assertFalse(someone_elses["Deleted"])

    def test_moderators_and_admins_can_delete_any_resource(self):
        manager = DataManager(self.tmp_path / "db.json")
        resource = manager.insert_resource({"OriginalName": "score.pdf", "UserID": 3})

        self.assertTrue(manager.delete_resource(resource["id"], 2)["Deleted"])
        other = manager.insert_resource({"OriginalName": "other.pdf", "UserID": 3})
        self.assertTrue(manager.delete_resource(other["id"], 1)["Deleted"])

    def test_migrates_joined_at_for_existing_users_without_losing_resources(self):
        database_path = self.tmp_path / "db.json"
        manager = DataManager(database_path)
        manager.insert_resource({"OriginalName": "existing.pdf", "UserID": 1})
        database = json.loads(database_path.read_text(encoding="utf-8"))
        database["schema_version"] = 5
        _downgrade_to_schema_8(database)
        user_table = database["tables"]["user"]
        user_table["rows"] = [user_table["rows"][0]]
        user_table["columns"] = [
            column for column in database["tables"]["user"]["columns"]
            if column["name"] not in {"JoinedAt", "UserType"}
        ]
        user_table["rows"][0].pop("JoinedAt")
        user_table["rows"][0].pop("UserType")
        database_path.write_text(json.dumps(database), encoding="utf-8")

        migrated = DataManager(database_path)

        self.assertEqual(migrated.rows("resource")[0]["OriginalName"], "existing.pdf")
        self.assertTrue(migrated.rows("user")[0]["JoinedAt"])
        self.assertEqual(migrated.rows("user")[0]["UserType"], "admin")
        self.assertEqual(json.loads(database_path.read_text(encoding="utf-8"))["schema_version"], 10)

    def test_migrates_user_types_and_updates_only_regular_or_moderator_users(self):
        database_path = self.tmp_path / "db.json"
        manager = DataManager(database_path)
        resource = manager.insert_resource({"OriginalName": "existing.pdf", "UserID": 1})
        database = json.loads(database_path.read_text(encoding="utf-8"))
        database["schema_version"] = 7
        _downgrade_to_schema_8(database)
        user_table = database["tables"]["user"]
        user_table["columns"] = [column for column in user_table["columns"] if column["name"] != "UserType"]
        for user in user_table["rows"]:
            user.pop("UserType")
        user_table["rows"] = [user_table["rows"][0], {
            "UserID": 2,
            "Name": "Regular user",
            "Email": "regular@example.test",
            "JoinedAt": "2026-01-01 00:00:00",
        }]
        database_path.write_text(json.dumps(database), encoding="utf-8")

        migrated = DataManager(database_path)

        self.assertEqual([user["UserType"] for user in migrated.rows("user")], ["admin", "regular"])
        self.assertEqual(migrated.rows("resource")[0]["id"], resource["id"])
        self.assertEqual(migrated.update_user_type(2, "moderator")["UserType"], "moderator")
        self.assertEqual(migrated.update_user_type(2, "regular")["UserType"], "regular")
        self.assertIsNone(migrated.update_user_type(999, "regular"))
        with self.assertRaisesRegex(ValueError, "regular or moderator"):
            migrated.update_user_type(2, "admin")
        with self.assertRaisesRegex(ValueError, "Admin users"):
            migrated.update_user_type(1, "regular")

    def test_migrates_hidden_resources_and_existing_collections_to_deleted_schema(self):
        database_path = self.tmp_path / "db.json"
        manager = DataManager(database_path)
        resource = manager.insert_resource({"OriginalName": "old.pdf", "UserID": 1})
        manager.delete_resource(resource["id"], 1)
        collection = manager.create_collection(1, "Existing")
        database = json.loads(database_path.read_text(encoding="utf-8"))
        _downgrade_to_schema_8(database)
        database["schema_version"] = 8
        database_path.write_text(json.dumps(database), encoding="utf-8")

        migrated = DataManager(database_path)

        resource_row = migrated.rows("resource")[0]
        self.assertTrue(resource_row["Deleted"])
        self.assertNotIn("Hidden", resource_row)
        self.assertIsNone(resource_row["ReviewerId"])
        self.assertIsNone(resource_row["ReviewedAt"])
        self.assertTrue(migrated.rows("collection")[0]["CreationDate"])
        self.assertEqual(migrated.rows("collection")[0]["id"], collection["id"])
        saved = json.loads(database_path.read_text(encoding="utf-8"))
        self.assertEqual(saved["schema_version"], 10)

    def test_flag_schema_migration_preserves_resources_and_seeds_reasons_once(self):
        path = self.tmp_path / "db.json"
        manager = DataManager(path)
        resource = manager.insert_resource({"OriginalName": "score.pdf", "UserID": 1})
        database = json.loads(path.read_text(encoding="utf-8"))
        database["schema_version"] = 9
        for name in ("flag_reports", "flag_report_reasons"):
            database["tables"].pop(name, None)
            database["next_ids"].pop(name, None)
        path.write_text(json.dumps(database), encoding="utf-8")

        migrated = DataManager(path)
        self.assertEqual(migrated.rows("resource"), [resource])
        self.assertEqual(
            [reason["Code"] for reason in migrated.flag_report_reasons()],
            ["copyright", "inappropriate", "not_church_music", "metadata_mismatch", "other"],
        )
        first = migrated.create_flag_report(resource["id"], None, "copyright", " Rights concern ")
        reopened = DataManager(path)
        second = reopened.create_flag_report(resource["id"], 3, "other", "")
        self.assertEqual((first["id"], second["id"]), (1, 2))
        self.assertEqual(first["Notes"], "Rights concern")
        self.assertEqual(len(reopened.flag_report_reasons()), 5)
        self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["schema_version"], 10)

    def test_flag_queue_is_oldest_first_and_resolution_preserves_the_resource(self):
        path = self.tmp_path / "db.json"
        manager = DataManager(path)
        resource = manager.insert_resource({"OriginalName": "score.pdf", "UserID": 3})
        reports = [manager.create_flag_report(resource["id"], None, "other", "") for _ in range(3)]
        database = json.loads(path.read_text(encoding="utf-8"))
        for report, created in zip(database["tables"]["flag_reports"]["rows"], [
            "2026-01-02 00:00:00", "2026-01-01 00:00:00", "2026-01-01 00:00:00",
        ]):
            report["CreationDate"] = created
        path.write_text(json.dumps(database), encoding="utf-8")

        queue = manager.pending_flag_reports()
        self.assertEqual([report["id"] for report in queue], [2, 3, 1])
        self.assertEqual(queue[0]["resource"], resource)
        self.assertEqual(queue[0]["reason"]["Code"], "other")
        resolved = manager.resolve_flag_report(reports[1]["id"], 1, True, " Confirmed ")
        self.assertTrue(resolved["IsSustained"])
        self.assertEqual(resolved["ResolutionUserID"], 1)
        self.assertEqual(resolved["ResolutionNotes"], "Confirmed")
        self.assertTrue(resolved["ResolutionDate"])
        self.assertEqual([report["id"] for report in manager.pending_flag_reports()], [3, 1])
        self.assertEqual(DataManager(path).rows("resource"), [resource])
        with self.assertRaisesRegex(ValueError, "already resolved"):
            manager.resolve_flag_report(reports[1]["id"], 1, False, "Overwrite")

    def test_flag_migration_does_not_rewrite_an_invalid_database(self):
        path = self.tmp_path / "db.json"
        DataManager(path)
        database = json.loads(path.read_text(encoding="utf-8"))
        database["schema_version"] = 9
        for name in ("flag_reports", "flag_report_reasons"):
            database["tables"].pop(name)
            database["next_ids"].pop(name)
        database["tables"]["resource"]["columns"][0]["name"] = "invalid"
        original = json.dumps(database)
        path.write_text(original, encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "schema for table 'resource'"):
            DataManager(path)
        self.assertEqual(path.read_text(encoding="utf-8"), original)

    def test_flag_validation_and_admin_resolution_do_not_write_invalid_reports(self):
        manager = DataManager(self.tmp_path / "db.json")
        resource = manager.insert_resource({"OriginalName": "score.pdf", "UserID": 1})
        for user_id, reason, notes in [
            (999, "other", ""), (None, "unknown", ""), (None, "other", None),
            (None, "other", "x" * 2001),
        ]:
            with self.subTest(user_id=user_id, reason=reason, notes_type=type(notes).__name__):
                with self.assertRaises(ValueError):
                    manager.create_flag_report(resource["id"], user_id, reason, notes)
        self.assertEqual(manager.rows("flag_reports"), [])
        report = manager.create_flag_report(resource["id"], None, "other", "")
        self.assertEqual(report["id"], 1)
        for user_id in (2, 3, 999):
            with self.assertRaises(PermissionError):
                manager.resolve_flag_report(report["id"], user_id, True, "")
        for sustained in (1, "true", None):
            with self.assertRaises(ValueError):
                manager.resolve_flag_report(report["id"], 1, sustained, "")
        self.assertIsNone(manager.rows("flag_reports")[0]["ResolutionDate"])
        manager.delete_resource(resource["id"], 1)
        self.assertIsNone(manager.create_flag_report(resource["id"], None, "other", ""))
        self.assertEqual(len(manager.pending_flag_reports()), 1)

    def test_favorites_toggle_and_collection_members_are_private_and_unordered(self):
        manager = DataManager(self.tmp_path / "db.json")
        resource = manager.insert_resource({"OriginalName": "score.pdf", "UserID": 1})

        self.assertTrue(manager.toggle_favorite(1, resource["id"]))
        self.assertTrue(manager.is_favorite(1, resource["id"]))
        favorite = manager.rows("favorites")[0]
        self.assertTrue(favorite["FavoritedAt"])
        self.assertFalse(manager.toggle_favorite(1, resource["id"]))
        self.assertFalse(manager.rows("favorites"))

        collection = manager.create_collection(1, "Vespers")
        self.assertFalse(collection["Public"])
        self.assertTrue(collection["CreationDate"])
        self.assertTrue(manager.add_resource_to_collection(1, collection["id"], resource["id"]))
        self.assertFalse(manager.add_resource_to_collection(1, collection["id"], resource["id"]))
        member = manager.rows("collection_member")[0]
        self.assertIsNone(member["Order"])
        self.assertIsNone(member["Annotation"])
        self.assertEqual(manager.collections_for_user(1)[0]["Name"], "Vespers")

    def test_collection_rename_delete_and_item_removal(self):
        database_path = self.tmp_path / "db.json"
        manager = DataManager(database_path)
        resource = manager.insert_resource({"OriginalName": "score.pdf", "UserID": 1})
        collection = manager.create_collection(1, "Vespers")
        manager.add_resource_to_collection(1, collection["id"], resource["id"])
        database = json.loads(database_path.read_text(encoding="utf-8"))
        database["tables"]["collection"]["rows"][0]["Public"] = True
        database_path.write_text(json.dumps(database), encoding="utf-8")

        self.assertTrue(manager.collections_for_user(1)[0]["Public"])
        renamed = manager.rename_collection(1, collection["id"], "Liturgy")
        self.assertEqual(renamed["Name"], "Liturgy")
        self.assertIsNone(manager.rename_collection(2, collection["id"], "Other"))
        self.assertTrue(manager.remove_collection_item(1, collection["id"], resource["id"]))
        self.assertFalse(manager.remove_collection_item(1, collection["id"], resource["id"]))
        manager.add_resource_to_collection(1, collection["id"], resource["id"])
        self.assertTrue(manager.delete_collection(1, collection["id"]))
        self.assertFalse(manager.delete_collection(1, collection["id"]))
        self.assertFalse(manager.rows("collection"))
        self.assertFalse(manager.rows("collection_member"))
        self.assertEqual(len(manager.rows("resource")), 1)


if __name__ == "__main__":
    unittest.main()
