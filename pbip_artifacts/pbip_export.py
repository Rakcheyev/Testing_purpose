import json
import yaml
from typing import Dict, Any

# === Інструкції по деплою PBIP/PBIX у Power BI Service ===
#
# 1. Ручний деплой (поточна реалізація)
#    - Відкрий PBIP у Power BI Desktop
#    - Експортуй PBIP у PBIX (File → Export → PBIX)
#    - Опублікуй PBIX у Power BI Service вручну (кнопка Publish)
#    - Вибери workspace для публікації
#    - Контроль версій та рев'ю — через git та pull request
#
# 2. Enterprise деплой (рекомендовано для автоматизації)
#    - Зберігай PBIP/PBIX у git
#    - Використовуй CI/CD pipeline (Azure DevOps, GitHub Actions)
#    - Автоматизуй деплой через Power BI REST API або Deployment Pipelines
#    - MCP може керувати рев'ю, lint, стандартизацією, деплоєм
#    - Всі зміни проходять через pull request та CI/CD
#
# === Структура проекту для деплою ===
# pbip_artifacts/
#   ├── pbip_export.py         # Експорт моделей у TMDL, JSON, YAML
#   ├── pbip_report.py         # Генерація звітів відповідності
#   ├── pbip_validate.py       # Валідація PBIP/PBIX
#   ├── pbip_compare.py        # Порівняння моделей
#   ├── pbip_extract.py        # (Майбутнє) Автоматичний екстракт PBIX з PBIP
#   └── deploy_enterprise.py   # (Майбутнє) CI/CD деплой через REST API
#
# TODO: Для enterprise-автоматизації імпортуй та викликай deploy_enterprise.deploy_pbix_to_service
# from .deploy_enterprise import deploy_pbix_to_service
#
# === Маркер поточної реалізації ===
# [Ручний деплой: активний]

def save_tmdl(structure: Dict[str, Any], out_path: str):
    """Save structure in TMDL format. Placeholder."""
    # TODO: Реалізувати експорт у TMDL
    # Поточна реалізація: ручний експорт через Power BI Desktop
    with open(out_path, "w") as f:
        f.write("# TMDL export placeholder\n")
        f.write(str(structure))

def save_json(structure: Dict[str, Any], out_path: str):
    with open(out_path, "w") as f:
        json.dump(structure, f, indent=2)

def save_yaml(structure: Dict[str, Any], out_path: str):
    with open(out_path, "w") as f:
        yaml.dump(structure, f)
