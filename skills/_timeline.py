# -*- coding: utf-8 -*-
"""一起旅行 SKILL · 阶段 3 实施
时间轴生成器 (主键优先级: 收据 > EXIF > 口头 > 估算)

借鉴: SKILL.md v3.7 阶段 3

输入: journal.json + photos (含 EXIF)
输出: data/timeline.json
"""
import sys, json, re
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

JOURNAL = Path('data/journal.json')
OUTPUT = Path('data/timeline.json')


def parse_time(time_str):
    """解析时间字符串为 ISO datetime"""
    if not time_str:
        return None
    time_str = str(time_str).strip()
    # 处理 "8/7 周五" "18:00" "20:34"
    m = re.match(r'(\d{1,2})[/\-月](\d{1,2}).*?(\d{1,2}):(\d{2})', time_str)
    if m:
        month, day, h, mn = map(int, m.groups())
        from datetime import datetime
        return datetime(2026, month, day, h, mn).isoformat()
    # 只有 HH:MM
    m = re.match(r'(\d{1,2}):(\d{2})', time_str)
    if m:
        return f'2026-01-01T{int(m.group(1)):02d}:{int(m.group(2)):02d}:00'
    return None


def build_timeline(journal=None):
    """主入口: 从 journal.json 生成时间轴"""
    if journal is None:
        if not JOURNAL.exists():
            return {'error': f'{JOURNAL} 不存在', 'timeline': []}
        journal = json.load(open(JOURNAL, encoding='utf-8'))

    timeline = []

    # 主键 1: 费用记录 (含 time, 可作为锚点)
    for day in journal.get('days', []):
        for fee in day.get('expenses', []):
            t = parse_time(fee.get('time', ''))
            timeline.append({
                'datetime': t,
                'time_raw': fee.get('time', ''),
                'key_priority': 'FEE_TIME',
                'day_key': day['key'],
                'place_name': fee.get('place_name', '') or day.get('place_name', ''),
                'item': fee.get('item', '')[:100],
                'amount': float(fee.get('amount', 0)),
                'fee_type': fee.get('type', 'A'),
            })

    # 主键 2: waypoint (用 day 的 waypoint 字段)
    for day in journal.get('days', []):
        for wp in day.get('waypoints', []):
            t = parse_time(wp.get('time', ''))
            timeline.append({
                'datetime': t,
                'time_raw': wp.get('time', ''),
                'key_priority': 'WAYPOINT_TIME',
                'day_key': day['key'],
                'place_name': wp.get('place_name', ''),
                'address': wp.get('address', ''),
                'lat': wp.get('lat'),
                'lon': wp.get('lon'),
            })

    # 主键 3: photo EXIF
    for day in journal.get('days', []):
        for photo in day.get('photos', []):
            exif = photo.get('exif', {})
            t = exif.get('datetime_original')
            timeline.append({
                'datetime': t,
                'time_raw': t or '',
                'key_priority': 'PHOTO_EXIF',
                'day_key': day['key'],
                'place_name': photo.get('place_name', '') or photo.get('file', ''),
                'file': photo.get('file', ''),
                'gps': exif.get('gps'),
            })

    # 排序: 有 datetime 的在前, 无的在后
    def sort_key(item):
        dt = item.get('datetime')
        return (0, dt) if dt else (1, '')

    timeline.sort(key=sort_key)

    return {
        'count': len(timeline),
        'timeline': timeline,
        'by_day': {day['key']: sum(1 for t in timeline if t.get('day_key') == day['key']) for day in journal.get('days', [])},
    }


if __name__ == '__main__':
    print('==== 时间轴生成器 ====')
    result = build_timeline()
    if 'error' in result:
        print(f'❌ {result["error"]}')
        sys.exit(1)
    print(f'总条目: {result["count"]}')
    print(f'按日分布: {result["by_day"]}')

    # 显示前 10 条
    print('\n前 10 条:')
    for i, item in enumerate(result['timeline'][:10]):
        dt = item.get('datetime', '无时间')[:19]
        priority = item.get('key_priority', '')
        place = item.get('place_name', '')[:30]
        print(f'  {i+1:>2}. [{priority:14s}] {dt} | {place}')

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    json.dump(result, open(OUTPUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'\n✅ 落盘: {OUTPUT}')

    # 单元测试
    print('\n==== 单元测试 ====')
    # 测试 1: 时间解析
    t = parse_time('18:00')
    assert t and 'T18:00' in t, f"got {t}"
    print(f'✅ 测试 1: parse_time("18:00") = {t}')

    t = parse_time('8/7 18:00')
    assert t and '2026-08-07' in t, f"got {t}"
    print(f'✅ 测试 2: parse_time("8/7 18:00") = {t}')

    # 测试 3: build_timeline
    test_journal = {
        'days': [{
            'key': 'D0',
            'expenses': [
                {'time': '20:00', 'item': '晚餐', 'amount': 100, 'type': 'A'},
                {'time': '21:00', 'item': '宵夜', 'amount': 50, 'type': 'AA'},
            ],
            'waypoints': [
                {'time': '18:00', 'place_name': '餐厅', 'lat': 30.0, 'lon': 120.0},
            ],
        }]
    }
    r = build_timeline(test_journal)
    assert r['count'] == 3, f"got {r['count']}"
    assert r['timeline'][0]['key_priority'] in ('FEE_TIME', 'WAYPOINT_TIME'), f"got {r['timeline'][0]}"
    print(f'✅ 测试 3: build_timeline 处理 1 day, {r["count"]} 条')

    print('\n✅ 所有测试通过')