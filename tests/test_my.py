from conftest import load
from pgutil import Db
from schemas import SCHEMAS


def test_my_case():
    db = Db()
    try:
        # Завантажуємо схему й початкові дані Набору 2 (Магазин)
        db.run(SCHEMAS[2])

        # Додаємо тестову покупку для створення нового запису після 2024-02-01
        db.run(
            """
            INSERT INTO purchase (customer_id, product_id, quantity, ordered_on, shipped_on)
            VALUES (1, 1, 10, '2024-03-01', '2024-03-02');
            """
        )

        # Виконуємо розв'язок задачі 8 (variants/variant_08.py)
        rows = db.rows(load(8).query())

        # Перевіряємо, що результати повертаються та структура відповідна
        assert len(rows) > 0
        assert len(rows[0]) == 5  # У результаті має бути 5 стовпців (grp, title, qty, pct_group, pct_total)
    finally:
        db.close()