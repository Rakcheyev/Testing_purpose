from logging import log_result, report_results
from mcp_sql_validation.data_connector import MCPDataConnector
import os

# Example validation results
results = [
    ['users', 'schema_check', 'PASS', 'All columns present'],
    ['orders', 'procedure_check', 'FAIL', 'Missing index'],
]

# Log individual results
for table, check, status, details in results:
    msg = f"{table}: {check} - {status} ({details})"
    log_result(msg, 'info' if status == 'PASS' else 'warning')

# Save report
report_file = report_results(results)
print(f"Report generated: {report_file}")

# --- MCP Data Connector usage example ---

# Параметри підключення (тільки для метаданих, не зберігати паролі у відкритому вигляді)
server = os.getenv("MSSQL_SERVER", "localhost")
database = os.getenv("MSSQL_DB", "master")
user = os.getenv("MSSQL_USER", "readonly")
password = os.getenv("MSSQL_PASSWORD", "your_password")

connector = MCPDataConnector(server, database, user, password)
connector.connect()
metadata = connector.fetch_metadata()
print("Schemas:", metadata["schemas"])
print("Tables:", metadata["tables"])
print("Indexes:", metadata["indexes"])
connector.close()
# --- End MCP Data Connector example ---
