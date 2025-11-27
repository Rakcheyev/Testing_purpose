# PBIP Staging Workspace

Ця папка призначена для проміжного зберігання PBIP, M-коду, DAX-артефактів перед основним рев'ю та деплоєм.

## Призначення
- Експортуйте нові артефакти з Fabric/Power BI у цю папку
- Запускайте автоматичні перевірки (стандарти, MCP validation, lint)
- Всі зміни — через окремі гілки або pull request
- Якщо всі перевірки пройдені — переносіть артефакти у pbip_artifacts для подальшого рев'ю/деплою

## Структура
- `pbip/` — PBIP-файли проектів
- `m_query/` — M-код (Power Query)
- `dax/` — DAX-артефакти (міри, шаблони)
- `reports/` — звіти перевірок
- `input/` — за замовчуванням сканується локальним CLI для PBIP інспекції

## Робочий процес
1. Додавайте артефакти у pbip_staging
2. Запускайте MCP-модулі для перевірки
3. Якщо всі статуси "green" — переносіть у pbip_artifacts
4. Якщо є помилки — виправляйте у staging, повторюйте перевірки

### Локальний workflow без попередньо визначених кейсів
- Покладіть PBIP-експорти у `pbip_staging/input/` або передайте власні шляхи файлів/папок.
- Запустіть `python -m pbip_staging.pilot_pipeline` (опціонально `--dry-run` для пропуску генерації артефактів).
- Скрипт автоматично класифікує звіти за доменом (sales, finance, supply_chain, marketing, hr, multi-domain), використовуючи локальні метадані та евристики без попередньо збережених профілів.
- Крок `standards` перевіряє snake_case для мір, PascalCase для колонок, наявність/узгодженість display folders, форматування мір, додає попередження про антипатерни DAX (DIVIDE, COUNTROWS, VAR, ALL(<table>), LOOKUPVALUE) і генерує TMDL-рекомендації для перейменувань, display folders та formatString (`recommended_renames.tmdl`).
- CLI також підтримує PBIP-бандли (`*.pbip` директорії), автоматично читаючи `DataModelSchema.json`.
- Результати й логи перевірок зберігаються у `pbip_artifacts/reviews/<domain>__<назва>_<hash>/` разом із `standards.json`, `summary.json`, `audit.json`, `session_history.json`.

### Streamlit/Gradio dashboards
- `streamlit run pbip_staging/streamlit_app.py` — дозволяє завантажувати PBIP/JSON файли, автоматично запускати pipeline, переглядати детальні таблиці порушень та агреговану статистику по rule_id.
- `python -m pbip_staging.gradio_app` — легкий веб-інтерфейс із підтримкою аплоаду артефактів, швидкого перезапуску pipeline та перегляду TMDL-патчів.
- Обидва UI використовують `pbip_staging/ui_shared.py` для зберігання аплоадів у `pbip_staging/input/` і повторного використання логіки запуску CLI.
