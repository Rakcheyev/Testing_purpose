from logging import log_result, report_results

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
