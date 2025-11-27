# Review Artifacts

Артефакти, сформовані локальним CLI `python -m pbip_staging.pilot_pipeline`, зберігаються у цій директорії. Для кожного обробленого PBIP створюється підпапка формату `<domain>__<назва>_<hash>/` із наступними файлами:

- `summary.json` — короткий підсумок стану перевірки та виконаних кроків pipeline.
- `audit.json` — вибірковий аудит дій у сесії (`AuditTrail`).
- `session_history.json` — хронологія викликів `SessionManager`.
- `standards.json` — деталі виявлених порушень і рекомендацій (display folders, форматування, DAX антипатерни тощо).
- `<source>_report.json` — stub-звіт (пропускається у режимі `--dry-run`).
- `recommended_renames.tmdl` — TMDL-сумісні рекомендації перейменувань, display folders і formatString (якщо знайдено порушення стандартів).

Каталог автоматично створюється під час запуску скрипта, тому додаткові кроки від користувача не потрібні.
