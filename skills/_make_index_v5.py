# -*- coding: utf-8 -*-
"""按用户最终完全体规范生成 index.html (v5):
- Header: 220px Logo + sticky + 11 tab 硬编码
- _AMapSecurityConfig + plugin 全量 + setTimeout 300ms
- 580px 主图 + Satellite + RoadNet + 7 段 10 色静态 polyline
- coord[0] coord[1] 修正
- complete → resize + setFitView
- KPI: 3,200+ km / 70 笔 / ¥7,530
- 8 大费用类别
- ★ 双分类推荐: 12 景点 + 14 美食 (使用 '胖东来' 同时出现两次合并 30 项, 实际是 11+14=25)
  实际: 12 attractions + 14 restaurants + 12 day teaser = 30 cards (用户称"30 项完全体")
- 10 Teaser 卡片 (D0-D9)
- 240px 大图 + 120px 美食缩略图
- 无 data.js / 无 5400+
"""
import io, json, re, urllib.parse
from pathlib import Path
from collections import defaultdict

PHOTO_BASE = 'photos/'  # 同级路径 (HTML在travel目录下,photos也在travel目录下,直接相对)
# ⚠️ 安全: KEY 和 SEC 改为占位符, 实际 key 从 .env 文件读 (见 docs/amap_api_key.example.md)
# 原来硬编码 'e003da79...' / 'daff8e...' 已脱敏 (8-21, 因为发现 .gitignore 漏了 _make_index_v5.py, 防止 GitHub 公开暴露)
KEY = 'YOUR_AMAP_KEY_HERE'
SEC = 'YOUR_AMAP_SECURITY_HERE'

def esc(s):
    return str(s).replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace('"','&quot;')

with open('data/journal.json', encoding='utf-8') as f:
    data = json.load(f)

days = sorted(data['days'], key=lambda d: d['key'])

# 扫描 photos/ 目录
photos_dir = Path('photos')
by_day_photos = defaultdict(list)
for f in photos_dir.iterdir():
    if not f.is_file() or f.suffix.lower() != '.jpg':
        continue
    if '_sq' in f.stem:
        continue
    d_label = f.name[:2]
    by_day_photos[d_label].append(f.name)
for d in days:
    d['_photos_files'] = by_day_photos.get(d['key'], [])

# === 7 段精确坐标 (与 v4 一致) ===
HIGHWAY_PATHS = [
    {'name': 'D0-D1: 东阳 → 南昌 → 武汉', 'color': '#ef4444',
     'path': [[120.23, 29.272], [117.58, 28.950], [115.97, 28.710], [115.80, 28.660],
              [115.802, 28.658], [115.896, 28.679], [115.890, 28.689], [115.50, 29.50],
              [114.45, 30.51], [114.305, 30.544], [114.310, 30.547]]},
    {'name': 'D2: 武汉 → 南阳 → 西安', 'color': '#3b82f6',
     'path': [[114.311, 30.546], [114.16, 30.72], [112.55, 32.97], [112.528, 32.999],
              [112.51, 32.98], [109.063, 34.272], [108.95, 34.27], [108.962, 34.196]]},
    {'name': 'D3: 西安 · 兵马俑日', 'color': '#10b981',
     'path': [[108.95, 34.27], [109.063, 34.272], [109.273, 34.385], [109.273, 34.385],
              [109.063, 34.272], [108.943, 34.262], [108.945, 34.27], [108.95, 34.27],
              [108.94, 34.26], [108.940, 34.26]]},
    {'name': 'D4-D7: 西安多日 · 含许昌', 'color': '#f59e0b',
     'path': [[108.943, 34.262], [108.945, 34.27], [108.989, 34.265], [108.945, 34.262],
              [108.945, 34.265], [108.963, 34.218], [108.989, 34.265], [108.989, 34.265],
              [108.945, 34.262], [108.945, 34.265], [108.945, 34.265], [108.989, 34.265],
              [108.945, 34.265], [108.965, 34.22], [109.063, 34.272], [111.762, 34.765],
              [113.785, 34.035], [113.785, 34.035]]},
    {'name': 'D8: 许昌 → 合肥', 'color': '#8b5cf6',
     'path': [[113.785, 34.035], [113.785, 34.035], [113.780, 34.030], [114.01, 33.58],
              [113.85, 34.04], [117.25, 31.85]]},
    {'name': 'D9: 合肥 → 家 (东阳)', 'color': '#14b8a6',
     'path': [[117.22, 31.82], [117.21, 31.83], [117.25, 31.85], [120.13, 29.30],
              [120.23, 29.272]]},
]
HIGHWAY_PATHS_JSON = json.dumps(HIGHWAY_PATHS, ensure_ascii=False)

# === 12 景点 + 14 美食 (用户给) ===
ATTRACTIONS = [
    ('秦始皇兵马俑博物馆', 5, '陕西省西安市临潼区秦陵街', '世界第八大奇迹，一号坑方阵现场给四个孩子的历史震撼感无可替代。'),
    ('西安碑林博物馆', 5, '陕西省西安市碑林区三学街 15 号', '汇集历代碑石，文化底蕴极深，孩子买个盖章本留念非常有教育意义。'),
    ('安徽博物院（新馆）', 5, '安徽省合肥市蜀山区怀宁路 268 号', '国家一级博物馆，人少不用预约，整体体验感非常好！除了震撼的文明史陈列厅遗址墙和文房四宝专题，馆内更有极其罕见的【天文专展】，完整梳理了从古代的天文历法一直到现代航天的完整发展史，国内少见，非常值得二刷！'),
    ('西安交通大学 + 兴庆宫公园（含茶室）', 5, '陕西省西安市碑林区咸宁西路', '绝佳的备用中转方案！下雨天、行程太累或者由于人多导致博物馆预约失败时，来这里徜徉百年名校和遗址茶室，是缓冲一天的绝佳去处。'),
    ('西安明城墙（含城墙落日）', 4, '陕西省西安市碑林区南大街 2 号附近', '傍晚骑车一圈看城角楼日落剪影，是丈量古城最好的方式。'),
    ('小雁塔（荐福寺/西安博物院）', 4, '陕西省西安市碑林区友谊西路 72 号', '15层唐代方形密檐式古砖塔，免票且比大雁塔更具清幽的古长安底蕴。'),
    ('黄鹤楼', 4, '湖北省武汉市武昌区蛇山西山坡特 1 号', '天下江山第一楼，站在崔颢题诗处眺望滚滚长江，极具历史厚重感。'),
    ('武汉长江大桥', 4, '湖北省武汉市武昌区临江大道（横跨长江）', '万里长江第一桥，站在江边看火车从大桥下层隆隆驶过，两岸江景极其宏伟。'),
    ('方所书店（西安老城根 G park）', 4, '陕西省西安市莲湖区老城根 G park 商圈', '极具现代魔幻设计感的"星空地下书塔"，拍照出片，也是带孩子静心看书的好去处。'),
    ('南阳卧龙岗景区（东门售票处）', 3, '河南省南阳市卧龙区卧龙路 766 号（东门入口）', '诸葛亮十年躬耕地，在这里给全家人的精神充充电，自驾长途中完美的文旅驿站。'),
    ('胖东来时代广场店（打卡地标）', 3, '河南省许昌市魏都区七一路 34 号', '自驾返程必打卡的神级地标。【绝版提醒】作为胖东来最早的店，时代广场店今年就要关门了，想去拍照留念的要趁早！里面人巨多、爆挤，虽然有很多东西没太大必要跟风买，但是它的【茶叶超市】绝对是必去首选！黄金首饰区域很抢手，需要提前预约。'),
    ('大雁塔 + 大唐不夜城', 3, '陕西省西安市雁塔区广场东路 / 慈恩路', '西安夜景的颜值代表，但由于【人实在太多太多，导致体验极差】！属于"不去遗憾，去了后悔"的典型，商业气息太浓太浓，建议根据体力酌情打卡。'),
]

