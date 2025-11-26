# AGENTS.MD: Правила та інструментар MCP AI Integration Project

## Основні правила внесення змін
- Після кожної зміни у коді, структурі чи документації обов'язково фіксувати зміни у:
  - README.md (опис, архітектура, бізнес-логіка, вплив)
  - TODO.md (нові задачі, статус виконання, технічні деталі)
  - CHANGELOG.md (історія змін, дати, версії, ключові доповнення)
- Для кожного нового модуля, функції чи workflow — додавати короткий опис у AGENTS.MD
- Всі правила, best practices, workflow для рев'ю, staging, деплою, перевірок — зберігати у цьому файлі.

## Інструментар для рев'ю, staging, перевірок
- pbip_staging/: тимчасове зберігання PBIP, M-коду, DAX для рев'ю та тестування
- pbip_artifacts/: зберігання артефактів після успішних перевірок
- pbip_export.py: експорт моделей у TMDL, JSON, YAML
- pbip_report.py: генерація звітів відповідності
- pbip_validate.py: автоматична валідація PBIP/PBIX
- pbip_compare.py: порівняння моделей
- deploy_enterprise.py: автоматизація деплою PBIX через REST API (enterprise)
- fabric_external_data/parse_validate.py: парсинг та валідація Excel, CSV, API

## Best practices
- Додавати нові PBIP, M-код, DAX лише у staging
- Запускати автоматичні перевірки MCP/стандартів перед перенесенням у pbip_artifacts
- Переносити артефакти у pbip_artifacts лише після успішних перевірок
- Всі workflow описувати у AGENTS.MD для прозорості та повторюваності процесу


## TODO для AGENTS


### Protocol & Session
#### Session Management
- [x] Впровадити session_id (UUID) для кожної сесії
  - [x] Додати генерацію session_id при старті сесії
  - [x] Передавати session_id у всіх запитах/відповідях (API, internal calls)
  - [x] Описати формат session_id у README.md
- [ ] Async workflow
  - [x] Додати підтримку асинхронних запитів (FastAPI async endpoints)
  - [x] Реалізувати механізм очікування/повідомлення (callback, webhook, polling)
  - [x] Описати async workflow у документації
- [ ] Session management у server/api.py та orchestration.py
  - [x] Впровадити session_id у API endpoints
  - [x] Додати session context у orchestration.py
  - [x] Додати тестування session management

#### Session Lifecycle & Audit Trail
- [ ] Описати lifecycle сесії (init, process, close)
  - [ ] Додати функції старту, обробки, завершення сесії
  - [ ] Описати lifecycle у README.md
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
- [ ] Rate limiting, аудит sampling

### Metadata
- [x] Витяг структури PBIP, моделі, версій (реалізовано)
- [x] Реалізувати ендпоінт для оновлення/синхронізації метаданих моделей
  - [x] Додати unit-тести для оновлення/синхронізації метаданих

### Validation
- [x] Перевірка відповідності стандартам, lint, warnings/errors (реалізовано)
- [ ] Розширити типи перевірок

### Audit
- [x] Логування змін, контроль версій (реалізовано)
- [ ] Додати централізований audit trail

### Integration
- [ ] Інтеграція з REST API, DataGovernance
- [ ] Інтеграція з CI/CD pipeline

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
- [ ] Валідація та санітизація контенту
  - [x] Додати перевірку та очищення вхідних даних (input validation, sanitization)
- [ ] Rate limiting, аудит sampling
  - [x] Впровадити rate limiting для API
  - [x] Додати аудит sampling (логування запитів, вибірковий аудит)

### MS SQL Validation Layer
- [x] Налаштувати MCP Data Connector для доступу до INFORMATION_SCHEMA, sys.tables, sys.indexes
- [x] Вказати параметри підключення (тільки для метаданих)
