import unittest
from typing import Any
from ..elastic.dao import Results
from fastapi.testclient import TestClient
from ..main import app
from ..models.mcp import Mcp
from parameterized import parameterized
from datetime import datetime, timedelta

client = TestClient(app, headers={"Authorization": "Bearer token-1"})
minutesAgo = datetime.now() - timedelta(minutes=5)
minutesAhead = datetime.now() + timedelta(minutes=5)

VALUE = {
  "id": "mcp-1",
  "name": "Test 1",
  "slug": "test-1",
  "description": "Test One",
  "api_key": "test_1",
  "tools": [
    {
      "name": "First",
      "description": "Number one",
      "input_schema": {
        "key-1": "value 1",
        "key-2": "value 2"
      },
      "execution_config": {
        "url": "https://something.io/api",
        "method": "PUT",
        "headers": {
          "Accept": "application/json",
          "Content-Type": "application/json",
          "Authorization": "Bearer one-1"
        },
        "body_template": "body template 1",
        "authentication": "ApiKey"
      },
      "response_transform": "response 1",
      "timeout_ms": 5000
    }
  ]
}

class TestMcpEndpoints(unittest.TestCase):
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

    def test_010_post_get(self):
        response = client.get("/mcp/mcp-1")
        self.assertEqual(200, response.status_code, "Check status_code")

        value = Mcp(**response.json())
        self.assertEqual("mcp-1", value.id, "Check ID")
        self.assertEqual("Test 1", value.name, "Check name")
        self.assertIsNone(value.archived_at, "Check archived_at")
        self.assertIsNotNone(value.created_at, "Check created_at")
        self.assertEqual(value.created_at, value.updated_at, "Check updated_at")

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

    def test_050_archive(self):
        response = client.delete("/mcp/mcp-1")
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

if __name__ == '__main__':
    unittest.main()
