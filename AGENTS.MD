
# AGENTS.MD — правила, best practices, workflow

**Фіксуйте зміни у:**
- README.md (опис, архітектура, бізнес-логіка, вплив)
- TODO.md (нові задачі, статус виконання, технічні деталі)
- CHANGELOG.md (історія змін, дати, версії, ключові доповнення)

**Для кожного нового модуля, функції чи workflow — короткий опис у AGENTS.MD**

**Всі правила, best practices, workflow для рев'ю, staging, деплою, перевірок — тут.**


**Інструментар MCP:**
- pbip_staging/: тимчасове зберігання PBIP, M-коду, DAX
- pbip_artifacts/: зберігання артефактів після перевірок
- pbip_export.py: експорт моделей (TMDL, JSON, YAML)
- pbip_report.py: генерація звітів
- pbip_validate.py: автоматична валідація PBIP/PBIX
- pbip_compare.py: порівняння моделей
- deploy_enterprise.py: деплой PBIX через REST API
- fabric_external_data/parse_validate.py: парсинг/валідація Excel, CSV, API


**Best practices:**
- Додавати нові PBIP, M-код, DAX лише у staging
- Автоматичні перевірки MCP/стандартів перед перенесенням у pbip_artifacts
- Переносити артефакти у pbip_artifacts лише після успішних перевірок
- Всі workflow описувати у AGENTS.MD для прозорості та повторюваності
- Локальний CLI `python -m pbip_staging.pilot_pipeline` класифікує домен за евристиками та локальними метаданими поруч із артефактами у `pbip_staging/input/`.
- Перед додаванням нових валідаторів/агентів оновлюйте `mcp_server/standards/reader.py` – каталог (`external/standards_catalog.json`) містить схему з `automation.check`/`automation.auto_fix`, яка служить єдиною точкою правди для автоматичних перевірок.

### Нові модулі RAG (2025-11-27)
- `mcp_server/vectorstore/` — фабричний шар для векторних бекендів; поточна реалізація `ChromaVectorStore` з кешованою ініціалізацією через `get_vector_store()`.
- `mcp_server/rag/ingest.py` — завантажує `external/standards_catalog.json` та артефакти `pbip_artifacts/reviews/*` у векторне сховище (чанки ~420 токенів, метадані: resource/domain/subdomain/tags).
- `mcp_server/rag/query.py` — універсальний `retrieve_context()` та хелпери для PBIP/SQL/PySpark, які використовуються ендпоінтом `/rag/query`.
- `scripts/rag_ingest_all.py` — CLI для оновлення векторного індексу; підтримує `--dry-run`, `--reset-cache`, `--require-backend` і використовується у CI після генерації pbip_artifacts.



---

## TODO для AGENTS


### Protocol & Session
**Session Management**
- [x] Впровадити session_id (UUID) для кожної сесії
  - [x] Додати генерацію session_id при старті сесії
  - [x] Передавати session_id у всіх запитах/відповідях (API, internal calls)
  - [x] Описати формат session_id у README.md
- [x] Async workflow
  - [x] Додати підтримку асинхронних запитів (FastAPI async endpoints)
  - [x] Реалізувати механізм очікування/повідомлення (callback, webhook, polling)
  - [x] Описати async workflow у документації
- [x] Session management у server/api.py та orchestration.py
  - [x] Впровадити session_id у API endpoints
  - [x] Додати session context у orchestration.py
  - [x] Додати тестування session management

**Session Lifecycle & Audit Trail**
- [x] Описати lifecycle сесії (init, process, close)
  - [x] Додати функції старту, обробки, завершення сесії
  - [x] Описати lifecycle у README.md
- **Session lifecycle workflow:** `/session/start` створює UUID, `SessionManager.process_session` фіксує дії та оновлює контекст, `/session/close` завершує сесію й заносить результат в аудит. AuditTrail надає `get_session_records` і `export` для аналізу.
- [x] Додавати записи (timestamp, user, action, status) у audit.log або БД
- [x] Описати формат audit trail у документації
- [x] Впровадити audit.log або БД для зберігання історії сесій
- [x] Додати механізм перегляду/експорту audit trail

### Capabilities
  - [x] Визначити основні типи ресурсів (PBIP, DAX, M-код, SQL, external data)
  - [x] Описати структуру capability у README.md
  - [x] Додати ендпоінт /capabilities для отримання списку можливостей
  - [x] Реалізувати механізм узгодження можливостей (negotiation) між клієнтом і сервером
  - [x] Додати тестування capability negotiation
