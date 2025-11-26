import unittest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from mcp_server.api import router

app = FastAPI()
app.include_router(router)
client = TestClient(app)

class TestCapabilityNegotiation(unittest.TestCase):
    def test_negotiate_capabilities(self):
        client_caps = {
            "PBIP": ["review", "deploy", "unknown_action"],
            "DAX": ["lint", "optimize"],
            "SQL": ["execute", "drop"]
        }
        response = client.post("/capabilities/negotiate", json=client_caps)
        self.assertEqual(response.status_code, 200)
        negotiated = response.json()["negotiated"]
        self.assertIn("PBIP", negotiated)
        self.assertIn("review", negotiated["PBIP"])
        self.assertIn("deploy", negotiated["PBIP"])
        self.assertNotIn("unknown_action", negotiated["PBIP"])
        self.assertIn("lint", negotiated["DAX"])
        self.assertIn("optimize", negotiated["DAX"])
        self.assertIn("execute", negotiated["SQL"])
        self.assertNotIn("drop", negotiated["SQL"])

if __name__ == "__main__":
    unittest.main()
