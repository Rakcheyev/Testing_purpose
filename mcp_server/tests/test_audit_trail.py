import unittest
from mcp_server.orchestration import SessionManager, AuditTrail

class TestAuditTrail(unittest.TestCase):
    def setUp(self):
        self.audit = AuditTrail()
        self.session_id = "test-session"

    def test_log_and_retrieve(self):
        self.audit.log(self.session_id, "user1", "init", "started")
        self.audit.log(self.session_id, "user1", "process", "ok")
        records = self.audit.get_session_records(self.session_id)
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["action"], "init")
        self.assertEqual(records[1]["status"], "ok")

    def test_export(self):
        self.audit.log(self.session_id, "user1", "init", "started")
        exported = self.audit.export()
        self.assertTrue(isinstance(exported, list))
        self.assertEqual(exported[0]["session_id"], self.session_id)

if __name__ == "__main__":
    unittest.main()
