import unittest
from fastapi.testclient import TestClient
from mcp_server.main import app

class TestIntegrationEndpoint(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_integration_stub(self):
        payload = {"source": "external", "payload": {"test": True}}
        response = self.client.post("/integration", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("status", data)
        self.assertIn("integration_payload", data)
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["integration_payload"], payload)

if __name__ == "__main__":
    unittest.main()
