import unittest
from mcp_server.orchestration import SessionManager, AuditTrail

class TestSessionManager(unittest.TestCase):
    def setUp(self):
        self.audit = AuditTrail()
        self.manager = SessionManager(audit=self.audit)

    def test_start_session(self):
        session_id = self.manager.start_session()
        self.assertTrue(session_id)
        self.assertIn(session_id, self.manager.sessions)
        self.assertEqual(self.manager.sessions[session_id]["status"], "started")
        self.assertEqual(len(self.manager.sessions[session_id]["history"]), 1)

    def test_context(self):
        session_id = self.manager.start_session()
        context = {"user": "test"}
        self.manager.set_context(session_id, context)
        self.assertEqual(self.manager.get_context(session_id), context)

    def test_process_session(self):
        session_id = self.manager.start_session()
        entry = self.manager.process_session(session_id, action="validate", payload={"step": 1})
        self.assertEqual(entry["action"], "validate")
        self.assertEqual(entry["status"], "ok")
        self.assertEqual(self.manager.sessions[session_id]["status"], "processing")
        self.assertEqual(len(self.audit.get_session_records(session_id)), 2)

    def test_close_session(self):
        session_id = self.manager.start_session()
        closure = self.manager.close_session(session_id)
        self.assertEqual(self.manager.sessions[session_id]["status"], "closed")
        self.assertEqual(closure["status"], "closed")
        self.assertEqual(len(self.audit.get_session_records(session_id)), 2)

if __name__ == "__main__":
    unittest.main()
