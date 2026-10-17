"""Допоміжний завантажувач: підключає файл варіанта з теки variants/ (або з VARIANT_DIR) і дає з'єднання з БД."""
import importlib.util
import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent


def load(number):
    """Повертає модуль варіанта з номером number."""
    base = Path(os.environ.get("VARIANT_DIR", ROOT.parent / "variants"))
    for prefix in ("variant", "lab", "task"):
        path = base / f"{prefix}_{number:02d}.py"
        if path.exists():
            spec = importlib.util.spec_from_file_location(f"{prefix}_{number:02d}", path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
    raise FileNotFoundError(f"Не знайдено файл варіанта {number:02d} у {base}")


@pytest.fixture
def db():
    """З'єднання з PostgreSQL і окрема тимчасова схема на кожен тест."""
    import pgutil
    try:
        database = pgutil.Db()
    except Exception as error:  # noqa: BLE001
        pytest.fail(
            "Немає підключення до PostgreSQL (" + str(error).strip().splitlines()[0] + "). Запустіть сервер і перевірте "
            "змінні PGHOST, PGPORT, PGUSER, PGPASSWORD (див. README.md).", pytrace=False)
    yield database
    database.close()
