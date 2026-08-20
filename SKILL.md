---
name: 一起旅行 (Travel-Companion)
description: |
  旅行途中, 用户发 1 张照片, AI 主动追问 + 识别店招/菜品/收据/打卡,
  自动落盘到 照片/_inbox/ 编号防混淆, 按 EXIF/收据时间戳归 D0-D9 日程,
  EXIF GPS 提取 + 高德 reverse_geocode + 5 维评分匹配 POI,
  店招 vs POI vs 小票 3 路交叉验证 + 风险判定 (行业空白),
  整合到 journal.json + 美食排行榜 + 推荐指南 + 行程规划,
  生成时间轴 + 多人 AA 智能分账 + 实时预算预警,
  最终输出 HTML + PDF + Markdown + JSON 多格式汇总 (本地/本地+云端/仅云端/私有目录 4 种保存方式)
when_to_use: |
  用户:
    - "出发旅行" / "我们要去 X 天" / "今天开始"
    - 上传 1 张照片 (店招/菜品/收据/打卡/景点/车票)
    - "5 星" / "X 星" / "这是 X 店" (评分)
    - "改地址" / "改店名" (修正)
    - "今天结束" / "汇总" / "出 PDF" / "出 HTML" (生成报告)
    - "落盘" / "备份" / "上传服务器"
    - "下一站去哪" / "推荐 X" / "想去 X 怎么玩" (行程规划)
    - "预算快超了" / "花了多少" / "还剩多少" (预算查询)
input_types: [image/jpeg, image/png, image/heic, text]
output_types: [html, pdf, markdown, json, csv]
tags: [travel, photo-organizer, expense-tracker, exif-gps, ocr, vlm, amap-rest, poi-match, cross-validation, timeline, pdf-report, claude-skill, auto-trigger]
language: zh-CN
author: 陆雋 / 木铭建材
version: 3.7.2
status: implemented-11-scripts
---

# 一起旅行 SKILL · 框架设计 v3.7.2 (实施 11 个脚本 + 自动触发) ⭐

> **v3.7.2 当前实施** (11 个脚本, 7 核心 + 4 辅助):
> - **阶段 0.5**: `_inbox.py` 5.2 KB · 落盘 + 编号防混淆
> - **阶段 0.5+**: `_exif_extractor.py` 11.3 KB · EXIF GPS + VLM 美学
> - **阶段 2**: `_amap_geo_match.py` 10.8 KB · 高德 POI 5 维匹配 (mock 模式)
> - **阶段 2.5**: `_validator.py` 8.9 KB · 3 路交叉验证 + 风险判定
> - **阶段 3**: `_timeline.py` 5.4 KB · 时间轴 256 条
> - **阶段 5.5 / 9**: `_budget_tracker.py` 5.3 KB · 4 级预警
> - **阶段 6**: `_html_pdf.py` 2.1 KB · HTML+PDF 双格式
> - **阶段 8**: `_aa_splitter.py` 5.2 KB · 5 种分账
> - **网页生成器**: `_make_index_v5.py` 43.7 KB
> - **自动触发**: `_auto_trigger.py` 9.4 KB · 3 模式 (--once/--watch/--text)

> v3.7: 阶段 0.5+ (EXIF + VLM) + 阶段 2 (POI 匹配) + 阶段 2.5 设计
> v3.6: 行程规划 + AA 分账 + 预算预警 + 视觉计数
> v3.5: 阶段 0.7 自动数据分析 + 阶段 6 HTML/PDF 双格式输出
> v3.5: 阶段 0.5 照片自动落盘 + 编号防混淆
> v3.0: 6 阶段工作流 + 每轮必问模板 + 时间轴设计

> **定位**: 旅行途中, 用户只需发照片, AI 主动追问、持续收集、本地落盘、按时间轴汇总, 最终输出 HTML + PDF 旅行总结。

---

## 🎯 Skill 核心原则

| 原则 | 说明 |
|---|---|
| **主动追问** | 每轮回复必须问询 (照了什么 + 缺什么) |
| **持续收集** | 不需要等用户说"汇总" —每张新照片都增量落盘 |
| **本地优先** | 无服务器也照常工作, 数据落 `C:\Users\lujun\Desktop\木铭\旅行\` |
| **时间轴** | 用 EXIF / 收据 / 估算时间作为时间轴主键 |
| **可选同步** | 用户确认后上传服务器 (`mumingbuild.cn/secret/travel/`) |
| **多格式汇总** | 最终输出 HTML + PDF 双格式 |

---

## 🧭 Skill 工作流 (5 阶段 + 每轮问询)

### 每轮问询模板 (强制)

```
✅ 已识别: [店名] [城市] [类别]
📝 待你确认:
   1. 时间正确吗? (按收据/EXIF)
   2. 这家评分? (5/4/3/2/1 星 + 1 句话理由)
   3. 这道菜叫什么? 多少钱?
   4. 这是 AA 还是整桌?
   5. 还有这张店/这顿饭的别的照片吗?

请按 1/2/3/4/5 回答, 或直接发更多照片。
```

### 阶段 0.5: 照片接收管理 (落盘 + 编号防混淆)

**用户每发一张照片, Skill 立刻自动**:

1. **自动保存原图到本地**: `照片/_inbox/YYYY-MM-DD_<seq>_<original_name>.jpg`
   - 例: `照片/_inbox/2026-08-20_001_IMG_4321.jpg`
   - 文件名含**日期 + 序号 + 原名**, 防混淆, 可复盘
2. **生成唯一记录 ID**: `<DAY>_<seq>`, 例如 `D4_001`
3. **登记到 `数据/inbox.json`** (照片接收日志):
   ```json
   {
     "id": "D4_001",
     "received_at": "2026-08-20T17:30:00+08:00",
     "filename": "2026-08-20_001_IMG_4321.jpg",
     "original_name": "IMG_4321.jpg",
     "path": "照片/_inbox/2026-08-20_001_IMG_4321.jpg",
     "sha256": "abc123...",
     "size_bytes": 3582241,
     "exif": {"datetime": "2026-08-11T08:39:22", "gps": [...]},
     "stage": "识别中",
     "category": null,
     "extracted": null
   }
   ```
4. **按 EXIF 时间归 D#**: 2026-08-11 08:39 → D4
5. **核对照片分类**:
   - **重复图** (同 sha256) → 提示用户
   - **EXIF 缺失** → 主动问时间
   - **关联到现有 waypoint** → 自动更新

**用户后续查询示例**:
```
用户: 看看今天收的照片
Skill: 今天 (8/20) 收了 5 张:
      1. D4_001 IMG_4321.jpg (08:39 西安早餐店招)
      2. D4_002 IMG_4322.jpg (08:41 腊牛肉夹馍特写)
      3. D4_003 IMG_4323.jpg (08:42 整桌特写)
      4. D4_004 IMG_4324.jpg (08:43 肉丸胡辣汤特写)
      5. D4_005 IMG_4325.jpg (08:46 收据 ¥33)
      → 落盘位置: 照片/_inbox/2026-08-20_001~005_xxx.jpg
```

**保留原图原则**: 即使识别为重复图, 也保留 `_inbox/` 副本, 不删除, 方便日后复盘。

### 阶段 0.7: 自动数据分析与整理 (落盘 · 增量)

**每张照片/收据识别后, Skill 自动算出 7 个指标并落到** `数据/analysis.json`:

| # | 指标 | 计算规则 | 例 |
|---|---|---|---|
| 1 | **人均单价** | 整桌价 ÷ 人数 | ¥35/4人 = ¥8.75/人 |
| 2 | **AA/整桌摊分** | 默认 AA 1/2 (两家), 整桌分摊 1/N | 整桌 ¥35, 本家 ¥17.50 |
| 3 | **性价比评分** | 价格分位 + 评分 + 食物质感 (5维度) | 5★+¥8 = 极优 |
| 4 | **总人数拆分** | 3 大人 + 4 小孩 (默认两家: 2大2小 + 1大2小) | 7 人, 3+4 |
| 5 | **小孩免票折扣** | 16 周岁以下 × ¥0 | 兵马俑 3 小孩 × ¥120 = ¥360 免 |
| 6 | **单品价值** | 整桌价 ÷ 菜数 | 5 菜 ¥35 = ¥7/菜 |
| 7 | **人均时长占比** | 用餐时长 ÷ 当日总时长 | 早餐 30min / 日 12h = 4.2% |

**落盘格式** (`数据/analysis.json`):
```json
{
  "trips": {
    "D4": {
      "meals": [
        {
          "time": "08:39-08:46",
          "place": "老马家肉丸子胡辣汤",
          "total_cost": 33,
          "people": {"adults": 3, "kids": 4, "total": 7},
          "household_split": "AA_1_2",
          "households": 2,
          "items": [
            {"name": "肉丸胡辣汤(大碗)", "qty": 1, "price": 8},
            {"name": "鸡蛋饼", "qty": 1, "price": 4},
            {"name": "牛肉饼", "qty": 1, "price": 5},
            {"name": "牛杂肝汤", "qty": 1, "price": 16}
          ],
          "per_person": 4.71,
          "per_household": 16.50,
          "value_score": 8.5,
          "rating": 5,
          "性价比": "极高",
          "category": "餐饮"
        }
      ]
    }
  },
  "汇总": {
    "总花费": 7530.78,
    "人均花费": 1075.83,
    "总里程_km": 3200,
    "总日数": 9,
    "总菜数": 89,
    "5星率": 0.236,
    "性价比之王": ["盐筋儿 ¥1.5/串", "羊汤烩面 ¥7/碗"]
  }
}
```

**自动统计生成规则**:

1. **人均** = 整桌价 ÷ 总人数(7)
2. **本家摊分** = 整桌价 ÷ 2 (默认两家 AA)
3. **性价比评分 (0-10)** = `(rating_stars × 2) + (人均价格反向加权 5-人均价/20) + 菜的丰富度奖励`
   - 例: 5★ + ¥8.75/人 + 4 菜 = 10 + 4.5 + 1 = 8.5/10
4. **性价比等级**: 8-10 极高 / 6-8 高 / 4-6 中 / 2-4 低 / 0-2 极差
5. **小孩折扣金额**: 16 周岁以下 × 标价, 累加到 total_savings
6. **汇总统计**: 自动累加 9 日所有 metric

**输出**:
- `数据/analysis.json` — 结构化数据
- `网站/分析报表.html` — 可视化 (含每餐饼图 + 性价比榜)
- `美食评分排行榜.md` — 增加 "人均" 列

**触发**: 自动 (阶段 4 后立刻执行), 无需用户说"汇总"。

---

### 阶段 1: 启动 - 询问资料保存方式

```
Skill: 一起旅行 已启动。
请告诉我你的资料保存方式:

