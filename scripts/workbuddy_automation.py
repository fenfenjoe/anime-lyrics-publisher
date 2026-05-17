# -*- coding: utf-8 -*-
"""
WorkBuddy Automation 任务入口

本文件对应两条 WorkBuddy 定时 Automation：
  - 每周一次（周六凌晨 2:00）：执行歌词爬取 + 动画入库
  - 每日一次（早上 7:00）：执行歌词分析 + 文章生成 + 公众号发布

WorkBuddy AI 在执行每日 Automation 时，按以下步骤操作：
  1. 运行：python workbuddy_automation.py daily-prepare
     → 脚本从数据库取歌词，写入 data/pending_analysis.json
     → 脚本打印分析 prompt，AI 看到后对歌词进行翻译/语法分析
  2. AI 调用 ai_analyzer.write_result_to_file(json_str) 写入结果
  3. 运行：python workbuddy_automation.py daily-publish
     → 脚本读取 data/analysis_result.json
     → 格式化文章并发布到微信公众号草稿箱

使用方法：
  python workbuddy_automation.py weekly         # 每周爬取任务
  python workbuddy_automation.py daily          # 旧版一次性流程（保留兼容）
  python workbuddy_automation.py daily-prepare  # 每日任务第一步：准备分析任务
  python workbuddy_automation.py daily-publish  # 每日任务第二步：生成文章并发布
"""

