"""Schema-shaped, single-process JSON persistence for the local PoC."""

from __future__ import annotations

import copy
import json
import os
import tempfile
import threading
from datetime import datetime
from pathlib import Path
from typing import Any


TABLE_COLUMNS: dict[str, list[dict[str, Any]]] = {
    "user": [
        {"name": "UserID", "type": "int", "nullable": False, "primary_key": True},
        {"name": "Name", "type": "varchar(255)", "nullable": False},
        {"name": "Email", "type": "varchar(255)", "nullable": False},
        {"name": "JoinedAt", "type": "datetime", "nullable": False, "default": "CURRENT_TIMESTAMP"},
        {"name": "UserType", "type": "enum('regular','moderator','admin')", "nullable": False, "default": "regular"},
    ],
    "federated_credential": [
        {"name": "RowID", "type": "int", "nullable": False, "primary_key": True},
        {"name": "UserID", "type": "int", "nullable": False, "references": ["user", "UserID"]},
        {"name": "Provider", "type": "varchar(255)", "nullable": False},
        {"name": "ProfileID", "type": "varchar(255)", "nullable": False},
    ],
    "favorites": [
        {"name": "UserID", "type": "int", "nullable": False, "references": ["user", "UserID"], "primary_key": True},
        {"name": "ResourceID", "type": "int", "nullable": False, "references": ["resource", "id"], "primary_key": True},
        {"name": "FavoritedAt", "type": "datetime", "nullable": False, "default": "CURRENT_TIMESTAMP"},
    ],
    "resource": [
        {"name": "id", "type": "int", "nullable": False, "primary_key": True},
        {"name": "DisplayName", "type": "varchar(255)", "nullable": True, "default": None},
        {"name": "OriginalName", "type": "varchar(255)", "nullable": False},
        {"name": "MetaData", "type": "json", "nullable": True, "default": None},
        {"name": "GroupID", "type": "int", "nullable": True, "default": None, "references": ["resource", "id"]},
        {"name": "Source", "type": "varchar(255)", "nullable": True, "default": None},
        {"name": "UserID", "type": "int", "nullable": False, "references": ["user", "UserID"]},
        {"name": "Reviewed", "type": "boolean", "nullable": True, "default": False},
        {"name": "Public", "type": "boolean", "nullable": True, "default": False},
        {"name": "VisualHash", "type": "varchar(255)", "nullable": True, "default": None},
        {"name": "FileHash", "type": "varchar(64)", "nullable": True, "default": None},
        {"name": "Hidden", "type": "boolean", "nullable": True, "default": False},
        {"name": "DownloadCount", "type": "int", "nullable": True, "default": 0},
    ],
    "metadata": [
        {"name": "id", "type": "int", "nullable": False, "primary_key": True},
        {"name": "Name", "type": "varchar(255)", "nullable": False},
        {"name": "Type", "type": "varchar(255)", "nullable": False},
        {"name": "Options", "type": "json", "nullable": True, "default": None},
        {"name": "Core", "type": "boolean", "nullable": True, "default": False},
        {"name": "Extracted", "type": "boolean", "nullable": True, "default": False},
        {"name": "Searchable", "type": "boolean", "nullable": True, "default": False},
    ],
    "collection": [
        {"name": "id", "type": "int", "nullable": False, "primary_key": True},
        {"name": "Name", "type": "varchar(255)", "nullable": False},
        {"name": "Public", "type": "boolean", "nullable": True, "default": False},
        {"name": "UserId", "type": "int", "nullable": True, "default": None, "references": ["user", "UserID"]},
    ],
    "collection_member": [
        {"name": "id", "type": "int", "nullable": False, "primary_key": True},
        {"name": "CollectionID", "type": "int", "nullable": False, "references": ["collection", "id"]},
        {"name": "ResourceID", "type": "int", "nullable": False, "references": ["resource", "id"]},
        {"name": "Order", "type": "int", "nullable": True, "default": None},
        {"name": "Annotation", "type": "varchar(255)", "nullable": True, "default": None},
    ],
}

