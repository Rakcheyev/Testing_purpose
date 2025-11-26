import unittest
from fastapi.testclient import TestClient
from mcp_server.main import app

class TestStandardizeEndpoint(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_standardize_stub(self):
        payload = {"resource_type": "PBIP", "data": {"test": True}}
        response = self.client.post("/standardize", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("status", data)
        self.assertIn("resource_type", data)
        self.assertIn("result", data)
        self.assertEqual(data["status"], "standardized")
        self.assertEqual(data["resource_type"], payload["resource_type"])
        self.assertEqual(data["result"], "ok")

if __name__ == "__main__":
    unittest.main()
