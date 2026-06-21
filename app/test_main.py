import unittest
from .main import app
from fastapi.testclient import TestClient

client = TestClient(app)

class MainEndpointsTest(unittest.TestCase):
    def test_000_root(self):
        response = client.get("/")
        self.assertEqual(200, response.status_code, "Check status_code")
        self.assertEqual({"message": "Hello World"}, response.json(), "Check json")