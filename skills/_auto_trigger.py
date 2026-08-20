# -*- coding: utf-8 -*-
"""一起旅行 SKILL · 自动触发主控脚本

监听 data/inbox.json 变化, 自动按链式顺序跑:
  阶段 0.5+ (EXIF) → 阶段 1.5 (OCR 用户配) → 阶段 2 (POI) → 阶段 2.5 (验证) → 阶段 3 (时间轴)
  → 阶段 5 (记录) → 阶段 8 (AA 分账) → 阶段 9 (预算预警) → 阶段 6 (汇总)

触发条件 (自动检测):
  - inbox.json 新增 photo → 阶段 0.5+ 起链
  - journal.json expenses 新增 → 阶段 8 + 9
  - 用户文字 "今天结束" → 阶段 6 汇总
  - 文件系统 _inbox/ 新增 .jpg → 阶段 0.5+ 起链

用法:
  # 前台跑 (实时监控, 一直运行)
  python skills/_auto_trigger.py --watch

  # 单次跑 (处理完队列, 不监控)
  python skills/_auto_trigger.py --once

  # 装 Windows 服务 / systemd
  python skills/_auto_trigger.py --daemon
"""
import sys, os, time, json, hashlib
from pathlib import Path
from datetime import datetime
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, '.')
from skills._exif_extractor import extract_and_cache
from skills._amap_geo_match import match_waypoint
from skills._validator import validate_waypoint
from skills._aa_splitter import split_bill, accumulate_daily
from skills._budget_tracker import check_budget
from skills._timeline import build_timeline
from skills._html_pdf import generate_html, generate_pdf, upload_server

INBOX = Path('data/inbox.json')
JOURNAL = Path('data/journal.json')
INBOX_PHOTOS = Path('photos/_inbox')

# 状态: 跟踪已处理过的图片 (sha256), 避免重复触发
STATE_FILE = Path('data/_auto_trigger_state.json')

DEFAULT_CONFIG = {
    'watch_interval_sec': 5,   # 监控间隔
    'auto_upload': False,        # 自动上传到服务器 (需 SSH 配好)
    'auto_pdf': True,            # 自动生成 PDF
    'auto_summary': True,         # 自动生成 HTML 汇总
    'budget_total': 10000,      # 总预算 (¥
    'people': {'adults': 3, 'kids': 4, 'total': 7},  # 7 人两家人
    'households': 2,
}


def load_state():
    if STATE_FILE.exists():
        return json.load(open(STATE_FILE, encoding='utf-8'))
    return {'processed_photos': [], 'last_journal_hash': '', 'last_check': None}


