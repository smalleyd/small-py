import unittest
from typing import Any
from fastapi.testclient import TestClient
from ..main import app

client = TestClient(app, headers={"Authorization": "Bearer token-1"})

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

import sys

class TestMcpEndpoints(unittest.TestCase):
    def test_00_get_fail(self):
        print("SYSTEM:", sys, sys.argv)
        response = client.get("/mcp/mcp-1")
        self.assertEqual(404, response.status_code, "Check status_code")

    def test_10_post(self):
        response = client.post("/mcp", json=VALUE)
        self.assertEqual(201, response.status_code, "Check status_code")

        value: dict[str, Any] = response.json()
        self.assertEqual("mcp-1", value["id"], "Check ID")
        self.assertIsNone(value["archived_at"], "Check archived_at")

    def test_10_post_get(self):
        response = client.get("/mcp/mcp-1")
        self.assertEqual(200, response.status_code, "Check status_code")

        value: dict[str, Any] = response.json()
        self.assertEqual("mcp-1", value["id"], "Check ID")
        self.assertIsNone(value.get("archived_at", None), "Check archived_at")

if __name__ == '__main__':
    unittest.main()
