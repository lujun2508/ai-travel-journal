# -*- coding: utf-8 -*-
"""一起旅行 SKILL · tests/test_aa_splitter.py
阶段 8 AA 智能分账 smoke test
"""
import sys
from pathlib import Path

# 让 tests/ 能 import 同级 skills/
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from skills._aa_splitter import split_bill, accumulate_daily, DEFAULT_PEOPLE  # noqa: E402


def test_split_bill_A_整桌_1_家():
    """fee_type='A' 整桌 1 家出, A家付全额, B家 0"""
    r = split_bill(100, DEFAULT_PEOPLE, fee_type='A')
    assert r['split_type'] == '整桌_1_家'
    assert r['household_breakdown'][0]['amount'] == 100.0
    assert r['household_breakdown'][1]['amount'] == 0.0
    assert abs(r['per_person'] - 100 / 7) < 0.01
    print('  [PASS] test_split_bill_A_整桌_1_家')


def test_split_bill_AA_1_2():
    """fee_type='AA' 两家各半, A家 = B家 = total / 2"""
    r = split_bill(200, DEFAULT_PEOPLE, fee_type='AA')
    assert r['split_type'] == 'AA_1_2'
    assert r['household_breakdown'][0]['amount'] == 100.0
    assert r['household_breakdown'][1]['amount'] == 100.0
    print('  [PASS] test_split_bill_AA_1_2')


def test_split_bill_AA_KIDS_FREE():
    """fee_type='AA_KIDS_FREE' AA + 小孩免票, A家全额 + B家 0 (示意)"""
    r = split_bill(300, DEFAULT_PEOPLE, fee_type='AA_KIDS_FREE')
    assert r['split_type'] == 'AA_KIDS_FREE'
    print('  [PASS] test_split_bill_AA_KIDS_FREE')


def test_split_bill_total_zero():
    """边界: total=0 不崩"""
    r = split_bill(0, DEFAULT_PEOPLE, fee_type='AA')
    assert r['household_breakdown'][0]['amount'] == 0.0
    print('  [PASS] test_split_bill_total_zero')


def test_accumulate_daily_empty():
    """空输入返回空结构"""
    r = accumulate_daily({})
    assert r['household_A'] == 0.0
    assert r['household_B'] == 0.0
    assert r['total'] == 0.0
    print('  [PASS] test_accumulate_daily_empty')


if __name__ == '__main__':
    print('test_aa_splitter.py:')
    test_split_bill_A_整桌_1_家()
    test_split_bill_AA_1_2()
    test_split_bill_AA_KIDS_FREE()
    test_split_bill_total_zero()
    test_accumulate_daily_empty()
    print('  [ALL PASS] 5 / 5')
