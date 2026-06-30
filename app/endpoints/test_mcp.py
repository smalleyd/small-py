import unittest
from typing import Any
from ..main import app
from ..models.mcp import Mcp
from ..elastic.dao import Results
from ..models.common import Result
from parameterized import parameterized
from datetime import datetime, timedelta
from ..models.person import Person, Type
from fastapi.testclient import TestClient
from ..models.common import HEADER_API_KEY
from ..dao.startup import mcp_dao, session_dao

client = TestClient(app, headers={HEADER_API_KEY: "token-1"})
minutesAgo = datetime.now() - timedelta(minutes=5)
minutesAhead = datetime.now() + timedelta(minutes=5)

TOOL = {
    "method": "PUT",
    "name": "First",
    "description": "Number one",
    "url": "https://something.io/api",
    "headers": {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": "Bearer one-1"
    },
    "body_template": "body template 1",
    "input_schema": {
        "key-1": "value 1",
        "key-2": {"sub-2": "second", "sub-2.1": "Tuesday"},
        "key-3": 3,
        "key-4": 4.4,
        "key-5": [{"sub-5": "fifth", "sub-5.1": "Friday"}]
    },
    "response_transform": "response 1",
    "timeout_ms": 5000
}

VALUE = {
    "id": "mcp-1",
    "name": "Test 1",
    "slug": "test-1",
    "description": "Test One",
    "tools": [ TOOL ],
    "authentication": {
        "type": "ApiKey",
        "header": "X-Techmo-Key",
        "url": "https://something.io/login"
    },
    "oauth": {
        "authorization_url": "https://authorization.url",
        "token_url": "https://token.url",
        "client_id": "client_id_1",
        "client_secret": "client_secret_1",
        "scopes": ["read", "write"],
        "extra_params": {
            "extra": "params"
        }
    }
}

class TestMcpEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        session_dao.load([
            {"id": "token-1", "person": {"id": "person-1", "email": "one@test.com", "name": "Name", "first_name": "First", "last_name": "Last", "type": Type.ADMIN.value}, "duration": None},
            {"id": "token-2", "person": {"id": "person-2", "email": "one@test.com", "name": "Name", "first_name": "First", "last_name": "Last", "type": Type.USER.value}, "duration": None},
            {"id": "token-3", "person": {"id": "person-1", "email": "one@test.com", "name": "Name", "first_name": "First", "last_name": "Last", "type": Type.USER.value}, "duration": None}
        ])

    @classmethod
    def tearDownClass(cls):
        session_dao.remove("token-1", "token-2", "token-3")

    def test_000_find(self):
        response = client.get("/mcp")
        self.assertEqual(200, response.status_code, "Check status_code")

        value = Results[Mcp](**response.json())
        self.assertEqual(0, value.total, "Check total")
        self.assertEqual(0, len(value.data), "Check data")

    def test_000_get_fail(self):
        response = client.get("/mcp/mcp-1")
        self.assertEqual(404, response.status_code, "Check status_code")

    def test_010_post(self):
        response = client.post("/mcp", json=VALUE)
        self.assertEqual(201, response.status_code, "Check status_code")

        value = Mcp(**response.json())
        self.assertEqual("mcp-1", value.id, "Check ID")
        self.assertEqual("Test 1", value.name, "Check name")
        self.assertIsNone(value.archived_at, "Check archived_at")
        self.assertIsNotNone(value.created_at, "Check created_at")
        self.assertEqual(value.created_at, value.updated_at, "Check updated_at")

    def test_010_post_dupe(self):
        value = VALUE.copy()
        value["id"] = "mcp-0"
        response = client.post("/mcp", json=value)
        self.assertEqual(422, response.status_code, "Check status_code")

        results = response.json()
        self.assertIsNotNone(results, "Check results")
        self.assertEqual({"detail":[], "title": "The slug is already in use by another mcp."}, results, "Check results")

    def test_010_post_get(self):
        response = client.get("/mcp/mcp-1")
        self.assertEqual(200, response.status_code, "Check status_code")

        value = Mcp(**response.json())
        self.assertEqual("mcp-1", value.id, "Check ID")
        self.assertEqual("Test 1", value.name, "Check name")
        self.assertEqual(1, len(value.tools), "Check tools")
        self.assertIsNone(value.archived_at, "Check archived_at")
        self.assertIsNotNone(value.created_at, "Check created_at")
        self.assertEqual(value.created_at, value.updated_at, "Check updated_at")

        tool = value.tools[0]
        self.assertEqual("First", tool.name, "Check tools[0].name")
        self.assertIsNotNone(tool.input_schema, "Check tools[0].input_schema")
        self.assertEqual(TOOL["input_schema"], tool.input_schema, "Check tools[0].input_schema")

    @parameterized.expand([
        ("slug-1", False),
        ("test-1", True)
    ])
    def test_010_post_has_slug(self, slug: str, expected: bool):
        response = client.get(f"/mcp/slugs/{slug}/exists")
        self.assertEqual(200, response.status_code, "Check status_code")

        result = Result[bool](**response.json())
        self.assertIsNotNone(result, "Check result")
        self.assertEqual(expected, result.value, "Check result.value")

    def test_010_post_get_by_slug_fail(self):
        response = client.get("/mcp/slugs/slug-1")
        self.assertEqual(404, response.status_code, "Check status_code")

    def test_010_post_get_by_slug_success(self):
        response = client.get("/mcp/slugs/test-1")
        self.assertEqual(200, response.status_code, "Check status_code")

        value = Mcp(**response.json())
        self.assertIsNotNone(value, "Exists")
        self.assertEqual("mcp-1", value.id, "Check ID")

    def test_020_put(self):
        VALUE["name"] = "Name 1"

        response = client.put("/mcp", json=VALUE)
        self.assertEqual(200, response.status_code, "Check status_code")

        value = Mcp(**response.json())
        self.assertEqual("mcp-1", value.id, "Check ID")
        self.assertEqual("Name 1", value.name, "Check name")
        self.assertIsNone(value.archived_at, "Check archived_at")
        self.assertIsNotNone(value.created_at, "Check created_at")
        self.assertLess(value.created_at, value.updated_at, "Check updated_at")

    def test_020_put_find(self):
        response = client.get("/mcp")
        self.assertEqual(200, response.status_code, "Check status_code")

        value = Results[Mcp](**response.json())
        self.assertEqual(1, value.total, "Check total")
        self.assertEqual(1, len(value.data), "Check data")

    def test_020_put_get(self):
        response = client.get("/mcp/mcp-1")
        self.assertEqual(200, response.status_code, "Check status_code")

        value = Mcp(**response.json())
        self.assertEqual("mcp-1", value.id, "Check ID")
        self.assertEqual("Name 1", value.name, "Check name")
        self.assertIsNone(value.archived_at, "Check archived_at")
        self.assertIsNotNone(value.created_at, "Check created_at")
        self.assertLess(value.created_at, value.updated_at, "Check updated_at")

    def test_030_patch(self):
        response = client.patch("/mcp/mcp-1", json={"name": "Patch 1"})
        self.assertEqual(200, response.status_code, "Check status_code")

        value = Mcp(**response.json())
        self.assertEqual("mcp-1", value.id, "Check ID")
        self.assertEqual("Patch 1", value.name, "Check name")
        self.assertIsNone(value.archived_at, "Check archived_at")
        self.assertIsNotNone(value.created_at, "Check created_at")
        self.assertLess(value.created_at, value.updated_at, "Check updated_at")

    def test_030_patch_fail(self):
        response = client.patch("/mcp/mcp-1", json={"name": "a" * 501})
        self.assertEqual(422, response.status_code, "Check status_code")

        value = response.json()
        print("VALUE:", value)
        expected = {"detail": [{
            "type": "string_too_long",
            "loc": ["name"],
            "msg": "String should have at most 500 characters",
            "input": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "ctx": {"max_length": 500},
            "url": "https://errors.pydantic.dev/2.13/v/string_too_long"
        }], "title": "Patch Error"}

        self.assertIsNotNone(value, "Exists")
        self.assertEqual(expected, value, "Check value")

    def test_030_patch_get(self):
        response = client.get("/mcp/mcp-1")
        self.assertEqual(200, response.status_code, "Check status_code")

        value = Mcp(**response.json())
        self.assertEqual("mcp-1", value.id, "Check ID")
        self.assertEqual("Patch 1", value.name, "Check name")
        self.assertIsNone(value.archived_at, "Check archived_at")
        self.assertIsNotNone(value.created_at, "Check created_at")
        self.assertLess(value.created_at, value.updated_at, "Check updated_at")

    @parameterized.expand([
        ({"ids": ["mcp-0", "mcp-2"]}, 0),
        ({"ids": ["mcp-0", "mcp-1"]}, 1),
        ({"name": "Name"}, 0),
        ({"name": "patch"}, 1),
        ({"slug": "test-0"}, 0),
        ({"slug": "Test-1"}, 1),
        ({"description": "Zero"}, 0),
        ({"description": "one"}, 1),
        ({"tools_name": "Second"}, 0),
        ({"tools_name": "first"}, 1),
        ({"tools_description": "zero"}, 0),
        ({"tools_description": "One"}, 1),
        ({"authentication_type": "ApiKey"}, 1),
        ({"authentication_type": "Bearer"}, 0),
        ({"authentication_type": "Basic"}, 0),
        ({"authentication_header": "x-techmo-key"}, 1),
        ({"authentication_header": "X-Techmo-Keys"}, 0),
        ({"authentication_url": "https://something.io/login"}, 1),
        ({"authentication_url": "https://something.io/Login"}, 1),
        ({"authentication_url": "https://something.io/auth"}, 0),
        ({"has_authentication": True}, 1),
        ({"has_authentication": False}, 0),
        ({"has_oauth": True}, 1),
        ({"has_oauth": False}, 0),
        ({"creator_id": "person-1"}, 1),
        ({"creator_id": "person-2"}, 0),
        ({"creator_name": "name"}, 1),
        ({"creator_name": "invalid"}, 0),
        ({"created_at_from": minutesAhead}, 0),
        ({"created_at_from": minutesAgo}, 1),
        ({"created_at_to": minutesAhead}, 1),
        ({"created_at_to": minutesAgo}, 0),
        ({"created_at_from": minutesAhead, "created_at_to": minutesAgo}, 0),
        ({"created_at_from": minutesAgo, "created_at_to": minutesAhead}, 1),
        ({"updated_at_from": minutesAhead}, 0),
        ({"updated_at_from": minutesAgo}, 1),
        ({"updated_at_to": minutesAhead}, 1),
        ({"updated_at_to": minutesAgo}, 0),
        ({"updated_at_from": minutesAhead, "updated_at_to": minutesAgo}, 0),
        ({"updated_at_from": minutesAgo, "updated_at_to": minutesAhead}, 1),
        ({"archived_at_from": minutesAhead}, 0),
        ({"archived_at_from": minutesAgo}, 0),
        ({"archived_at_to": minutesAhead}, 0),
        ({"archived_at_to": minutesAgo}, 0),
        ({"has_archived_at": False}, 1),
        ({"has_archived_at": True}, 0),
    ])
    def test_040_find(self, f: dict[str, Any], expected: int):
        response = client.get("/mcp", params=f)
        self.assertEqual(200, response.status_code, "Check status_code")

        value = Results[Mcp](**response.json())
        self.assertEqual(expected, value.total, "Check total")
        self.assertEqual(expected, len(value.data), "Check data")
        self.assertIsNone(value.scroll_id, "Check scroll_id")

        if expected == 1:
            self.assertEqual("mcp-1", value.data[0]["id"], "Check ID")

    @parameterized.expand([
        ("token-2", 0),
        ("token-3", 1)
    ])
    def test_040_find_as(self, token: str, expected: int):
        with TestClient(app, headers={HEADER_API_KEY: token}) as client_:
            response = client_.get("/mcp")
            self.assertEqual(200, response.status_code, "Check status_code")

            results = Results[Mcp](**response.json())
            self.assertIsNotNone(results, "Exists")
            self.assertEqual(expected, results.total, "Check total")
            self.assertEqual(expected, len(results.data), "Check data")
            self.assertEqual(expected, len(results.scores), "Check scores")

    def test_050_archive(self):
        response = client.delete("/mcp/mcp-1/archive")
        self.assertEqual(204, response.status_code, "Check status_code")

    def test_050_archive_get(self):
        response = client.get("/mcp/mcp-1")
        self.assertEqual(200, response.status_code, "Check status_code")

        value = Mcp(**response.json())
        self.assertEqual("mcp-1", value.id, "Check ID")
        self.assertEqual("Patch 1", value.name, "Check name")
        self.assertIsNotNone(value.archived_at, "Check archived_at")
        self.assertIsNotNone(value.created_at, "Check created_at")
        self.assertLess(value.created_at, value.updated_at, "Check updated_at")
        self.assertEqual(value.archived_at, value.updated_at, "Check updated_at")

    @parameterized.expand([
        ({"has_archived_at": False}, 0),
        ({"has_archived_at": True}, 1),
    ])
    def test_050_archive_find(self, f: dict[str, Any], expected: int):
        response = client.get("/mcp", params=f)
        self.assertEqual(200, response.status_code, "Check status_code")

        value = Results[Mcp](**response.json())
        self.assertEqual(expected, value.total, "Check total")
        self.assertEqual(expected, len(value.data), "Check data")
        self.assertIsNone(value.scroll_id, "Check scroll_id")

        if expected == 1:
            self.assertEqual("mcp-1", value.data[0]["id"], "Check ID")

    def test_60_load(self):
        v = []
        for i in range(2, 11):
            value = VALUE.copy()
            value["id"] = f"mcp-{i}"
            value["name"] = f"MCP {i}"
            value["slug"] = f"slug-{i}"
            v.append(value)

        mcp_dao.load(v)
        mcp_dao.refresh()

    def test_60_load_find(self):
        response = client.get("/mcp", params={"size": 5, "scroll": "30s"})
        self.assertEqual(200, response.status_code, "Check status_code")

        value = Results[Mcp](**response.json())
        self.assertEqual(10, value.total, "Check total")
        self.assertEqual(5, len(value.data), "Check data")
        self.assertIsNotNone(value.scroll_id, "Check scroll_id")

        response = client.get(f"/mcp/scroll/{value.scroll_id}")
        self.assertEqual(200, response.status_code, "Check status_code")

        value = Results[Mcp](**response.json())
        self.assertEqual(10, value.total, "Check total")
        self.assertEqual(5, len(value.data), "Check data")
        self.assertIsNotNone(value.scroll_id, "Check scroll_id")

        response = client.get(f"/mcp/scroll/{value.scroll_id}")
        self.assertEqual(200, response.status_code, "Check status_code")

        value = Results[Mcp](**response.json())
        self.assertEqual(10, value.total, "Check total")
        self.assertEqual(0, len(value.data), "Check data")
        self.assertIsNone(value.scroll_id, "Check scroll_id")

    def test_70_set_tools(self):
        TOOL["name"] = "Tool 1"
        response = client.put("/mcp/mcp-1/tools", json=[TOOL])
        self.assertEqual(204, response.status_code, "Check status_code")

    def test_70_set_tools_get(self):
        response = client.get("/mcp/mcp-1")
        self.assertEqual(200, response.status_code, "Check status_code")

        value = Mcp(**response.json())
        self.assertIsNotNone(value, "Exists")
        self.assertEqual(1, len(value.tools), "Check tools")
        self.assertEqual("Tool 1", value.tools[0].name, "Check tools[0].name")

    def test_999_delete(self):
        response = client.delete("/mcp/mcp-1")
        self.assertEqual(204, response.status_code, "Check status_code")

    def test_999_delete_get(self):
        response = client.get("/mcp/mcp-1")
        self.assertEqual(404, response.status_code, "Check status_code")

if __name__ == '__main__':
    unittest.main()
