import unittest
from fastapi.testclient import TestClient
from mcp_server.main import app

class TestMonitoringEndpoint(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_monitoring_stub(self):
        response = self.client.get("/monitoring")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("status", data)
        self.assertIn("timestamp", data)
        self.assertEqual(data["status"], "active")
        self.assertIsInstance(data["timestamp"], float)

if __name__ == "__main__":
    unittest.main()