def save_state(s):
    json.dump(s, open(STATE_FILE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


def journal_hash():
    """journal.json 的 hash, 用于检测内容变化"""
    if not JOURNAL.exists():
        return ''
    return hashlib.md5(open(JOURNAL, 'rb').read()).hexdigest()


def inbox_hash():
    if not INBOX.exists():
        return ''
    return hashlib.md5(open(INBOX, 'rb').read()).hexdigest()


def process_new_photo(photo_record, state):
    """处理一张新照片: 阶段0.5+ → 2 → 2.5"""
    src = photo_record.get('path', '')
    if not src or not Path(src).exists():
        return False
    print(f'\n  📸 新照片: {Path(src).name}')
    # 阶段 0.5+: EXIF + VLM
    exif = extract_and_cache(Path(src))
    print(f'    EXIF GPS: {exif["exif_full"].get("gps")}')
    print(f'    VLM aesthetic: {exif["vlm_score"]["aesthetic"]}')
    print(f'    smart_category: {exif["smart_category"]}')
    # 阶段 2: POI 匹配 (有 GPS 才匹配)
    gps = exif['exif_full'].get('gps')
    if gps:
        wp = {
            'id': photo_record.get('id', ''),
            'place_name': '',
            'lat': gps['lat'],
            'lon': gps['lon'],
            'ocr_result': {'parsed_fields': {'shop_name': ''}},
            'exif_gps': [gps['lon'], gps['lat']],
        }
        result = match_waypoint(wp, use_api=bool(os.environ.get('AMAP_KEY')))
        print(f'    POI 匹配: {result["status"]} / {result.get("poi_match", {}).get("name", "无")}')
        # 阶段 2.5: 交叉验证
        if result.get('poi_match'):
            validation = validate_waypoint({
                'ocr': {'shop_name': wp['place_name']},
                'ocr_receipt': {},
                'poi_match': result['poi_match'],
                'exif_gps': wp['exif_gps'],
                'exif_time': exif['exif_full'].get('datetime_original'),
            })
            print(f'    验证: score={validation["score"]}, risk={validation["risk"]}')
    state['processed_photos'].append(photo_record.get('sha256', ''))
    return True


def check_journal_changes(state):
    """检测 journal.json 新增 → 阶段 5/8/9 触发"""
    cur_hash = journal_hash()
    if cur_hash == state.get('last_journal_hash', ''):
        return
    state['last_journal_hash'] = cur_hash
    if not JOURNAL.exists():
        return
    d = json.load(open(JOURNAL, encoding='utf-8'))
    print(f'\n  📋 journal.json 变化检测 (md5: {cur_hash[:8]})')
    # 阶段 8: AA 分账
    daily_aa = accumulate_daily(d, DEFAULT_CONFIG['people'])
    print(f'    AA 分账: A家 ¥{daily_aa["household_A"]:.2f}, B家 ¥{daily_aa["household_B"]:.2f}')
    # 阶段 9: 预算预警
    budget_status = check_budget(d, DEFAULT_CONFIG['budget_total'])
    print(f'    预算预警: {budget_status["overall_level"]} / 累计 ¥{budget_status["cumulative_actual"]:.2f}')


def check_inbox_changes(state):
    """检测 inbox.json 新增照片"""
    if not INBOX.exists():
        return
    log = json.load(open(INBOX, encoding='utf-8'))
    processed = set(state.get('processed_photos', []))
    new_count = 0
    for p in log.get('photos', []):
        if p.get('sha256') in processed:
            continue
        # 处理新照片
        if process_new_photo(p, state):
            new_count += 1
    if new_count == 0:
        return
    print(f'\n  ✅ 处理了 {new_count} 张新照片')


def check_filesystem_changes(state):
    """检测 _inbox/ 目录新增 .jpg"""
    if not INBOX_PHOTOS.exists():
        return
    current_files = set(f.name for f in INBOX_PHOTOS.glob('*.jpg'))
    if not state.get('known_inbox_files'):
        state['known_inbox_files'] = list(current_files)
        save_state(state)
        return
    new_files = current_files - set(state['known_inbox_files'])
    for fname in new_files:
        path = INBOX_PHOTOS / fname
        print(f'\n  📂 _inbox/ 新文件: {fname}')
        try:
            from skills._inbox import receive_photo
            info = receive_photo(str(path))
            print(f'    落盘: {info["id"]} | EXIF datetime: {info["exif"]["datetime"]}')
        except Exception as e:
            print(f'    [ERR] {e}')
    state['known_inbox_files'] = list(current_files)


def trigger_summary(state):
    """阶段 6: HTML + PDF 汇总"""
    print(f'\n  📄 阶段 6 汇总: 生成 HTML + PDF')
    try:
        generate_html()
        if DEFAULT_CONFIG['auto_pdf']:
            generate_pdf()
        if DEFAULT_CONFIG['auto_upload']:
            upload_server()
        print(f'    ✅ HTML + PDF 已落盘')
    except Exception as e:
        print(f'    [ERR] {e}')


def auto_trigger_text(text, state):
    """文字触发: 检测用户说 "今天结束" / "汇总" / "AA 算一下" 等"""
    text = text.strip().lower()
    triggers = {
        '今天结束': trigger_summary,
        '汇总': trigger_summary,
        '生成报告': trigger_summary,
        'aa算': lambda s: print('  → 阶段 8: AA 分账 (见 console)'),
        '预算': lambda s: print('  → 阶段 9: 预算预警 (见 console)'),
        '下一站': lambda s: print('  → 阶段 7: 行程规划 (见 console)'),
    }
    for key, func in triggers.items():
        if key in text:
            func(state)
            return True
    return False


def run_once():
    """单次跑 (处理完队列, 不监控)"""
    print('=' * 50)
    print('一起旅行 SKILL · 自动触发 · 单次模式')
    print('=' * 50)
    state = load_state()
    print(f'已处理照片: {len(state.get("processed_photos", []))} 张')
    check_inbox_changes(state)
    check_filesystem_changes(state)
    check_journal_changes(state)
    save_state(state)
    print('\n✅ 单次运行完成')


def run_watch():
    """前台实时监控"""
    print('=' * 50)
    print('一起旅行 SKILL · 自动触发 · 监控模式')
    print(f'监控间隔: {DEFAULT_CONFIG["watch_interval_sec"]} 秒')
    print('按 Ctrl+C 停止')
    print('=' * 50)
    state = load_state()
    interval = DEFAULT_CONFIG['watch_interval_sec']
    try:
        while True:
            check_inbox_changes(state)
            check_filesystem_changes(state)
            check_journal_changes(state)
            state['last_check'] = datetime.now().isoformat()
            save_state(state)
            time.sleep(interval)
    except KeyboardInterrupt:
        print('\n⏸  监控停止')


if __name__ == '__main__':
    args = sys.argv[1:]
    if not args or args[0] == '--once':
        run_once()
    elif args[0] == '--watch':
        run_watch()
    elif args[0] == '--daemon':
        print('daemon 模式: TODO - 后台进程')
    elif args[0] == '--text':
        # 文字触发 (供 Claude 调用)
        state = load_state()
        text = ' '.join(args[1:])
        auto_trigger_text(text, state)
        save_state(state)
    else:
        print('用法:')
        print('  python _auto_trigger.py --once       # 单次')
        print('  python _auto_trigger.py --watch      # 前台监控')
        print('  python _auto_trigger.py --daemon     # 后台')
        print('  python _auto_trigger.py --text "今天结束"  # 文字触发')