METADATA_SEED = [
    {"Name": "Composer", "Type": "string", "Options": None, "Core": True, "Extracted": False, "Required": False, "Searchable": False},
    {"Name": "Arranger", "Type": "string", "Options": None, "Core": True, "Extracted": False, "Required": False, "Searchable": False},
    {"Name": "Style", "Type": "string", "Options": None, "Core": False, "Extracted": False, "Required": False, "Searchable": False},
    {"Name": "Tone", "Type": "string", "Options": ["Tone 1", "Tone 2", "Tone 3", "Tone 4", "Tone 5", "Tone 6", "Tone 7", "Tone 8"], "Core": False, "Extracted": True, "Required": False, "Searchable": True},
    {"Name": "Tradition", "Type": "string", "Options": ["Byzantine", "Kievan", "Obikhod", "Znamenny", "Georgian", "Bulgarian", "Byzantine", "Serbian", "Romanian", "Carpatho-Rusyn", "Ruthenian", "Strochnoi"], "Core": False, "Extracted": True, "Required": False, "Searchable": True},
    {"Name": "Feast", "Type": "string", "Options": None, "Core": False, "Extracted": False, "Required": False, "Searchable": True},
    {"Name": "Feast Rank", "Type": "string", "Options": ["Ordinary", "Double", "Six Stichera", "Great Doxology", "Polyeleos", "Vigil", "Great Feast"], "Core": False, "Extracted": False, "Required": False, "Searchable": True},
    {"Name": "Service", "Type": "string", "Options": ["Vespers","Matins","Liturgy","Presanctified Liturgy","Compline","Hours","Midnight Office","Services of Need"], "Core": False, "Extracted": True, "Required": False, "Searchable": True},
	{"Name": "Part of Service", "Type": "string", "Options": None, "Core": False, "Extracted": False, "Required": False, "Searchable": False},
    {"Name": "Parts", "Type": "number", "Options": ["Unison","One Part","Two Parts","Three Parts","Four Parts","Five+ Parts"], "Core": False, "Extracted": False, "Required": False, "Searchable": True},
    {"Name": "Chorus Type", "Type": "string", "Options": ["male", "female", "mixed"], "Core": False, "Extracted": True, "Required": False, "Searchable": True},
    {"Name": "Voicing", "Type": "string", "Options": ["SATB","SA","SSA","SSAA"], "Core": False, "Extracted": True, "Required": False, "Searchable": True},
    {"Name": "Difficulty", "Type": "string", "Options": ["Difficulty 1", "Difficulty 2", "Difficulty 3", "Difficulty 4", "Difficulty 5"], "Core": False, "Extracted": False, "Required": False, "Searchable": True},
    {"Name": "Liturgical Date", "Type": "date", "Options": None, "Core": False, "Extracted": False, "Required": False, "Searchable": True},
    {"Name": "Copyright", "Type": "string", "Options": None, "Core": False, "Extracted": False, "Required": False, "Searchable": False},
    {"Name": "Language", "Type": "string", "Options": ["English","Greek","Church Slavonic","Georgian","Bulgarian","Serbian","Romanian","Carpatho-Rusyn","Ruthenian"], "Core": True, "Extracted": False, "Required": False, "Searchable": True},
    {"Name": "English Title", "Type": "string", "Options": None, "Core": False, "Extracted": False, "Required": False, "Searchable": False},
]

ID_COLUMNS = {
    "user": ("UserID", "UserID"),
    "federated_credential": ("RowID", "RowID"),
    "resource": ("id", "id"),
    "metadata": ("id", "id"),
    "collection": ("id", "id"),
    "collection_member": ("id", "id"),
}


