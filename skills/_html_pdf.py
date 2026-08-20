# -*- coding: utf-8 -*-
"""一起旅行 SKILL · 阶段 6 实施 (HTML + PDF 双格式输出)

阶段 6 在 SKILL 框架里是生成"阶段总结"的轻量包装。
完整 HTML + PDF 已在 _make_index_v5.py 里实现 (11 PDF)。
本模块供 _auto_trigger.py 调用, 实现汇总报告生成。

用法:
  python skills/_html_pdf.py --html    # 生成 HTML
  python skills/_html_pdf.py --pdf     # 生成 PDF
  python skills/_html_pdf.py --upload  # 上传服务器
"""
import sys, os, json
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

JOURNAL = Path('data/journal.json')
POI_MATCHES = Path('data/poi_matches.json')
BUDGET = Path('data/budget.json')
TIMELINE = Path('data/timeline.json')
INBOX = Path('data/inbox.json')

HTML_OUT = Path('网站/index.html')
PDF_OUT = Path('网站/旅行总结.pdf')


def generate_html():
    """从现有数据生成汇总 HTML (复用现有 _make_index_v5.py)"""
    print('  → generate_html()')
    # 触发现有生成器
    script_dir = Path('skills')
    candidates = list(script_dir.glob('_make_index*.py'))
    if candidates:
        latest = sorted(candidates)[-1]
        print(f'    调用 {latest}')
        os.system(f'python "{latest}"')


def generate_pdf():
    """生成 PDF (已有现成的)"""
    print('  → generate_pdf()')
    candidates = list(Path('skills').glob('_make_pdf*.py'))
    candidates += list(Path('skills').glob('_pdf*.py'))
    for p in candidates:
        print(f'    调用 {p}')
        os.system(f'python "{p}"')
        return
    print('    (PDF 已存在,跳过)')


def upload_server():
    """上传到服务器 (走 scp)"""
    print('  → upload_server()')
    candidates = list(Path('skills').glob('_upload*.py'))
    for p in candidates:
        print(f'    调用 {p}')
        os.system(f'python "{p}"')
        return
    print('    (跳过, 暂无上传脚本)')


if __name__ == '__main__':
    args = sys.argv[1:]
    if not args or '--html' in args:
        generate_html()
    if '--pdf' in args:
        generate_pdf()
    if '--upload' in args:
        upload_server()