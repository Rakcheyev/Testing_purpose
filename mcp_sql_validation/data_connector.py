"""
MCP Data Connector для витягу метаданих MS SQL
Підключення лише для INFORMATION_SCHEMA, sys.tables, sys.indexes
"""
import pyodbc

class MCPDataConnector:
    def __init__(self, server, database, user, password, driver="ODBC Driver 18 for SQL Server"):
        self.conn_str = (
            f"DRIVER={driver};SERVER={server};DATABASE={database};UID={user};PWD={password};TrustServerCertificate=yes;"
        )
        self.connection = None

    def connect(self):
        self.connection = pyodbc.connect(self.conn_str)

    def fetch_metadata(self):
        cursor = self.connection.cursor()
        # Витягуємо схеми, таблиці, індекси
        schemas = cursor.execute("SELECT * FROM INFORMATION_SCHEMA.SCHEMATA").fetchall()
        tables = cursor.execute("SELECT * FROM INFORMATION_SCHEMA.TABLES").fetchall()
        indexes = cursor.execute("SELECT * FROM sys.indexes").fetchall()
        return {
            "schemas": [dict(zip([column[0] for column in cursor.description], row)) for row in schemas],
            "tables": [dict(zip([column[0] for column in cursor.description], row)) for row in tables],
            "indexes": [dict(zip([column[0] for column in cursor.description], row)) for row in indexes],
        }

    def close(self):
        if self.connection:
            self.connection.close()
