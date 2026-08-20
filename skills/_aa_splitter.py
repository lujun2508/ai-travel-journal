# -*- coding: utf-8 -*-
"""一起旅行 SKILL · 阶段 8 实施
多人 AA 智能分账 (按 households + 默认规则)

借鉴: SKILL.md v3.7 阶段 8

输入: journal.json + 人数配置
输出: data/分账.json + 累计看板

用法:
  python skills/_aa_splitter.py  # 全量处理 journal.json
"""
import sys, json
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

JOURNAL = Path('data/journal.json')
OUTPUT = Path('data/分账.json')

DEFAULT_PEOPLE = {'adults': 3, 'kids': 4, 'total': 7, 'households': 2}


def split_bill(total, people=DEFAULT_PEOPLE, fee_type='A'):
    """单笔费用分账

    fee_type:
      'A'  = 整桌 1 家出 (默认一家人)
      'AA' = AA 1/2 (两家各半)
      'AA_KIDS_FREE' = AA + 小孩免票

    people = {'adults': 3, 'kids': 4, 'total': 7, 'households': 2}
    """
    households = people.get('households', 2)
    total = float(total or 0)
    if fee_type == 'A':
        return {
            'split_type': '整桌_1_家',
            'household_breakdown': [
                {'party': 'A家', 'amount': total},
                {'party': 'B家', 'amount': 0.0},
            ],
            'per_person': total / max(people['total'], 1),
        }
    elif fee_type == 'AA':
        per_household = total / max(households, 1)
        return {
            'split_type': 'AA_1_2',
            'household_breakdown': [
                {'party': 'A家', 'amount': per_household},
                {'party': 'B家', 'amount': per_household},
            ],
            'per_person': total / max(people['total'], 1),
        }
    elif fee_type == 'AA_KIDS_FREE':
        adults = max(people['adults'], 1)
        return {
            'split_type': 'AA_KIDS_FREE',
            'household_breakdown': [
                {'party': 'A家', 'amount': total},
                {'party': 'B家', 'amount': 0.0},
            ],
            'per_person': total / adults,
        }
    # 未知类型: 默认整桌
    return {
        'split_type': f'未知_{fee_type}',
        'household_breakdown': [
            {'party': 'A家', 'amount': total},
            {'party': 'B家', 'amount': 0.0},
        ],
        'per_person': total / max(people['total'], 1),
    }


def accumulate_daily(journal, people=DEFAULT_PEOPLE):
    """累积每日分账 → A家 / B家 各多少"""
    by_day = {}
    household_a = 0
    household_b = 0

    for day in journal.get('days', []):
        day_key = day['key']
        day_a = 0
        day_b = 0
        for fee in day.get('expenses', []):
            amt = float(fee.get('amount', 0))
            fee_type = fee.get('type', 'A')
            result = split_bill(amt, people, fee_type)
            breakdown = result['household_breakdown']
            if len(breakdown) >= 1:
                day_a += breakdown[0]['amount']
            if len(breakdown) >= 2:
                day_b += breakdown[1]['amount']
        by_day[day_key] = {
            'date': day.get('date', ''),
            'household_A': roundround(day_a),
            'household_B': roundround(day_b),
            'total': roundround(day_a + day_b),
        }
        household_a += day_a
        household_b += day_b

    return {
        'by_day': by_day,
        'household_A': roundround(household_a),
        'household_B': roundround(household_b),
        'total': roundround(household_a + household_b),
        'people': people,
    }


def roundround(x):
    """2 位小数四舍五入"""
    return round(x, 2)


if __name__ == '__main__':
    print('==== AA 分账工具 ====')
    if not JOURNAL.exists():
        print(f'❌ {JOURNAL} 不存在')
        sys.exit(1)
    d = json.load(open(JOURNAL, encoding='utf-8'))

    # 默认人数配置 (2 大2 小 + 1 大 2 小 = 7 人)
    people = DEFAULT_PEOPLE
    print(f'人数配置: {people}')

    result = accumulate_daily(d, people)
    print(f'\n累计 A家: ¥{result["household_A"]:.2f}')
    print(f'累计 B家: ¥{result["household_B"]:.2f}')
    print(f'合计: ¥{result["total"]:.2f}')

    print('\n按日:')
    for day_key, day_data in result['by_day'].items():
        print(f'  {day_key} {day_data["date"]}: A家 ¥{day_data["household_A"]:.2f}, B家 ¥{day_data["household_B"]:.2f}')

    # 落盘
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    json.dump(result, open(OUTPUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'\n✅ 落盘: {OUTPUT}')

    # 单元测试
    print('\n==== 单元测试 ====')
    # 测试 1: 整桌 ¥269
    r = split_bill(269, DEFAULT_PEOPLE, 'A')
    assert r['household_breakdown'][0]['amount'] == 269
    assert r['household_breakdown'][1]['amount'] == 0
    print('✅ 测试 1: 整桌 ¥269 → A家 ¥269')

    # 测试 2: AA ¥35
    r = split_bill(35, DEFAULT_PEOPLE, 'AA')
    assert abs(r['household_breakdown'][0]['amount'] - 17.5) < 0.01
    print('✅ 测试 2: AA ¥35 → 各家 ¥17.50')

    # 测试 3: AA KIDS_FREE ¥120 (小孩免票, 仅 3 成人)
    r = split_bill(120, DEFAULT_PEOPLE, 'AA_KIDS_FREE')
    assert r['per_person'] == 40.0  # 120 / 3
    print('✅ 测试 3: AA KIDS_FREE ¥120 → 成人 ¥40/人')

    print('\n✅ 所有测试通过')