class DataManager:
    """Persists schema definitions and table rows in one atomic JSON file."""

    def __init__(self, path: str | Path):
        self.path = Path(path).resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        if not self.path.exists():
            self._write(self._empty_database())
        else:
            self._read()

    @staticmethod
    def _empty_database() -> dict[str, Any]:
        tables = {
            name: {"columns": copy.deepcopy(columns), "rows": []}
            for name, columns in TABLE_COLUMNS.items()
        }
        database = {
            "schema_version": 8,
            "tables": tables,
            "next_ids": {name: 1 for name in TABLE_COLUMNS},
        }
        owner = {
            "UserID": 1,
            "Name": "Local Owner",
            "Email": "local@kliros.invalid",
            "JoinedAt": datetime.now().replace(microsecond=0).isoformat(sep=" "),
            "UserType": "admin",
        }
        database["tables"]["user"]["rows"].append(owner)
        database["next_ids"]["user"] = 2
        for row_id, metadata in enumerate(METADATA_SEED, start=1):
            database["tables"]["metadata"]["rows"].append({"id": row_id, **copy.deepcopy(metadata)})
        database["next_ids"]["metadata"] = len(METADATA_SEED) + 1
        return database

    def _read(self) -> dict[str, Any]:
        try:
            database = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ValueError(f"Could not read local database {self.path}: {error}") from error
        if not isinstance(database, dict) or not isinstance(database.get("tables"), dict):
            raise ValueError("Local database must contain a tables object.")
        legacy_user_columns = [
            column for column in TABLE_COLUMNS["user"]
            if column["name"] not in {"JoinedAt", "UserType"}
        ]
        legacy_user_columns_with_joined_at = [
            column for column in TABLE_COLUMNS["user"]
            if column["name"] != "UserType"
        ]
        if database.get("schema_version") == 5:
            user_table = database["tables"].get("user")
            if (
                isinstance(user_table, dict)
                and user_table.get("columns") == legacy_user_columns
                and isinstance(user_table.get("rows"), list)
            ):
                joined_at = datetime.now().replace(microsecond=0).isoformat(sep=" ")
                for user in user_table["rows"]:
                    user.setdefault("JoinedAt", joined_at)
                user_table["columns"] = copy.deepcopy(legacy_user_columns_with_joined_at)
                database["schema_version"] = 6
                self._write(database)
        if database.get("schema_version") == 6:
            metadata_table = database["tables"].get("metadata")
            legacy_columns = [column for column in TABLE_COLUMNS["metadata"] if column["name"] != "Searchable"]
            legacy_columns_with_required = [
                *legacy_columns,
                {"name": "Required", "type": "boolean", "nullable": True, "default": False},
            ]
            if (
                isinstance(metadata_table, dict)
                and isinstance(metadata_table.get("rows"), list)
                and metadata_table.get("columns") in (legacy_columns, legacy_columns_with_required)
            ):
                searchable_by_name = {row["Name"]: row["Searchable"] for row in METADATA_SEED}
                for row in metadata_table["rows"]:
                    row["Searchable"] = searchable_by_name.get(row.get("Name"), False)
                metadata_table["columns"] = copy.deepcopy(TABLE_COLUMNS["metadata"])
            if isinstance(metadata_table, dict) and metadata_table.get("columns") == TABLE_COLUMNS["metadata"]:
                database["schema_version"] = 7
                self._write(database)
        if database.get("schema_version") == 7:
            user_table = database["tables"].get("user")
            if (
                isinstance(user_table, dict)
                and user_table.get("columns") == legacy_user_columns_with_joined_at
                and isinstance(user_table.get("rows"), list)
            ):
                for user in user_table["rows"]:
                    user["UserType"] = "admin" if user.get("UserID") == 1 else "regular"
                user_table["columns"] = copy.deepcopy(TABLE_COLUMNS["user"])
                database["schema_version"] = 8
                self._write(database)
        for name, columns in TABLE_COLUMNS.items():
            table = database["tables"].get(name)
            if not isinstance(table, dict) or not isinstance(table.get("rows"), list):
                raise ValueError(f"Local database table '{name}' is missing or malformed.")
            if table.get("columns") != columns:
                raise ValueError(f"Local database schema for table '{name}' does not match this app version.")
        return database

    def _write(self, database: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path: str | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.path.parent,
                prefix=f".{self.path.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary_file:
                temporary_path = temporary_file.name
                json.dump(database, temporary_file, ensure_ascii=False, indent=2)
                temporary_file.write("\n")
                temporary_file.flush()
                os.fsync(temporary_file.fileno())
            os.replace(temporary_path, self.path)
        finally:
            if temporary_path and os.path.exists(temporary_path):
                os.unlink(temporary_path)

    def table(self, name: str) -> dict[str, Any]:
        with self._lock:
            database = self._read()
            if name not in database["tables"]:
                raise KeyError(f"Unknown table: {name}")
            return copy.deepcopy(database["tables"][name])

    def rows(self, name: str) -> list[dict[str, Any]]:
        return self.table(name)["rows"]

    def visible_resources(self) -> list[dict[str, Any]]:
        return [resource for resource in self.rows("resource") if not resource.get("Hidden", False)]

    def metadata_definitions(self) -> list[dict[str, Any]]:
        return self.rows("metadata")

    SEARCH_SORTS = ("uploaded", "popularity", "name")
    SEARCH_PAGE_SIZES = (24, 48, 96)

    @staticmethod
    def resource_title(resource: dict[str, Any]) -> str:
        return resource.get("DisplayName") or Path(resource.get("OriginalName") or "Untitled").stem

    @classmethod
    def metadata_values(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, dict):
            if "value" in value:
                return cls.metadata_values(value["value"])
            return [item for child in value.values() for item in cls.metadata_values(child)]
        if isinstance(value, list):
            return [item for child in value for item in cls.metadata_values(child)]
        text = str(value).strip()
        return [text] if text else []

    def search_facets(self) -> dict[str, list[str]]:
        with self._lock:
            database = self._read()
        tables = database["tables"]
        resources = [row for row in tables["resource"]["rows"] if not row.get("Hidden", False)]
        facets: dict[str, list[str]] = {}
        for definition in tables["metadata"]["rows"]:
            if definition.get("Searchable") is not True:
                continue
            options = [str(option) for option in definition.get("Options") or []]
            seen = {option.casefold() for option in options}
            for resource in resources:
                for value in self.metadata_values((resource.get("MetaData") or {}).get(definition["Name"])):
                    if value.casefold() not in seen:
                        seen.add(value.casefold())
                        options.append(value)
            facets[definition["Name"]] = options
        return facets

    def search_resources(
        self,
        query: str = "",
        filters: dict[str, Any] | None = None,
        sort: str = "uploaded",
        page: int = 1,
        page_size: int = 24,
    ) -> dict[str, Any]:
        """Filter, sort, and page visible resources; returns raw resource rows plus search fields."""
        with self._lock:
            database = self._read()
        tables = database["tables"]
        definitions = [
            definition for definition in tables["metadata"]["rows"]
            if definition.get("Searchable") is True
        ]
        searchable_names = {definition["Name"] for definition in definitions}
        selected_filters = {
            name: value.strip().casefold()
            for name, value in (filters or {}).items()
            if name in searchable_names and isinstance(value, str) and value.strip()
        }
        normalized_query = query.strip().casefold()
        sort = sort if sort in self.SEARCH_SORTS else "uploaded"
        page_size = page_size if page_size in self.SEARCH_PAGE_SIZES else 24
        page = max(1, page)

        resources = [row for row in tables["resource"]["rows"] if not row.get("Hidden", False)]
        favorites_by_resource: dict[int, int] = {}
        for favorite in tables["favorites"]["rows"]:
            resource_id = favorite.get("ResourceID")
            if isinstance(resource_id, int):
                favorites_by_resource[resource_id] = favorites_by_resource.get(resource_id, 0) + 1

        results = []
        for resource in resources:
            metadata = resource.get("MetaData") or {}
            if normalized_query:
                search_text = " ".join([
                    self.resource_title(resource),
                    str(resource.get("OriginalName") or ""),
                    *(item for value in metadata.values() for item in self.metadata_values(value)),
                ]).casefold()
                if normalized_query not in search_text:
                    continue
            if any(
                selected not in {value.casefold() for value in self.metadata_values(metadata.get(name))}
                for name, selected in selected_filters.items()
            ):
                continue

            source = resource.get("Source")
            try:
                uploaded_at = Path(source).stat().st_mtime if source else float(resource["id"])
            except OSError:
                uploaded_at = float(resource["id"])
            download_count = resource.get("DownloadCount")
            popularity = (
                float(download_count)
                if isinstance(download_count, (int, float)) and not isinstance(download_count, bool)
                else favorites_by_resource.get(resource["id"], 0)
            )
            results.append({
                "resource": copy.deepcopy(resource),
                "uploaded_at": uploaded_at,
                "popularity": popularity,
            })

        if sort == "name":
            results.sort(key=lambda row: (self.resource_title(row["resource"]).casefold(), row["resource"]["id"]))
        elif sort == "popularity":
            results.sort(
                key=lambda row: (row["popularity"], row["uploaded_at"], row["resource"]["id"]),
                reverse=True,
            )
        else:
            results.sort(key=lambda row: (row["uploaded_at"], row["resource"]["id"]), reverse=True)

        total = len(results)
        page_count = (total + page_size - 1) // page_size
        page = min(page, max(page_count, 1))
        start = (page - 1) * page_size
        return {
            "results": results[start:start + page_size],
            "total": total,
            "page": page,
            "page_size": page_size,
            "page_count": page_count,
        }

    def find_resource_by_file_hash(self, file_hash: str) -> dict[str, Any] | None:
        normalized_hash = file_hash.casefold()
        with self._lock:
            database = self._read()
            for row in database["tables"]["resource"]["rows"]:
                if not row.get("Hidden", False) and self.resource_file_hash(row) == normalized_hash:
                    return copy.deepcopy(row)
        return None

    @staticmethod
    def resource_file_hash(resource: dict[str, Any]) -> str:
        file_hash = resource.get("FileHash")
        return file_hash.casefold() if isinstance(file_hash, str) else ""

    def update_resource_file_hash(self, resource_id: int, file_hash: str) -> None:
        with self._lock:
            database = self._read()
            for row in database["tables"]["resource"]["rows"]:
                if row["id"] == resource_id:
                    row["FileHash"] = file_hash
                    self._write(database)
                    return
            raise ValueError(f"Resource id {resource_id} does not exist.")

    def delete_resource(self, resource_id: int) -> dict[str, Any] | None:
        with self._lock:
            database = self._read()
            tables = database["tables"]
            resource = next((
                row for row in tables["resource"]["rows"]
                if row["id"] == resource_id and not row.get("Hidden", False)
            ), None)
            if resource is None:
                return None
            resource["Hidden"] = True
            self._write(database)
            return copy.deepcopy(resource)

    def insert_resource(self, values: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            database = self._read()
            tables = database["tables"]
            row = {column["name"]: copy.deepcopy(column.get("default")) for column in TABLE_COLUMNS["resource"]}
            row.update(copy.deepcopy(values))
            if not row.get("OriginalName"):
                raise ValueError("Resource OriginalName is required.")
            if row.get("UserID") not in {user["UserID"] for user in tables["user"]["rows"]}:
                raise ValueError("Resource UserID must reference an existing user.")
            if row.get("GroupID") is not None and row["GroupID"] not in {
                item["id"] for item in tables["resource"]["rows"] if not item.get("Hidden", False)
            }:
                raise ValueError("Resource GroupID must reference an existing resource.")
            if row.get("MetaData") is not None and not isinstance(row["MetaData"], dict):
                raise ValueError("Resource MetaData must be an object or null.")
            unknown_columns = set(values) - {column["name"] for column in TABLE_COLUMNS["resource"]}
            if unknown_columns:
                raise ValueError(f"Unknown resource columns: {', '.join(sorted(unknown_columns))}")
            row["id"] = database["next_ids"]["resource"]
            tables["resource"]["rows"].append(row)
            database["next_ids"]["resource"] += 1
            self._write(database)
            return copy.deepcopy(row)

    def track_download(self, resource_id: int) -> None:
        with self._lock:
            database = self._read()
            for row in database["tables"]["resource"]["rows"]:
                if row["id"] == resource_id and not row.get("Hidden", False):
                    row["DownloadCount"] = (row.get("DownloadCount") or 0) + 1
                    self._write(database)
                    return

    def update_resource_metadata(
        self,
        resource_id: int,
        display_name: str,
        metadata_values: dict[str, Any],
    ) -> dict[str, Any] | None:
        with self._lock:
            database = self._read()
            for row in database["tables"]["resource"]["rows"]:
                if row["id"] != resource_id:
                    continue
                row["DisplayName"] = display_name
                metadata = row.get("MetaData")
                if not isinstance(metadata, dict):
                    metadata = {}
                for name, value in metadata_values.items():
                    if value is None or (isinstance(value, str) and not value.strip()):
                        metadata.pop(name, None)
                    else:
                        metadata[name] = {"value": value, "source": "user", "reviewed": True}
                row["MetaData"] = metadata
                self._write(database)
                return copy.deepcopy(row)
            return None

    def get_user(self, user_id: int) -> dict[str, Any] | None:
        return next((row for row in self.rows("user") if row["UserID"] == user_id), None)

    def update_user_name(self, user_id: int, name: str) -> dict[str, Any] | None:
        normalized_name = name.strip() if isinstance(name, str) else ""
        if not normalized_name or len(normalized_name) > 255:
            raise ValueError("Display name must contain 1 to 255 characters.")
        with self._lock:
            database = self._read()
            user = next((row for row in database["tables"]["user"]["rows"] if row["UserID"] == user_id), None)
            if user is None:
                return None
            user["Name"] = normalized_name
            self._write(database)
            return copy.deepcopy(user)

    def update_user_type(self, user_id: int, user_type: str) -> dict[str, Any] | None:
        if user_type not in {"regular", "moderator"}:
            raise ValueError("UserType must be regular or moderator.")
        with self._lock:
            database = self._read()
            user = next((row for row in database["tables"]["user"]["rows"] if row["UserID"] == user_id), None)
            if user is None:
                return None
            if user["UserType"] == "admin":
                raise ValueError("Admin users cannot be changed through this endpoint.")
            user["UserType"] = user_type
            self._write(database)
            return copy.deepcopy(user)

    def count_resources_for_user(self, user_id: int) -> int:
        return sum(1 for row in self.visible_resources() if row["UserID"] == user_id)

    def is_favorite(self, user_id: int, resource_id: int) -> bool:
        return any(
            row["UserID"] == user_id and row["ResourceID"] == resource_id
            for row in self.rows("favorites")
        )

    def toggle_favorite(self, user_id: int, resource_id: int) -> bool:
        with self._lock:
            database = self._read()
            users = {row["UserID"] for row in database["tables"]["user"]["rows"]}
            resources = {
                row["id"] for row in database["tables"]["resource"]["rows"]
                if not row.get("Hidden", False)
            }
            if user_id not in users or resource_id not in resources:
                raise ValueError("Favorite must reference an existing user and resource.")
            favorites = database["tables"]["favorites"]["rows"]
            existing = next((
                row for row in favorites
                if row["UserID"] == user_id and row["ResourceID"] == resource_id
            ), None)
            if existing:
                favorites.remove(existing)
                is_favorite = False
            else:
                favorites.append({
                    "UserID": user_id,
                    "ResourceID": resource_id,
                    "FavoritedAt": datetime.now().replace(microsecond=0).isoformat(sep=" "),
                })
                is_favorite = True
            self._write(database)
            return is_favorite

    def remove_favorite(self, user_id: int, resource_id: int) -> None:
        with self._lock:
            database = self._read()
            favorites = database["tables"]["favorites"]["rows"]
            favorites[:] = [
                row for row in favorites
                if not (row["UserID"] == user_id and row["ResourceID"] == resource_id)
            ]
            self._write(database)

    def collections_for_user(self, user_id: int) -> list[dict[str, Any]]:
        collections = [row for row in self.rows("collection") if row.get("UserId") == user_id]
        return sorted(collections, key=lambda row: row["Name"].casefold())

    def collection_resource_ids(self, collection_ids: list[int], resource_id: int) -> list[int]:
        collection_id_set = set(collection_ids)
        return [
            row["CollectionID"]
            for row in self.rows("collection_member")
            if row["ResourceID"] == resource_id and row["CollectionID"] in collection_id_set
        ]

    def create_collection(self, user_id: int, name: str) -> dict[str, Any]:
        normalized_name = name.strip()
        if not normalized_name:
            raise ValueError("Collection name is required.")
        with self._lock:
            database = self._read()
            if user_id not in {row["UserID"] for row in database["tables"]["user"]["rows"]}:
                raise ValueError("Collection UserId must reference an existing user.")
            collection = {
                "id": database["next_ids"]["collection"],
                "Name": normalized_name,
                "Public": False,
                "UserId": user_id,
            }
            database["tables"]["collection"]["rows"].append(collection)
            database["next_ids"]["collection"] += 1
            self._write(database)
            return copy.deepcopy(collection)

    def add_resource_to_collection(self, user_id: int, collection_id: int, resource_id: int) -> bool:
        with self._lock:
            database = self._read()
            collection = next((
                row for row in database["tables"]["collection"]["rows"]
                if row["id"] == collection_id and row.get("UserId") == user_id
            ), None)
            if collection is None:
                raise ValueError("Collection does not belong to this user.")
            if resource_id not in {
                row["id"] for row in database["tables"]["resource"]["rows"]
                if not row.get("Hidden", False)
            }:
                raise ValueError("Resource does not exist.")
            members = database["tables"]["collection_member"]["rows"]
            if any(row["CollectionID"] == collection_id and row["ResourceID"] == resource_id for row in members):
                return False
            members.append({
                "id": database["next_ids"]["collection_member"],
                "CollectionID": collection_id,
                "ResourceID": resource_id,
                "Order": None,
                "Annotation": None,
            })
            database["next_ids"]["collection_member"] += 1
            self._write(database)
            return True

    def rename_collection(self, user_id: int, collection_id: int, name: str) -> dict[str, Any] | None:
        normalized_name = name.strip()
        if not normalized_name or len(normalized_name) > 255:
            raise ValueError("Collection name must contain 1 to 255 characters.")
        with self._lock:
            database = self._read()
            collection = next((
                row for row in database["tables"]["collection"]["rows"]
                if row["id"] == collection_id and row.get("UserId") == user_id
            ), None)
            if collection is None:
                return None
            collection["Name"] = normalized_name
            self._write(database)
            return copy.deepcopy(collection)

    def delete_collection(self, user_id: int, collection_id: int) -> bool:
        with self._lock:
            database = self._read()
            collections = database["tables"]["collection"]["rows"]
            collection = next((
                row for row in collections
                if row["id"] == collection_id and row.get("UserId") == user_id
            ), None)
            if collection is None:
                return False
            collections.remove(collection)
            database["tables"]["collection_member"]["rows"] = [
                row for row in database["tables"]["collection_member"]["rows"]
                if row["CollectionID"] != collection_id
            ]
            self._write(database)
            return True

    def remove_collection_item(self, user_id: int, collection_id: int, resource_id: int) -> bool:
        with self._lock:
            database = self._read()
            collection = next((
                row for row in database["tables"]["collection"]["rows"]
                if row["id"] == collection_id and row.get("UserId") == user_id
            ), None)
            if collection is None:
                raise ValueError("Collection does not belong to this user.")
            members = database["tables"]["collection_member"]["rows"]
            remaining = [
                row for row in members
                if not (row["CollectionID"] == collection_id and row["ResourceID"] == resource_id)
            ]
            if len(remaining) == len(members):
                return False
            database["tables"]["collection_member"]["rows"] = remaining
            self._write(database)
            return True