import os
import sys
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from database import db

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(config.LOG_FILE, encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


def run_weekly_task():
    """
    ══════════════════════════════════════════════
    【每周任务】每周六凌晨 2:00 执行

    任务内容：
      1. 从热门动画列表随机选取一部动画
      2. 爬取该动画所有 OP/ED 的歌词
      3. 将歌词存入 SQLite 数据库
    ══════════════════════════════════════════════
    """
    logger.info("=" * 50)
    logger.info("【每周任务】开始：歌词爬取")
    logger.info("=" * 50)

    from anime_lyrics_spider import crawl_weekly_lyrics
    crawl_weekly_lyrics()

    logger.info("【每周任务】完成")


def run_daily_prepare():
    """
    ══════════════════════════════════════════════
    【每日任务 Step 1】准备分析任务

    任务内容：
      - 从数据库随机取一首未分析的歌词
      - 写入 data/pending_analysis.json
      - 打印分析 prompt，WorkBuddy AI 执行分析后
        调用 ai_analyzer.write_result_to_file() 写入结果
    ══════════════════════════════════════════════
    """
    logger.info("=" * 50)
    logger.info("【每日任务 Step 1】准备歌词分析任务")
    logger.info("=" * 50)

    from article_generator import prepare_analysis_task
    from ai_analyzer import load_pending_task, build_analysis_prompt

    lyrics_list = db.get_random_unused_lyrics(limit=1)
    if not lyrics_list:
        logger.warning("数据库中没有可用歌词，跳过今日任务")
        return False

    lyrics = lyrics_list[0]
    # get_random_unused_lyrics 已通过 JOIN 带出 anime_name / anime_name_jp，无需再查

    if not prepare_analysis_task(lyrics):
        logger.error("准备分析任务失败")
        return False

    # 打印分析 prompt，WorkBuddy AI 看到后执行分析
    task   = load_pending_task()
    prompt = build_analysis_prompt(task)
    total  = len(task.get('lyrics_lines', []))

    print("\n" + "=" * 60)
    print("【WorkBuddy AI 请执行以下歌词分析】")
    print("=" * 60)
    print(prompt)
    print("=" * 60)
    print(f"\n[重要提醒] 本次共 {total} 句歌词，result 数组必须恰好有 {total} 个元素。")
    print("   如一次输出不够，请分批输出后合并，确保不遗漏任何一句。")
    print("   分析完成后，调用 ai_analyzer.write_result_to_file(json_str) 写入结果。")
    print("   若条数不足，write_result_to_file 会报错并提示你补全。")
    print()
    print("[JSON 字段规范] 每条 result 元素必须使用以下字段名（大小写敏感）：")
    print("   original   - 歌词原文（必填，不能用 'line' 替代）")
    print("   furigana   - 带注音的版本（如无汉字可与 original 相同）")
    print("   translation - 中文翻译（必填）")
    print("   grammar    - 语法要点（日语歌词必填，其他语言可为空字符串）")
    print("   顶层还需有 song_intro 字段（50~100字曲目简介，必填）")
    print("\n分析完成后，请运行：python workbuddy_automation.py daily-publish")

    return True


def run_daily_publish():
    """
    ══════════════════════════════════════════════
    【每日任务 Step 2】生成文章并发布

    前提：data/analysis_result.json 已由 AI 写入
    任务内容：
      - 读取 analysis_result.json
      - 爬取动画封面图和配图（作为封面+正文插图）
      - 格式化为微信公众号文章
      - 发布到公众号草稿箱
    ══════════════════════════════════════════════
    """
    logger.info("=" * 50)
    logger.info("【每日任务 Step 2】生成文章并发布")
    logger.info("=" * 50)

    import json
    from article_generator import format_article
    from wechat_publisher import WechatPublisher, publish_article_to_wechat
    from ai_analyzer import PENDING_FILE, RESULT_FILE
    from image_spider import crawl_images_for_article

    # 读取分析结果
    if not os.path.exists(RESULT_FILE):
        logger.error(f"分析结果文件不存在: {RESULT_FILE}，请先运行 daily-prepare 并由 AI 完成分析")
        return False

    with open(RESULT_FILE, 'r', encoding='utf-8') as f:
        result = json.load(f)

    if result.get('status') != 'done' or not result.get('result'):
        logger.error("分析结果文件状态异常或内容为空")
        return False

    with open(PENDING_FILE, 'r', encoding='utf-8') as f:
        task = json.load(f)

    # 查找对应歌词记录
    lyrics_list = db.get_random_unused_lyrics(limit=50)
    lyrics_id = None
    for l in lyrics_list:
        if l.get('song_name') == task.get('song_name'):
            lyrics_id = l['id']
            break
    if not lyrics_id and lyrics_list:
        lyrics_id = lyrics_list[0]['id']
    if not lyrics_id:
        logger.error("找不到对应歌词记录")
        return False

    song_name  = task.get('song_name', '')
    singer     = task.get('singer', '')
    anime_name    = task.get('anime_name', '')
    anime_name_jp = task.get('anime_name_jp', '')

    # ── 计算所需正文配图数 ─────────────────────────
    # 每 5 句歌词配 1 张图（开头已用 1 张），正文最少 2 张
    lyrics_count = len(result.get('result', []))
    article_img_count = max(2, lyrics_count // 5)
    logger.info(f"歌词 {lyrics_count} 句，计划正文配图 {article_img_count} 张")

    # ── 读取历史已用微信图片 URL，用于排重 ───────────
    used_wechat_urls = db.get_used_wechat_image_urls()
    logger.info(f"历史已用图片 URL 数量: {len(used_wechat_urls)}")

    # ── 爬取图片 ──────────────────────────────────
    logger.info(f"开始爬取《{anime_name}》相关图片...")
    images_info = crawl_images_for_article(
        anime_name, anime_name_jp,
        article_image_count=article_img_count,
        song_name=song_name,
        singer=singer,
        used_wechat_urls=used_wechat_urls,
    )
    cover_path    = images_info.get('cover')
    article_imgs  = images_info.get('article_images', [])
    logger.info(f"封面图: {cover_path}，正文配图: {len(article_imgs)} 张")

    # ── 上传配图到微信素材，获取 CDN URL ──────────
    publisher = WechatPublisher()
    access_token = publisher.get_access_token()
    wechat_img_urls = []
    if access_token:
        for img_path in article_imgs:
            cdn_url = _upload_image_get_url(publisher, access_token, img_path)
            if cdn_url:
                wechat_img_urls.append(cdn_url)
                logger.info(f"配图上传成功: {cdn_url}")
            else:
                logger.warning(f"配图上传失败，跳过: {img_path}")

    # ── 格式化文章（传入微信 CDN 图片 URL 和 QQ 音乐播放器）────────
    article = format_article(task, result, article_images=wechat_img_urls)
    logger.info(f"文章标题: {article['title']}")

    # 存库
    article_id = db.add_article(
        lyrics_id=lyrics_id,
        article_title=article['title'],
        article_content=article['content'],
        status='draft'
    )
    if cover_path:
        import sqlite3 as _sqlite3
        with _sqlite3.connect(config.DB_PATH) as _conn:
            _conn.execute("UPDATE articles SET cover_image_path=? WHERE id=?", (cover_path, article_id))

    article['article_id'] = article_id
    logger.info(f"文章已存库: ID={article_id}")

    # 发布到微信公众号草稿箱
    publish_article_to_wechat(article_id)
    logger.info("【每日任务 Step 2】完成")
    return True


def _upload_image_get_url(publisher, access_token: str, img_path: str):
    """上传图片到微信永久素材，返回微信 CDN URL（url 字段）"""
    import requests as req
    import urllib3
    urllib3.disable_warnings()
    try:
        _sess = req.Session()
        _sess.trust_env = False  # 绕过无效系统代理
        with open(img_path, 'rb') as f:
            ext = os.path.splitext(img_path)[1].lower() or '.jpg'
            mime = 'image/jpeg' if ext in ('.jpg', '.jpeg') else 'image/png'
            resp = _sess.post(
                'https://api.weixin.qq.com/cgi-bin/material/add_material',
                params={'access_token': access_token, 'type': 'image'},
                files={'media': (os.path.basename(img_path), f, mime)},
                timeout=30, verify=False
            )
        data = resp.json()
        # 微信返回 {"media_id": "...", "url": "https://mmbiz.qpic.cn/..."}
        return data.get('url')  # url 可直接在 <img src="..."> 中使用
    except Exception as e:
        logger.warning(f"上传配图异常: {e}")
        return None


def run_daily_task():
    """
    旧版一次性流程（保留向后兼容），与 daily-prepare 逻辑相同。
    在 WorkBuddy Automation 环境中，脚本打印 prompt 后退出，
    AI 完成分析后需手动运行 daily-publish。
    """
    run_daily_prepare()


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''

    if cmd == 'weekly':
        run_weekly_task()
    elif cmd == 'daily-prepare':
        run_daily_prepare()
    elif cmd == 'daily-publish':
        run_daily_publish()
    elif cmd == 'daily':
        run_daily_task()
    else:
        print(__doc__)
        print("\n用法: python workbuddy_automation.py [weekly|daily-prepare|daily-publish|daily]")