RESTAURANTS = [
    ('西安交通大学食堂（特色三合一油泼面）', 5, '陕西省西安市碑林区交大校内食堂', '交大食堂的神级招牌！实际上是三合一油泼面的一种，【价格巨便宜，分量量巨大】，性价比无敌，一口吃回无忧无虑的大学时代。'),
    ('晓长安·新陕菜（曲江店老同学聚会）', 4, '陕西省西安市雁塔区曲江池东路', '极致的精致宴席，堪称【陕菜小吃的巅峰集大成者】！砂锅红烧肉和带鱼浓油赤酱，环境与品质极其适合老同学聚会，能一次性尝遍最正宗的陕菜精华。'),
    ('南昌大学特色早餐', 4, '江西省南昌市南昌大学周边老店', '经典的江西打卡组合，【价格超级实惠】！尤其是里面的【皮蛋肉饼汤】非常惊艳、非常鲜美，搭配一碗热气腾腾的江西拌粉，大早上瞬间唤醒火热的味蕾。'),
    ('丽华早点（武汉大成路过早）', 4, '湖北省武汉市武昌区大成路老街', '武汉大成路过早的灵魂地标之一！【神级强烈推荐搭配：热干面 + 面窝 + 绿豆沙】。如果食量大，加个糯米鸡或酥饺非常惊艳；实测里面的糍粑和油香品质比较平庸，不太推荐。'),
    ('余记三鲜豆皮老店（武汉过早）', 4, '湖北省武汉市武昌区大成路 8 号', '纯正的武汉大成路过早经典，糯米软糯猪肉鲜嫩，到店【推荐搭配：直接点一份招牌三鲜豆皮】即可，蹲在街边塑料桶上吃才有武汉江湖味道。'),
    ('刁家村老马家肉丸胡辣汤（文昌门老店）', 4, '陕西省西安市碑林区文昌门附近老街区', '绝非游客扎堆的洒金桥，这才是【正宗都是西安本地人吃】的灵魂胡辣汤！汤头浓郁爽辣，肉丸扎实，西安硬核早餐的真正首选。'),
    ('诚意和葫芦头三鲜煮馍（交大店）', 4, '陕西省西安市碑林区咸宁西路（交大旁）', '黑底金字老字号，青花瓷大碗里高汤浓白，葫芦头厚切肥而不腻。'),
    ('澄城水盆羊肉（交大附近诚意和边上）', 4, '陕西省西安市碑林区咸宁西路', '位于交大附近诚意和葫芦头的旁边。清汤鲜美，肉质软烂，把刚出炉的月牙饼夹上鲜嫩羊肉，就着糖蒜吃，大饱口福。'),
    ('魏斯理汉堡（临潼兵马俑店）', 4, '陕西省西安市临潼区兵马俑景区周边', '全国连锁，价格透明统一，绝无景区宰客套路！从兵马俑暴走出来后直接就餐非常棒。同店连锁的【魏家凉皮和肉夹馍】水平都非常在线，是景区周边最靠谱的能量补给。'),
    ('打平伙·鲜辣小炒（蛤蟆街店）', 4, '江西省南昌市东湖区胜利路与蛤蟆街交叉口', '正宗南昌小炒的锅气天花板！味道非常好吃，但是【非常辣】！而且【店里人巨多】，想吃一定要提前去排队，否则排到怀疑人生。'),
    ('小六汤包（龙湖星悦荟店）', 4, '陕西省西安市新城区长乐坡龙湖星悦荟', '老字号中华名小吃，汤包皮薄馅大、汤汁浓郁。在这里点上几笼汤包和几盘家常菜，闭眼不踩雷。'),
    ('福缘厚饺子（汉城首座店）', 3, '陕西省西安市莲湖区大庆西路汉城首座 1 号楼商铺', '同学聚会当晚实拍的店，烤肉不错，听闻饺子也相当可以。虽未实际尝饺子，但烤肉盘子被清光。属于莲湖回民街周边的实力小店，可以试试。'),
    ('老韩家肉丸糊辣汤（二环南路东段店）', 4, '陕西省西安市碑林区二环南路东段（兴庆宫附近）', 'D5 早上兴庆宫遛弯后的灵魂早餐！腊牛肉夹馍惊艳，肉量惊人。肉丸子胡辣汤大碗浓郁，配油条/腊牛肉夹馍/豆浆，7 人份 ¥62 默认一家人，性价比超高。跟 8/11 清真·刘家是不同一家，但同样硬核。'),
    ('许昌回民街·支干烧麦油茶老店', 3, '河南省许昌市魏都区引龙街（回民街）', '40 年回族老字号，大份丸子汤搭配浓郁油茶和烧麦。实测确实没有想象中那么惊艳好吃，但胜在充满街坊市井的烟火气，路过回民街可以一试。'),
    ('胖东来时代广场店（精酿与熟食）', 3, '河南省许昌市魏都区七一路 34 号', '返程必抢的中转货仓。店里人巨多、爆挤，虽然有很多没太大必要跟风买，但是强力推荐【熟食区和烘焙食物】，尤其是里面的【韩式炸鸡】非常好吃！分量超大、用量非常实惠，【20块钱一大盒】，闭眼买不踩雷。'),
    ('李培丸子汤（许昌老店）', 3, '河南省许昌市老城区特色汤馆', '许昌本地人极多、经常排长队的硬核小吃。推荐点一碗【牛肉汤加丸子汤的两掺吃法】，肉量极其惊人，里面的素丸子炸得金黄酥脆很好吃。不过整体【味道略重，口味偏重者推荐】，不一定每个人都吃得惯。'),
    ('阿鹏烧烤（西安酒店附近店）', 3, '陕西省西安市酒店同级老街区', '西安传统的夜市烤串，价格和味道都在线，烤肉滋滋冒油，但整体属于中规中矩并不惊艳，可作为深夜下楼小憩的靠谱深夜食堂。'),
    ('勇利赵家烤肉坊（响塘广场店）', 3, '陕西省西安市大唐不夜城周边/响塘广场', '西安夜市烤肉老字号，很适合朋友深夜把酒言欢。价格味道都在线，但是不惊艳，同质化略多，属于散场后可以一吃的安全牌。'),
    ('阿鹏烧烤 + 酒店附近就餐点', 3, '陕西省西安市酒店周边特色夜市', '西安传统的夜市烤串，价格和味道都在线，烤肉滋滋冒油，氛围很放松，适合作为长途自驾一整天后的深夜能量补给站。'),
    ('姚老表方城烩面（人民路店）', 3, '河南省宛城区人民路钢材市场旁', '南阳自驾路上的中转快餐。虽然这里的【烩面味道确实不错】，汤头醇厚，但是【服务管理非常混乱】，服务员沟通比较困难，在很多菜都没上的情况下依然硬生生给我们上了 7 碗面！配菜也很一般，期望值不要太高。'),
    ('老马家泡馍馆（振兴路店）', 2, '陕西省西安市碑林区振兴路', '【不推荐卡片（平庸提醒）】本次旅途的不太推荐点。羊肉泡馍的整体体验非常一般，虽然味道还算过得去、羊肉切得也比较大块，但由于价格略高，整体性价比偏低，不建议特意前往。'),
    ('姚家厨房（合肥万象城店）', 2, '安徽省合肥市蜀山区潜山路 111 号万象城内', '【不推荐卡片（平庸提醒）】价格略贵，且店内的服务态度与价格产生了一定落差，整体性价比较低，属于本次旅途中体验不太理想的一站。'),
    ('玲玲面屋（碑林后门老店）—— 特色油泼面与 biangbiang 面', 2, '陕西省西安市碑林区碑林博物馆后门旁', '【不推荐卡片（平庸提醒）】店里挂了几张明星的照片，但价格比较高，面食味道也就那样，基本属于正常普通水平。服务态度非常不友好，需要食客自己去端面，且店员会比较急切地推荐你点各种菜，整体体验不推荐。'),
]

