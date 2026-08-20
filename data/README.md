# data/ · 数据目录

> ⚠️ **本目录的"真实"JSON 文件含 PII, 已加入 `.gitignore` 不会上传**
> 上传的只有 3 个 `sample_*.json` 假数据 (示例, 全虚构)

## 已上传 (4 个 sample)

| 文件 | 大小 | 用途 |
|---|---:|---|
| `sample_inbox.json` | 0.7 KB | 演示 inbox 结构 (1 张测试图, 英文 path) |
| `sample_journal.json` | 2.0 KB | 演示 journal 结构 (3 waypoint, 全虚构) |
| `sample_poi_matches.json` | 1.4 KB | 演示 POI 匹配结构 (mock 标记 `_mock: true`) |
| `sample_timeline.json` | 1.2 KB | 演示时间轴结构 (4 events) |

实际使用: 用户跑 SKILL 后, 自动生成自己的 `inbox.json` / `journal.json` / `poi_matches.json` / `timeline.json` (本地, 不会上传)。

## 不上传 (.gitignore 排除)

| 文件 | 原因 |
|---|---|
| `journal.json` | 真实家庭住址 + GPS 轨迹 + 消费 (PII) |
| `poi_matches.json` | 真实 POI + GPS (PII) |
| `timeline.json` | 真实时间地点 (PII) |
| `budget.json` | 真实家庭 AA 消费 (隐私) |
| `分账.json` | 真实家庭 AA 消费 (隐私) |
| `inbox.json` | 路径含中文 `照片\_inbox` (跟框架英文 `photos/_inbox` 不符) |
| `_auto_trigger_state.json` | 真实状态 (含 sha256 + 路径) |
| `exif_cache/` | 真实 EXIF 数据 (PII) |

## 为什么

SKILL 借鉴自真实 9 日自驾游项目 (东阳⇄西安, 2026-08-07~16), 真实数据含:
- 家庭住址 (浙江省东阳市白云街道兴平西路428号)
- 9 天 GPS 轨迹 (71 个 waypoint)
- 70 笔消费 (¥7,530.78)
- 小孩免票记录 (16 周岁以下 × ¥0)
- 542 张真实照片 (含小孩面部)

这些数据**不适合公开**, 但数据结构 + 模式适合开源。

## 重新生成

```bash
# 1. 配置 .env (从 .env.example 复制, 填入真 key)
cp .env.example .env

# 2. 跑 SKILL 全流程 (会生成你自己的真实数据)
python skills/_auto_trigger.py --once
```

输出 `journal.json` / `poi_matches.json` / `timeline.json` / `budget.json` / `分账.json` 等, **全部本地, 不会上传**。
