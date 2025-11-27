# CHANGELOG

## 2025-11-26

### MCP Server Endpoints
- Реалізовано базові ендпоінти MCP Server: /integration, /review, /standardize, /monitoring (api.py, main.py)
- Додано stub-логіку для payload/response
- Додано unit-тести для всіх базових ендпоінтів (tests/)

### Session Lifecycle & Audit Trail
- Розширено `SessionManager`: додано `process_session`, аудит історії, статуси `started/processing/closed`.
- Ендпоінти `/session/start`, `/process`, `/session/close` тепер використовують спільний менеджер та повертають деталізований стан сесії.
- Додано тести `test_session_lifecycle.py`, оновлено `test_session_manager.py` для перевірки життєвого циклу.
- README, TODO та AGENTS доповнені описом workflow і доступними статусами.

### LLM Integration Planning
- TODO.md доповнено задачами з інтеграції локальних моделей (Llama/Mistral/Phi) та прошарку зовнішніх моделей із фільтрацією даних.

### PBIP TMDL Standardization
- У TODO.md додано критичні підзадачі для модулю пакетного перепису TMDL: парсер, правила зі стандартів, pipeline трансформацій, тестування, інтеграція та безпекові налаштування.


## [Unreleased]
 - Створено каркас серверної частини MCP (mcp_server/): main.py, config.py, api.py, security.py, orchestration.py, standards/, tests/
 - Оновлено README.md: додано секцію про MCP server, його структуру та інтеграцію
 - Оновлено TODO.md: додано пункт про MCP server, його структуру та задачі
 - Дороблено плейсхолдер-скрипт external/update_standards.py для автоматичного оновлення external/standards_mcp.json при зміні підмодулів/стандартів. Додано TODO для CI/CD інтеграції.

### Архітектура та документація
- Створено README.md з бізнес-описом, цінністю, ризиками, перевагами, DataGovernance
- Додано архітектурні діаграми MCP (Mermaid), коментарі, пояснення
- Описано всі MCP AI Integration Layers, їх вплив, альтернативи, безпеку
- Додано секцію про enterprise деплой PBIX через REST API
- Оновлено TODO.md: додано пункти щодо автоматизації деплою, рев'ю, DataGovernance

### Стандарти та інтеграція
- Додано підмодулі external/Power_Query_guide та external/DAX_Templates для корпоративних стандартів M-Query та DAX
- Зчитано та структуровано стандарти у external/standards_mcp.json для MCP

### Модулі та автоматизація
- Створено каркас pbip_artifacts для рев'ю, експорту, валідації, порівняння PBIP/PBIX
- Додано плейсхолдер pbip_artifacts/deploy_enterprise.py для enterprise-автоматизації деплою PBIX
- Додано pbip_report.py, pbip_validate.py, pbip_compare.py, pbip_extract.py (плейсхолдери)
- Створено каркас для автоматичного парсингу та валідації Excel, CSV, API (fabric_external_data/parse_validate.py)

### Рев'ю, CI/CD, DataGovernance
- Описано процес рев'ю PBIP через pull request, контроль версій, аудит
- Додано концепт DataGovernance, політики доступу, аудит, інтеграція з платформами (Purview, Collibra)
- Описано можливість CI/CD деплою через Azure DevOps, GitHub Actions, Power BI Deployment Pipelines

### Інше
- Всі зміни фіксуються у README.md, TODO.md, CHANGELOG.md
