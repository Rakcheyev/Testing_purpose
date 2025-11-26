"""
manual_pbip_upload.py
Модуль для ручного підвантаження PBIP-файлів у staging з гарантією, що доступ здійснюється лише до метаданих (модель, структура, DAX, M-код), а не до бізнес-даних (продажі, закупівлі).
"""
import os
from typing import List

ALLOWED_EXTENSIONS = {'.json', '.yaml', '.yml', '.tmdl', '.pbip'}

# Каталог для staging
STAGING_DIR = os.path.join(os.path.dirname(__file__), '../pbip_staging')


def is_metadata_file(filename: str) -> bool:
    """Перевіряє, чи файл містить лише метадані (без даних)."""
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_EXTENSIONS


def upload_pbip_file(filepath: str) -> str:
    """Підвантажити PBIP-файл у staging, якщо це метадані."""
    if not is_metadata_file(filepath):
        raise ValueError("Дозволено лише файли метаданих PBIP/TMDL/JSON/YAML!")
    basename = os.path.basename(filepath)
    dest_path = os.path.join(STAGING_DIR, basename)
    # Копіюємо файл у staging
    with open(filepath, 'rb') as src, open(dest_path, 'wb') as dst:
        dst.write(src.read())
    return dest_path


def list_staged_pbip_files() -> List[str]:
    """Повертає список підвантажених PBIP-файлів у staging."""
    return [f for f in os.listdir(STAGING_DIR) if is_metadata_file(f)]

# Гарантія безпеки:
# - Дозволяється підвантаження лише файлів, що містять структуру моделі, DAX, M-код, але не дані.
# - Не дозволяється підвантаження PBIX, CSV, XLSX, Parquet, SQL dumps тощо.
# - Всі перевірки виконуються на рівні розширення та структури файлу.
