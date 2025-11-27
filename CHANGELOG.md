# CHANGELOG

## 2025-11-27

### Pilot PBIP Workflow
- Ліквідовано статичні профілі `pbip_staging/profiles/`; pipeline тепер покладається на метадані поруч із PBIP та евристики класифікації.
- Реалізовано локальний CLI `python -m pbip_staging.pilot_pipeline` для запуску workflow без HTTP API.
- Історичні артефакти `pbip_artifacts/pilot_case/<id>/` позначені як legacy; поточні результати формуються у `pbip_artifacts/reviews/`.
- README, TODO, AGENTS оновлені описом сценарію та наступними кроками (UI для презентації).

### Pipeline Refinement
- CLI оновлено до кейс-агностичного режиму: PBIP-файли скануються з `pbip_staging/input/` або заданих шляхів, стандартні профілі підтягуються автоматично.
- Додано розгорнуті перевірки кроку `standards`: snake_case для мір, PascalCase для колонок, контроль display folders, обов'язковість formatString, виявлення базових DAX-антипатернів, генерація `standards.json` та `recommended_renames.tmdl` (включає перейменування, display folders, formatString).
- Розширено класифікацію доменів (sales, finance, supply_chain, marketing, hr, multi-domain) із врахуванням метаданих та структури моделі.
- Артефакти переносяться у `pbip_artifacts/reviews/<domain>__<назва>_<hash>/` з окремими `summary.json`, `audit.json`, `session_history.json`, `standards.json`.
- CLI тепер напряму обробляє директорії `*.pbip`, зчитуючи `DataModelSchema.json`.
- Документацію (`README.md`, `pbip_staging/README.md`, `AGENTS.MD`, `TODO.md`) синхронізовано з новою логікою.

### Standards Catalog Schema
- Розширено `StandardRule` у `mcp_server/standards/reader.py`: додано `applies_to`, `automation.check`, `automation.auto_fix`, згенеровано перформанс-правила.
- `python -m mcp_server.standards.sync` тепер випускає 25 правил у `external/standards_catalog.json`, включаючи machine-friendly підказки для майбутніх валідаторів.
- README.md та AGENTS.MD доповнені інструкціями щодо каталогу та порядку розширення схеми.
- `pbip_staging/pilot_pipeline.py` під час перевірок і авто-фіксів використовує `automation.*` з каталогу (pattern, membership, assign/transform), тож усі рекомендації йдуть напряму з `external/standards_catalog.json`.

### UI Prototypes
- Створено спільні утиліти `pbip_staging/ui_shared.py` для читання артефактів та повторного запуску pipeline.
- Додано Streamlit-панель `pbip_staging/streamlit_app.py` з візуалізацією порушень, авто-fix та TMDL-патчів.
- Додано Gradio-додаток `pbip_staging/gradio_app.py` з можливістю оновити список запусків і запустити pipeline напряму з UI.
- README, TODO, AGENTS оновлені інструкціями щодо нових UI та подальших кроків (auth, фільтри, завантаження PBIP).

### Архітектурне планування
- Оновлено TODO.md: додано секції "MCP + RAG Architecture", "MCP API & UI Gateway" та "MCP Admin Console" з деталізованими підзадачами.
- Зафіксовано roadmap для RAG service, ingestion-пайплайна знань та інтеграції оркестратора з векторними індексами.
- Розплановано розвиток UI (Streamlit/Gradio) та адмін-панелі з фокусом на RBAC, telemetry й повторне використання API Gateway.

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
