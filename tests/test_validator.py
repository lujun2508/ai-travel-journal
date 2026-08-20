# -*- coding: utf-8 -*-
"""一起旅行 SKILL · tests/test_validator.py
阶段 2.5 3 路交叉验证 smoke test

实际 API 返回: {score, risk, issues, breakdown}
  - score: 0-100 评分
  - risk:  '可信' / '存疑' / '需人工确认'
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from skills._validator import validate_waypoint  # noqa: E402


def test_validate_waypoint_empty():
    """空 waypoint 不崩, 返回 4 个字段 (score/risk/issues/match_breakdown)"""
    r = validate_waypoint({})
    assert 'score' in r, f"缺 score 字段, 实际: {list(r.keys())}"
    assert 'risk' in r
    assert 'issues' in r
    assert 'match_breakdown' in r
    # 实际行为: 空 waypoint = score 100 (没数据不扣分), risk '可信'
    # 这是 SKILL 设计: "没数据 = 不扣分" 而非 "没数据 = 0 分"
    assert isinstance(r['score'], int)
    assert r['risk'] in ('可信', '存疑', '需人工确认')
    print(f'  [PASS] test_validate_waypoint_empty (score={r["score"]}, risk={r["risk"]})')


def test_validate_waypoint_完美匹配():
    """EXIF GPS + 店招 + 小票三路完全一致, 应该 score 高 + risk 可信"""
    waypoint = {
        'ocr': {'shop_name': '示例餐馆'},
        'ocr_receipt': {'merchant_name': '示例餐馆', 'datetime': '2026-05-01T12:30:00', 'total': 100.0},
        'poi_match': {
            'name': '示例餐馆',
            'location': [116.3974, 39.9087],  # [经度, 纬度]
            'rating': 4.5,
            'business_hours': '10:00-22:00',
        },
        'exif_gps': [116.3974, 39.9087],  # [经度, 纬度]
        'exif_time': '2026-05-01T12:30:00',
    }
    r = validate_waypoint(waypoint)
    assert r['score'] >= 85, f"应 ≥85, 实际 {r['score']}, issues={r.get('issues')}"
    assert r['risk'] == '可信'
    print(f'  [PASS] test_validate_waypoint_完美匹配 (score={r["score"]}, risk={r["risk"]})')


def test_validate_waypoint_GPS_偏离():
    """EXIF GPS 离 POI 很远, score 应扣 + risk 升级"""
    waypoint = {
        'ocr': {'shop_name': '示例餐馆'},
        'poi_match': {
            'name': '示例餐馆',
            'location': [116.3974, 39.9087],  # 北京
            'rating': 4.5,
            'business_hours': '10:00-22:00',
        },
        'exif_gps': [121.4737, 31.2304],  # 上海
        'exif_time': '2026-05-01T12:30:00',
    }
    r = validate_waypoint(waypoint)
    assert r['risk'] in ('存疑', '需人工确认'), f"应存疑或需人工确认, 实际 {r['risk']}"
    assert r['score'] < 85
    print(f'  [PASS] test_validate_waypoint_GPS_偏离 (score={r["score"]}, risk={r["risk"]})')


def test_validate_waypoint_店招_不一致():
    """店招 OCR 跟 POI 名称差太多, score 应扣"""
    waypoint = {
        'ocr': {'shop_name': '沙县小吃'},
        'poi_match': {
            'name': '海底捞火锅',
            'location': [116.3974, 39.9087],
            'rating': 4.5,
        },
        'exif_gps': [116.3974, 39.9087],
    }
    r = validate_waypoint(waypoint)
    assert r['risk'] in ('存疑', '需人工确认')
    print(f'  [PASS] test_validate_waypoint_店招_不一致 (score={r["score"]}, risk={r["risk"]})')


if __name__ == '__main__':
    print('test_validator.py:')
    test_validate_waypoint_empty()
    test_validate_waypoint_完美匹配()
    test_validate_waypoint_GPS_偏离()
    test_validate_waypoint_店招_不一致()
    print('  [ALL PASS] 4 / 4')
