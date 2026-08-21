# Changelog

所有显著的变更都会记录在这个文件。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本号遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

## [Unreleased] · 2026-08-21 · v3.8.0 准备

### Planned (基于 4 个 agent 报告, 8-21 拍板)
- **P0-1**: 阶段 5.5 跨币种自动换算 (CNY/USD/EUR/THB + EXCHANGE_RATE_API_KEY)
- **P0-2**: 阶段 8 "自驾均摊" 模式 (油+过路+餐均摊, 车辆归车主)
- **P0-3**: 阶段 9 场景化预算模板 (自驾/亲子/探险/城市 4 套阈值)
- **P1-1**: 阶段 1.5 高速服务区 3 类模板 (油+过路+餐)
- **P1-2**: 阶段 1.5 国外多语种 + VLM 兜底 (英/泰/日/西班牙 + Qwen-VL)
- **P1-3**: 阶段 2 Google Places 备选 (国外场景自动切换)
- **P1-4**: 阶段 6 4 大报告模板 (风景/美食/亲子/探险)
- **P1-5**: 新功能 A 风景文案生成器 (房琪金句模板)
- **P1-6**: 新功能 B 智能筛选 (VLM 评分 必发/备选/删)
- **P1-7**: 新功能 F 场景自动识别 (EXIF+时间+GPS 模式选模板)

详见 `ROADMAP.md` (P0/P1/P2/P3 全部 12 建议 + 6 新功能)。

### Added
- `ROADMAP.md` (4 优先级 + 6 模拟场景 + 时间线 + 借鉴来源)

### Changed
- SKILL.md frontmatter name 改为 `ai-travel-journal (一起旅行 / Travel-Companion)` (跟仓库名一致)
- README.md H1 标题加 GitHub URL 大字号

## [Unreleased] · GitHub 开源准备 (8-20)

### Changed
- 路径统一: 11 个 Python 脚本内部 `脚本/数据/照片` (中文) → `skills/data/photos` (英文), 跟 SKILL/ 子目录现状一致
- README.md: 引用 `高德API-Key.md` → `amap_api_key.example.md`
- SKILL.md: 修正状态自相矛盾 (实际 11 个脚本, 文档旧版写 7 个)

### Added
- `.gitignore` (含 PII 数据 + 真实照片 + API key 文件排除)
- `LICENSE` (MIT)
- `.env.example` (AMAP_KEY / VISION_API_KEY / 阈值, 用户自己配)
- `requirements.txt` (Pillow / piexif / python-dotenv / requests / reportlab / pytest)
- `data/sample_*.json` × 3 (假数据, 全虚构, 别人 clone 能跑演示)
- `tables/sample_expenses.md` (假数据费用表)
- `amap_api_key.example.md` (真 key 占位符, 替代明文 key)
- `data/README.md` (PII 排除说明)
- `archive/README.md` (早期 demo 脚本说明)
- `tests/test_*.py` (2 个 smoke test)

### Removed
- `高德API-Key.md` (重复副本, 内容跟 amap_api_key.md 一字不差, 改用 .gitignore 排除)
- `_make_samples.py` (早期 demo, 跟 v3.7.2 主体不配套, 改用 .gitignore 排除)
- `__pycache__/` (运行时生成, .gitignore 排除)
- 4 个 PII JSON (`journal.json` / `poi_matches.json` / `timeline.json` / `budget.json` / `分账.json` 等, .gitignore 排除)

## [3.7.2] · 2026-08-20 · 当前

### Added
- 11 个 Python 脚本实施 (阶段 0.5+ / 1.5 / 2 / 2.5 / 3 / 5.5 / 6 / 6+ / 8 / 9 + 自动触发)
- 阶段 2.5 3 路交叉验证 (店招 vs POI vs 小票, 行业空白, 自创)
- 阶段 8 AA 智能分账 (5 种类型: AA 1/N / AA 两家 1/2 / 整桌 1 家 / 小孩免票 / 加权)
- 阶段 9 实时预算预警 (4 级: 🟢 健康 / 🟡 接近 / 🟠 超支 / 🔴 警告)
- 借鉴 12 个 GitHub 项目 (EXIF + VLM/OCR + 高德 POI + 学术)

## [3.7.0] · 2026-08-19

### Added
- 阶段 0.5+ EXIF GPS + VLM 美学评分
- 阶段 2 高德 POI 5 维匹配 (距离/名称/类别/评分/营业时间)
- 阶段 2.5 设计 (3 路交叉验证)

## [3.6.0] · 2026-08-18

### Added
- 行程规划 (阶段 7)
- AA 分账 (阶段 8)
- 预算预警 (阶段 9)
- 视觉计数 (阶段 2.7)
- 6 大数据产物 (journal / inbox / poi_matches / budget / 分账 / timeline)

## [3.5.0] · 2026-08-16

### Added
- 阶段 0.5 照片自动落盘 + 编号防混淆
- 阶段 6 HTML/PDF 双格式输出

## [3.0.0] · 2026-08-07

### Added
- 6 阶段工作流 (启动 / 识别 / POI / 追问 / 记录 / 汇总)
- 每轮必问模板 (5 个问题)
- 时间轴设计

[Unreleased]: https://github.com/lujun2508/ai-travel-journal/compare/v3.7.2...HEAD
[3.7.2]: https://github.com/lujun2508/ai-travel-journal/compare/v3.7.0...v3.7.2
