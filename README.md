# 一起旅行 (Travel-Companion)

> 旅行途中, 用户发 1 张照片, AI 自动落盘 + 追问 + EXIF/GPS + POI 匹配 + 交叉验证 + AA 分账 + 预算预警 + HTML/PDF 汇总

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](requirements.txt)
[![Code style: PEP 8](https://img.shields.io/badge/code%20style-PEP%208-orange.svg)](https://peps.python.org/pep-0008/)

## ✨ 这是什么

**旅行伴侣 AI Skill** — 13 阶段工作流, 从用户发照片到出 PDF 旅行总结, 全自动:

```
用户发 1 张照片
   ↓
[阶段 0.5]   落盘 + 编号防混淆 + 重复图检测
[阶段 0.5+]  EXIF GPS + VLM 美学评分 (用户配 VLM)
[阶段 2]     EXIF GPS → 高德 reverse_geocode + POI 5 维评分
[阶段 2.5]   店招 vs POI vs 小票 3 路交叉验证 (行业空白, 自创)
[阶段 3]     时间轴 (256 条)
[阶段 5.5]   实时预算预警 (4 级)
[阶段 6]     HTML + PDF 双格式汇总
[阶段 8]     AA 智能分账 (5 种类型)
[阶段 9]     累计看板 + 预算预警
   ↓
输出: HTML 网页 + PDF 汇总 + JSON 数据 + Markdown 笔记
```

## 📦 包含什么

- **11 个 Python 脚本** (~125 KB, 阶段 0.5+ → 9 + 自动触发)
- **SKILL.md** (~67 KB, 完整设计文档 v3.7.2)
- **3 个 sample 假数据** (别人 clone 下来能跑演示)
- **.env.example** (用户自己配 AMAP_KEY + VISION_API_KEY)
- **tests/** (smoke test)
- **archive/** (早期 demo, 历史参考)

## 🚀 快速开始 (5 分钟)

### 1. 安装

```bash
git clone https://github.com/lujun2508/ai-travel-journal.git
cd travel-companion
pip install -r requirements.txt
```

### 2. 配置

```bash
# 复制 env 模板
cp .env.example .env

# 编辑 .env, 填入两个 key:
#   AMAP_KEY        — https://lbs.amap.com/dev/key/app
#   VISION_API_KEY  — https://dashscope.console.aliyun.com/apiKey (或任何 OpenAI 兼容 VLM)
```

### 3. 跑演示

```bash
# 用 sample 假数据跑一次 (不需要任何 key)
python skills/_auto_trigger.py --once

# 前台实时监控 (5 秒间隔)
python skills/_auto_trigger.py --watch

# 单阶段触发 (供 AI 调用)
python skills/_auto_trigger.py --text "今天结束"
```

## 🧭 SKILL 13 阶段

| 阶段 | 名称 | 状态 | 脚本 |
|---|---|---|---|
| 0 | YAML Frontmatter | ✅ | (文档) |
| 0.5 | 照片接收 + 编号防混淆 | ✅ | `skills/_inbox.py` |
| 0.5+ | EXIF GPS + VLM 美学 | ✅ | `skills/_exif_extractor.py` |
| 1 | 启动 - 4 种保存方式 | ✅ | (流程) |
| 1.5 | 店招/菜品/小票 (用户配) | 📝 | 用户自配 (OCR 让用户自选) |
| 2 | EXIF GPS → 高德 POI | ✅ | `skills/_amap_geo_match.py` |
| 2.5 | 3 路交叉验证 + 风险 | ✅ | `skills/_validator.py` |
| 2.7 | 通过照片分析人数 | 📝 | 用户配 VLM |
| 3 | 时间轴 | ✅ | `skills/_timeline.py` |
| 4 | 追问 (每轮必问 5 个) | ✅ | (流程) |
| 5 | 记录 + 时间轴汇总 | ✅ | (流程) |
| 5.5 | 实时预算预警 | ✅ | `skills/_budget_tracker.py` |
| 6 | HTML+PDF 双格式 | ✅ | `skills/_html_pdf.py` |
| 6+ | 验证报告面板 | ✅ | `skills/_validator.py` |
| 7 | 行程规划与推荐 | ✅ | (流程) |
| 8 | 多人 AA 智能分账 | ✅ | `skills/_aa_splitter.py` |
| 9 | 实时预算预警 + 看板 | ✅ | `skills/_budget_tracker.py` |
| (auto) | 自动触发主控 | ✅ | `skills/_auto_trigger.py` |

## 🏗️ 目录结构

```
travel-companion/
├── SKILL.md                   # 完整设计文档 v3.7.2 (1851 行)
├── README.md                  # 本文件
├── CHANGELOG.md               # 版本历史
├── LICENSE                    # MIT
├── .gitignore                 # PII + 真实数据 + API key 排除
├── .env.example               # 用户自己配 AMAP_KEY / VISION_API_KEY
├── requirements.txt           # Pillow / piexif / python-dotenv / ...
├── amap_api_key.example.md    # 高德 key 占位符说明
├── data/                      # 真实数据 .gitignore 排除 + 3 个 sample 假数据
│   ├── README.md
│   ├── sample_journal.json
│   ├── sample_poi_matches.json
│   └── sample_timeline.json
├── tables/
│   └── sample_expenses.md     # 假数据费用表
├── skills/                    # 11 个 Python 脚本
│   ├── _auto_trigger.py       ⭐ 主控: --once/--watch/--text
│   ├── _inbox.py              阶段 0.5
│   ├── _exif_extractor.py     阶段 0.5+
│   ├── _amap_geo_match.py     阶段 2
│   ├── _validator.py          阶段 2.5 (3 路交叉验证, 自创)
│   ├── _timeline.py           阶段 3
│   ├── _budget_tracker.py     阶段 5.5 / 9
│   ├── _aa_splitter.py        阶段 8 (5 种分账)
│   ├── _html_pdf.py           阶段 6
│   ├── _make_index_v5.py      网页生成器
│   └── _make_samples.py       (历史 demo, 已 archive 排除)
├── archive/                   # 历史脚本
│   ├── README.md
│   └── _make_samples.py
└── tests/                     # 单元测试
    ├── test_validator.py
    └── test_aa_splitter.py
```

## 🔑 关键设计: OCR 让用户自配

阶段 1.5 (店招/菜品/小票 OCR) **不写 OCR 脚本**, 让用户按需 4 选 1:

| 方案 | 安装 | 离线? | 推荐 |
|---|---|---|---|
| **A. VLM API** | `VISION_API_KEY=xxx` | ❌ | ⭐ (中文强, 一调用解决) |
| **B. PaddleOCR** | `pip install paddleocr` | ✅ | 中文场景 |
| **C. Tesseract** | 下载 `chi_sim.traineddata` | ✅ | 简单场景 |
| **D. RapidOCR** | `pip install rapidocr_onnxruntime` | ✅ | 轻量 |

详见 [SKILL.md §阶段 1.5](SKILL.md#阶段-15-店招菜品小票ocr-用户配)。

## 🎯 阶段 2.5: 3 路交叉验证 (独家, 自创)

行业空白: 旅行照片场景下, 同时验证 3 个独立来源互相佐证:

```
输入: 1 张照片 (EXIF GPS + 店招 OCR + 小票 OCR)
   ↓
路 1: 店招 OCR (text)     ──┐
路 2: 高德 POI (API)       ─┼─→ 5 维评分 + 风险判定
路 3: 小票 OCR (text)     ──┘
   ↓
输出: confidence 0-1 + risk (low/medium/high) + issues 列表
```

详见 [SKILL.md §阶段 2.5+](SKILL.md#阶段-25-交叉验证-行业空白-自创-)。

## 🙏 借鉴开源项目 (12 个 GitHub)

- **EXIF**: `jaxx2104/exiftool-skill`, `majiayu000/image-metadata-tool`, `photo-cli/photo-cli`
- **VLM/OCR**: `aAAaqwq/AGI-Super-Team/image-vision`, `4399dw/image-vision-skill`, `opencr-skill`, `hzydy00/qwen-vision`, `DYAI2025/Simavi`
- **高德 POI**: `AMap-Web/amap-skills` (官方)
- **学术**: `GLOBE` (NeurIPS 2025)

## 📜 License

[MIT](LICENSE) © 2026 陆雋 (Lu Jun) / 木铭建材 (Muming Building Materials)

## 📞 联系方式

- 项目: 木铭建材 — https://mumingbuild.cn
- Issues: GitHub Issues
- Email: (见 GitHub profile)

---

**真实案例**: 2026-08-07~16 东阳⇄西安 9 日自驾美食游, 7 人 2 家, 5400+ km, ¥7,530.78, 71 个 waypoint, 256 条时间轴事件。完整数据仅作者本地保留 (PII), 此仓库只含框架 + 假数据。
