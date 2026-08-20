# -*- coding: utf-8 -*-
"""一起旅行 SKILL · 阶段 2 实施
EXIF GPS → 高德 reverse_geocode + POI 搜索 + 5 维评分匹配

借鉴: AMap-Web/amap-skills (官方) + henrywen98/amap-agent-skill (纯 curl 风格)

输入: waypoint 含 exif_gps + ocr_result.shop_name
输出: waypoint.poi_match (含 name/poi_id/address/location/distance_to_exif_m/
       name_similarity/category/rating/business_hours/confidence)

用法:
    # 测试模式 (用 mock 数据, 不需要 AMAP_KEY)
    python skills/_amap_geo_match.py --mock

    # 单 waypoint 处理 (从 journal.json 读, 需 AMAP_KEY)
    python skills/_amap_geo_match.py D4_001

    # 全量处理 (阶段 4 后自动跑)
    python skills/_amap_geo_match.py --all

env 变量 (env.example):
    AMAP_KEY=你的高德 Web 服务 key
    AMAP_MATCH_RADIUS=200         # around 搜索半径(米)
    AMAP_MIN_SIMILARITY=0.7       # 名称相似度阈值
"""
import os, sys, json, math, re, urllib.parse, urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

JOURNAL = Path('data/journal.json')
OUTPUT = Path('data/poi_matches.json')

AMAP_KEY = os.environ.get('AMAP_KEY', '')
RADIUS = int(os.environ.get('AMAP_MATCH_RADIUS', 200))
MIN_SIM = float(os.environ.get('AMAP_MIN_SIMILARITY', 0.7))


def amap_request(path, params):
    """高德 REST API 调用 (借鉴 henrywen98/amap-agent-skill)"""
    if not AMAP_KEY:
        return {'status': '0', 'info': 'AMAP_KEY 未配置 (需 .env)'}
    params['key'] = AMAP_KEY
    url = f'https://restapi.amap.com/v3/{path}?' + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            return json.load(r)
    except Exception as e:
        return {'status': '0', 'info': str(e)}


def amap_regeocode(lon, lat, coordtype='wgs84'):
    """reverse geocode: 坐标 → 地址 + 行政区"""
    data = amap_request('geocode/regeo', {
        'location': f'{lon},{lat}',
        'extensions': 'base',
        'coordtype': coordtype,
        'radius': 500,
    })
    if data.get('status') == '1':
        regeo = data.get('regeocode', {})
        return {
            'formatted_address': regeo.get('formatted_address', ''),
            'city': regeo.get('addressComponent', {}).get('city', ''),
            'district': regeo.get('addressComponent', {}).get('district', ''),
            'township': regeo.get('addressComponent', {}).get('township', ''),
        }
    return {'formatted_address': '', 'city': '', 'district': '', 'township': ''}


def amap_around_search(lon, lat, keywords, radius=RADIUS):
    """around search: 坐标 + 关键词 → 候选 POI"""
    data = amap_request('place/around', {
        'keywords': keywords,
        'location': f'{lon},{lat}',
        'radius': radius,
        'extensions': 'all',
        'sortrule': 'distance',
    })
    if data.get('status') == '1':
        return data.get('pois', [])
    return []


def amap_text_search(keywords, city=None):
    """text search: 关键词 + 城市 → 候选 POI"""
    params = {'keywords': keywords, 'extensions': 'all'}
    if city:
        params['city'] = city
    data = amap_request('place/text', params)
    if data.get('status') == '1':
        return data.get('pois', [])
    return []


def haversine(lon1, lat1, lon2, lat2):
    """两点间 haversine 距离 (米)"""
    R = 6371000  # 地球半径 m
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c


def levenshtein(s1, s2):
    """字符串 Levenshtein 距离 (简单实现)"""
    s1 = re.sub(r'[^\w\u4e00-\u9fff]', '', s1.lower())
    s2 = re.sub(r'[^\w\u4e00-\u9fff]', '', s2.lower())
    if not s1 and not s2:
        return 1.0
    if not s1 or not s2:
        return 0.0
    n, m = len(s1), len(s2)
    if n > m:
        s1, s2 = s2, s1
        n, m = m, n
    dp = list(range(m + 1))
    for i in range(1, n + 1):
        prev, dp = dp[0], [i] + [0] * m
        for j in range(1, m + 1):
            cost = 0 if s1[i-1] == s2[j-1] else 1
            dp[j] = min(prev + cost, dp[j-1] + 1, dp[j-1] + cost)
            prev = dp[j] if j == 1 else dp[j-1]
    distance = dp[m]
    return 1 - distance / max(n, m)


def score_poi(poi, exif_gps, shop_name, exif_time=None):
    """5 维 POI 评分"""
    if not poi or not poi.get('location'):
        return None
    poi_lon, poi_lat = poi['location'].split(',')
    poi_lon, poi_lat = float(poi_lon), float(poi_lat)
    # 1. 距离
    dist = haversine(exif_gps[0], exif_gps[1], poi_lon, poi_lat)
    # 2. 名称相似
    poi_name = poi.get('name', '')
    name_sim = levenshtein(shop_name, poi_name) if shop_name else 0.5
    # 3. 类别
    cat_match = poi.get('type') in ('餐饮', '购物', '风景名胜', '住宿', '生活服务')
    # 4. 评分
    poi_rating = float(poi.get('biz_ext', {}).get('rating', '0') or '0')
    rating_score = min(poi_rating / 5.0, 1.0) if poi_rating else 0.5
    # 5. 营业时间 (省略, 需复杂解析)
    return {
        'poi_id': poi.get('id', ''),
        'name': poi_name,
        'address': poi.get('address', ''),
        'location': [poi_lon, poi_lat],
        'distance_to_exif_m': round(dist, 1),
        'name_similarity': round(name_sim, 3),
        'category': poi.get('type', ''),
        'rating': poi_rating,
        'business_hours': poi.get('biz_ext', {}).get('opentime', ''),
        'score': round(
            (1 - min(dist / 1000, 1)) * 0.3 +  # 距离权重30%
            name_sim * 0.4 +                       # 名称相似40%
            (1 if cat_match else 0) * 0.1 +       # 类别10%
            rating_score * 0.2,                   # 评分20%
            3
        ),
    }