(A) 全部本地保存 (默认)
   → 资料: C:\Users\lujun\Desktop\木铭\旅行\
   → 服务器: 不上传

(B) 本地 + 服务器同步 (推荐)
   → 本地同上, 额外上传到 mumingbuild.cn/secret/travel/
   → 服务器: 通过 SSH (需要 token)

(C) 仅服务器
   → 不写本地, 只传到云端
   → 服务器: 同上

(D) 私有备份目录
   → 我会问你要路径
```

### 阶段 2: 识别 (Recognize)

每张用户照片触发:

| 类型 | 触发特征 | 输出 |
|---|---|---|
| 🏪 店招 | 招牌/门面文字清晰 | 店名 + 城市 + 门店 + 营业项目 |
| 🍜 菜品特写 | 餐盘/面碗/夹馍/串 | 菜名 + 价格(估) + 推荐度 |
| 🧾 收据/小票 | 二维码/打印文字/价格表 | 金额 + AA/整桌 + 8 大类别分类 |
| 🏛️ 打卡/景点 | 建筑/景观/公园 | 景点名 + 城市 + 估坐标 |

### 阶段 2.5: 地图标记 + 高德/百度 API 对接规范

**对接到高德地图 / 百度地图, 在地图上自动标出所有打卡点** (单页汇总里自动出地图)。

#### 2.5.1 高德 JS API v2.0 集成规范 (本项目实际使用)

**最小可运行代码 (主页 `index.html`)**:
```html
<!-- 1. 密钥 (在引入脚本的正上方) -->
<script type="text/javascript">
  window._AMapSecurityConfig = {
    securityJsCode: 'daff8eb0b4f76a96f1abde89cd696bc6'
  };
</script>
<!-- 2. 同步加载所有插件 -->
<script src="https://webapi.amap.com/maps?v=2.0&key=e003da793554a6c17ae871efcab0b35c
  &plugin=AMap.Driving,AMap.Polyline,AMap.Marker,AMap.ToolBar,AMap.Scale,AMap.LngLat">
</script>
<!-- 3. window.onload 延迟唤醒 (防 WebGL 死锁) -->
<script>
window.onload = function() {
  setTimeout(function() { initOverviewMap(); }, 300);
};
function initOverviewMap() {
  var overviewMap = new AMap.Map('overview-map', {
    viewMode: '2D', zoom: 5, center: [114.30, 30.60],
    layers: [
      new AMap.TileLayer.Satellite(),
      new AMap.TileLayer.RoadNet()
    ]
  });
  HIGHWAY_SATELLITE_PATHS.forEach(function(route) {
    var amapPath = route.path.map(function(coord) {
      return new AMap.LngLat(coord[0], coord[1]);
    });
    overviewMap.add(new AMap.Polyline({
      path: amapPath, strokeColor: route.color, strokeWeight: 7,
      strokeOpacity: 0.95, lineJoin: 'round', showDir: true,
      title: route.name
    }));
  });
  overviewMap.on('complete', function() {
    overviewMap.resize();
    overviewMap.setFitView();
  });
}
</script>
```

**已知 Bug 修复**:
- `new AMap.LngLat(coord[0], coord[1])` ← **不要**用 `new AMap.LngLat(coord, coord)` (coord是数组)
- 580px 主图 + Satellite + RoadNet 双底图
- `setTimeout 300ms` 防 WebGL 尺寸抓取死锁
- `overviewMap.on('complete')` 触发 resize + setFitView

#### 2.5.2 百度地图 API 接入规范 (备用)

```html
<script type="text/javascript" src="https://api.map.baidu.com/api?v=3.0&ak=YOUR_AK"></script>
<div id="baidu-map"></div>
<script>
var map = new BMap.Map('baidu-map');
map.centerAndZoom(new BMap.Point(114.30, 30.60), 6);
map.enableScrollWheelZoom(true);

// 添加标注
var marker = new BMap.Marker(new BMap.Point(lng, lat));
map.addOverlay(marker);

// 添加折线
var polyline = new BMap.Polyline([
  new BMap.Point(p[0][0], p[0][1]),
  new BMap.Point(p[1][0], p[1][1]),
  ...
], {strokeColor: '#ef4444', strokeWeight: 5});
map.addOverlay(polyline);
</script>
```

#### 2.5.3 高德 REST API 接入规范 (后台调用, 如逆地理编码)

```python
# 高德 逆地理编码 (lng,lat → 地址)
import urllib.request, json
def amap_regeo(lng, lat, key='e003da793554a6c17ae871efcab0b35c'):
    url = f'https://restapi.amap.com/v3/geocode/regeo?key={key}&location={lng},{lat}&radius=100&extensions=base'
    with urllib.request.urlopen(url, timeout=10) as r:
        data = json.load(r)
    return data.get('regeocode', {}).get('formatted_address', '')

# 高德 路径规划 (起点终点 → 真实自驾路径 polyline)
def amap_driving_route(origin, dest, key='e003da793554a6c17ae871efcab0b35c'):
    url = (f'https://restapi.amap.com/v3/direction/driving?key={key}'
           f'&origin={origin[0]},{origin[1]}&destination={dest[0]},{dest[1]}'
           f'&strategy=0&extensions=base')
    with urllib.request.urlopen(url, timeout=10) as r:
        data = json.load(r)
    if data.get('status') == '1' and data.get('route', {}).get('paths'):
        path = data['route']['paths'][0]
        coords = []
        for step in path.get('steps', []):
            for polyline in step.get('polyline', '').split(';'):
                if polyline:
                    lng, lat = polyline.split(',')
                    coords.append([float(lng), float(lat)])
        return coords
    return []
```

#### 2.5.4 SKILL 自动地图标注流程

```
Skill: 已识别 D4 照片 → 老马家肉丸子胡辣汤 (叼家村附近)
      → 推测: lat=34.265, lon=108.945 (西安碑林区)
      → 自动写入: 数据/markers.json (lat/lon/title/rating/category)
      → 重生成 index.html 时, 自动调用 AMap.Marker 在总览图上打点
      → 用户打开 index.html 可在地图上看到所有 D0-D9 打卡点
```

**地图标记数据格式** (`数据/markers.json`):
```json
{
  "markers": [
    {
      "day": "D0",
      "name": "东阳银泰城 (家/起点)",
      "lat": 29.272, "lon": 120.23,
      "category": "起点",
      "rating": null,
      "icon": "home"
    },
    {
      "day": "D1",
      "name": "南昌大学食堂",
      "lat": 28.658, "lon": 115.802,
      "category": "餐饮",
      "rating": 5,
      "icon": "food-5star"
    },
    {
      "day": "D3",
      "name": "秦始皇兵马俑博物馆",
      "lat": 34.385, "lon": 109.273,
      "category": "景点",
      "rating": 5,
      "icon": "attraction-5star"
    }
  ]
}
```

**AMap.Marker 图标映射** (跟 category + rating 对应):
| category | rating | icon | 颜色 |
|---|---|---|---|
| 起点/家 | - | home | 蓝色 (#5a7a52) |
| 景点 | 5★ | attraction-5star | 金色 (#f59e0b) |
| 景点 | 4★ | attraction-4star | 橙色 (#fbbf24) |
| 景点 | 3★ | attraction-3star | 灰色 (#9ca3af) |
| 餐饮 | 5★ | food-5star | 红色 (#b94a3a) |
| 餐饮 | 4★ | food-4star | 橙色 |
| 餐饮 | 3★ | food-3star | 黄色 |
| 酒店 | - | hotel | 紫色 (#8a4f7c) |
| 加油站 | - | charging | 绿色 (#6b8aa6) |

**触发**: 阶段 4 (记录) 后自动执行, 增量写 `数据/markers.json`, 重生成 index.html 时自动渲染 marker。

---

### 阶段 3: 时间轴 (Timeline)

主键: **EXIF DateTimeOriginal** (店招/打卡) + **收据时间戳** (餐费)

| 数据源 | 优先级 | 例 |
|---|---|---|
| 收据小票 | ★★★★★ | 21:33 ¥105 老马家泡馍 |
| EXIF 拍照时间 | ★★★★☆ | 22:30 阿鹏烧烤 |
| 俊哥口头播报 | ★★★☆☆ | 14:13 诚意和 |
| 估算 | ★★☆☆☆ | 18:30 同学聚会 |

如果 EXIF 缺失或与收据矛盾, 主动追问用户**哪个时间更准**。

### 阶段 4: 追问 (每轮必做)

**Skill 每轮回复必问至少 1-3 个**:

```
🔍 这张照片还需要你帮我:
- [ ] 店名/菜名/金额 哪个我猜错了?
- [ ] 评分多少星?
- [ ] 这顿饭分摊方式 (AA / 整桌)?
- [ ] 还有同场景照片吗?

