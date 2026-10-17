"""Задача 8. Частка від підсумку: у групі й у цілому.

Опис і умови: student.md, розділ «Опис задач», задача 8; картка вашого варіанта.
Відкриті тести: pytest -k "T08"
"""

# Впишіть номер свого варіанта (22-24).
VARIANT = 23

def query():
    return """
    SELECT 
        COALESCE(c.name, '(без категорії)') AS grp,
        p.title,
        sum(pr.quantity) AS qty,
        round(100.0 * sum(pr.quantity) / sum(sum(pr.quantity)) OVER (PARTITION BY p.category_id), 1) AS pct_group,
        round(100.0 * sum(pr.quantity) / sum(sum(pr.quantity)) OVER (), 1) AS pct_total
    FROM purchase pr
    JOIN product p ON p.id = pr.product_id
    LEFT JOIN category c ON c.id = p.category_id
    WHERE pr.ordered_on >= '2024-02-01'
    GROUP BY p.id, p.title, c.name, p.category_id
    ORDER BY pct_total DESC, p.id;
    """