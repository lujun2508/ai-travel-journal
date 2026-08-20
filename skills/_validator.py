# -*- coding: utf-8 -*-
"""一起旅行 SKILL · 阶段 2.5 实施
3 路交叉验证 + 风险判定 (行业空白, 自创)

借鉴: SKILL.md v3.7 阶段 2.5

输入: waypoint (含 ocr.shop_name, ocr_receipt.merchant_name, poi_match, exif_gps, exif_time)
输出: waypoint_validation {score, risk, issues, match_breakdown}
"""
import sys, math, re, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# 可调阈值 (来自 .env 或默认)
DEFAULT_THRESHOLDS = {
    'shop_poi_min': 0.5,
    'shop_poi_warn': 0.7,
    'shop_receipt_min': 0.5,
    'distance_max': 200,
    'distance_warn': 100,
    'time_max_min': 120,
    'time_warn_min': 60,
    'business_hours_max_penalty': 10,
}


def levenshtein(s1, s2):
    """字符串 Levenshtein 距离 → 相似度 (0-1)
    改进: 预处理去分店后缀
    修正: 使用 temp 变量避免 prev 引用错误"""
    if not s1 and not s2:
        return 1.0
    if not s1 or not s2:
        return 0.0
    s1 = str(s1).lower().strip()
    s2 = str(s2).lower().strip()
    # 预处理: 去常见分店后缀
    for suf in ['(总店)', '(旗舰店)', '(分店)', '(本店)']:
        s1 = s1.replace(suf, '')
        s2 = s2.replace(suf, '')
    # 去所有括号内容 (中英文括号都支持)
    import re as _re
    s1 = _re.sub(r'[\(（][^\)）]*[\)）]', '', s1)
    s2 = _re.sub(r'[\(（][^\)）]*[\)）]', '', s2)
    s1 = _re.sub(r'\s+', '', s1)
    s2 = _re.sub(r'\s+', '', s2)
    n, m = len(s1), len(s2)
    if n == 0 and m == 0:
        return 1.0
    if n == 0 or m == 0:
        return 0.0
    if n > m:
        s1, s2 = s2, s1
        n, m = m, n
    # DP 表 (n+1) x (m+1)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = 0 if s1[i-1] == s2[j-1] else 1
            dp[i][j] = min(
                dp[i-1][j] + 1,       # 删除
                dp[i][j-1] + 1,       # 插入
                dp[i-1][j-1] + cost,  # 替换
            )
    distance = dp[n][m]
    return 1 - distance / max(n, m)


def haversine(lon1, lat1, lon2, lat2):
    """两点间 haversine 距离 (米)"""
    R = 6371000
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))


def parse_opentime(opentime_str, exif_time):
    """简易营业时间解析: '10:00-22:00' / '24小时' / 空"""
    if not opentime_str or not exif_time:
        return True  # 缺数据, 不扣分
    if '24小时' in opentime_str or '全天' in opentime_str:
        return True
    try:
        m = re.search(r'(\d{1,2}):(\d{2})-(\d{1,2}):(\d{2})', opentime_str)
        if not m:
            return True
        sh, sm, eh, em = int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))
        from datetime import datetime
        exif_dt = datetime.fromisoformat(exif_time.replace('Z', '+00:00').replace('T', ' ').split('+')[0].strip())
        exif_min = exif_dt.hour * 60 + exif_dt.minute
        open_min = sh * 60 + sm
        close_min = eh * 60 + em
        if open_min <= close_min:
            return open_min <= exif_min <= close_min
        else:  # 跨夜
            return exif_min >= open_min or exif_min <= close_min
    except Exception:
        return True


