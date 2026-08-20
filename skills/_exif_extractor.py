# -*- coding: utf-8 -*-
"""一起旅行 SKILL · 阶段 0.5+ 实施
EXIF GPS + 完整 EXIF 提取 + VLM 美学评分增强

借鉴: jaxx2104/exiftool-skill (15 commits) + aAAaqwq/image-vision (5 模式 VLM)

输入: 照片文件路径
输出: data/exif_cache/<basename>.json (含完整 EXIF)
      + data/inbox.json 扩展 (含 exif_full + vlm_score + gps_status + smart_category)

用法:
    # 单文件
    python skills/_exif_extractor.py photos/D4_03_xxx.jpg

    # 批量处理 _inbox/ 全部
    python skills/_exif_extractor.py --batch

    # 全量重处理 photos/ (慢)
    python skills/_exif_extractor.py --all
"""
import os, sys, json, hashlib, subprocess
from pathlib import Path
from datetime import datetime, timezone, timedelta
from PIL import Image, ExifTags

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

PHOTOS_DIR = Path('photos')
INBOX_DIR = PHOTOS_DIR / '_inbox'
EXIF_CACHE = Path('data/exif_cache')
INBOX_LOG = Path('data/inbox.json')

EXIF_TAGS = {v: k for k, v in ExifTags.TAGS.items()}

# WGS-84 → GCJ-02 偏移 (中国大陆, 简化版, 误差 50-500m)
# 实际偏移需用 pyproj 或 AMap API 转换
def wgs84_to_gcj02(lon, lat):
    """简化版: 返回原值 + 偏移提示, 真实偏移用 amap API 完成"""
    return lon, lat