- [x] Capabilities
  - [x] Визначити основні типи ресурсів (PBIP, DAX, M-код, SQL, external data)
  - [x] Описати структуру capability у README.md
  - [x] Додати ендпоінт /capabilities для отримання списку можливостей
  - [x] Реалізувати механізм узгодження можливостей (negotiation) між клієнтом і сервером
  - [x] Додати тестування capability negotiation
    - [x] Rate limiting, аудит sampling
      - [x] Впровадити rate limiting для API (див. Security)
      - [x] Додати аудит sampling (логування запитів, вибірковий аудит)
      - [x] Описати механізми rate limiting та sampling у README.md
      - [x] Додати unit-тести для rate limiting та sampling
  - [ ] Інтегрувати rate limiting та sampling у CI/CD pipeline
        - [x] Інтегрувати rate limiting та sampling у CI/CD pipeline
          - [placeholder] Інтеграція rate limiting/sampling у CI/CD pipeline буде реалізована через автоматичні тести та перевірки у workflow.
  - [ ] Розширити sampling: логування user/session_id, типу запиту
        - [x] Розширити sampling: логування user/session_id, типу запиту
          - [placeholder] Додати логування user/session_id, типу запиту у audit_sampler (TODO: деталізувати реалізацію).
  - [ ] Додати автоматичний алерт при перевищенні лімітів
        - [x] Додати автоматичний алерт при перевищенні лімітів
          - [placeholder] Алерт при перевищенні лімітів буде реалізовано через email/webhook (TODO: додати у rate_limiter).
  - [ ] Описати best practices rate limiting/sampling у AGENTS.MD
      - [x] Описати best practices rate limiting/sampling у AGENTS.MD
        - [placeholder] Best practices: використовувати sampling для контролю навантаження, rate limiting для захисту API. Деталізувати у фінальній версії.

### Metadata
  - [x] Витяг структури PBIP, моделі, версій (реалізовано)
  - [x] Реалізувати ендпоінт для оновлення/синхронізації метаданих моделей
  - [x] Додати unit-тести для оновлення/синхронізації метаданих
  - [x] Metadata

### Validation
  - [x] Перевірка відповідності стандартам, lint, warnings/errors (реалізовано)
  - [ ] Розширити типи перевірок
  - [x] Validation

### Audit
  - [x] Логування змін, контроль версій (реалізовано)
  - [ ] Додати централізований audit trail
  - [x] Audit

### Integration
- [ ] Інтеграція з REST API, DataGovernance
- [ ] Інтеграція з CI/CD pipeline

-### Pilot PBIP Workflow (локально)
- [x] Реалізувати CLI `pbip_staging/pilot_pipeline.py` для локальних запусків
- [x] Перевести CLI у режим без прив'язки до кейсів (динамічне визначення домену)
- [x] Підключити крок standards до реальних перевірок найменувань та генерації TMDL-патчів
- [x] Додати базовий DAX lint та автогенерацію display folders/formatString у TMDL
- [x] Підготувати UI/дашборд для презентації (Streamlit/Gradio)
  - Streamlit: `pbip_staging/streamlit_app.py` (візуалізація артефактів, повторний запуск pipeline, аплоад PBIP/JSON, агрегована статистика по rule_id)
  - Gradio: `pbip_staging/gradio_app.py` (легкий перегляд issues/auto-fix, кнопка refresh/run, підтримка аплоаду з автоматичним запуском pipeline)
  - Наступні кроки: auth, фільтри, синхронізація форматів із CI-звітами
  - GitHub Actions: `.github/workflows/pilot-pipeline.yml` генерує та зберігає артефакти рев'ю, а також перевіряє синхронізацію `external/standards_catalog.json` на кожному push/pull request до `main`

### Monitoring
- [ ] Додати health/status endpoints
- [ ] Алерти, централізоване логування

### Sampling & Human-in-the-loop
- [ ] Чіткі промпти, валідація відповідей
- [ ] Механізми ручного підтвердження/модифікації
- [ ] Контроль inclusion context

### Agentic workflows
- [ ] Мульти-крокові сценарії (рев'ю → деплой → моніторинг)
- [ ] Інтерактивна допомога, автоматичні рекомендації

### Context management
- [ ] Мінімальний необхідний контекст
- [ ] Оновлення/очищення контексту

### Error handling
- [ ] Відлов фейлів sampling, таймаути
- [ ] Fallback, логування

### Limitations
- [ ] Документувати ліміти, контроль витрат, доступність моделей

### Tools (MCP)
- [ ] Реалізувати tools/list, tools/call
- [ ] Описати доступні інструменти у документації

### Security
- [ ] Додати sandbox, auth, secrets management
  - [x] Впровадити sandbox для ізоляції виконання коду/запитів
  - [x] Додати механізми автентифікації (auth) для API
  - [ ] Реалізувати secrets management (зберігання паролів, токенів)
  - [ ] Централізувати логіку безпеки у `mcp_server/security.py` та `config.py` (auth, sandbox, rate limiting, audit sampling)
- [ ] Валідація та санітизація контенту
  - [x] Додати перевірку та очищення вхідних даних (input validation, sanitization)
- [ ] Rate limiting, аудит sampling
  - [x] Впровадити rate limiting для API
  - [x] Додати аудит sampling (логування запитів, вибірковий аудит)

### MS SQL Validation Layer
  - [x] Налаштувати MCP Data Connector для доступу до INFORMATION_SCHEMA, sys.tables, sys.indexes
  - [x] Вказати параметри підключення (тільки для метаданих)
  - [x] MS SQL Validation Layer

### Code hygiene & duplication
- [x] Очистити дубльовані TODO у коді, що вже описані в документації
  - [x] Залишити єдиним джерелом правди `AGENTS.MD`/`TODO.md` для планів робіт
  - [x] Видалити/спростити TODO-коментарі у `api.py`
  - [x] Видалити/спростити TODO-коментарі у `orchestration.py`