def validate_waypoint(wp, thresholds=None):
    """
    主入口: 5 维交叉验证 + 风险判定

    wp 格式:
      {
        'ocr': {'shop_name': '海底捞'},
        'ocr_receipt': {'merchant_name': '海底捞火锅', 'datetime': '2026-08-11T12:34', 'total': 269.0},
        'poi_match': {'name': '海底捞火锅(延安西路店)', 'location': [121.47, 31.23], 'business_hours': '10:00-02:00'},
        'exif_gps': [121.47, 31.23],
        'exif_time': '2026-08-11T12:34:56'
      }
    """
    th = dict(DEFAULT_THRESHOLDS)
    if thresholds:
        th.update(thresholds)

    score = 100
    issues = []
    breakdown = {}

    # 1. 店招 vs POI 名称
    shop_name = wp.get('ocr', {}).get('shop_name', '') or wp.get('shop_name', '')
    poi_name = wp.get('poi_match', {}).get('name', '')
    if shop_name and poi_name:
        sim = levenshtein(shop_name, poi_name)
        breakdown['shop_vs_poi'] = round(sim, 3)
        if sim < th['shop_poi_min']:
            score -= 30
            issues.append(f"店招 vs POI 名称差异大: '{shop_name}' vs '{poi_name}'")
        elif sim < th['shop_poi_warn']:
            score -= 15
            issues.append(f"店招 vs POI 名称中度差异: {sim:.2f}")

    # 2. 店招 vs 小票商户名
    receipt_name = wp.get('ocr_receipt', {}).get('merchant_name', '') or wp.get('receipt_name', '')
    if shop_name and receipt_name:
        sim = levenshtein(shop_name, receipt_name)
        breakdown['shop_vs_receipt'] = round(sim, 3)
        if sim < th['shop_receipt_min']:
            score -= 20
            issues.append(f"店招 vs 小票商户名差异大: '{shop_name}' vs '{receipt_name}'")

    # 3. EXIF GPS vs POI 距离
    exif_gps = wp.get('exif_gps')
    poi_location = wp.get('poi_match', {}).get('location')
    if exif_gps and poi_location:
        try:
            dist = haversine(exif_gps[0], exif_gps[1], poi_location[0], poi_location[1])
            breakdown['exif_distance_m'] = round(dist, 1)
            if dist > th['distance_max']:
                score -= 25
                issues.append(f"距离 {dist:.0f}m 太远")
            elif dist > th['distance_warn']:
                score -= 10
                issues.append(f"距离 {dist:.0f}m 略远")
        except Exception:
            pass

    # 4. EXIF 时间 vs 小票时间
    exif_time = wp.get('exif_time')
    receipt_time = wp.get('ocr_receipt', {}).get('datetime', '') or wp.get('receipt_time', '')
    if exif_time and receipt_time:
        try:
            from datetime import datetime
            exif_dt = datetime.fromisoformat(exif_time.replace('Z', '+00:00').replace('T', ' ').split('+')[0].strip())
            receipt_dt = datetime.fromisoformat(receipt_time.replace('Z', '+00:00').replace('T', ' ').split('+')[0].strip())
            diff_min = abs((exif_dt - receipt_dt).total_seconds() / 60)
            breakdown['exif_receipt_time_diff_min'] = round(diff_min, 1)
            if diff_min > th['time_max_min']:
                score -= 15
                issues.append(f"时间差 {diff_min:.0f} 分钟过大")
            elif diff_min > th['time_warn_min']:
                score -= 5
        except Exception:
            pass

    # 5. 营业时间匹配
    business_hours = wp.get('poi_match', {}).get('business_hours', '')
    if business_hours and exif_time:
        in_business = parse_opentime(business_hours, exif_time)
        breakdown['poi_business_hours_match'] = in_business
        if not in_business:
            score -= th['business_hours_max_penalty']
            issues.append(f"拍摄时间不在 POI 营业时间内")

    score = max(0, score)
    if score >= 85:
        risk = '可信'
    elif score >= 60:
        risk = '存疑'
    else:
        risk = '需人工确认'

    return {
        'score': score,
        'risk': risk,
        'issues': issues,
        'match_breakdown': breakdown,
    }


# 单元测试
if __name__ == '__main__':
    print('==== 单元测试 _validator.py ====')
    # 测试 1: 完美匹配
    wp = {
        'ocr': {'shop_name': '海底捞火锅'},
        'ocr_receipt': {'merchant_name': '海底捞火锅', 'datetime': '2026-08-11T12:34', 'total': 269.0},
        'poi_match': {'name': '海底捞火锅(延安西路店)', 'location': [121.4737, 31.2304], 'business_hours': '10:00-02:00'},
        'exif_gps': [121.4737, 31.2304],
        'exif_time': '2026-08-11T12:34:56',
    }
    r = validate_waypoint(wp)
    print(json.dumps(r, ensure_ascii=False, indent=2))
    assert r['risk'] == '可信', f"期望可信, got {r['risk']}"
    assert r['score'] >= 85, f"期望 >=85, got {r['score']}"
    print('✅ 测试 1 通过: 完美匹配')

    # 测试 2: 差异大
    wp2 = {
        'ocr': {'shop_name': '老马家'},
        'ocr_receipt': {'merchant_name': '海底捞', 'datetime': '2026-08-11T12:34', 'total': 269.0},
        'poi_match': {'name': '晓长安·新陕菜', 'location': [121.4737, 31.2304], 'business_hours': '10:00-02:00'},
        'exif_gps': [108.94, 34.27],  # 距离很远
        'exif_time': '2026-08-11T12:34:56',
    }
    r2 = validate_waypoint(wp2)
    print(json.dumps(r2, ensure_ascii=False, indent=2))
    assert r2['risk'] == '需人工确认', f"期望需人工确认, got {r2['risk']}"
    assert r2['score'] < 60, f"期望 <60, got {r2['score']}"
    print('✅ 测试 2 通过: 差异大')

    print('\n✅ 所有单元测试通过')