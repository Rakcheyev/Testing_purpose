import unittest
from fastapi.testclient import TestClient

from mcp_server.main import app
from mcp_server.orchestration import session_manager


class TestSessionLifecycleEndpoints(unittest.TestCase):
    def setUp(self):
        session_manager.reset()
        session_manager.audit.reset()
        self.client = TestClient(app)

    def tearDown(self):
        session_manager.reset()
        session_manager.audit.reset()

    def test_full_lifecycle(self):
        start_response = self.client.post("/session/start", headers={"X-User-ID": "tester"})
        self.assertEqual(start_response.status_code, 200)
        data = start_response.json()
        session_id = data["session_id"]
        self.assertEqual(data["status"], "started")

        process_response = self.client.post(
            "/process",
            headers={"X-Session-ID": session_id, "X-User-ID": "tester"},
            json={"action": "validate", "data": {"step": 1}},
        )
        self.assertEqual(process_response.status_code, 200)
        process_data = process_response.json()
        self.assertEqual(process_data["status"], "ok")
        self.assertEqual(process_data["session_state"], "processing")

        close_response = self.client.post(
            "/session/close",
            headers={"X-Session-ID": session_id, "X-User-ID": "tester"},
            json={"status": "closed"},
        )
        self.assertEqual(close_response.status_code, 200)
        close_data = close_response.json()
        self.assertEqual(close_data["status"], "closed")
        self.assertEqual(close_data["session_state"], "closed")

        history = session_manager.sessions[session_id]["history"]
        self.assertEqual(len(history), 3)
        audit_records = session_manager.audit.get_session_records(session_id)
        self.assertEqual(len(audit_records), 3)

    def test_missing_session(self):
        response = self.client.post("/process", headers={"X-Session-ID": "unknown"})
        self.assertEqual(response.status_code, 404)
        self.assertIn("Session not found", response.text)


if __name__ == "__main__":
    unittest.main()