# 验证数量
assert len(ATTRACTIONS) == 12, f'景点数={len(ATTRACTIONS)}'
assert len(RESTAURANTS) == 23, f'美食数={len(RESTAURANTS)}'

# === 美食评分排行榜 (从 美食评分排行榜.md 解析) ===
RANKING_MD = open('美食评分排行榜.md', encoding='utf-8').read()

# 解析表格的辅助函数
def parse_md_table(text, start_keyword):
    """从 markdown 文本里找出 start_keyword 后面第一个 |---|...| 表格，返回 list of rows"""
    idx = text.find(start_keyword)
    if idx < 0:
        return []
    # 找 "|---|" 起始的表格
    lines = text[idx:].split('\n')
    rows = []
    in_table = False
    for line in lines:
        line = line.strip()
        if line.startswith('|---') or '|:---:' in line or '|---' in line:
            in_table = True
            continue
        if in_table:
            if not line.startswith('|'):
                break
            cells = [c.strip() for c in line.strip('|').split('|')]
            rows.append(cells)
    return rows

def render_ranking_table(rows, max_col=6):
    """渲染 markdown 表格为 HTML"""
    if not rows:
        return ''
    html = ['<table class="rank-table">']
    # 第一行是表头
    html.append('<thead><tr>')
    for c in rows[0]:
        html.append(f'<th>{esc(c)}</th>')
    html.append('</tr></thead>')
    html.append('<tbody>')
    for row in rows[1:]:
        html.append('<tr>')
        for c in row:
            # 表格行可能比表头少，补空
            html.append(f'<td>{esc(c)}</td>')
        html.append('</tr>')
    html.append('</tbody></table>')
    return ''.join(html)

# 解析 5 块: ⭐⭐⭐⭐⭐, ⭐⭐⭐⭐, ⭐⭐⭐, ⭐⭐ 一般, 按店家 5星聚集, 城市推荐, 性价比, 9日时序
rank_5star = parse_md_table(RANKING_MD, '## ⭐⭐⭐⭐⭐ 必吃榜 (21 道)')
rank_4star = parse_md_table(RANKING_MD, '## ⭐⭐⭐⭐ 非常不错榜 (35 道)')
rank_3star = parse_md_table(RANKING_MD, '## ⭐⭐⭐ 好吃榜 (31 道)')
rank_2star = parse_md_table(RANKING_MD, '## ⭐⭐ 一般榜 (2 道)')
rank_by_store = parse_md_table(RANKING_MD, '## 🏆 按店家 5星聚集')
rank_by_city = parse_md_table(RANKING_MD, '## 📌 城市推荐 Top')
rank_by_price = parse_md_table(RANKING_MD, '## 💰 性价比榜')
rank_by_day = parse_md_table(RANKING_MD, '## 🏆 9 日按日时序汇总')
rank_concl = parse_md_table(RANKING_MD, '## 📊 统计总览')

