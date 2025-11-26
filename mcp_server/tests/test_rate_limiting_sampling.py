import unittest
from fastapi.testclient import TestClient
from mcp_server.main import app

class TestRateLimitingAndSampling(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_rate_limiting(self):
        # Send RATE_LIMIT requests, should be ok
        for _ in range(5):
            response = self.client.get("/limited/health")
            self.assertEqual(response.status_code, 200)
        # 6th request should be rate limited
        response = self.client.get("/limited/health")
        self.assertEqual(response.status_code, 429)
        self.assertIn("Rate limit exceeded", response.text)

    def test_audit_sampling(self):
        # Send 10 requests, some should be sampled
        for _ in range(10):
            self.client.get("/sampled/health")
        response = self.client.get("/audit/sampled")
        data = response.json()
        self.assertIn("sampled_requests", data)
        # Should be between 1 and 10 sampled requests (30% sample rate)
        self.assertTrue(0 <= len(data["sampled_requests"]) <= 10)

if __name__ == "__main__":
    unittest.main()