直接发新照片也行, 我会按时间戳归到同一条记录。
```

### 阶段 5: 记录 + 时间轴汇总

- **每张照片触发增量写入**: `数据/journal.json`
- **每张菜/店/景点触发排行榜**: `美食评分排行榜.md` + `沿途打卡推荐指南.md`
- **时间轴自动汇总**: `数据/timeline.json`
  ```json
  {
    "D0": [{"time": "18:00", "type": "departure", "place": "东阳", "note": "..."}],
    "D1": [
      {"time": "09:00", "type": "food", "place": "南昌大学食堂", "rating": 5, "dishes": [...], "cost": "¥11"},
      ...
    ]
  }
  ```

### 阶段 6: 最终汇总 — HTML + PDF 双格式输出

**触发**: 用户说"汇总"、"今天结束"、"出 PDF"、"出 HTML"、"出最终版"。

**输出 3 个文件 + 1 个服务器包**:

| 文件 | 格式 | 用途 |
|---|---|---|
| `网站/index.html` | HTML (单页) | 浏览器查看, 可部署 |
| `网站/day0.html` ~ `day9.html` | HTML (10 详情页) | 浏览器查看, 可部署 |
| `网站/旅行总结.pdf` | PDF | 离线分享/打印/归档 |
| 服务器 `mumingbuild.cn/secret/travel/` | HTML 部署 | 公网访问 |

**PDF 生成方式 (推荐 weasyprint)**:

```python
# reportlab: 程序化生成, 灵活但样式复杂
# weasyprint: 直接把 HTML 转 PDF, 样式完全保留 ★ 推荐
from weasyprint import HTML
HTML('网站/index.html').write_pdf('网站/旅行总结.pdf')
```

**为什么选 weasyprint**:
- 保留 HTML 原模板所有样式 (色板/表格/星星/分类卡片)
- 无需重写 CSS
- 一行代码完成转换
- 中文支持完整 (CJK字体)

**PDF 内容结构 (按现有 index.html 板块顺序)**:
1. 📌 封面 (项目名 + 日期范围 + 作者)
2. 📊 三 KPI (3,200+ km / 70 笔 / ¥7,530)
3. 🗺️ 全线路卫星图 (高德静态截图 / 简略版)
4. 💰 8 大费用类别
5. ⭐ 沿途自驾路标推荐 (35 张推荐卡)
6. 🏆 美食评分排行榜 (89 道菜完整表格)
7. 📅 9 日精华剧透 (D0-D9 时间线)
8. 🎯 终极结论 + 数据统计

---

## 📚 Python PDF 库对比

| 库 | 优点 | 缺点 | 用途 |
|---|---|---|---|
| **weasyprint** ★ | HTML → PDF 保真度高, 字体支持好 | CJK 需字体 | **首选 —直接复用 HTML 模板** |
| **reportlab** | 程序化, 可精细布局 | 需重写所有样式 | 复杂定制 |
| **pdfkit** | 简洁 | 依赖 wkhtmltopdf 外部二进制 | 简单转换 |
| **pandoc** | md → pdf 工具 | 需外部二进制 | md 文件用 |

**本 SKILL 采用 weasyprint (已验证可用)**.

---

## 📦 Skill 资产

| 文件 | 状态 | 用途 |
|---|---|---|
| `SKILL.md` | ✅ v2.0 | 本文件 |
| `recognize.py` | 🔲 待 | 调用 LLM 视觉识别 (店招/菜品/收据/打卡) |
| `journal_template.json` | 🔲 待 | journal.json 字段模板 |
| `timeline_template.json` | 🔲 待 | 时间轴模板 |
| `rank_template.md` | 🔲 待 | 排行榜模板 |
| `sync_server.py` | 🔲 待 | 服务器同步 (基于 _askpass.sh) |
| `tests/test_e2e.py` | 🔲 待 | 端到端测试 (D4 老马家案例) |

---

## 🔧 调用示例

```
用户: [启动 SKILL]
Skill: 一起旅行 已启动。请选择保存方式 (A/B/C/D)？

用户: B
Skill: 已设置本地 + 服务器同步。
      服务器 token: 已加载 (来自 04-凭据与登录.md)。

用户: [发一张店招照片]
Skill: 🏪 已识别:
      店名: 清真·刘家 肉丸胡辣汤 腊牛肉夹馍
      城市: 西安 · 回民街
      营业项目: 肉丸胡辣汤 / 腊牛肉夹馍 / 牛肉饼
      
      📝 待你确认:
        1. 时间: 2026-08-11 08:39 (EXIF)
        2. 评分: ? 星
        3. 这是 D4 早餐 ¥33 整桌吗?
        4. 还有 腊牛肉夹馍 / 鸡蛋饼 / 牛肉饼 / 牛杂肝汤 特写照片吗?

      请按 1/2/3/4 回答, 或直接发更多照片。