# 拼成 HTML 块
RANKING_HTML = f'''
<div class="ranking-block">
  <p class="ranking-intro">9 日西安自驾 · 89 道菜完整评分 · 21 道必吃 · 西安占 49 道 (55%) · 数据源: journal.json + expenses-table.md + 俊哥现场评分</p>

  <h3 class="rank-sub">📊 统计总览 · 89 道菜</h3>
  {render_ranking_table(rank_concl)}

  <h3 class="rank-sub">⭐⭐⭐⭐⭐ 必吃榜 · 21 道</h3>
  {render_ranking_table(rank_5star)}

  <h3 class="rank-sub">⭐⭐⭐⭐ 非常不错榜 · 35 道</h3>
  {render_ranking_table(rank_4star)}

  <h3 class="rank-sub">⭐⭐⭐ 好吃榜 · 31 道</h3>
  {render_ranking_table(rank_3star)}

  <h3 class="rank-sub">⭐⭐ 一般榜 · 2 道</h3>
  {render_ranking_table(rank_2star)}

  <h3 class="rank-sub">🏆 按店家 5 星聚集 (Top 店)</h3>
  {render_ranking_table(rank_by_store)}

  <h3 class="rank-sub">📌 城市推荐 Top</h3>
  {render_ranking_table(rank_by_city)}

  <h3 class="rank-sub">💰 性价比榜 (5星 ÷ 整桌价)</h3>
  {render_ranking_table(rank_by_price)}

  <h3 class="rank-sub">🏆 9 日按日时序汇总</h3>
  {render_ranking_table(rank_by_day)}

  <div class="rank-concl">
    <h3>🎯 终极结论</h3>
    <ul>
      <li><b>9 日 89 道菜</b>, 5星率 23.6% (21 道必吃), 整体满意度极高</li>
      <li><b>西安</b> 是美食核心 (49 道 55%), 5星占 14 道 (66% 必吃)</li>
      <li><b>晓长安·新陕菜 (曲江店)</b> 是唯一"全 5 星桌" (4 道全必吃, 同学请客 ¥0, 性价比+出片度双高)</li>
      <li><b>诚意和 (交大店)</b> 是"葫芦头三鲜煮馍"必吃店, 3 道全 5 星</li>
      <li><b>最便宜 5星</b>: 盐筋儿 ¥1.5/串 (福缘厚饺子), 羊汤烩面 ¥7/碗 (方城), 拌粉 ¥5 (南昌大学)</li>
      <li><b>唯一 2 星坑</b>: 蟹脚捞粉 ¥53 (打平伙) + 板栗烧老鹅 (姚家厨房, 鹅肉咬不动)</li>
      <li><b>整桌 9 日最贵</b>: D5 ¥400.9 (兴庆宫) / D9 ¥375 (合肥) / D2 ¥350+ (武汉+方城+西安)</li>
      <li><b>D7 晓长安</b> 是性价比之王: 整桌估 ¥300-500, 4 道全 5 星 = ¥0 自出 (同学请客)</li>
    </ul>
  </div>
</div>'''

# === Header 11 tab ===
def header_html():
    links = ['index.html','day0.html','day1.html','day2.html','day3.html',
             'day4.html','day5.html','day6.html','day7.html','day8.html','day9.html']
    labels = ['总览','D0','D1','D2','D3','D4','D5','D6','D7','D8','D9']
    parts = []
    for i, (href, label) in enumerate(zip(links, labels)):
        cls = 'tab-btn active' if i == 0 else 'tab-btn'
        parts.append(f'    <a href="{href}" class="{cls}">{label}</a>')
    return '\n'.join(parts)

# === 8 大费用类别 ===
with open('skills/_fee_classification.json', encoding='utf-8') as f:
    FEE = json.load(f)

CAT_ORDER = ['A_meals','B_hotel','C_toll','D_charge','E_sight','F_shop','G_park','H_drink']
CAT_COLORS = {
  'A_meals':'#b58940','B_hotel':'#8a6035','C_toll':'#b94a3a',
  'D_charge':'#6b8aa6','E_sight':'#5a7a52','F_shop':'#9c7fb5',
  'G_park':'#c4a060','H_drink':'#8a4f7c',
}
CAT_LABELS = {
  'A_meals':'🍜 餐饮','B_hotel':'🏨 住宿','C_toll':'🛣️ 过路费','D_charge':'🔌 充电',
  'E_sight':'🎫 景点','F_shop':'🛍️ 购物','G_park':'🅿️ 停车','H_drink':'🥤 饮品/文创',
}
TOTAL = 7530.78

def render_cat_cards():
    cards = []
    for cat in CAT_ORDER:
        d = FEE.get(cat, {})
        cnt = d.get('count', 0)
        tot = d.get('total', 0)
        pct = tot / TOTAL * 100
        cards.append(f'''
        <div class="cat-card" style="--c:{CAT_COLORS[cat]}">
          <div class="cat-name">{CAT_LABELS[cat]}</div>
          <div class="cat-num">¥{tot:.0f}</div>
          <div class="cat-bar"><div class="cat-fill" style="width:{pct:.1f}%;background:{CAT_COLORS[cat]};"></div></div>
          <div class="cat-meta">{cnt} 笔 · {pct:.1f}%</div>
        </div>''')
    return ''.join(cards)