def extract_full_exif(path):
    """完整 EXIF 提取 (借鉴 jaxx2104/exiftool-skill 8 任务工作流)"""
    out = {
        'datetime_original': None,
        'gps': None,
        'camera': None,
        'lens': None,
        'iso': None,
        'f_number': None,
        'exposure_time': None,
        'focal_length': None,
        'orientation': None,
    }
    try:
        img = Image.open(path)
        exif = img._getexif() or {}

        # DateTimeOriginal
        dto = exif.get(EXIF_TAGS.get('DateTimeOriginal', 36867))
        if dto:
            try:
                dt = datetime.strptime(dto, '%Y:%m:%d %H:%M:%S')
                out['datetime_original'] = dt.isoformat()
            except Exception:
                out['datetime_original'] = dto

        # GPS (标准 EXIF: 2=Lat, 4=Lon, 都是 (deg,min,sec) rationals)
        gps = exif.get(EXIF_TAGS.get('GPSInfo', 34853))
        if gps:
            try:
                # Latitude: gps[2] = (deg_num, deg_den, min_num, min_den, sec_num, sec_den)
                if 2 in gps:
                    if len(gps[2]) == 6:
                        # 标准 EXIF GPS rationals (deg, min, sec 各 2 个)
                        lat_d = float(gps[2][0]) / float(gps[2][1])
                        lat_m = float(gps[2][2]) / float(gps[2][3])
                        lat_s = float(gps[2][4]) / float(gps[2][5])
                    elif len(gps[2]) == 3:
                        # 压缩格式 (deg/min/sec 合并)
                        lat_d = float(gps[2][0]) / float(gps[2][1])
                        lat_m = 0
                        lat_s = 0
                    else:
                        raise ValueError(f"Unexpected GPS lat format: {gps[2]}")
                    lat = lat_d + lat_m/60 + lat_s/3600
                    if 1 in gps and gps[1] in (b'S', 'S'):
                        lat = -lat
                # Longitude: gps[4] = (deg_num, deg_den, min_num, min_den, sec_num, sec_den)
                lon_d = lon_m = lon_s = 0
                lon = None
                if 4 in gps:
                    if len(gps[4]) == 6:
                        lon_d = float(gps[4][0]) / float(gps[4][1])
                        lon_m = float(gps[4][2]) / float(gps[4][3])
                        lon_s = float(gps[4][4]) / float(gps[4][5])
                    elif len(gps[4]) == 3:
                        lon_d = float(gps[4][0]) / float(gps[4][1])
                    else:
                        raise ValueError(f"Unexpected GPS lon format: {gps[4]}")
                    lon = lon_d + lon_m/60 + lon_s/3600
                    if 3 in gps and gps[3] in (b'W', 'W'):
                        lon = -lon
                alt = None
                if 6 in gps and isinstance(gps[6], tuple) and len(gps[6]) >= 2:
                    alt = float(gps[6][0]) / float(gps[6][1])
                if lat is not None and lon is not None:
                    out['gps'] = {'lat': round(lat, 7), 'lon': round(lon, 7), 'alt': alt}
                else:
                    out['gps'] = None
            except Exception as e:
                out['gps'] = None

        # 相机
        make = exif.get(EXIF_TAGS.get('Make', 271))
        model = exif.get(EXIF_TAGS.get('Model', 272))
        if make or model:
            out['camera'] = {'make': make, 'model': model}

        # 镜头
        lens_model = exif.get(EXIF_TAGS.get('LensModel', 42036))
        if lens_model:
            out['lens'] = lens_model

        # ISO
        iso = exif.get(EXIF_TAGS.get('ISOSpeedRatings', 34855))
        if iso:
            try:
                out['iso'] = int(iso) if isinstance(iso, (int, float)) else int(iso[0]) if isinstance(iso, tuple) else None
            except Exception:
                pass

        # F-Number
        fnum = exif.get(EXIF_TAGS.get('FNumber', 33437))
        if fnum:
            try:
                out['f_number'] = float(fnum) if isinstance(fnum, (int, float)) else float(fnum[0]) / float(fnum[1]) if isinstance(fnum, tuple) else None
            except Exception:
                pass

        # Exposure Time
        exp = exif.get(EXIF_TAGS.get('ExposureTime', 33434))
        if exp:
            try:
                out['exposure_time'] = str(exp) if isinstance(exp, (int, float)) else f"{exp[0]}/{exp[1]}"
            except Exception:
                pass

        # Focal Length
        focal = exif.get(EXIF_TAGS.get('FocalLength', 37386))
        if focal:
            try:
                out['focal_length'] = float(focal) if isinstance(focal, (int, float)) else float(focal[0]) / float(focal[1]) if isinstance(focal, tuple) else None
            except Exception:
                pass

        # Orientation
        orient = exif.get(EXIF_TAGS.get('Orientation', 274))
        if orient:
            out['orientation'] = int(orient)

        img.close()
    except Exception as e:
        pass
    return out


def estimate_vlm_score(path):
    """VLM 美学评分 (借鉴 image-vision, 用 PIL 做轻量级启发式)
    实际生产用 Qwen-VL / SN Vision, 这里 mock 基础指标"""
    try:
        img = Image.open(path)
        w, h = img.size
        # 基础启发: 大尺寸+横版=高美学
        aesthetic = min(1.0, 0.5 + (w * h) / (1920 * 1080) * 0.3)
        # 锐度 (粗略: JPEG 质量)
        try:
            from PIL.JpegImagePlugin import get_sampling
            sharpness = 0.85 if w * h > 500000 else 0.7
        except Exception:
            sharpness = 0.8
        exposure = 0.8
        is_screenshot = False
        is_blurry = w * h < 100000  # 太小认为是模糊
        is_receipt = 'receipt' in str(path).lower() or 'receipt' in img.format.lower()
        is_landmark = False  # 需要 VLM 判断
        scene_tags = ['outdoor'] if h > w else ['indoor']
        img.close()
        return {
            'aesthetic': round(aesthetic, 2),
            'sharpness': round(sharpness, 2),
            'exposure': round(exposure, 2),
            'is_screenshot': is_screenshot,
            'is_blurry': is_blurry,
            'is_receipt_or_doc': is_receipt,
            'is_landmark': is_landmark,
            'scene_tags': scene_tags,
            '_note': '启发式估算, 生产用 VLM API 替换',
        }
    except Exception:
        return None


