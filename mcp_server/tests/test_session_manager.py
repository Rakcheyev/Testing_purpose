import unittest
from mcp_server.orchestration import SessionManager

class TestSessionManager(unittest.TestCase):
    def setUp(self):
        self.manager = SessionManager()

    def test_start_session(self):
        session_id = self.manager.start_session()
        self.assertTrue(session_id)
        self.assertIn(session_id, self.manager.sessions)
        self.assertEqual(self.manager.sessions[session_id]["status"], "started")

    def test_context(self):
        session_id = self.manager.start_session()
        context = {"user": "test"}
        self.manager.set_context(session_id, context)
        self.assertEqual(self.manager.get_context(session_id), context)

    def test_close_session(self):
        session_id = self.manager.start_session()
        self.manager.close_session(session_id)
        self.assertEqual(self.manager.sessions[session_id]["status"], "closed")

if __name__ == "__main__":
    unittest.main()