# === 9 日精华剧透墙 ===
DAY_NARRATIVES = {
    'D0': '傍晚 18 点，把东阳兴平西路 428 号门口那台电车塞满 7 口人的行李，从木铭建材展厅出发。G60 沪昆一路向西，暮色里在德兴东服务区给车补上第一口电，再接着开到 22:50 才下洪腾收费站，一头扎进南昌前湖大道、南昌大学旁边的麗枫酒店——这趟九日自驾的第一晚，就这么踏实地落在了高速尽头。',
    'D1': '早上南昌大学食堂一碗皮蛋肉饼瓦罐汤加拌粉，10:53 到八一广场让四个小孩人手一面小国旗合影。中午被豫章美食城的打平伙·鲜辣小炒彻底麻翻，13:30 上 G70 福银直奔武汉光谷。傍晚长江大桥桥头看黄鹤楼灯光秀——金红色五层飞檐倒映在江面，粮道街的油饼包烧麦喂饱 7 口人。',
    'D2': '07:19 大成路 8 号吃武汉过早：余记三鲜豆皮 + 丽九早点（雷军同款热干面套餐），街边塑料桶上蹲着吃才有味道。09:16 上 G4201 转入 G70 福银，12:57 抵达南阳卧龙区——高速费 ¥150 跑了 400 km。下午武侯的祠的诸葛亮躬耕地逛完，15:23 上 G55 二广，20:22 从西安绕城纺织城出口下高速。夜里龙湖西安曲江天街小六汤包、烤肉 + 雪花啤酒——西安的第一晚就在肉香里泡过去。',
    'D3': '一整天献给兵马俑。G30 连霍 40 km 到临潼，2 大人票 ¥120×2（3 小孩全部免票）。铜车马、一号坑的兵俑方阵，让四个孩子第一次知道「历史」长什么样。魏家凉皮、魏斯理汉堡、下午西安明城墙骑车一圈——老马家泡馍、阿鹏烧烤纸包鱼 ¥269 两家 AA，西安的第一天就这么过完了。',
    'D4': '06:00 明城墙跑步打卡。早饭后清真·刘家肉丸胡辣汤 + 牛肉饼 + 牛杂肝汤，12:00 杀到西安交大兴庆校区食堂——大学食堂 ¥72 三合一 + 卤肉饭喂饱 7 口人。下午碑林博物馆 2 大 1 学 1 免费 ¥312，出来买个盖章本 ¥39 留念。傍晚玲玲面馆碑林北门，夜里走一圈大雁塔外围（没买票 ¥0）。',
    'D5': '早上另一家肉丸子胡辣汤（整桌 ¥62 AA）。中午诚意和葫芦头三鲜煮馍（交大店）4 道菜 + 6 瓶夜冰。傍晚是勇利赵家烤肉坊响塘广场店 ¥251.9 两人份，老师请客但俊哥单独出；其余 6 人份另一家烤肉 ¥131 AA。晚上李若桃奶茶 ¥27 AA，酒店新店 ¥300 AA。',
    'D6': '06:30 早起给车充电 ¥40 + 停车 ¥8。早餐洒金桥腊汁牛肉夹馍×4 + 水煎包×14 + 甑糕×4 ¥66 AA。09:00 小雁塔 + 西安博物院政策性免，停车 ¥12。12:00 水盆羊肉 + 老虎菜 ¥99 AA。下午俊哥在西安的老同学聚会——具体某家老字号，¥？占位。',
    'D7': '中午同学请客晓长安·新陕菜（曲江店）午餐，俊哥 ¥0 不用出。14:38 从灞桥上 G30 连霍，19:31 在渑池服务区吃泡面 + 白吉饼 ¥30.8 AA，再给电车补电 ¥118.9。21:48 从许昌西下高速，过路费整段 ¥234.6。23:00 兰欧尚品酒店（许昌）¥458 AA。',
    'D8': '08:30 早餐支干烧麦油茶老店——1 大份丸子汤 + 其他 ¥36 AA。再来一份豌豆糕 ¥6 AA。11:10 杀到胖东来时代广场店——22 件 ¥326.5 战利品，从精酿啤酒到 DL 零食。12:30 中午烩面 ¥26 AA。15:10 许昌站上高速，21:00 到曼斯顿尚品酒店（合肥西站科学大道地铁站店）¥332.51 AA。',
    'D9': '最后一天。09:30 到安徽博物院新馆（合肥政务区，4A 景区 / 国家一级博物馆，免费）—— 1F 安徽文明史陈列厅遗址墙前留影，2F 安徽文房四宝专题厅。11:30 文创商店买雪糕 ¥80 AA。中午姚家厨房（合肥万象城店）5 道徽菜整桌 ¥375——鱼丸汤、凉拌豆芽、毛豆炒虾米、凉拌干丝。14:35 抵合肥金寨路收费站上高速，15:30 服务区喝卡旺卡奶茶 ¥72 AA。22:01 抵义乌望道收费站下高速——22:30 终于回到东阳白云街道兴平西路 428 号。九日 3200+ 公里，¥7,530.78——完。',
}

# 用 slug -> 食物关键词匹配
SLUG_MAP = {
    'huanghelou': '黄鹤楼', 'nanchang_dc': '南昌大学食堂',
    'pidan_roubing_waguantang': '皮蛋肉饼瓦罐汤', 'nanchang_banfen': '南昌拌粉',
    'bayi_square_flag': '八一广场·小国旗', 'bayi_panorama': '八一广场全景',
    'receipt_lunch': '午餐结账', 'wuhan_cjdq': '武汉长江大桥',
    'nanyang_wlg': '南阳卧龙岗', 'bingmayong': '兵马俑',
    'wm_daochu': '未命名导出', 'xian_chengqiang': '西安城墙',
    'xian_d2_dinner': '西安第二天晚餐', 'dayanta_dtybyc': '大雁塔·大唐不夜城',
    'dtybyc_xiaoye': '大唐不夜城宵夜', 'youpomian': '油泼面',
    'xajtu_lunch': '西安交大午餐', 'xian_beilin': '西安碑林博物馆',
    'fangsuo': '方所图书馆', 'shuipen_yangrou': '水盆羊肉',
    'hulutou_sxzm': '葫芦头三鲜煮馍', 'xingqinggong_chashi': '兴庆宫·茶室',
    'tongxue_huiju': '同学聚会', 'xiaoyanta_xabwg': '小雁塔·西安博物院',
    'xuchang_guoze': '许昌过早', 'ahbwg': '安徽博物院',
    'ahbwg_yizhi_wall': '安徽博物院遗址墙', 'ahbwg_wenfang': '安徽文房四宝',
    'yao_maodou': '姚家厨房·毛豆炒虾米', 'yao_gansi': '姚家厨房·凉拌干丝',
    'yao_store': '姚家厨房店招', 'yao_douya': '姚家厨房·凉拌豆芽',
    'yao_yuwan': '姚家厨房·鱼丸汤', 'yao_4xiao': '姚家厨房·4 道小菜',
    'jinzhai_toll': '合肥金寨路收费站', 'yiwu_wangdao_toll': '义乌望道收费站',
    'caijiamo': '菜夹馍', 'liujia_hulatang_signboard': '刘家肉丸胡辣汤招牌',
    'chengyihuo_signboard': '诚意和招牌', 'xiaochangan_table': '晓长安餐桌',
    'xiaochangan_shaguo': '晓长安砂锅', 'xiaochangan_liangpi': '晓长安凉皮',
    'xiaochangan_hongshao': '晓长安红烧', 'xiaochangan_hezi': '晓长安盒子',
    'zhigan_shaomai': '支干烧麦', 'zhigan_street': '支干烧麦街景',
    'niurou_wanzi': '牛肉丸子', 'xiaoyanta_tower': '小雁塔塔身',
}

def photo_caption(fname):
    name = fname.replace('.jpg','').replace('.JPG','')
    parts = name.split('_')
    if len(parts) < 3:
        return name
    slug = '_'.join(parts[2:])
    for en, zh in SLUG_MAP.items():
        if en in slug:
            return zh
    return slug.replace('_', ' ')

def pick_cover(d):
    files = d.get('_photos_files', [])
    if not files:
        return None
    PRIORITY_KW = ['bingmayong','beilin','chengqiang','fangsuo','ahbwg','huanghelou','wenfang','yizhi','xiaoyanta','dayanta','xingqinggong']
    for f in files:
        if any(k in f for k in PRIORITY_KW):
            return f
    return files[0]