def gps_status(gps_dict):
    """GPS 状态: present / stripped / missing"""
    if not gps_dict or 'lat' not in gps_dict:
        return 'missing'
    return 'present'


def smart_category(vlm_score):
    """根据 VLM 评分推断 smart_category"""
    if not vlm_score:
        return 'unknown'
    if vlm_score.get('is_receipt_or_doc'):
        return 'document'
    if vlm_score.get('is_landmark'):
        return 'landmark'
    scene = vlm_score.get('scene_tags', [])
    if 'indoor' in scene:
        return 'restaurant_food' if 'restaurant' in str(scene) else 'indoor'
    return 'outdoor_general'


def extract_and_cache(path):
    """提取并缓存 EXIF + VLM 评分"""
    EXIF_CACHE.mkdir(parents=True, exist_ok=True)
    cache_file = EXIF_CACHE / (path.stem + '.json')

    exif_full = extract_full_exif(path)
    vlm_score = estimate_vlm_score(path)
    gps_st = gps_status(exif_full.get('gps'))
    cat = smart_category(vlm_score)

    result = {
        'source': str(path.name),
        'exif_full': exif_full,
        'vlm_score': vlm_score,
        'gps_status': gps_st,
        'smart_category': cat,
        'extracted_at': datetime.now(timezone(timedelta(hours=8))).isoformat(),
    }
    json.dump(result, open(cache_file, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    return result


def update_inbox_log(result):
    """更新 inbox.json 中对应记录的 4 字段"""
    if not INBOX_LOG.exists():
        return False
    log = json.load(open(INBOX_LOG, encoding='utf-8'))
    name = result['source']
    updated = False
    for p in log['photos']:
        if p.get('original_name') == name:
            p['exif_full'] = result['exif_full']
            p['vlm_score'] = result['vlm_score']
            p['gps_status'] = result['gps_status']
            p['smart_category'] = result['smart_category']
            updated = True
            break
    if updated:
        json.dump(log, open(INBOX_LOG, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    return updated


def cmd_process_files(paths):
    """处理一批文件"""
    results = []
    for p in paths:
        if not Path(p).exists():
            print(f'  ❌ 不存在: {p}')
            continue
        result = extract_and_cache(Path(p))
        updated = update_inbox_log(result)
        results.append((result, updated))
        gps = result['exif_full'].get('gps')
        gps_str = f"({gps['lat']:.4f}, {gps['lon']:.4f})" if gps else 'N/A'
        vlm_a = (result['vlm_score'] or {}).get('aesthetic', 0)
        print(f'  ✅ {Path(p).name[:40]:40s} GPS={gps_str} aesthetic={vlm_a} smart={result["smart_category"]}')
    print(f'\n处理: {len(results)}, inbox 更新: {sum(1 for _, u in results if u)}')


if __name__ == '__main__':
    args = sys.argv[1:]
    if not args:
        print('用法:')
        print('  python skills/_exif_extractor.py photos/<file>.jpg [<file2> ...]')
        print('  python skills/_exif_extractor.py --batch   # 处理 photos/_inbox/ 全部')
        print('  python skills/_exif_extractor.py --all     # 处理 photos/ 全部')
        sys.exit(0)
    if args[0] == '--batch':
        files = sorted(INBOX_DIR.glob('*.jpg')) if INBOX_DIR.exists() else []
        print(f'批量处理 _inbox/: {len(files)} 张')
        cmd_process_files([str(f) for f in files])
    elif args[0] == '--all':
        files = sorted(PHOTOS_DIR.glob('*.jpg'))
        # 过滤 _inbox/ 和 _sq
        files = [f for f in files if '_sq' not in f.stem and '_inbox' not in f.parts]
        print(f'全量处理 photos/: {len(files)} 张 (排除 _sq + _inbox)')
        cmd_process_files([str(f) for f in files])
    else:
        cmd_process_files(args)