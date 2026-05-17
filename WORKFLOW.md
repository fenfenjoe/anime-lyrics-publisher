# 动漫歌词发布系统 — 定时任务流程图

> **维护说明**：每次修改 `workbuddy_automation.py` 或 `anime_lyrics_spider.py` 中的任务逻辑后，  
> 必须同步更新本文件。自动化任务的提示词已包含此要求。

---

## 一、每周任务（周六凌晨 2:00）

```
python workbuddy_automation.py weekly
```

```
┌─────────────────────────────────────────────────────────────────┐
│                      每周歌词爬取任务                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │   init_weekly_anime()          │
              │   补充待爬取队列               │
              └───────────────────────────────┘
                              │
              ┌───────────────┼───────────────────────────┐
              │               │                           │
              ▼               ▼                           ▼
   ┌──────────────┐  ┌─────────────────┐     ┌─────────────────────┐
   │ 主池有未入库  │  │ 主池已耗尽       │     │ 主池+后备池均耗尽    │
   │ 动画？        │  │ 后备池有新动画？ │     │ → 尝试 AniList      │
   │              │  │                 │     │   自动发现新动画     │
   └──────┬───────┘  └────────┬────────┘     └──────────┬──────────┘
          │ Yes               │ Yes                      │
          ▼                   ▼                          ▼
   随机取 ≤3部         从后备池随机取 ≤3部      ┌──────────────────────┐
   加入 pending 队列   加入 pending 队列        │ AniList API 获取     │
                                               │ 热门动漫列表（Top50） │
                                               └──────────┬───────────┘
                                                          │
                                               ┌──────────▼───────────┐
                                               │ 筛选：不在数据库 &&   │
                                               │ 在 ANIME_SONG_CONFIG │
                                               │ 中有歌曲配置         │
                                               └──────────┬───────────┘
                                                          │
                                               ┌──────────▼───────────┐
                                               │ 有匹配？              │
                                               │  Yes → 加入 pending  │
                                               │  No  → 写警告日志    │
                                               └──────────────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │  get_random_pending_anime()    │
              │  从 pending 队列随机取 1 部    │
              └───────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              │ pending 为空？                 │
              │  Yes → 记录日志，退出          │
              └───────────────────────────────┘
                              │ No
                              ▼
              ┌───────────────────────────────┐
              │  LyricsCrawler.crawl_anime_   │
              │  lyrics(anime)                │
              │  → 从 ANIME_SONG_CONFIG 查配置 │
              └───────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              │ 在配置表中？                   │
              │  No → 标记 failed，退出        │
              └───────────────────────────────┘
                              │ Yes
                              ▼
              ┌───────────────────────────────┐
              │  QQMusicSpider.crawl(anime)   │
              │  逐首搜索 + 歌手交叉验证       │
              │  → 过滤纯音乐、匹配失败曲目    │
              └───────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              │  有歌词？                      │
              │  Yes → 存入 SQLite，           │
              │         状态改 completed       │
              │  No  → 状态改 failed           │
              └───────────────────────────────┘
                              │
                              ▼
                      ┌───────────────┐
                      │   任务结束     │
                      │  更新 task_log │
                      └───────────────┘
```

### 动画池优先级（从高到低）

```
ANIME_LIST（主池，config.py）
    ↓ 耗尽
ANIME_RESERVE_LIST（后备池，config.py）
    ↓ 耗尽
AniList API 自动发现（网络获取热门动漫 Top 50）
    ↓ 网络失败 / 无匹配
记录警告日志（需人工追加 ANIME_SONG_CONFIG 配置）
```

---

## 二、每日任务（每天早上 7:00）

```
python workbuddy_automation.py daily-prepare
      ↓（AI 完成歌词分析后）
python workbuddy_automation.py daily-publish
```

```
┌──────────────────────────────────────────────────────────────────┐
│                     每日文章发布任务                              │
└──────────────────────────────────────────────────────────────────┘

Step 1: daily-prepare
──────────────────────────────────────────────
  数据库取 1 首未使用歌词
      │
      ▼
  写入 data/pending_analysis.json
      │
      ▼
  打印歌词分析 Prompt
      │
      ▼
  [等待 WorkBuddy AI 执行分析]
  AI 调用 ai_analyzer.write_result_to_file(json_str)
  → 写入 data/analysis_result.json

Step 2: daily-publish
──────────────────────────────────────────────
  读取 data/analysis_result.json
      │
      ▼
  爬取动画封面图 + 正文配图（image_spider）
      │
      ▼
  上传配图到微信永久素材，获取 CDN URL
      │
      ▼
  format_article() 格式化文章 HTML
      │
      ▼
  存入数据库 articles 表（status=draft）
      │
      ▼
  publish_article_to_wechat() 发布到草稿箱
      │
      ▼
  任务完成
```

---

## 三、关键数据流

```
config.py
  ANIME_LIST ─────────────┐
  ANIME_RESERVE_LIST ─────┤──→ init_weekly_anime() ──→ SQLite anime(status=pending)
  AniList API（自动） ─────┘         │
                                     ▼
                          crawl_weekly_lyrics()
                                     │
                                     ▼
                          ANIME_SONG_CONFIG（anime_lyrics_spider.py）
                                     │
                                     ▼
                          QQ Music API ──→ SQLite lyrics 表
                                                  │
                                                  ▼
                                     daily-prepare / daily-publish
                                                  │
                                                  ▼
                                          微信公众号草稿箱
```

---

## 四、数据库表结构（简）

| 表名 | 关键字段 |
|------|---------|
| `anime` | id, name, name_jp, year, status（pending/completed/failed） |
| `lyrics` | id, anime_id, song_name, singer, song_type, lyrics_content |
| `articles` | id, lyrics_id, article_title, article_content, status |
| `task_logs` | id, task_type, status, message, created_at |

---

*最后更新：2026-03-24*