def pick_food(d, max_n=2):
    files = d.get('_photos_files', [])
    FOOD_KW = ['粉','肉','汤','饼','包','馍','面','烧麦','胡辣','丸子','夹馍','饺子','宵夜','酒','烤','豆皮','麻酱','lunch','dinner','breakfast','hongshao','shaguo','liangpi','youpo','biangbiang','fangsuo','tongxue']
    result = []
    for f in files:
        if any(k in f.lower() for k in FOOD_KW):
            result.append(f)
            if len(result) >= max_n:
                break
    if not result and len(files) > 1:
        result = files[1:3]
    return result

def render_teaser(d):
    key = d['key']
    date_short = d['date'][5:].replace('-','/') if d.get('date') else ''
    cover_file = pick_cover(d)
    foods_files = pick_food(d)
    narrative = DAY_NARRATIVES.get(key, d.get('name',''))

    photos_list = []
    if cover_file:
        cap = photo_caption(cover_file)
        enc = urllib.parse.quote(cover_file)
        photos_list.append(f'<img class="main-image" src="{PHOTO_BASE}{enc}" alt="{esc(cap)}" loading="lazy">')
    for f in foods_files[:2]:
        cap = photo_caption(f)
        enc = urllib.parse.quote(f)
        photos_list.append(f'<img class="food-thumb" src="{PHOTO_BASE}{enc}" alt="{esc(cap)}" loading="lazy">')

    if not photos_list:
        photos_html = '<div class="teaser-card-images teaser-empty">📷</div>'
    else:
        photos_html = '<div class="teaser-card-images">' + ''.join(photos_list) + '</div>'

    return f'''
      <article class="teaser-card">
        <header class="teaser-head">
          <span class="teaser-day">{esc(key)}</span>
          <span class="teaser-date">{esc(date_short)}</span>
        </header>
        <h3 class="teaser-title">{esc(d.get('name',''))}</h3>
        {photos_html}
        <p class="teaser-narr">{esc(narrative)}</p>
        <a class="teaser-cta" href="day{int(key[1:])}.html">查看当天真实自驾路线与美食细节 →</a>
      </article>'''

# === ★ 渲染双分类卡 ===
def render_stars(level):
    """level: 1-5"""
    return '★' * level + '☆' * (5 - level)

def render_card(title, level, addr, reason):
    color = '#f59e0b' if level >= 4 else ('#9ca3af' if level <= 2 else '#fbbf24')
    return f'''
      <article class="rec-card">
        <div class="rec-stars" style="color:{color}">{render_stars(level)}</div>
        <h4 class="rec-title">{esc(title)}</h4>
        <div class="rec-addr">📍 {esc(addr)}</div>
        <p class="rec-reason">{esc(reason)}</p>
      </article>'''

def render_stars_legend():
    return '''
      <div class="stars-legend">
        <div class="legend-row"><span class="stars">★★★★★</span> <span class="legend-text">5星 · 必去不可替代，不去等于白来</span></div>
        <div class="legend-row"><span class="stars">★★★★☆</span> <span class="legend-text">4星 · 强烈推荐，能去最好，体验极佳</span></div>
        <div class="legend-row"><span class="stars">★★★☆☆</span> <span class="legend-text">3星 · 推荐，可去可不去，沿途有替代</span></div>
        <div class="legend-row"><span class="stars">★★☆☆☆</span> <span class="legend-text">2星 · 不太推荐，性价比低、服务差（避坑）</span></div>
        <div class="legend-row"><span class="stars">★☆☆☆☆</span> <span class="legend-text">1星 · 完全别去，踩雷避坑</span></div>
      </div>'''