def match_waypoint(waypoint, use_api=True):
    """匹配单个 waypoint"""
    exif_gps = waypoint.get('exif_gps') or (waypoint.get('lat'), waypoint.get('lon'))
    shop_name = waypoint.get('ocr_result', {}).get('parsed_fields', {}).get('shop_name') or \
                waypoint.get('place_name', '') or \
                waypoint.get('name', '')
    if not exif_gps or len(exif_gps) != 2:
        return {'status': 'no_gps', 'poi_match': None}

    candidates = []
    if use_api and AMAP_KEY:
        # 优先 around 搜
        candidates = amap_around_search(exif_gps[0], exif_gps[1], shop_name, radius=RADIUS)
        # 若 around 无结果, 试 reverse_geocode + text
        if not candidates:
            regeo = amap_regeocode(exif_gps[0], exif_gps[1])
            city = regeo.get('city', '')
            if city:
                candidates = amap_text_search(shop_name, city=city)

    # 评分所有候选
    scored = []
    for poi in candidates:
        s = score_poi(poi, exif_gps, shop_name)
        if s:
            scored.append(s)
    # 按 score 降序
    scored.sort(key=lambda x: -x['score'])
    if scored:
        top = scored[0]
        top['confidence'] = round(top['score'] / 3.0, 3)
        return {'status': 'ok', 'poi_match': top}
    # 无 API 或无结果, 用 mock 数据
    if not use_api or not AMAP_KEY:
        return {'status': 'mock', 'poi_match': mock_poi_match(waypoint, exif_gps, shop_name)}
    return {'status': 'no_match', 'poi_match': None}


def mock_poi_match(waypoint, exif_gps, shop_name):
    """Mock POI (无 API 时返回)"""
    return {
        'poi_id': 'MOCK_' + (waypoint.get('id', 'unknown')),
        'name': shop_name or '未知 POI',
        'address': f'Mock 地址 (基于 GPS {exif_gps[1]:.4f}, {exif_gps[0]:.4f})',
        'location': list(exif_gps),
        'distance_to_exif_m': 0.0,
        'name_similarity': 1.0,
        'category': waypoint.get('category', '其他'),
        'rating': 0,
        'business_hours': '未知',
        'score': 3.0,
        'confidence': 1.0,
        '_mock': True,
    }


def main():
    args = sys.argv[1:]
    if not args:
        print('用法:')
        print('  python _amap_geo_match.py --mock       # mock 数据演示')
        print('  python _amap_geo_match.py <waypoint_id> # 单个匹配')
        print('  python _amap_geo_match.py --all         # 全量处理 journal.json')
        if not AMAP_KEY:
            print('\n⚠️  AMAP_KEY 未配置 (运行 --mock 演示)')
        sys.exit(0)

    if args[0] == '--mock':
        print('=== Mock 模式 (无 AMAP_KEY) ===')
        # Mock 一个 waypoint
        wp = {
            'id': 'D4_MOCK',
            'place_name': '老马家肉丸子胡辣汤',
            'lat': 34.2621, 'lon': 108.9918,
            'ocr_result': {'parsed_fields': {'shop_name': '老马家肉丸子胡辣汤'}},
        }
        result = match_waypoint(wp, use_api=False)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if args[0] == '--all':
        if not JOURNAL.exists():
            print(f'❌ {JOURNAL} 不存在')
            return
        d = json.load(open(JOURNAL, encoding='utf-8'))
        all_matches = []
        for day in d.get('days', []):
            for wp in day.get('waypoints', []):
                lat, lon = wp.get('lat'), wp.get('lon')
                if lat is None or lon is None:
                    continue
                result = match_waypoint(wp, use_api=bool(AMAP_KEY))
                wp_id = f"{day['key']}_{wp.get('place_name', 'unknown')[:20]}"
                all_matches.append({
                    'waypoint_id': wp_id,
                    'place_name': wp.get('place_name', ''),
                    'exif_gps': [lon, lat],
                    'result': result,
                })
        # 落盘
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        json.dump({'matches': all_matches, 'count': len(all_matches)}, open(OUTPUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        ok = sum(1 for m in all_matches if m['result']['status'] == 'ok')
        mock = sum(1 for m in all_matches if m['result']['status'] == 'mock')
        print(f'\n✅ 处理 {len(all_matches)} 个 waypoint')
        print(f'   API 匹配: {ok} | Mock: {mock} | 落盘: {OUTPUT}')
        return

    # 单个处理
    if not JOURNAL.exists():
        print(f'❌ {JOURNAL} 不存在')
        return
    d = json.load(open(JOURNAL, encoding='utf-8'))
    target = args[0]
    for day in d.get('days', []):
        for wp in day.get('waypoints', []):
            wp_id = f"{day['key']}_{wp.get('place_name', 'unknown')[:20]}"
            if target in wp_id:
                result = match_waypoint(wp)
                print(json.dumps({'waypoint_id': wp_id, 'result': result}, ensure_ascii=False, indent=2))
                return
    print(f'❌ 未找到 waypoint: {target}')


if __name__ == '__main__':
    main()