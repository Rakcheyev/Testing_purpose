import unittest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from mcp_server.api import router

app = FastAPI()
app.include_router(router)
client = TestClient(app)

class TestMetadataSync(unittest.TestCase):
    def test_sync_metadata(self):
        payload = {
            "model_id": "pbip-2025-001",
            "metadata": {
                "name": "Sales Analytics",
                "version": "v1.0",
                "description": "Модель для аналізу продажів",
                "resources": ["PBIP", "DAX", "SQL"],
                "structure": {
                    "tables": ["Sales", "Customers", "Products"],
                    "measures": ["Total Sales", "Average Price"],
                    "relations": [{"from": "Sales", "to": "Customers", "type": "many-to-one"}]
                },
                "created_at": "2025-11-26T10:00:00Z",
                "updated_at": "2025-11-26T12:00:00Z",
                "owner": "bi-team"
            }
        }
        response = client.post("/metadata/sync", json=payload)
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result["model_id"], payload["model_id"])
        self.assertEqual(result["metadata"], payload["metadata"])
        self.assertEqual(result["status"], "synced")

if __name__ == "__main__":
    unittest.main()
