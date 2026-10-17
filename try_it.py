"""Ручний прогін вашого запиту без тестів.

Використання:  python try_it.py <номер_задачі>
Скрипт створює тимчасову схему, завантажує схему й дані вашого набору (за VARIANT у файлі variants/variant_NN.py),
виконує запит із функції query() і друкує назви стовпців та рядки результату. Тимчасова схема видаляється наприкінці.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tests"))

import pgutil  # noqa: E402
from conftest import load  # noqa: E402
from schemas import SCHEMAS  # noqa: E402


def main():
    if len(sys.argv) < 2 or not sys.argv[1].isdigit():
        print(__doc__)
        return 1
    task = int(sys.argv[1])
    mod = load(task)
    variant = getattr(mod, "VARIANT", 0)
    if not variant or (variant - 1) // 3 + 1 != task:
        print(f"Вкажіть у variant_{task:02d}.py змінну VARIANT зі значенням {3 * task - 2}-{3 * task}.")
        return 1
    set_no = (variant - 1) % 3 + 1
    db = pgutil.Db()
    try:
        db.run(SCHEMAS[set_no])
        sql = mod.query()
        cur = db.conn.execute(sql)
        names = [d.name for d in cur.description]
        rows = cur.fetchall()
        print(" | ".join(names))
        print("-" * 40)
        for row in rows:
            print(" | ".join("NULL" if v is None else str(v) for v in row))
        print(f"--- рядків: {len(rows)}")
    except pgutil.psycopg.Error as error:
        print("Помилка SQL:", error)
        return 1
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
