# 高德 API Key - 旅行网站密钥 (示例占位符)

> ⚠️ **本文件是示例占位符, 真实 key 替换为占位符**
> **真 key 放到 .env 文件 (已 .gitignore 排除)**
> 详细说明见根目录 `amap_api_key.md` (真 key 文件, 不上传)

## 🔑 占位符

```
# 请到 https://lbs.amap.com/dev/key/app 申请
# 复制 .env.example 为 .env, 然后填入:

AMAP_KEY=YOUR_AMAP_KEY_HERE
AMAP_SECURITY=YOUR_SECURITY_CODE_HERE
```

**应用名称**: 一起旅行 (Travel-Companion)
**用途**: 高德 JS API v2.0 (地图 + 驾车路径规划) + REST API (POI 搜索 + reverse_geocode)
**Key 申请日期**: 任意 (2021-12-02 之后, 必须配 securityJsCode)

## 📊 调用情况 (示例)

| 项目 | 数量 | 说明 |
|---|---:|---|
| 9 日 waypoint 总数 | 71 | 每 day 1 张地图 |
| D1-D8 起点→终点 query | 8 次 | AMap.Driving.search |
| D9 多段 query (4 段) | 4 次 | 合并 1 条完整 polyline |
| 总 API 调用 | 12 次/页面加载 | 一次性, 不频繁 |

## 🛡️ 安全措施

### 必须: 高德后台加 referer 白名单

1. 登录 https://lbs.amap.com/dev/key/app
2. 找到你的 key
3. 编辑 → Referer 白名单 → 添加你的域名
4. 保存

效果: 只能从你的域名调用, 别人 copy key 也用不了。

### 备选: IP 白名单

固定 IP 服务器可加 IP 白名单, 但 CDN 域名 IP 会变, 不推荐。

## 🔄 Key 被拉黑 / 失效 怎么办

1. 登录高德后台 → 重置或新建 key
2. 新建类型: **Web 端 (JS API)**
3. Referer 白名单: 你的域名/*
4. 替换 .env 里的 `AMAP_KEY` + `AMAP_SECURITY`
5. 重启服务

## 📞 联系方式

- 高德客服: https://lbs.amap.com/
- 文档: https://lbs.amap.com/api/jsapi-v2/documentation
