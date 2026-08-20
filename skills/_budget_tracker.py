# -*- coding: utf-8 -*-
"""一起旅行 SKILL · 阶段 9 实施
实时预算预警 + 4 级看板

借鉴: SKILL.md v3.7 阶段 9

输入: journal.json + 预算配置
输出: data/budget.json + 4 级预警 (🟢 健康 / 🟡 接近 / 🟠 超支 / 🔴 警告)

用法:
  python skills/_budget_tracker.py  # 默认 10000 总预算
  BUDGET_TOTAL=8000 python skills/_budget_tracker.py
"""
import sys, os, json
from pathlib import Path
from datetime import datetime
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

JOURNAL = Path('data/journal.json')
OUTPUT = Path('data/budget.json')

DEFAULT_BUDGET = float(os.environ.get('BUDGET_TOTAL', 10000))
DEFAULT_PEOPLE = 7
DAYS = 9  # D1-D9 (D0 是出发夜, 通常没预算)


def check_budget(journal=None, budget_total=DEFAULT_BUDGET, people=DEFAULT_PEOPLE):
    """主入口: 累计 + 每日预算 + 4 级预警"""
    if journal is None:
        if JOURNAL.exists():
            journal = json.load(open(JOURNAL, encoding='utf-8'))
        else:
            return {'error': f'{JOURNAL} 不存在'}

    daily_budget = budget_total / DAYS
    per_person_total = budget_total / people
    per_person_daily = daily_budget / people

    by_day = {}
    cumulative = 0
    day_count = 0
    for day in journal.get('days', []):
        if day['key'] == 'D0':
            continue  # 跳过出发夜
        day_count += 1
        day_total = sum(float(f.get('amount', 0)) for f in day.get('expenses', []))
        cumulative += day_total
        planned = daily_budget * day_count
        diff = cumulative - planned
        if cumulative <= planned * 0.8:
            level = 'healthy'
        elif cumulative <= planned:
            level = 'close'
        elif cumulative <= planned * 1.2:
            level = 'over'
        else:
            level = 'warning'
        by_day[day['key']] = {
            'date': day.get('date', ''),
            'day_number': day_count,
            'planned': round(planned, 2),
            'actual': round(day_total, 2),
            'cumulative_planned': round(planned, 2),
            'cumulative_actual': round(cumulative, 2),
            'diff': round(diff, 2),
            'level': level,
        }

    if cumulative <= budget_total * 0.8:
        overall = 'healthy'
    elif cumulative <= budget_total:
        overall = 'close'
    elif cumulative <= budget_total * 1.2:
        overall = 'over'
    else:
        overall = 'warning'

    return {
        'budget_total': budget_total,
        'people': people,
        'daily_budget': round(daily_budget, 2),
        'per_person_total': round(per_person_total, 2),
        'per_person_daily': round(per_person_daily, 2),
        'by_day': by_day,
        'cumulative_actual': round(cumulative, 2),
        'remaining': round(budget_total - cumulative, 2),
        'overall_level': overall,
    }


LEVEL_EMOJI = {
    'healthy': '🟢 健康',
    'close': '🟡 接近',
    'over': '🟠 超支',
    'warning': '🔴 警告',
}


if __name__ == '__main__':
    print('==== 预算预警工具 ====')
    result = check_budget()
    if 'error' in result:
        print(f'❌ {result["error"]}')
        sys.exit(1)

    print(f'总预算: ¥{result["budget_total"]:.2f}')
    print(f'日均预算: ¥{result["daily_budget"]:.2f}')
    print(f'人均预算: ¥{result["per_person_total"]:.2f}')
    print(f'累计实际: ¥{result["cumulative_actual"]:.2f}')
    print(f'剩余: ¥{result["remaining"]:.2f}')
    print(f'整体等级: {LEVEL_EMOJI[result["overall_level"]]}')

    print('\n按日:')
    for day_key, day in result['by_day'].items():
        emoji = LEVEL_EMOJI[day['level']]
        bar_len = min(int(day['actual'] / day['planned'] * 20), 40) if day['planned'] > 0 else 0
        bar = '█' * bar_len
        print(f'  {day_key} ({day["date"]}): '
              f'{emoji} ¥{day["actual"]:.0f} / ¥{day["planned"]:.0f} {bar:<20} '
              f'累计 ¥{day["cumulative_actual"]:.0f} (差 ¥{day["diff"]:+.0f})')

    # 落盘
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    json.dump(result, open(OUTPUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'\n✅ 落盘: {OUTPUT}')

    # 单元测试 (独立)
    print('\n==== 单元测试 ====')
    test_journal = {
        'days': [
            {'key': 'D0', 'expenses': [{'amount': 800}]},
            {'key': 'D1', 'expenses': [{'amount': 1000}, {'amount': 500}]},
            {'key': 'D2', 'expenses': [{'amount': 1200}]},
        ]
    }
    # 测试 1: 健康 (D0 跳过, 累计 1000+500+1200 = 2700)
    r = check_budget(test_journal, budget_total=10000)
    assert r['cumulative_actual'] == 2700, f"got {r['cumulative_actual']}"
    print(f'✅ 测试 1: 累计 ¥2700, 整体 {r["overall_level"]}')

    # 测试 2: 超支
    r = check_budget(test_journal, budget_total=2000)
    assert r['cumulative_actual'] == 2700
    assert r['overall_level'] == 'warning', f"got {r['overall_level']}"
    print(f'✅ 测试 2: 累计 ¥2700 > 预算 ¥2000, 警告')

    # 测试 3: 临界
    r = check_budget(test_journal, budget_total=2700)
    assert r['overall_level'] in ('close', 'over'), f"got {r['overall_level']}"
    print(f'✅ 测试 3: 累计 ¥2700 = 预算, {r["overall_level"]}')

    print('\n✅ 所有测试通过')