import unittest
from fastapi.testclient import TestClient
from mcp_server.main import app

class TestReviewEndpoint(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_review_stub(self):
        payload = {"resource_type": "PBIP", "data": {"test": True}}
        response = self.client.post("/review", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("status", data)
        self.assertIn("resource_type", data)
        self.assertEqual(data["status"], "reviewed")
        self.assertEqual(data["resource_type"], payload["resource_type"])

if __name__ == "__main__":
    unittest.main()
