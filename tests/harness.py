"""Виконання перевірок зі специфікацій (specs.py): результат запиту студента порівнюється з очікуваним."""
import inspect
import re
from datetime import date, datetime
from decimal import Decimal

import pytest

import pgutil
from schemas import SCHEMAS


def fail(message):
    pytest.fail(message, pytrace=False)


def norm(value):
    """Єдиний текстовий вигляд значення: числа порівнюються за величиною, а не за кількістю знаків після коми."""
    if value is None:
        return None
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float, Decimal)):
        text = format(Decimal(str(value)).normalize(), "f")
        return "0" if text in ("-0", "") else text
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return str(value)


def norm_rows(rows):
    return [tuple(norm(v) for v in row) for row in rows]


def call(mod, task, set_no):
    """Викликає query() варіанта. Еталон приймає номер набору; студентська функція без параметрів
    працює для набору, що випливає з константи VARIANT."""
    fn = getattr(mod, "query", None)
    if fn is None:
        fail("У файлі варіанта немає функції query()")
    if inspect.signature(fn).parameters:
        return fn(set_no)
    variant = getattr(mod, "VARIANT", 0)
    if not variant:
        fail("Змінну VARIANT не задано: впишіть номер свого варіанта (1-30) на початку файла")
    if (variant - 1) // 3 + 1 != task:
        fail(f"VARIANT = {variant} не відповідає задачі {task}: файл variant_{task:02d}.py призначений "
             f"для варіантів {3 * task - 2}-{3 * task}")
    if (variant - 1) % 3 + 1 != set_no:
        pytest.skip("перевірка іншого набору даних")
    try:
        return fn()
    except NotImplementedError:
        fail("Функція query() ще не реалізована (NotImplementedError)")


def clean_query(value):
    if not isinstance(value, str) or not value.strip():
        fail("query() має повертати непорожній рядок з одним запитом SELECT")
    text = value.strip()
    while text.endswith(";"):
        text = text[:-1].rstrip()
    body = re.sub(r"'(?:[^']|'')*'", "''", text)
    if ";" in body:
        fail("query() має повертати рівно один запит: прибирайте зайві «;» і додаткові команди")
    if not re.match(r"(?is)^\s*(select|with|values|table)\b", text):
        fail("Запит має починатися зі SELECT (або WITH); змінювати дані й схему не можна")
    return text


def run_query(db, sql):
    """Виконує запит студента в режимі «лише читання» з обмеженням часу; повертає кількість стовпців і рядки."""
    db.conn.execute("SET default_transaction_read_only = on")
    db.conn.execute("SET statement_timeout = 10000")
    try:
        cur = db.conn.execute(sql)
        rows = cur.fetchall()
        return len(cur.description), rows
    except pgutil.psycopg.errors.QueryCanceled:
        fail("Запит виконується понад 10 секунд: схоже на декартів добуток (забута умова з'єднання?)")
    except pgutil.psycopg.Error as error:
        fail("Помилка SQL " + f"{error.sqlstate}: {str(error).strip().splitlines()[0]}")
    finally:
        db.conn.execute("SET default_transaction_read_only = off")


def run_case(db, mod, task, set_no, spec, chk):
    db.run(SCHEMAS[set_no])
    for sql in chk["setup"]:
        db.run(sql)
    sql = clean_query(call(mod, task, set_no))
    ncols, rows = run_query(db, sql)
    want = norm_rows(chk["expect"])
    if ncols != spec["columns"]:
        fail(f"Перевірка «{chk['id']}»: очікувалось стовпців {spec['columns']}, запит повернув {ncols}. "
             f"Потрібні стовпці по порядку: {spec['column_list']}")
    got = norm_rows(rows)
    if chk["ordered"]:
        same = got == want
    else:
        same = sorted(got, key=repr) == sorted(want, key=repr)
    if same:
        return
    lines = [f"Перевірка «{chk['id']}»: очікувалось рядків {len(want)}, отримано {len(got)}."]
    if chk["ordered"] and sorted(got, key=repr) == sorted(want, key=repr):
        lines.append("Набір рядків правильний, але порядок інший: перевірте ORDER BY.")
        for pos, (a, b) in enumerate(zip(got, want), 1):
            if a != b:
                lines.append(f"Перший розбіг на рядку {pos}: отримано {a}, очікувалось {b}.")
                break
    else:
        missing = [r for r in want if r not in got]
        extra = [r for r in got if r not in want]
        if missing:
            lines.append("Бракує: " + "; ".join(map(str, missing[:3])) + (" ..." if len(missing) > 3 else ""))
        if extra:
            lines.append("Зайві або інші: " + "; ".join(map(str, extra[:3])) + (" ..." if len(extra) > 3 else ""))
        if not missing and not extra:
            lines.append("Є повтори рядків: перевірте розмноження після JOIN або потрібність DISTINCT.")
    if chk["setup"]:
        lines.append("Цей тест додатково змінює дані: " + chk["note"])
    fail("\n".join(lines))
