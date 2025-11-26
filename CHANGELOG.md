# CHANGELOG

## 2025-11-26
- Реалізовано логування та репортинг результатів для прошарку MS SQL Validation (`mcp_sql_validation/logging.py`, `mcp_sql_validation/example_usage.py`)
- Відмічено виконання пункту TODO у README.md

- Додано підмодулі Power_Query_guide та DAX_Templates для стандартів M-Query та DAX
- Стандарти зчитано та структуровано у external/standards_mcp.json для MCP
- Оновлено README.md та TODO.md для відображення інтеграції external standards

- Створено папку pbip_artifacts для мірорингу PBIP, M-коду, DAX та тестування модулів рев'ю/стандартизації

- Створено папку pbip_staging для проміжного зберігання PBIP, M-коду, DAX
- Описано процес автоматичних перевірок та перенесення артефактів у pbip_artifacts лише після успішного рев'ю

- Створено каркас для автоматичного парсингу та валідації Excel, CSV, API (fabric_external_data/parse_validate.py)