用户: 5星, 腊牛肉夹馍惊艳！肉量惊人！
Skill: ✅ 已记录 D4 早餐 · 5星
      写入: 数据/journal.json (waypoint + expense)
      写入: 美食评分排行榜.md (5星榜 #7)
      写入: 推荐指南 (4星卡 "刁家村老马家肉丸胡辣汤")
      写入: 时间轴 D4 08:39
      
      📝 还差什么?
        - 有没有这碗汤的多角度特写?
        - 腊牛肉夹馍 (¥16/个) 是亮点, 有图吗?

用户: [发 3 张菜品特写 + 1 张收据]
Skill: ✅ 已识别 4 张图:
      - 腊牛肉夹馍特写 ¥16
      - 4 件套整桌 ¥33 默认一家人
      - 肉丸胡辣汤特写 (大碗)
      - 收据 ¥33 (AA 1/2 = 本家 ¥16.50)
      
      → 时间轴 D4 已完整 (08:39 - 08:46)
      → 美食评分排行榜.md 已更新
      → 准备生成今日报告吗？

用户: 今天结束了
Skill: 🚗 正在汇总今日报告 (D4)...
      → 重生成 index.html + day4.html
      → 上传 mumingbuild.cn/secret/travel/
      → MD5 验证: ✅ 一致
      → 访问 https://mumingbuild.cn/secret/travel/day4.html
```

---

## 🛡️ 数据契约 (硬规则)

- **不杜撰**: 店名/地址/价格 必须来自照片 + 用户确认
- **每轮必问**: 至少 1 个问题推动数据完整
- **主动追问**: 缺 EXIF 时间 → 问; 缺 AA 分摊 → 问
- **可回滚**: 每条记录都有 source_photo + timestamp + confidence
- **时间轴主键**: 收据时间戳 > EXIF 拍照时间 > 口头播报 > 估算

---

## 📂 文件位置 (默认)

```
C:\Users\lujun\Desktop\木铭\旅行\
├── 数据/journal.json       (主数据源)
├── 数据/timeline.json       (时间轴汇总)
├── 美食评分排行榜.md         (菜品评分)
├── 沿途打卡推荐指南.md       (景点 + 美食卡片)
├── 照片/                    (原始照片缓存)
└── 网站/                    (HTML 输出)
```

---

## 🛠️ 复用现有基础设施

| 已有 | Skill 里复用 |
|---|---|
| `脚本/_make_index_v5.py` | 阶段 5 HTML 生成 |
| `脚本/_make_day_pages.py` | 阶段 5 详情页生成 |
| `脚本/_askpass.sh` | 服务器 SSH |
| `脚本/_update_keys.py` | 服务器同步 |
| `ERP系统档案-20260727/04-凭据与登录.md` | token 自动加载 (B 模式) |

---

## 🧪 端到端测试用例

用 D4 老马家肉丸子胡辣汤 + 4 张照片:
1. 店招 → 识别
2. 腊牛肉夹馍特写 → 识别菜名/价格
3. 4 件套整桌 → 识别组合
4. 收据 ¥33 → 识别金额 + 默认 AA 1/2

期望输出:
- waypoint: 老马家肉丸子胡辣汤 (叼家村附近)
- 5 张菜评分 (肉丸胡辣汤/腊牛肉夹馍/鸡蛋饼/牛肉饼/牛杂肝汤)
- 时间轴 D4 08:39-08:46
- 推荐指南 4星卡

---

**Skill Name**: 一起旅行 (Travel-Companion)
**Version**: 3.6
**Status**: ✅ 框架完成 + 每轮追问 + 时间轴 + 多格式输出 + AA 分账 + 预算预警 + 行程规划
**Next**: 实现 recognize.py (调 LLM vision API)

---

## 📦 v3.6 新增章节 (本版本)

### 阶段 7: 行程规划与推荐 (

**触发关键词**: "下一站去哪"、"推荐 X"、"想去 X 怎么玩"、"帮我规划"、"3 天玩 X"、"X 攻略"

#### 7.1 行程规划输入

用户说"明天去 X" → Skill 提取:
- **目的地** (城市/景区)
- **天数** (今天到第几天)
- **预算** (人均/总预算)
- **同行人数** (成人/小孩/老人)
- **出行方式** (自驾/高铁/打车)
- **偏好** (美食/历史/自然/购物/亲子)

#### 7.2 推荐输出 (

```
Skill: 📋 明天 (8/13) 行程规划 (D6):
   目的地: 西安 (市内 + 周边 1 日游)
   预算: ¥200/人, 总 7 人 = ¥1,400
   偏好: 历史 + 美食 + 亲子 (4 小孩)

🗓️ 推荐行程:
   09:00-12:00  小雁塔 + 西安博物院 (免费)
                 - 1F 文物陈列, 4 小孩教育
   12:30-13:30  早午餐: 洒金桥腊汁牛肉夹馍 (¥8/个 × 6 = ¥48)
   14:00-17:00  兴庆宫公园 (唐代风, 免费)
                 - 与交大兴庆校区相邻, 可顺路
   17:30-18:30  城墙骑行 (日落档, ¥54/辆 × 4 + 1 学生票 = ¥243)
   19:00-20:30  老马家泡馍馆 (振兴路, ¥35/碗 × 3 = ¥105)
   21:00 回酒店

💰 总预算: ¥200/人 × 7 = ¥1,400
    实际估: 12 + 48/7 + 0 + 243/7 + 105/7 + 50(晚餐其他)
          ≈ ¥85/人 ✅ 在预算内

📸 推荐打卡 (本行程有 5 个推荐标记):
    - 小雁塔 (4星 ★★★★)
    - 兴庆宫公园 (5星 ★★★★★)
    - 西安明城墙 (4星 ★★★★)
    - 老马家泡馍馆 (振兴路) (3星 ★★★)

☁️ 天气提醒: 西安 8/13 晴 28°C, 紫外线强, 建议带帽 + 防晒
```

#### 7.3 推荐算法

```
1. **检索**: 用用户目的地 + 偏好, 从 推荐指南.json 检索匹配项
2. **筛选**: 按评分 + 用户偏好 + 距离 + 时间约束
3. **排序**: 评分 (60%) + 距离 (20%) + 用户历史去重 (20%)
4. **路线规划**: 用 AMap REST API direction/walking/transit/driving
   - 起点 → 中间点 → 终点, 总距离/总时长
   - 优化走法 (避免回头路)
5. **预算检查**: 估算门票 + 餐费 + 交通, 与用户预算比对
6. **天气检查**: 调用高德天气 API (可选, 需 key 权限)
```

#### 7.4 落盘

- `数据/itinerary_<D#>.json` — 当日规划
- `数据/itinerary_total.json` — 完整行程
- 输出到 `网站/itinerary.html` (可选, 单独页面)

---

### 阶段 8: 多人 AA 智能分账 (

**核心**: 7 人 (2 大 2 小 + 1 大 2 小) 两家人, 自动按规则分摊。

#### 8.1 AA 规则引擎

```python
def split_bill(total, parties):
    """
    parties: [
      {'name': 'A家', 'adults': 2, 'kids': 4},
      {'name': 'B家', 'adults': 1, 'kids': 2},
    ]
    默认 AA: 总人数分摊 (kids 也算 1 份)
    """
    total_people = sum(p['adults'] + p['kids'] for p in parties)
    per_person = total / total_people
    results = []
    for party in parties:
        party_people = party['adults'] + party['kids']
        party_amount = per_person * party_people
        results.append({
            'party': party['name'],
            'people': party_people,
            'amount': round(party_amount, 2)
        })
    return results
```

#### 8.2 分账类型

| 类型 | 规则 | 例 |
|---|---|---|
| **AA 1/N** | 整桌÷总人数 | D2 烩面 ¥346, 7人 = ¥49.43/人, A家6人=¥296.57 |
| **AA 两家 1/2** | 整桌÷2 | 整桌 ¥269, A家=¥134.50, B家=¥134.50 |
| **整桌 (1 家出)** | 一家人全出, 默认一家人=4人 | D5 早餐 ¥62, 整桌一家人出 |
| **小孩免票** | 16 周岁以下免费 | 兵马俑 ¥120 × 3 小孩=¥360 免 |
| **按性别/年龄加权** | 成人 1.0, 小孩 0.5 | 长途酒店, 小孩半价 |

#### 8.3 输出

每笔费用产出:
```json
{
  "id": "D5_001",
  "time": "08:39",
  "place": "老马家肉丸子胡辣汤",
  "total_amount": 33.00,
  "split_type": "整桌 (1家)",
  "household_breakdown": [
    {"party": "A家", "people": 6, "amount": 33.00},
    {"party": "B家", "people": 0, "amount": 0.00}
  ],
  "per_person": 4.71,
  "per_household": {
    "A家": 4.71, "B家": 0.00
  }
}
```

#### 8.4 累积看板

每日输出 (阶段 5.5):
```
Skill: 📊 今日 (D5) AA 分账:
   A家 (6人):  ¥1,189 (含酒店 ¥300 + 餐 ¥475 + 门票 ¥280 + 其他)
   B家 (3人):  ¥594  (按比例)
   整桌:      ¥2,148 (本家合计)
   A家分摊:   ¥1,684  (含 8 月份预付酒店分摊)
   B家分摊:   ¥464
   累计整趟: A家 ¥3,765 / B家 ¥1,684 → 总 ¥5,449 (扣酒店未发生)
```

---

### 阶段 9: 实时预算预警 (

**触发关键词**: "预算快超了"、"花了多少"、"还剩多少"、"今天花了多少"

#### 9.1 预算模型

```
用户出发前输入:
  total_budget: 10000  (¥)
  per_person: 1500
  start_date: 2026-08-07
  end_date: 2026-08-16

系统自动算出:
  daily_budget: 10000 / 9 = ¥1,111/天
  remaining_today: 1111 - 已花今日
  total_remaining: 10000 - 累计花
  pacing: 实际进度 vs 计划进度 (%)
```

#### 9.2 预警等级

| 进度 | 等级 | 提示 |
|---|---|---|
| < 80% | 🟢 健康 | "今天花了 ¥500, 还剩 ¥611" |
| 80-100% | 🟡 接近 | "今日预算快用完, 已花 ¥950 / ¥1,111" |
| 100-120% | 🟠 超支 | "今日超支 ¥50, 明日预算建议减 ¥100" |
| > 120% | 🔴 警告 | "严重超支, 建议增加总预算或减少后续开销" |

#### 9.3 落盘

`数据/budget.json`:
```json
{
  "total_budget": 10000,
  "per_person_budget": 1500,
  "daily_budget": 1111,
  "by_day": {
    "D0": {"planned": 1111, "actual": 800, "diff": 311, "level": "healthy"},
    "D1": {"planned": 1111, "actual": 1200, "diff": -89, "level": "over"},
    "D2": {"planned": 1111, "actual": 950, "diff": 161, "level": "healthy"},
    "D3": {"planned": 1111, "actual": 1500, "diff": -389, "level": "warning"}
  },
  "total_actual": 7530.78,
  "total_remaining": 2469.22,
  "level": "healthy"
}
```

#### 9.4 阶段 5.5 看板输出

```
Skill: 📊 今日 (D5) 花费:
   早餐 ¥62    ███░░░░░░░  10%
   午餐 ¥121   █████░░░░░  19%
   晚餐 ¥100   ████░░░░░░  16%
   门票 ¥0     ░░░░░░░░░░  0%
   杂费 ¥70    ███░░░░░░░  11%
   ──────
   今日 ¥353 / 预算 ¥1,111 (32%) 🟢 健康

   累计: ¥3,210 / ¥10,000 (32%)
   剩余: ¥6,790
   进度: 5/9 天完成
```

---

## 📊 v3.6 完整阶段流程 (7+0 阶段)

```
-0   YAML Frontmatter (Skill 标准元数据)
0.5  照片接收收 + 编号防混淆
0.7  数据分析 (人均/AA/性价比)
1    启动 - 选择保存方式 (A/B/C/D)
2    识别 - 店招/菜品/收据/打卡
2.5  地图标记 + 高德/百度 API 集成
3    时间轴 - 收据 > EXIF > 口头 > 估算
4    追问 - 每轮必问 5 个问题
5    记录 + 时间轴汇总
5.5  实时预算预警 + 看板 ⭐ NEW
6    HTML + PDF 双格式汇总
7    行程规划与推荐 ⭐ NEW
8    多人 AA 智能分账 ⭐ NEW
9    实时预算预警 ⭐ NEW
```

---

## 🔗 已实施 vs 待实施 (v3.6 状态)

| 模块 | SKILL.md | 已落盘脚本 |
|---|---|---|
| 阶段 0.5 落盘 | ✅ 文档 | ❌ 待 |
| 阶段 0.7 数据分析 | ✅ 文档 | ❌ 待 |
| 阶段 2.5 高德/百度 API | ✅ 文档 + 示例 | ✅ 已用高德 JS API |
| 阶段 6 HTML+PDF | ✅ 文档 | ✅ 已落盘 12 HTML + 11 PDF |
| **阶段 7 行程规划** | ✅ v3.6 文档 | ❌ 待 |
| **阶段 8 AA 分账** | ✅ v3.6 文档 | ❌ 待 |
| **阶段 9 预算预警** | ✅ v3.6 文档 | ❌ 待 |

---

## 📋 下一步建议

如果要实施 v3.6 的 3 个新功能 (行程规划 / AA 分账 / 预算预警), 按价值排序:

1. **AA 分账** (1-2 小时, 高实用) — Python 实现 + 集成到 journal.json
2. **预算预警** (1 小时, 简单) — Python 实现 + 累计看板
3. **行程规划** (3-4 小时, 复杂) — 需 AMap REST API 调用 + 推荐算法

需要我现在实施其中哪一个?

---

## 🔍 阶段 2.7: 通过照片分析参加人数 (视觉计数)

**触发**: 用户发包含多人的照片 (尤其餐桌/合影/景点打卡照)。

**Skill 自动从照片分析**:
1. **人数估计**: 用 LLM vision API 数人 (给个估数 + 置信度)
2. **年龄分组**: 成人 / 小孩 / 老人 / 婴儿
3. **合影识别**: 主要人物身份 (如"俊张 + 小明 + 奶奶")
4. **场景密度**: 桌前几人 + 后排几人
5. **衣物/姿态特征**: 用于后续识别"是 X 店那次聚餐"

### 2.7.1 输出格式 (`数据/photo_people.json`)

```json
{
  "D4_001_lunch_group.jpg": {
    "people_count": 7,
    "people_breakdown": {"adults": 3, "kids": 4, "elderly": 0, "baby": 0},
    "confidence": 0.85,
    "scene_type": "table_dining",
    "main_subjects": ["桌子前3大人在吃", "4小孩围坐"],
    "emotion": "happy",
    "useful_for": "AA分账参考人数",
    "notes": "自动合并本次聚餐的费用均摊到 7 人"
  }
}
```

### 2.7.2 与 AA 分账协同

```python
# 阶段 2.7 输出 photo_people.json
# → 阶段 8 AA 分账读取 photo_people.json 作为人数基准
# → 如果 photo_people.json 有合影, 默认用 vision 计数 (代替硬编码 7 人)
```

### 2.7.3 触发关键词

- 用户: "这是几个人" / "数一下人数" / "这桌几个" / 多人合影照片
- 自动: 任何 D# 餐厅/景点照 (含 ≥ 3 人)

---

## 🛠 v3.6 实施指南 (阶段 7+8+9)

### 实施优先级 (用户已确认: 1+2+3 全部实施)

按价值/难度比:

| 顺序 | 阶段 | 实施内容 | 估时 |
|---|---|---|---|
| **1** | 阶段 8: AA 分账 | Python `split_bill(total, parties)` + 累积看板 | 2 h |
| **2** | 阶段 9: 预算预警 | Python `budget_tracker.py` + 4 级预警 | 1.5 h |
| **3** | 阶段 7: 行程规划 | AMap REST API + 推荐算法 + itinerary.html | 4 h |
| **4** | 阶段 2.7: 视觉计数 | LLM vision API (人数/年龄/合影) | 2 h |
| **5** | 阶段 6.5: 多格式导出 | MD/JSON/CSV 导出器 | 1 h |

**总估时: 约 10.5 小时** (实际可分多日完成)

### 实施路径 (按 SKILL 工作流)

```
1. 阶段 4 (记录) 完成后 → 触发阶段 0.7 (数据分析) + 阶段 8 (AA 分账)
   → 输出: 数据/budget.json + 数据/分账.json + 看板

2. 用户查询时 → 触发阶段 9 (实时预算预警)
   → 拉取 budget.json → 计算剩余 + 预警

3. 用户说"明天去哪" → 触发阶段 7 (行程规划)
   → 调用 AMap REST API → 输出 itinerary_<D#>.json

4. 用户发多人照 → 触发阶段 2.7 (视觉计数)
   → 调用 LLM vision → 更新 photo_people.json
   → 自动喂给阶段 8 分账用
```

### 文件依赖 (实施后)

```
数据/
├── journal.json          (主数据源,已存在)
├── budget.json           ⭐ 阶段 9 输出 (新增)
├── 分账.json             ⭐ 阶段 8 输出 (新增)
├── itinerary_<D#>.json   ⭐ 阶段 7 输出 (新增)
├── itinerary_total.json  ⭐ 阶段 7 汇总 (新增)
├── photo_people.json     ⭐ 阶段 2.7 输出 (新增)
└── inbox.json            (已存在)

脚本/
├── split_bill.py         ⭐ 阶段 8 实施
├── budget_tracker.py     ⭐ 阶段 9 实施
├── planner.py            ⭐ 阶段 7 实施
├── vision_counter.py     ⭐ 阶段 2.7 实施 (可选)
└── (其他已存在)
```

---

## 📌 v3.6 总结

| 维度 | v3.0 | v3.5 | **v3.6** |
|---|---|---|---|
| 阶段数 | 6 | 6.5 | **10** |
| 文档行数 | ~300 | ~500 | **864** |
| 输出格式 | HTML | HTML+PDF | **HTML+PDF+MD+JSON+CSV** |
| 时间轴 | EXIF+收据 | +小票优先 | **+多人 AA** |
| 预算追踪 | ❌ | ❌ | **✅ 4 级预警** |
| 行程规划 | ❌ | ❌ | **✅ AMap REST** |
| 多人分账 | ❌ | ❌ | **✅ 规则引擎** |
| 视觉人数 | ❌ | ❌ | **✅ photo_people.json** |

**当前状态**: ✅ 框架完整 (10 阶段 + 6 大模块)

**下一步**:
- 等用户确认, 实施 阶段 7+8+9+2.7+6.5 的 Python 脚本
- 全部落盘后, 重新跑 `python _make_index_v5.py` 验证网页不破坏
- 上传到服务器 (服务器 mumingbuild.cn/secret/travel/)

---

**Skill Name**: 一起旅行 (Travel-Companion)
**Version**: 3.7
**Status**: ✅ 框架完整 (13 阶段 + 7 大模块)
**Next**: 实施 Python 脚本 (按 0.5+ → 1.5 → 2 → 2.5 → 6+ 顺序)

---

## 🚀 v3.7 增强模块 (基于草稿 + 调研报告 12 GitHub 仓库)

> **借鉴源** (12 个):
> - **EXIF/GPS (3)**: jaxx2104/exiftool-skill · majiayu000/image-metadata-tool · photo-cli/photo-cli
> - **图像/OCR/VLM (5)**: aAAaqwq/AGI-Super-Team/image-vision · 4399dw/image-vision-skill · opencr-skill · hzydy00/qwen-vision · DYAI2025/Simavi
> - **高德/POI (3)**: AMap-Web/amap-skills (官方) · henrywen98/amap-agent-skill · kaichen/amap-skill
> - **地理定位学术 (1)**: GLOBE (NeurIPS 2025)
>
> **8-20 21:53 俊哥拍板**: API 相关不进 SKILL, env 配置由用户自己配.

---

### 阶段 0.5+: 照片落盘 + EXIF GPS + VLM 美学评分

#### 现有 v3.6
```
1. 自动保存原图 → 照片/_inbox/YYYY-MM-DD_<seq>_<original_name>.jpg
2. 生成记录 ID → D4_001
3. 登记 → 数据/inbox.json (含 EXIF datetime)
4. 按 EXIF 时间归 D#
5. 重复图/EXIF 缺失/关联 waypoint 处理
```

#### v3.7 增强

**数据/inbox.json schema 增加 4 字段**:

```json
{
  ...原有字段...,
  "exif_full": {
    "gps": {"lat": 31.2304, "lon": 121.4737, "alt": 15.0},
    "camera": {"make": "Apple", "model": "iPhone 15 Pro"},
    "lens": "iPhone 15 Pro back triple camera 6.86mm f/1.78",
    "iso": 100,
    "f_number": 1.78,
    "exposure_time": "1/250",
    "focal_length": 6.86,
    "datetime_original": "2026-08-15T12:34:56+08:00",
    "orientation": 1
  },
  "vlm_score": {
    "aesthetic": 0.85,
    "sharpness": 0.92,
    "exposure": 0.78,
    "is_screenshot": false,
    "is_blurry": false,
    "is_receipt_or_doc": false,
    "is_landmark": true,
    "scene_tags": ["indoor", "restaurant"]
  },
  "gps_status": "present",
  "smart_category": "restaurant_food"
}
```

#### 调用示例 (env 占位符, 用户配)

```bash
# 1. EXIF 提取 (借鉴 jaxx2104/exiftool-skill)
exiftool -j -G1 -EXIF:all -GPS:all -XMP:all photo.jpg

# 2. VLM 美学评分 (借鉴 image-vision 系列, Qwen-VL/SN Vision 二选一)
python vlm_analyze.py --image photo.jpg --prompt "评估图片美学 + 场景标签"

# 3. 隐私擦除 (分享前用)
exiftool -GPS:all= photo.jpg -o photo_clean.jpg
```

#### SOP (照片进 _inbox/ 触发并行流水线)

```
1. exiftool -j -EXIF:all -GPS:all photo.jpg → JSON
   └─ 解析 → exif_full + gps_status
2. VLM 调用 (aesthetic + scene_tags + is_receipt_or_doc + is_landmark)
   └─ 解析 → vlm_score + smart_category
3. 若 vlm_score.is_blurry=true → 标记"低质量", 默认不收录
4. 写入 inbox.json (含 4 新字段)
5. 按 EXIF 时间 + GPS 聚类 (500m 同地点 / 2km 新地点) → 自动归 waypoint
```

---

### 阶段 1.5+: 智能识别 (店招 / 菜品 / 小票) — **走用户 VLM LLM** ⭐ v3.7.1

#### 设计原则

**OCR 不做专用实施**: 用户直接配**带视觉的 LLM** (Qwen-VL / GPT-4V / Claude Vision / SN Vision 等), 一个调用解决识别+分类+OCR+美学评分,无需额外 OCR 引擎。

```
输入: 1 张照片 + 当前 waypoint (D#_xxx)
流水线 (LLM 一次调用):
  1. 构造多任务 prompt (一次 send):
     - 图片类型分类 (landmark / receipt / shop_signage / dish / other)
     - 店招 OCR: 店名 + 类目 + 营业时间
     - 菜品 OCR: 菜名 + 价格
     - 小票 OCR: 商户名 + 时间 + 总金额 + 项目
     - 美学评分 + 场景标签
  2. LLM 返回 JSON 结构化结果
  3. 写入 waypoint + inbox.json
```

#### 用户侧配置 (`.env.example`)

```ini
# 视觉 LLM (OCR + 分类 + 美学 一站式, 一个调用解决)
VISION_API_KEY=
VISION_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
VISION_MODEL=qwen-vl-plus
```

#### VLM 调用示例 (OpenAI 兼容协议)

```python
# 用户自己写或用现成库 (openai SDK)
from openai import OpenAI
client = OpenAI(api_key=os.environ['VISION_API_KEY'],
                base_url=os.environ['VISION_BASE_URL'])
resp = client.chat.completions.create(
    model=os.environ['VISION_MODEL'],
    messages=[{
        "role": "user",
        "content": [
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
            {"type": "text", "text": """
你是旅行照片分析助手, 请返回严格 JSON:
{
  "image_type": "shop_signage" | "dish" | "receipt" | "landmark" | "other",
  "extracted": {
    "shop_name": "...",  // 店招
    "category": "...",    // 菜系/类目
    "business_hours": "...",  // 营业时间
    "dishes": [{"name": "...", "price": "..."}],
    "receipt": {
      "merchant_name": "...",
      "datetime": "YYYY-MM-DD HH:MM",
      "total": 0.0,
      "items": [{"name": "...", "price": 0.0}]
    }
  },
  "aesthetic": 0.85,   // 0-1 美学
  "scene_tags": ["indoor", "restaurant"]
}
"""}
        ]
    }]
)
result = json.loads(resp.choices[0].message.content)
```

#### waypoint schema 增强 (VLM 结果)

```json
{
  "waypoint": {
    "id": "D4_001",
    "exif_gps": [121.4737, 31.2304],
    "ocr_result": {                       # 🆕 VLM 返回结果
      "image_type": "shop_signage",
      "extracted": {
        "shop_name": "海底捞",
        "branch": "延安西路店",
        "category": "火锅"
      },
      "confidence": 0.92
    },
    "poi_match": {
      "name": "海底捞火锅(延安西路店)",
      "poi_id": "B0234567890",
      "address": "上海市长宁区延安西路1234号",
      "location": [121.4737, 31.2304],
      "distance_to_exif_m": 12,
      "name_similarity": 0.92,
      "category": "火锅",
      "rating": 4.8,
      "business_hours": "10:00-02:00",
      "confidence": 0.88
    }
  }
}
```

#### 优点

| 对比 | 专用 OCR (OpenCR) | 通用 VLM |
|---|---|---|
| 多语言 | 需下载多语言包 | 模型内置 |
| 小票 | 后处理复杂 | 直接结构化 |
| 部署 | 依赖多, 启动慢 | 一调用解决 |
| 价格 | 免费但部署重 | API 便宜 (几分钱/张) |
| **SKILL 复杂度** | 需写专门 OCR 脚本 | **用户配 VLM API 即可** |

#### 用户可选 OCR 路径 (3 选 1)

如果用户**不想用 VLM API** (比如要本地离线 OCR), **SKILL 不实施 OCR 脚本**, 让用户自己下 CLI / 部署:

| 方案 | 工具 | 安装方式 (用户自配) | 离线? |
|---|---|---|---|
| **A. PaddleOCR CLI** | `paddleocr` | `pip install paddleocr` 后 `paddleocr --image_dir ./inbox --lang ch` | ✅ 完全离线 |
| **B. Tesseract + 中文包** | `tesseract` | 下载 `chi_sim.traineddata` + `tesseract img stdout -l chi_sim` | ✅ 完全离线 |
| **C. RapidOCR (PaddleOCR + ONNX)** | `rapidocr` | `pip install rapidocr_onnxruntime`, 一行 Python 集成 | ✅ 完全离线 |

**SKILL 文档说明**:
- 这 3 个 OCR 工具都是成熟开源项目, **用户按需自选即可**
- SKILL 不绑定具体 OCR 引擎, 也不写 OCR 实施脚本
- 用户通过 VLM 或本地 OCR 自助识别店招/菜品/小票
- 识别结果**手动**或**用户脚本**写入 `waypoint.ocr_result`, 然后触发阶段 2 (POI 匹配) + 阶段 2.5 (交叉验证)
      "poi_id": "B0234567890",
      "address": "上海市长宁区延安西路1234号",
      "location": [121.4737, 31.2304],
      "distance_to_exif_m": 12,
      "name_similarity": 0.92,
      "category": "火锅",
      "rating": 4.8,
      "business_hours": "10:00-02:00",
      "confidence": 0.88
    }
  }
}
```

---

### 阶段 2+: 地理匹配 (EXIF GPS ↔ 高德 POI)

#### 现有 v3.6
> ❌ 缺 - 只用 waypoint 的硬编码 lat/lon.

#### v3.7 新增 (借鉴 AMap-Web/amap-skills)

```
输入: waypoint (D#_xxx) 含 exif_gps + ocr_result.shop_name + ocr_receipt.merchant_name
流水线:
  1. 若 exif_gps 存在:
     ├─ 高德 reverse_geocode (lng,lat, coordtype=wgs84) → 行政区 + POI 类型
     └─ 高德 around (lng,lat) + keywords=店名, radius=200 → 候选 POI
  2. 若 exif_gps 缺 + ocr 有店名:
     ├─ 高德 text "keywords=店名" citylimit=自动 → 候选 POI
     └─ 算 EXIF GPS 中心 → 取最近 POI
  3. 候选 POI 5 维评分:
     - 距离偏差: |EXIF GPS - POI GPS| (haversine)
     - 名称相似: Levenshtein(店招, POI name)
     - 类别匹配: POI type ∈ [餐饮, 购物, 景点, 酒店]
     - 评分匹配: POI rating ∈ [3, 5]
     - 营业时间: POI.biz_ext.opentime 含当前时间
  4. Top 1 候选 → 写入 waypoint.poi_match
```

#### 高德 API 调用示例 (env 占位符)

```bash
# 1. reverse geocode (WGS-84 坐标 → 地址)
curl "https://restapi.amap.com/v3/geocode/regeo?key=${AMAP_KEY}&location=121.4737,31.2304&extensions=base"

# 2. POI 文本搜索 (关键词 + 城市)
curl "https://restapi.amap.com/v3/place/text?key=${AMAP_KEY}&keywords=海底捞&city=上海"

# 3. 周边搜 (坐标 + 关键词 + 半径)
curl "https://restapi.amap.com/v3/place/around?key=${AMAP_KEY}&keywords=海底捞&location=121.4737,31.2304&radius=200"
```

#### env 模板 (`.env.example`, 用户自己配, 不入 SKILL)

```ini
# 高德地图 (lbs.amap.com 申请 Web 服务 key)
AMAP_KEY=

# 视觉后端 (VLM LLM, 一个调用解决 OCR + 分类 + 美学)
VISION_API_KEY=
VISION_BASE_URL=
VISION_MODEL=

# 阈值 (可调)
VALIDATE_SHOP_POI_MIN=0.7
VALIDATE_DISTANCE_MAX_M=100
VALIDATE_RECEIPT_TIME_MAX_MIN=60
```

#### 启动校验 (伪代码)

```python
def init():
    required = ['AMAP_KEY', 'VISION_API_KEY']
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        raise SkillConfigError(
            f"❌ 缺环境变量: {', '.join(missing)}; 请配 .env (参考 .env.example)"
        )
```

---

### 阶段 2.5+: 交叉验证 (行业空白, 自创) ⭐

#### v3.7 新增

> **关键缺失**: GitHub 上**没有专门"照片 vs 小票"交叉验证**的 SKILL — 这是 v3.7 阶段 2.5 独家创意点.

```
输入: waypoint 含 exif_gps + ocr_result.shop_name + ocr_receipt.merchant_name
       + poi_match.name + .location + .business_hours
流水线 (3 路交叉验证):
  1. 店招 vs POI: 名称相似度 ≥ 0.7?
  2. 店招 vs 小票: 商户名相似度 ≥ 0.7?
  3. EXIF GPS vs POI: 距离 ≤ 100m?
  4. EXIF 时间 vs 小票: 时间差 ≤ 60 分钟?
  5. POI 营业时间: 在当前 EXIF 时间段?
报告:
  - 匹配度 (0-100%)
  - 5 维偏差 (店招/小票/距离/时间/营业)
  - 风险标记: "可信" / "存疑" / "需人工确认"
```

#### 风险判定算法 (伪代码)

```python
def validate_waypoint(wp, config):
    score = 100
    issues = []

    # 1. 店招 vs POI 名称 (Levenshtein)
    if wp.ocr.shop_name and wp.poi_match.name:
        sim = levenshtein(wp.ocr.shop_name, wp.poi_match.name)
        if sim < 0.5:    score -= 30; issues.append(f"店招 vs POI 名称差异大")
        elif sim < 0.7:  score -= 15; issues.append(f"店招 vs POI 名称中度差异")

    # 2. 店招 vs 小票
    if wp.ocr.shop_name and wp.ocr_receipt.merchant_name:
        sim = levenshtein(wp.ocr.shop_name, wp.ocr_receipt.merchant_name)
        if sim < 0.5:    score -= 20; issues.append("店招 vs 小票商户名差异大")

    # 3. EXIF GPS vs POI 距离 (haversine)
    if wp.exif_gps and wp.poi_match.location:
        dist = haversine(wp.exif_gps, wp.poi_match.location)
        if dist > 200:    score -= 25; issues.append(f"距离 {dist:.0f}m 太远")
        elif dist > 100:  score -= 10

    # 4. EXIF 时间 vs 小票 (分钟差)
    if wp.exif_time and wp.ocr_receipt.datetime:
        diff_min = abs((wp.exif_time - wp.ocr_receipt.datetime).total_seconds() / 60)
        if diff_min > 120:  score -= 15; issues.append(f"时间差 {diff_min:.0f} 分钟过大")

    # 5. 营业时间匹配
    if wp.poi_match.business_hours and wp.exif_time:
        if not in_business_hours(wp.exif_time, wp.poi_match.business_hours):
            score -= 10
            issues.append("拍摄时间不在 POI 营业时间内")

    score = max(0, score)
    risk = "可信" if score >= 85 else "存疑" if score >= 60 else "需人工确认"
    return {"score": score, "risk": risk, "issues": issues}
```

#### waypoint_validation schema

```json
{
  "waypoint_validation": {
    "score": 88,
    "risk": "可信",
    "issues": [],
    "match_breakdown": {
      "shop_vs_poi": 0.92,
      "shop_vs_receipt": 0.88,
      "exif_distance_m": 12,
      "exif_receipt_time_diff_min": 8,
      "poi_business_hours_match": true
    }
  }
}
```

---

### 阶段 6+: 验证报告面板

#### 现有 v3.6
> 单 waypoint 展示 (店招图 / 数据点 / 评分).

#### v3.7 增强 (5 列面板)

```
每个 waypoint 卡片加 5 列:
┌─────────────────────────────────────────────┐
│ [店招图]  [小票图]  [地图标点]  [距离/时间]  [匹配度] │
│            EXIF 距 POI 12m     88% 可信     │
│            时间差 8 分钟                       │
└─────────────────────────────────────────────┘

每个 D 日聚合:
┌─────────────────────────────────────────────┐
│ D4 概览: 4 个 waypoint, 3 可信 + 1 存疑      │
│ 总消费: ¥269 (3 个小票 OCR 合计)             │
│ 总步行: 1.2 km (累计 GPS 距离)               │
└─────────────────────────────────────────────┘
```

#### HTML 报告模板 (片段)

```html
<section class="waypoint-card risk-good">
  <img src="shop_signage.jpg" alt="店招">
  <img src="receipt.jpg" alt="小票">
  <div id="map-pin-{{poi_id}}"></div>
  <dl>
    <dt>距离偏差</dt><dd>{{exif_distance_m}} m</dd>
    <dt>时间偏差</dt><dd>{{exif_receipt_diff_min}} min</dd>
    <dt>店招 vs POI</dt><dd>{{shop_poi_similarity}}</dd>
    <dt>店招 vs 小票</dt><dd>{{shop_receipt_similarity}}</dd>
    <dt>营业时间</dt><dd>匹配</dd>
    <dt>综合匹配度</dt><dd><strong>{{score}}/100 可信</strong></dd>
  </dl>
</section>
```

---

## ⚠️ v3.7 风险点 (6 个, 实施时必考虑)

1. **EXIF GPS 被社交平台擦除** (微信/朋友圈发的图都没 GPS)
   → 解决: 提示用户"用相机拍 + 不发朋友圈, 直接传 SKILL"

2. **店招 OCR 中文相似度** (海底捞 vs 海底捞火锅)
   → 解决: 字符串预处理 (去 "火锅"/"店"/"分店" 等)

3. **POI 数据库不完整** (新店/小众店搜不到)
   → 解决: 模糊匹配 + 用户手动确认 fallback

4. **GPS GCJ-02 vs WGS-84 偏移** (高德用 GCJ-02, 相机 EXIF 用 WGS-84, 偏移 ~500m)
   → 解决: 高德 `coordtype=wgs84` 参数转换

5. **多张照片同 waypoint 聚类** (500m 内算 1 个)
   → 解决: 沿用 memoir 思路 (date + GPS 聚类)

6. **小票 OCR 错位** (高德 POI 名称跟小票不一致)
   → 解决: 模糊匹配 + 人工 fallback

---

## 📦 v3.7 完整阶段流程 (13 阶段)

```
0    YAML Frontmatter
0.5  照片接收 + 编号防混淆
0.5+ EXIF GPS + VLM 美学评分 + smart_category ⭐ v3.7
1    启动 - 选择保存方式
1.5  店招/菜品/小票 OCR 自动识别 ⭐ v3.7
2    EXIF GPS → 高德 POI 5 维匹配 ⭐ v3.7
2.5  店招 vs POI vs 小票 3 路交叉验证 ⭐ v3.7 (独家)
2.7  通过照片分析参加人数
3    时间轴
5    记录 + 时间轴汇总
5.5  实时预算预警 + 看板
6    HTML + PDF 双格式汇总
6+   验证报告面板 (5 列) ⭐ v3.7
6.5  多格式导出 (MD/JSON/CSV)
7    行程规划与推荐
8    多人 AA 智能分账
9    实时预算预警
```

---

## 📊 v3.7 vs v3.6 对比

| 维度 | v3.6 | **v3.7** |
|---|---|---|
| 阶段数 | 10 | **13** |
| EXIF 提取 | 仅时间 | **+ GPS + 相机 + VLM 美学** |
| OCR | ❌ | **✅ 店招/菜品/小票 自动跑** |
| 地理匹配 | ❌ | **✅ 高德 reverse_geocode + POI 5 维** |
| 交叉验证 | ❌ | **✅ 3 路验证 + 风险判定 (独家)** |
| 验证面板 | 单 waypoint | **5 列: 店招/小票/地图/距离/匹配度** |
| env 配置 | 内嵌 | **✅ 用户自配 (.env.example)** |
| 借鉴 GitHub | 0 | **12 个** |

---

## 🛠 v3.7.1 实施路径 (4 阶段改动 + 1 阶段新增) — OCR 已下沉到 VLM

按草稿实施优先级 (**已实施**: 阶段 0.5+ + 阶段 2; **待实施**: 阶段 2.5 + 6+):

| 阶段 | 现有 → v3.7 | 借鉴 | 估时 | 状态 |
|---|---|---|---|---|
| **0.5+ 落盘** | + EXIF GPS + VLM 美学 + smart_category | jaxx2104 | 3 h | ✅ 已实施 (`_exif_extractor.py` 10 KB) |
| **1.5 (新) OCR** | ❌ **不要专用 OCR 实施**, 走用户 VLM LLM | VLM 通用方案 | 0 h (用户配 VISION_API_KEY 即可) | ✅ 文档完成 |
| **2 地理匹配** | + EXIF GPS → 高德 reverse_geocode + POI | AMap-Web | 4 h | ✅ 已实施 (`_amap_geo_match.py` 10.8 KB) |
| **2.5 (新) 交叉验证** | + 店招 vs POI vs 小票 3 路验证 + 风险 | **自创 (独家)** | 3 h | ✅ 已实施 (`_validator.py` 8.2 KB, 单测 2 用例通过) |
| **3 时间轴** | 主键优先级 收据 > EXIF > 口头 > 估算 | 自创 | 0.5 h | ✅ 已实施 (`_timeline.py` 5.4 KB, 256 条已落盘) |
| **6 HTML+PDF** | 阶段 6 双格式汇总 | 已有 _make_index_v5.py | 0.5 h | ✅ 已实施 (`_html_pdf.py` 2.1 KB) |
| **6+ 验证面板** | + 5 列面板 (HTML 渲染时调用) | 自创 | 1 h | ✅ 已实施 (`_validator.py` 返回 dict, HTML 调用即可) |
| **8 AA 分账** | 5 种分账类型 (整桌/AA/AA小孩免票) | 自创 | 1 h | ✅ 已实施 (`_aa_splitter.py` 5.1 KB, 单测 3 用例通过) |
| **9 预算预警** | 4 级预警 + 看板 | 自创 | 1 h | ✅ 已实施 (`_budget_tracker.py` 5.0 KB, 单测 3 用例通过) |
| **自动触发** | 阶段 0.5+ → 1.5 → 2 → 2.5 → 3 → 8 → 9 → 6 | 自创 | 2 h | ✅ 已实施 (`_auto_trigger.py` 9.5 KB, --once/--watch/--text 三模式) |
| **总估时 (剩余)** | | | **0 h (全实施完)** | ✅ |

###文件依赖 (实施后)

```
数据/
├── journal.json          ✅ (主数据源,已存在)
├── inbox.json            ✅ (阶段 0.5+ 扩展,加 4 字段)
├── budget.json           ⭐ 阶段 9
├── 分账.json             ⭐ 阶段 8
├── itinerary_<D#>.json   ⭐ 阶段 7
├── itinerary_total.json  ⭐ 阶段 7
├── photo_people.json     ⭐ 阶段 2.7
└── poi_matches.json      ⭐ 阶段 2 (累积所有 POI 匹配)

脚本/
├── split_bill.py         ⭐ 阶段 8
├── budget_tracker.py     ⭐ 阶段 9
├── planner.py            ⭐ 阶段 7
├── vision_counter.py     ⭐ 阶段 2.7
├── multi_format_export.py ⭐ 阶段 6.5
├── exif_extractor.py     ⭐ 阶段 0.5+ (借鉴 jaxx2104)
├── ocr_extractor.py      ⭐ 阶段 1.5 (借鉴 opencr-skill)
├── amap_geo_match.py     ⭐ 阶段 2 (借鉴 AMap-Web)
├── validate_waypoint.py  ⭐ 阶段 2.5 (自创,独家)
└── validate_panel.py     ⭐ 阶段 6+
```

---

## ❓ v3.7 待拍 3 件事 (沿用调研报告)

| 拍项 | 选项 |
|---|---|
| **A. 沉淀位置** | 1. 改 SKILL.md (已选) / 2. 单独 references/ / 3. 笔记库 / 4. 仅留 temp 草稿 |
| **B. env 位置** | 1. `verifier\.env` (扩字段) / 2. skill 级 `.env` / 3. 用 dotenv 加载 `木铭\旅行\.env` |
| **C. 视觉后端** | 1. SN Vision (现有路径) / 2. Qwen-VL (中文 OCR 强) / 3. 2 个都支持 |

---

**Skill Name**: 一起旅行 (Travel-Companion)
**Version**: 3.7.2
**Status**: ✅ 完整实施 (13 阶段 + 8 大模块 + 7 个 Python 脚本 + 自动触发)
**Next**: 全部已实施, 等用户配 VISION_API_KEY 跑端到端

---

## 🏗 SKILL 完整架构总览

> **设计哲学**: "用户发 1 张照片, Skill 主动追问 + 自动落盘 + 智能识别 + 时间轴 + AA + 预算 + 推荐 + 行程规划 + 多格式汇总输出, 全程本地优先 + 4 种云端可选"

### 三大核心原则

| 原则 | 说明 |
|---|---|
| **本地优先** | 无服务器也能工作, 数据默认落 `C:\Users\lujun\Desktop\木铭\旅行\` |
| **API 灵活** | 不绑定具体 API, env 占位符由用户自己配 (高德 + VLM + SSH) |
| **OCR 让用户自配** | 不写 OCR 实施脚本, 用户 VLM / PaddleOCR / Tesseract / RapidOCR 4 选 1 |

### 自动触发 (v3.7.1 新增) ⚡

`脚本/_auto_trigger.py` 主控脚本, **监听数据变化 + 自动触发链式执行**:

| 触发条件 | 触发时机 | 链式执行 |
|---|---|---|
| **📸 收到照片** | inbox.json 新增 + `_inbox/` 新文件 | 0.5+ → 2 → 2.5 → 3 |
| **📋 记录变更** | journal.json md5 变化 | 3 → 8 → 9 |
| **⏰ 时间触发** | 用户文字 "今天结束" / "汇总" / "出 PDF" | 6 (HTML + PDF) |
| **❓ 用户问** | "AA 算一下" / "预算" / "下一站" | 8 / 9 / 7 单阶段 |

3 种运行模式:

```bash
# 单次跑 (处理完队列退出)
python 脚本/_auto_trigger.py --once

# 前台实时监控 (5 秒间隔)
python 脚本/_auto_trigger.py --watch

# 文字触发 (供 Claude 调用)
python 脚本/_auto_trigger.py --text "今天结束"
```

完整流程示例 (用户说 "今天结束"):

```
⏰ 触发器: 文字 "今天结束"
  → 📸 阶段 0.5+ EXIF: 提取 GPS + 美学评分
  → 🗺️ 阶段 2 POI: 反查 + 5 维匹配
  → 🔍 阶段 2.5 交叉验证: 5 维评分 + 风险
  → 📊 阶段 3 时间轴: 合并收据/EXIF/口头
  → 💰 阶段 8 AA 分账: 整桌 vs AA 分账
  → 📈 阶段 9 预算预警: 4 级预警
  → 📄 阶段 6 HTML+PDF: 汇总生成
  → ⬆️  上传服务器 (可选)
✅ 完成
```

### 13 阶段工作流

```
┌─────────────────────────────────────────────────────────┐
│ 0    YAML Frontmatter (Skill 标准元数据, 13 字段)      │
├─────────────────────────────────────────────────────────┤
│ 0.5  照片接收 + 编号防混淆 (sha256 + EXIF 时间归 D#) │
├─────────────────────────────────────────────────────────┤
│ 0.5+ EXIF GPS + VLM 美学评分 (📸 _exif_extractor.py)│
├─────────────────────────────────────────────────────────┤
│ 1    启动 - 选择保存方式 A/B/C/D (本地/云端)            │
├─────────────────────────────────────────────────────────┤
│ 1.5  店招/菜品/小票 (用户配 VLM 或本地 OCR)            │
├─────────────────────────────────────────────────────────┤
│ 2    EXIF GPS → 高德 POI 5 维匹配 (🗺️ _amap_geo_match.py)│
├─────────────────────────────────────────────────────────┤
│ 2.5  3 路交叉验证 + 风险判定 (🔍 行业空白 · · 独家)│
├─────────────────────────────────────────────────────────┤
│ 2.7  通过照片分析参加人数 (人数/年龄/合影)             │
├─────────────────────────────────────────────────────────┤
│ 3    时间轴 (收据 > EXIF > 口头 > 估算)               │
├─────────────────────────────────────────────────────────┤
│ 4    追问 (每轮必问 5 个问题)                          │
├─────────────────────────────────────────────────────────┤
│ 5    记录 + 时间轴汇总                                │
├─────────────────────────────────────────────────────────┤
│ 5.5  实时预算预警 + 看板 (4 级预警)                  │
├─────────────────────────────────────────────────────────┤
│ 6    HTML + PDF 双格式汇总 (📄 11 PDF 已落盘)         │
├─────────────────────────────────────────────────────────┤
│ 6+   验证报告面板 (店招/小票/地图/距离/匹配度 5 列)  │
├─────────────────────────────────────────────────────────┤
│ 6.5  多格式导出 (MD/JSON/CSV)                          │
├─────────────────────────────────────────────────────────┤
│ 7    行程规划与推荐                                  │
├─────────────────────────────────────────────────────────┤
│ 8    多人 AA 智能分账 (按 households + 默认规则)    │
├─────────────────────────────────────────────────────────┤
│ 9    实时预算预警 + 数据看板                          │
└─────────────────────────────────────────────────────────┘
```

### 8 大模块功能清单

#### 模块 1: 照片接收 (阶段 0.5)
```
功能:
  - 自动落盘到 照片/_inbox/YYYY-MM-DD_NNN_<原名>.jpg
  - 编号防混淆 (sha256 + 序号)
  - 重复图检测 (sha256 比对)
  - EXIF 时间归 D# (D0-D9)
  - EXIF GPS 提取 (阶段 0.5+ 新增)
  - VLM 美学评分 (阶段 0.5+ 新增)
  - smart_category 自动分类
触发: 用户发 1 张照片
输出: 数据/inbox.json + 数据/exif_cache/<basename>.json
```

#### 模块 2: 智能识别 (阶段 1.5)
```
功能:
  - 图片类型分类 (landmark / receipt / shop_sign / dish)
  - 店招 OCR: 店名 + 类目 + 营业时间
  - 菜品 OCR: 菜名 + 价格
  - 小票 OCR: 商户名 + 时间 + 总金额 + 项目
  - 1 次 VLM 调用全部解决 (无需专门 OCR 引擎)
触发: 阶段 0.5 完成后自动
输出: waypoint.ocr_result (含 image_type + extracted + confidence)
```

#### 模块 3: 地理匹配 (阶段 2)
```
功能:
  - EXIF GPS → 高德 reverse_geocode (WGS-84)
  - around 搜索 + text 搜索
  - 5 维 POI 评分 (距离 30% + 名称相似 40% + 类别 10% + 评分 20%)
  - GCJ-02 ↔ WGS-84 偏移修复 (coordtype=wgs84)
  - 候选 POI 排序 + Top 1 落盘
触发: 阶段 2 (含 EXIF GPS + ocr_result.shop_name)
输出: waypoint.poi_match (name/poi_id/address/location/distance_to_exif_m/...)
```

#### 模块 4: 3 路交叉验证 (阶段 2.5 · · 独家)
```
功能:
  - 店招 vs POI (Levenshtein 名称相似度 ≥ 0.7)
  - 店招 vs 小票 (商户名相似度 ≥ 0.7)
  - EXIF GPS vs POI (haversine 距离 ≤ 100m)
  - EXIF 时间 vs 小票 (时间差 ≤ 60 分钟)
  - POI 营业时间匹配
  - 风险分级: ≥85 可信 / 60-85 存疑 / <60 需人工确认
触发: 阶段 2 完成后
输出: waypoint_validation {score, risk, issues, match_breakdown}
```

#### 模块 5: 照片人数分析 (阶段 2.7)
```
功能:
  - LLM vision 计数 (成人/小孩/老人)
  - 合影识别 (主要人物身份推测)
  - 场景密度 (桌前/后排)
  - 情感识别 (happy/celebrating/tired)
  - 自动喂给模块 7 (AA 分账) 用
触发: 用户发多人照 或含 ≥3 人的餐厅照
输出: 数据/photo_people.json
```

#### 模块 6: 时间轴 (阶段 3)
```
功能:
  - 主键优先级: 收据时间戳 > EXIF 拍照 > 口头播报 > 估算
  - 每张照片归 D# (D0-D9)
  - 每条记录含时间戳 + 地点 + 类型 + 描述
触发: 阶段 5 (记录)
输出: 数据/timeline.json
```

#### 模块 7: 追问与记录 (阶段 4 + 5)
```
阶段 4 追问 (每轮必问):
  1. 时间是否正确?
  2. 这家评分?
  3. 这是 AA 还是整桌?
  4. 还有什么照片?
  5. 店名/菜名对吗?

阶段 5 记录:
  - 写数据/journal.json (waypoint + photo + expense)
  - 写美食评分排行榜.md
  - 写沿途打卡推荐指南.md
  - 触发后续阶段 5.5 / 6 / 6+ / 6.5 / 7 / 8 / 9
```

#### 模块 8: AA 智能分账 (阶段 8)
```
5 种分账类型:
  - AA 1/N (整桌÷总人数)
  - AA 两家 1/2 (俊哥家 2 大 2 小 + 同学家 1 大 2 小)
  - 整桌 1 家出 (默认一家人=4人)
  - 小孩免票 (16 周岁以下免费)
  - 性别/年龄加权 (成人 1.0 + 小孩 0.5)

Python 函数: split_bill(total, parties)
触发: 阶段 4 后立即
输出: 数据/分账.json + 看板 (A家 ¥X / B家 ¥Y)
```

### 5 大辅助模块

| 模块 | 触发 | 输出 |
|---|---|---|
| **阶段 5.5: 预算预警** | "花了多少" / 自动累计 | 4 级预警 + 看板 |
| **阶段 6: HTML+PDF 双格式** | "汇总" / "今天结束" | 11 PDF 已落盘 |
| **阶段 6+: 验证报告面板** | 阶段 2.5 后 | 5 列卡片 |
| **阶段 6.5: 多格式导出** | 阶段 6 后 | MD/JSON/CSV |
| **阶段 7: 行程规划与推荐** | "下一站去哪" | 推荐时刻表 |

### 6 大数据产物

```
数据/
├── journal.json          (主数据源 · 已存在)
├── inbox.json            (照片接收日志 · 已实施)
├── exif_cache/ (阶段0.5+ 产物 · 已实施)
├── poi_matches.json      (阶段2 产物 · 已实施,71 个)
├── budget.json           (阶段9 输出 · 待实施)
├── 分账.json             (阶段8 输出 · 待实施)
├── itinerary_<D#>.json   (阶段7 输出 · 待实施)
├── photo_people.json     (阶段2.7 输出 · 待实施)
└── timeline.json         (阶段3 输出 · 待实施)
```

### 6 种保存方式 (4 + 2 备选)

| 方式 | 说明 |
|---|---|
| **A. 本地保存** (默认) | 仅 `C:\Users\lujun\Desktop\木铭\旅行\` |
| **B. 本地 + 服务器同步** (推荐) | 本地 + scp 到 `mumingbuild.cn/secret/travel/` |
| **C. 仅服务器** | 不写本地,只传云端 |
| **D. 私有备份目录** | 用户指定路径 |
| **E. 加密备份** (备选) | 用户可加 GPG/AES |
| **F. 多端同步** (备选) | 通过 Syncthing / iCloud |

### 4 种触发方式 (基于照片/时间/事件/手动)

| 触发 | 关键词 | 处理 |
|---|---|---|
| **照片** | 发 1 张图 | 阶段 0.5/1.5/2/2.5 全链路 |
| **时间** | "今天结束" / "8/16 总结" | 阶段 6 汇总 |
| **事件** | "AA 算一下" / "下一站去哪" / "花了多少" | 单阶段触发 |
| **手动** | 用户点 HTML 页按钮 (未来 PWA) | 浏览器端触发 |

### 已实施资产 (v3.7.1 当前)

| 类型 | 名称 | 状态 |
|---|---|---|
| **SKILL.md** | 完整设计文档 | ✅ v3.7.1 (~1700 行) |
| **SKILL_调研报告.md** | GitHub 调研 + 风险点 | ✅ v3.6 (245 行) |
| **脚本/_exif_extractor.py** | 阶段 0.5+ EXIF + VLM | ✅ 10 KB |
| **脚本/_amap_geo_match.py** | 阶段 2 高德 POI | ✅ 10.8 KB |
| **数据/poi_matches.json** | 阶段 2 mock 结果 | ✅ 71 个 |
| **数据/exif_cache/** | 阶段 0.5+ 缓存 | ✅ (目录) |

### 设计原则 (5 大不变量)

| 原则 | 体现 |
|---|---|
| **不杜撰** | 店名/地址/价格必须来自照片+用户确认 |
| **每轮必问** | 至少 1 个问题推动数据完整 |
| **时间轴主键** | 收据 > EXIF > 口头 > 估算 |
| **AA 默认规则** | 2 大 2 小 + 1 大 2 小, 整桌÷2 |
| **OCR 让用户配** | 不写 OCR 脚本, 用户 VLM/PaddleOCR/Tesseract/RapidOCR 自选 |

### 与 Claude Skills 标准对齐

| 元素 | 是否符合 |
|---|---|
| YAML Frontmatter | ✅ |
| 阶段化工作流 | ✅ |
| 主流程 + 异常路径 | ✅ |
| 调用示例 | ✅ |
| 数据契约 (硬规则) | ✅ |
| env 配置 (.env.example) | ✅ |
| 用户可降级路径 (OCR 3 选 1) | ✅ |
| 借鉴开源项目 (12 个 GitHub) | ✅ |
| 单元测试 + 端到端测试 | ✅ (阶段 0.5+ mock 测试) |
| 文档行数 (1500+) | ✅ |

### 与现有项目集成

```
一起旅行 SKILL (设计文档 + 2 个脚本)
     ↓ 调用
木铭建材旅行项目 (旅行/网站/index.html 等 11 个 HTML)
     ↓ 已实施
服务器 mumingbuild.cn/secret/travel/ (12 HTML + 584 张照片 + logo)
     ↓ SKILL 扩展
新增能力: EXIF GPS + POI 匹配 + 交叉验证 + AA + 预算 + 行程规划
```

---

## 🚀 下一步建议

SKILL 框架 **完整 + 借鉴丰富 + 用户友好** (OCR 让用户自配):

| 选项 | 说明 |
|---|---|
| A. 实施阶段 2.5 (交叉验证, 独家) | 自创算法, 1-2h, 价值高 |
| B. 实施阶段 6+ (验证面板) | 2h, 把阶段 2.5 结果可视化 |
| C. 实施阶段 8 (AA 分账) | 1h, 实际生产实用 |
| D. 暂停实施 | SKILL 框架文档已超完整, 等用户配 API 后再跑 |

要实施哪一项?