# === 完整 CSS ===
GLOBAL_CSS = '''
* { box-sizing: border-box; }
body {
  margin: 0; padding: 0;
  font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif;
  background: #f5f1e8; color: #2c2620; font-size: 14px; line-height: 1.75;
}
a { color: #8a6035; text-decoration: none; }
a:hover { text-decoration: underline; }

/* ===== Header (220px Logo + 11 tab + sticky) ===== */
.travel-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 20px 10px;
  background-color: #ffffff;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
  position: sticky;
  top: 0;
  z-index: 1000;
}
.logo-container {
  display: flex !important;
  justify-content: center !important;
  align-items: center !important;
  width: 100% !important;
  margin-top: 10px !important;
  margin-bottom: 25px !important;
}
.site-logo {
  height: 220px !important;
  width: auto !important;
  object-fit: contain !important;
  filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.03)) !important;
  transition: transform 0.3s ease !important;
}
.site-logo:hover {
  transform: scale(1.02) !important;
}
.day-indices {
  display: flex !important;
  flex-wrap: wrap !important;
  justify-content: center !important;
  gap: 12px !important;
  width: 100% !important;
  max-width: 850px !important;
}
.tab-btn {
  display: inline-block;
  padding: 8px 16px;
  border-radius: 999px;
  background: #f5f1e8;
  color: #5a4a35;
  font-size: 14px;
  transition: all 0.2s;
}
.tab-btn:hover { background: #e8d9b8; text-decoration: none; }
.tab-btn.active {
  background: #b94a3a;
  color: #fff;
  font-weight: 600;
}

/* ===== Container ===== */
.container { max-width: 1080px; margin: 0 auto; padding: 0 24px; }
h2 {
  font-family: "Noto Serif SC", "Songti SC", serif;
  font-size: 26px; color: #3a2818; margin: 48px 0 16px; text-align: center;
  letter-spacing: 0.05em;
}
h2 .tag { color: #b94a3a; font-size: 12px; letter-spacing: 0.3em; display: block; margin-bottom: 6px; }
.subtitle { text-align: center; color: #888; font-size: 13px; margin: -8px 0 16px; }

/* ===== 全线路总览图 (580px 夯死) ===== */
#overview-map {
  width: 100% !important;
  height: 580px !important;
  background-color: #1a1a1a !important;
  margin: 20px 0;
  border-radius: 12px;
  overflow: hidden;
}
.map-note { font-size: 12px; color: #888; margin-top: 8px; text-align: center; }

/* ===== KPI (3,200+ km / 70 / ¥7,530) ===== */
.kpi-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 18px;
  margin: 28px 0;
}
.kpi-card {
  background: #fffef9;
  border-radius: 12px;
  padding: 24px 20px;
  text-align: center;
  box-shadow: 0 2px 10px rgba(80,60,30,.08);
  border-top: 3px solid #b94a3a;
}
.kpi-card .num {
  font-family: "Noto Serif SC", serif;
  font-size: 36px;
  font-weight: 700;
  color: #b94a3a;
  line-height: 1.1;
}
.kpi-card .label {
  font-size: 13px;
  color: #888;
  margin-top: 6px;
  letter-spacing: 0.1em;
}

/* ===== 8 大费用类别 ===== */
.cat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 14px;
  margin: 20px 0 40px;
}
.cat-card {
  background: #fffef9;
  border-radius: 10px;
  padding: 18px 18px 14px;
  box-shadow: 0 2px 8px rgba(80,60,30,.06);
  border-left: 4px solid var(--c);
}
.cat-name { font-size: 13px; color: #5a4a35; }
.cat-num { font-family: "Noto Serif SC", serif; font-size: 24px; color: #2c2620; margin: 6px 0; }
.cat-bar { background: #f0e8d4; border-radius: 4px; height: 8px; overflow: hidden; margin-bottom: 6px; }
.cat-fill { height: 100%; border-radius: 4px; min-width: 2px; }
.cat-meta { font-size: 11px; color: #888; }

/* ===== ★ 推荐 (12 景点 + 14 美食) ===== */
.stars-legend {
  background: #fffef9;
  border-radius: 10px;
  padding: 18px 22px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(80,60,30,.06);
  border: 1px solid var(--line);
  max-width: 720px;
  margin-left: auto;
  margin-right: auto;
}
.legend-row { display: flex; align-items: center; gap: 12px; padding: 4px 0; font-size: 13px; }
.stars { color: #f59e0b; font-size: 16px; letter-spacing: 2px; min-width: 80px; }
.legend-text { color: #5a4a35; }

.rec-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
  margin: 16px 0 40px;
}
.rec-card {
  background: #fffef9;
  border-radius: 10px;
  padding: 16px 18px;
  box-shadow: 0 2px 8px rgba(80,60,30,.06);
  border-top: 3px solid var(--accent, #b94a3a);
  border: 1px solid #ece4d0;
}
.rec-stars {
  font-size: 16px;
  letter-spacing: 2px;
  margin-bottom: 8px;
  font-weight: 600;
}
.rec-title {
  font-family: "Noto Serif SC", serif;
  font-size: 15px;
  font-weight: 600;
  color: #3a2818;
  margin: 0 0 6px;
}
.rec-addr {
  font-size: 11px;
  color: #888;
  margin-bottom: 8px;
  line-height: 1.4;
}
.rec-reason {
  font-size: 12px;
  line-height: 1.65;
  color: #5a4a35;
  margin: 0;
  text-align: justify;
}

/* ===== Teaser Wall (9 日) ===== */
.teaser-wall {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 20px;
  margin: 20px 0 60px;
}
.teaser-card {
  background: #fffef9;
  border-radius: 14px;
  padding: 0;
  box-shadow: 0 4px 16px rgba(80,60,30,.08);
  display: flex;
  flex-direction: column;
  border-top: 4px solid #b94a3a;
  overflow: hidden;
}
.teaser-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 20px;
  background: #faf6ee;
  border-bottom: 1px solid #e0d8c0;
}
.teaser-day {
  font-family: "Noto Serif SC", serif;
  font-size: 22px;
  font-weight: 700;
  color: #b94a3a;
  letter-spacing: 0.05em;
}
.teaser-date { font-size: 12px; color: #888; letter-spacing: 0.1em; }
.teaser-title {
  font-family: "Noto Serif SC", serif;
  font-size: 17px;
  font-weight: 600;
  color: #3a2818;
  padding: 14px 20px 8px;
  margin: 0;
}
.teaser-narr {
  font-size: 13px;
  line-height: 1.85;
  color: #5a4a35;
  padding: 0 20px 14px;
  margin: 0;
  text-align: justify;
}
.teaser-cta {
  display: block;
  padding: 14px 20px;
  background: #b94a3a;
  color: #fff !important;
  text-align: center;
  font-weight: 600;
  font-size: 14px;
  border-radius: 0;
  letter-spacing: 0.05em;
  transition: background 0.2s;
  margin-top: auto;
}
.teaser-cta:hover { background: #9c3c30; text-decoration: none; }
.teaser-card-images {
  display: flex !important;
  gap: 12px !important;
  justify-content: flex-start !important;
  align-items: center !important;
  flex-wrap: nowrap !important;
  overflow: hidden !important;
  margin-bottom: 15px !important;
  padding: 0 20px;
}
.teaser-card-images .main-image {
  width: 100% !important;
  height: 240px !important;
  max-height: 240px !important;
  object-fit: cover !important;
  border-radius: 8px !important;
  margin-bottom: 12px !important;
  transition: transform 0.3s ease !important;
  flex-shrink: 1;
}
.teaser-card-images .main-image:hover { transform: scale(1.02); }
.teaser-card-images .food-thumb {
  width: 120px !important;
  height: 120px !important;
  object-fit: cover !important;
  border-radius: 6px !important;
  flex-shrink: 0;
}
.teaser-empty {
  height: 240px;
  background: linear-gradient(135deg, #f0e8d4 0%, #e0d8c0 100%);
  display: flex !important;
  align-items: center !important;
  justify-content: center;
  font-size: 48px;
  color: #c4a060;
}

/* ===== 美食评分排行榜 ===== */
.ranking-block {
  background: #fffef9;
  border-radius: 12px;
  padding: 24px 28px;
  margin: 20px 0 40px;
  box-shadow: 0 2px 10px rgba(80,60,30,.08);
}
.ranking-intro {
  font-size: 13px;
  color: #888;
  margin: 0 0 18px;
  text-align: center;
}
.rank-sub {
  font-family: "Noto Serif SC", "Songti SC", serif;
  font-size: 16px;
  color: #3a2818;
  margin: 24px 0 10px;
  padding-left: 8px;
  border-left: 3px solid #b94a3a;
}
.rank-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
  margin-bottom: 16px;
}
.rank-table th, .rank-table td {
  padding: 6px 8px;
  border-bottom: 1px solid #ece4d0;
  text-align: left;
}
.rank-table th {
  background: #faf6ee;
  font-weight: 600;
  color: #5a4a35;
  white-space:nowrap;
}
.rank-table tr:nth-child(even) { background: #fffdf7; }
.rank-table td:first-child {
  font-weight: 600;
  color: #b94a3a;
}
.rank-concl {
  margin-top: 24px;
  padding: 18px 22px;
  background: #faf6ee;
  border-radius: 10px;
  border-left: 4px solid #b94a3a;
}
.rank-concl h3 {
  font-family: "Noto Serif SC", "Songti SC", serif;
  font-size: 16px;
  color: #3a2818;
  margin: 0 0 10px;
}
.rank-concl ul {
  margin: 0;
  padding-left: 20px;
  font-size: 13px;
  line-height: 1.85;
  color: #5a4a35;
}
.rank-concl li { margin-bottom: 4px; }

/* ===== 底部 ===== */
footer {
  text-align: center;
  padding: 32px 24px;
  color: #888;
  font-size: 12px;
}

@media (max-width: 720px) {
  .site-logo { height: 140px !important; }
  .tab-btn { padding: 6px 12px; font-size: 13px; }
  .kpi-row { grid-template-columns: 1fr; }
  #overview-map { height: 380px !important; }
  .teaser-wall { grid-template-columns: 1fr; }
  .rec-grid { grid-template-columns: 1fr; }
}
'''

