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
- Описати workflow для CI/CD деплою
- Додати приклади інтеграції з MCP, REST API, DataGovernance
