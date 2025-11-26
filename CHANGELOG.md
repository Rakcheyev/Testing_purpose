# CHANGELOG

## 2025-11-26



## [Unreleased]

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
