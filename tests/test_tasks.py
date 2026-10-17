"""Відкриті тести задач (приклади перевірок; повний набір є у викладача): 10 задач × 3 набори даних. Ідентифікатор тесту: T<задача>-S<набір>-<перевірка>.

Запуск повного набору: pytest. Одна задача: pytest -k T05. Один набір: pytest -k "T05-S2".
"""
import pytest
from conftest import load
from harness import run_case
from specs import SPECS

CASES = [(t, s, chk) for (t, s), spec in sorted(SPECS.items()) for chk in spec["checks"]]


@pytest.mark.parametrize("task,set_no,chk", CASES, ids=[f"T{t:02d}-S{s}-{c['id']}" for t, s, c in CASES])
def test_check(db, task, set_no, chk):
    run_case(db, load(task), task, set_no, SPECS[(task, set_no)], chk)
