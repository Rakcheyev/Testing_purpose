import os
import shutil
from pbip_artifacts.pbip_validate import validate_pbip

STAGING_DIR = 'pbip_staging'
ARTIFACTS_DIR = 'pbip_artifacts'


def manual_pbip_review(filename):
    """
    Обробка вручну підвантаженого PBIP-файлу:
    - Копіює файл у staging
    - Запускає рев'ю через validate_pbip
    - Якщо рев'ю успішне, переносить у pbip_artifacts
    """
    if not os.path.exists(STAGING_DIR):
        os.makedirs(STAGING_DIR)
    if not os.path.exists(ARTIFACTS_DIR):
        os.makedirs(ARTIFACTS_DIR)

    basename = os.path.basename(filename)
    staging_path = os.path.join(STAGING_DIR, basename)
    shutil.copy2(filename, staging_path)
    print(f"Файл {basename} додано у staging.")

    # Запуск рев'ю
    review_result = validate_pbip(staging_path)
    print(f"Результат рев'ю: {review_result}")

    if review_result.get('status') == 'success':
        final_path = os.path.join(ARTIFACTS_DIR, basename)
        shutil.move(staging_path, final_path)
        print(f"Файл {basename} перенесено у pbip_artifacts.")
    else:
        print(f"Файл {basename} залишено у staging для доопрацювання.")

if __name__ == "__main__":
    # Приклад використання: manual_pbip_review('path/to/manual.pbip')
    pass