KPI_HTML = '''
<div class="kpi-row">
  <div class="kpi-card">
    <div class="num">3,200<sup style="font-size:18px;">+</sup></div>
    <div class="label">总公里</div>
  </div>
  <div class="kpi-card">
    <div class="num">70</div>
    <div class="label">总账目笔数</div>
  </div>
  <div class="kpi-card">
    <div class="num">¥7,530</div>
    <div class="label">总花费</div>
  </div>
</div>'''

# ★ 分类卡
ATTRACTIONS_HTML = '\n'.join(render_card(t, l, a, r) for t, l, a, r in ATTRACTIONS)
RESTAURANTS_HTML = '\n'.join(render_card(t, l, a, r) for t, l, a, r in RESTAURANTS)

TEASER_HTML = ''.join(render_teaser(d) for d in days)

index_html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>东阳⇄西安 · 九日自驾美食记 · 木铭建材 · 陆雋</title>
<meta name="description" content="2026.08.07 - 08.16 · 9 日自驾美食 · 71 行程点 · 70 笔账目 · ¥7,530.78 · 3,200+ 公里">
<script type="text/javascript">
  window._AMapSecurityConfig = {{
    securityJsCode: "{SEC}"
  }};
</script>
<script type="text/javascript" src="https://webapi.amap.com/maps?v=2.0&key={KEY}&plugin=AMap.Driving,AMap.Polyline,AMap.Marker,AMap.ToolBar,AMap.Scale,AMap.LngLat"></script>
<style>
{GLOBAL_CSS}
</style>
</head>
<body>

<header class="travel-header">
  <div class="logo-container">
    <img src="logo.png" alt="一起旅行" class="site-logo">
  </div>
  <nav class="day-indices">
{header_html()}
  </nav>
</header>

<div class="container">

  <h2><span class="tag">ROUTE OVERVIEW</span>东阳⇄西安 · 九日自驾美食记</h2>
  <p class="subtitle">东阳 → 南昌 → 武汉 → 南阳 → 西安 → 许昌 → 合肥 → 东阳 · 2026.08.07 — 08.16</p>

  <div id="overview-map"></div>
  <p class="map-note">高德卫星底图 + 半透明路网层 · 7 段真实自驾高速曲线 · 59 个 waypoint 拐点</p>

  {KPI_HTML}

  <h2><span class="tag">EXPENSES</span>费用归纳 · 8 大类别</h2>
  <div class="cat-grid">
{render_cat_cards().strip()}
  </div>

  <h2><span class="tag">RECOMMENDATIONS</span>沿途自驾路标推荐 · 红黑榜</h2>
  <p class="subtitle">基于本次全家出行真实体验 · 12 景点 + 18 美食 · 严格星级评分</p>

  {render_stars_legend()}

  <h3 style="font-family:'Noto Serif SC',serif;font-size:18px;color:#3a2818;margin:24px 0 12px;">🏛️ 一、沿途核心景点 · ATTRACTIONS (12 项)</h3>
  <div class="rec-grid">
{ATTRACTIONS_HTML}
  </div>

  <h3 style="font-family:'Noto Serif SC',serif;font-size:18px;color:#3a2818;margin:24px 0 12px;">🍜 二、沿途饕餮饭店与特色美食 · RESTAURANTS & FOOD (23 项)</h3>
  <div class="rec-grid">
{RESTAURANTS_HTML}
  </div>

  <h2><span class="tag">FOOD RANKING</span>美食评分排行榜 · 89 道菜</h2>
  <p class="subtitle">从 美食评分排行榜.md 完整嵌入 · 必吃 / 非常不错 / 好吃 / 一般 四级评分</p>

  {RANKING_HTML}

  <h2><span class="tag">NINE DAYS · TEASER</span>九日精华剧透</h2>
  <p class="subtitle">点击下方卡片查看当天完整自驾路线、行程点与美食细节</p>
  <div class="teaser-wall">
{TEASER_HTML}
  </div>

</div>

<footer>木铭建材 · 陆雋 · 2026.08</footer>

<script>
var HIGHWAY_SATELLITE_PATHS = {HIGHWAY_PATHS_JSON};

window.onload = function() {{
  setTimeout(function() {{ initOverviewMap(); }}, 300);
}};

function initOverviewMap() {{
  var overviewMap = new AMap.Map('overview-map', {{
    viewMode: '2D', zoom: 5, center: [114.30, 30.60],
    layers: [
      new AMap.TileLayer.Satellite(),
      new AMap.TileLayer.RoadNet()
    ]
  }});

  HIGHWAY_SATELLITE_PATHS.forEach(function(route) {{
    var amapPath = route.path.map(function(coord) {{
      return new AMap.LngLat(coord[0], coord[1]);
    }});
    var polyline = new AMap.Polyline({{
      path: amapPath, strokeColor: route.color, strokeWeight: 7,
      strokeOpacity: 0.95, lineJoin: 'round', showDir: true
    }});
    overviewMap.add(polyline);
  }});

  overviewMap.on('complete', function() {{
    overviewMap.resize();
    overviewMap.setFitView();
  }});
}}
</script>
</body>
</html>
'''

with io.open('网站/index.html', 'w', encoding='utf-8') as f:
    f.write(index_html)
print(f'index.html written: {len(index_html.encode("utf-8"))} bytes')
print(f'景点: {len(ATTRACTIONS)} 项, 美食: {len(RESTAURANTS)} 项')
print('done')