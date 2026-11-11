import json
import tempfile
import unittest
from pathlib import Path

from data_manager import DataManager, METADATA_SEED


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
        self.assertEqual(owner["Name"], "Local Owner")
        self.assertEqual(owner["Email"], "local@kliros.invalid")
        self.assertTrue(owner["JoinedAt"])
        self.assertEqual(len(manager.metadata_definitions()), len(METADATA_SEED))
        tradition = next(row for row in manager.metadata_definitions() if row["Name"] == "Tradition")
        self.assertIn("Byzantine", tradition["Options"])
        self.assertTrue(manager.metadata_definitions()[0]["Core"])
        self.assertEqual(manager.metadata_definitions()[2]["Type"], "string")
        database = json.loads(database_path.read_text(encoding="utf-8"))
        self.assertEqual(database["schema_version"], 7)
        self.assertIn("FileHash", [column["name"] for column in manager.table("resource")["columns"]])
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

    def test_deletes_resource_and_clears_relationships(self):
        manager = DataManager(self.tmp_path / "db.json")
        first = manager.insert_resource({"OriginalName": "score.png", "UserID": 1})
        second = manager.insert_resource({"OriginalName": "part.png", "UserID": 1, "GroupID": first["id"]})

        deleted = manager.delete_resource(first["id"])

        self.assertEqual(deleted["OriginalName"], "score.png")
        self.assertEqual([row["id"] for row in manager.rows("resource")], [second["id"]])
        self.assertIsNone(manager.rows("resource")[0]["GroupID"])

    def test_migrates_joined_at_for_existing_users_without_losing_resources(self):
        database_path = self.tmp_path / "db.json"
        manager = DataManager(database_path)
        manager.insert_resource({"OriginalName": "existing.pdf", "UserID": 1})
        database = json.loads(database_path.read_text(encoding="utf-8"))
        database["schema_version"] = 5
        database["tables"]["user"]["columns"] = [
            column for column in database["tables"]["user"]["columns"] if column["name"] != "JoinedAt"
        ]
        database["tables"]["user"]["rows"][0].pop("JoinedAt")
        database_path.write_text(json.dumps(database), encoding="utf-8")

        migrated = DataManager(database_path)

        self.assertEqual(migrated.rows("resource")[0]["OriginalName"], "existing.pdf")
        self.assertTrue(migrated.rows("user")[0]["JoinedAt"])
        self.assertEqual(json.loads(database_path.read_text(encoding="utf-8"))["schema_version"], 6)

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
