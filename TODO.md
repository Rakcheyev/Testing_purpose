# TODO MCP AI Integration Project

## External Standards Integration
- [x] Додати підмодулі Power_Query_guide та DAX_Templates
- [x] Зчитати та структурувати стандарти у external/standards_mcp.json
- [ ] Використовувати стандарти для автоматичної валідації та рев’ю
  - [ ] Додати скрипт для автоматичного оновлення external/standards_mcp.json при зміні підмодулів/стандартів (поки плейсхолдер, потім інтегрувати у CI/CD)
    <!-- Після впровадження CI/CD: інтегрувати update_standards.py у pipeline для автоматичного запуску при оновленні підмодулів або стандартів. Поки запускати вручну. -->


## 1. MS SQL Validation Layer
- [ ] Підключення до MS SQL через MCP (тільки метадані та статистики)
  <!-- Безпека: доступ лише до метаданих мінімізує ризики витоку даних, знижує attack surface. Вплив: підвищує якість аудиту, але не дозволяє перевірити реальні дані. Альтернатива: використання read-only service account, ізоляція через views. -->
  - [ ] Налаштувати MCP Data Connector для доступу до INFORMATION_SCHEMA, sys.tables, sys.indexes
    <!-- Безпека: доступ до системних таблиць не дає змоги змінювати дані, але важливо обмежити права лише на читання. Вплив: дозволяє повний аудит структури, індексів, статистик. Альтернатива: snapshot metadata dumps, periodic export через secure channel. -->
  - [ ] Вказати параметри підключення (тільки для метаданих)
    <!-- Безпека: не зберігати паролі у відкритому вигляді, використовувати secrets management. Вплив: підвищує якість контролю доступу. Альтернатива: інтеграція з Azure Key Vault, HashiCorp Vault. -->
- [ ] Витяг та аналіз метаданих
  <!-- Безпека: аналіз метаданих не впливає на продуктивність бази, але важливо не витягувати зайві дані. Вплив: підвищує якість моделювання, стандартизації. Альтернатива: використання metadata API, автоматичний аудит через CI/CD. -->
  - [ ] Витягнути схеми, таблиці, типи, індекси, зв’язки, статистики (row count, index usage, fragmentation, etc.)
  - [ ] Перевірити відповідність стандартам (структура, naming, presence of keys)
- [ ] Перевірка процедур та тригерів
  <!-- Безпека: важливо не витягувати код процедур, якщо це заборонено політикою. Вплив: підвищує якість контролю логіки, але може бути обмежено. Альтернатива: перевірка лише presence, audit logs. -->
  - [ ] Витягнути метадані процедур, тригерів, їх параметри
  - [ ] Перевірити відповідність стандартам (naming, presence, security)
- [ ] Автоматична перевірка змін у схемах
  <!-- Безпека: аудит змін у схемах дозволяє швидко реагувати на несанкціоновані зміни. Вплив: підвищує якість контролю версій, знижує ризики. Альтернатива: використання database triggers для логування змін, periodic schema diff. -->
  - [ ] Виявляти зміни у структурі (додавання/видалення колонок, індексів, процедур)
  - [ ] Тестувати вплив змін на статистики (row count, fragmentation)
- [x] Log and report results
  - [x] Реалізовано логування результатів
  - [x] Збереження звітів у CSV

## 2. PBIP Review & Deployment Layer
- [ ] Integrate Power BI via MCP
  - [ ] Налаштувати MCP Fabric Connector
  - [ ] Вказати параметри PBIP
- [ ] Analyze PBIP files
  - [ ] Автоматичний аналіз PBIP-файлів
- [ ] Validate against templates/standards
  - [ ] Перевірка відповідності темплейтам
  - [ ] Витягувати структуру PBIP (модель, зв'язки, міри, параметри)
  - [ ] Зберігати PBIP структуру у форматах:
    - [ ] TMDL (Tabular Model Definition Language)
    - [ ] JSON (data schema, measures, folders)
    - [ ] YAML (data schema, measures)
  - [ ] Порівнювати PBIP структуру з MCP стандартами (external/standards_mcp.json)
  - [ ] Генерувати звіт відповідності у pbip_artifacts/reports
  - [ ] Виявляти та фіксувати невідповідності (lint, warnings, errors)
- [ ] Automate deploy/redeploy
  - [ ] Реалізувати деплой/редеплой PBIP
- [ ] Versioning & audit
  - [ ] Впровадити аудит змін та rollback

## PBIP Artifacts & Review
- [x] Створити папку pbip_artifacts для мірорингу PBIP, M-коду, DAX
- [ ] Додати артефакти для рев'ю та тестування
- [ ] Протестувати модулі MCP рев'ю та стандартизації

## PBIP Staging Workspace
- [x] Створити папку pbip_staging для проміжного зберігання артефактів
- [ ] Додавати нові PBIP, М-код, DAX у staging
  - [ ] Додати можливість вручну підвантажувати PBIP для подальшого аналізу та обробки
- [ ] Запускати автоматичні перевірки MCP/стандартів
- [ ] Переносити артефакти у pbip_artifacts лише після успішних перевірок

## 3. Monitoring Layer
- [ ] Implement MCP Monitoring
  - [ ] Реєстрація сервісів у MCP Monitoring
- [ ] Set up alerts/logs
  - [ ] Налаштувати алерти та логування
- [ ] Visualize status
  - [ ] Створити Dashboard для статусу
- [ ] Collect metrics
  - [ ] Автоматичний збір метрик

## 4. Fabric & External Data Layer
- [ ] Integrate external sources via MCP
  - [ ] Реєстрація зовнішніх джерел
- [ ] Parse/validate Excel, CSV, API
  - [x] Автоматичний парсинг та валідація (каркас створено: fabric_external_data/parse_validate.py)
  - [ ] Витягувати структуру даних у форматах:
    - [ ] TMDL (Tabular Model Definition Language)
    - [ ] JSON (data schema, sample, validation report)
    - [ ] YAML (data schema, sample)
  - [ ] Зберігати результати парсингу та валідації у pbip_artifacts/reports
  - [ ] Порівнювати структуру з MCP стандартами
- [ ] Describe models in MCP
  - [ ] Опис моделей даних
- [ ] Implement ETL
  - [ ] Впровадження ETL-процесів
- [ ] Log/audit imports
  - [ ] Логування та аудит імпортованих даних
