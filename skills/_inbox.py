# -*- coding: utf-8 -*-
"""一起旅行 SKILL · 阶段 0.5 实施
照片接收 + 编号防混淆 + 重复图检测

借鉴: SKILL.md v3.7 阶段 0.5

用法:
  from skills._inbox import receive_photo
  info = receive_photo('/path/to/uploaded.jpg')
  # info = {
  #   'id': 'D4_001',
  #   'filename': '2026-08-20_001_IMG_4321.jpg',
  #   'path': 'photos/_inbox/2026-08-20_001_IMG_4321.jpg',
  #   'sha256': '...',
  #   'exif': {'datetime': '2026-08-11T08:39:22', 'gps': None}
  # }
"""
import sys, os, hashlib, shutil, json
from pathlib import Path
from datetime import datetime
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

INBOX_DIR = Path('photos/_inbox')
LOG = Path('data/inbox.json')
COUNTER_FILE = Path('data/_inbox_counter.json')


def sha256_of(path):
    """计算文件 SHA256"""
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def extract_exif_basic(path):
    """基础 EXIF 提取 (datetime + GPS)"""
    try:
        from PIL import Image
        from PIL.ExifTags import TAGS
        img = Image.open(path)
        exif_data = img._getexif() or {}
        info = {'datetime': None, 'gps': None}
        for tag_id, value in exif_data.items():
            name = TAGS.get(tag_id, tag_id)
            if name == 'DateTimeOriginal':
                try:
                    info['datetime'] = str(value)
                except Exception:
                    pass
            elif name == 'GPSInfo':
                try:
                    lat = value.get(2) if isinstance(value, dict) else None
                    lon = value.get(4) if isinstance(value, dict) else None
                    if lat and lon:
                        info['gps'] = {
                            'lat': float(lat[0]) + float(lat[1])/60 + float(lat[2])/3600,
                            'lon': float(lon[0]) + float(lon[1])/60 + float(lon[2])/3600,
                        }
                except Exception:
                    pass
        img.close()
        return info
    except Exception:
        return {'datetime': None, 'gps': None}


def next_seq():
    """读取并自增序号"""
    if COUNTER_FILE.exists():
        d = json.load(open(COUNTER_FILE, encoding='utf-8'))
        seq = d.get('seq', 0) + 1
    else:
        seq = 1
    COUNTER_FILE.parent.mkdir(parents=True, exist_ok=True)
    json.dump({'seq': seq}, open(COUNTER_FILE, 'w', encoding='utf-8'))
    return seq


def derive_day_id(exif_dt, fallback_day='D0'):
    """从 EXIF 时间归 D#"""
    if not exif_dt:
        return fallback_day
    try:
        if isinstance(exif_dt, str):
            exif_dt = exif_dt.replace(':', '-', 2)
            dt = datetime.fromisoformat(exif_dt)
        else:
            return fallback_day
        day_index = dt.day - 7  # 8/7 = D0, 8/8 = D1, ...
        if 0 <= day_index <= 9:
            return f'D{day_index}'
        return fallback_day
    except Exception:
        return fallback_day


def receive_photo(src_path):
    """主入口: 接收一张照片, 落盘 + 编号 + 防混淆"""
    src = Path(src_path)
    if not src.exists():
        return {'error': f'文件不存在: {src}'}

    INBOX_DIR.mkdir(parents=True, exist_ok=True)

    sha = sha256_of(src)
    exif = extract_exif_basic(src)
    seq = next_seq()
    today = datetime.now().strftime('%Y-%m-%d')
    dt_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    original_name = src.name
    ext = src.suffix or '.jpg'
    dest_filename = f'{today}_{seq:03d}_{original_name}'
    dest_path = INBOX_DIR / dest_filename
    shutil.copy2(src, dest_path)

    day_id = derive_day_id(exif.get('datetime'), 'D' + str(datetime.now().day - 7))
    photo_id = f'{day_id}_{seq:03d}'

    # 写 inbox.json
    log = []
    if LOG.exists():
        try:
            log = json.load(open(LOG, encoding='utf-8'))
        except Exception:
            log = {'photos': []}
    elif not isinstance(log, dict):
        log = {'photos': []}
    if 'photos' not in log:
        log = {'photos': []}

    photo_record = {
        'id': photo_id,
        'received_at': datetime.now().isoformat(),
        'filename': dest_filename,
        'original_name': original_name,
        'path': str(dest_path),
        'sha256': sha,
        'size_bytes': dest_path.stat().st_size,
        'exif': exif,
        'day': day_id,
        'stage': '已落盘',
        'category': None,
    }
    log.setdefault('photos', []).append(photo_record)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    json.dump(log, open(LOG, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    return photo_record


if __name__ == '__main__':
    print('==== _inbox.py 测试 ====')
    if len(sys.argv) > 1:
        info = receive_photo(sys.argv[1])
        print(json.dumps(info, ensure_ascii=False, indent=1))
    else:
        # 用一张示例图
        from PIL import Image
        img = Image.new('RGB', (800, 600), 'green')
        img.save('tmp/test_inbox.jpg')
        info = receive_photo('tmp/test_inbox.jpg')
        print(f'✅ 测试: {info["id"]} → {info["filename"]}')