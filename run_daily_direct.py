# -*- coding: utf-8 -*-
"""直接执行文章生成+发布（跳过等待循环，结果已就绪）"""
import sys
import logging
sys.path.insert(0, r'c:\Users\Admin\WorkBuddy\Claw\anime-lyrics-publisher')

import config
from database import db

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

import json

# 读取已就绪的分析结果
RESULT_FILE = r'c:\Users\Admin\WorkBuddy\Claw\anime-lyrics-publisher\data\analysis_result.json'
PENDING_FILE = r'c:\Users\Admin\WorkBuddy\Claw\anime-lyrics-publisher\data\pending_analysis.json'

with open(RESULT_FILE, 'r', encoding='utf-8') as f:
    result = json.load(f)

with open(PENDING_FILE, 'r', encoding='utf-8') as f:
    task = json.load(f)

logger.info(f"读取结果: {result.get('status')}, 共 {len(result.get('result', []))} 条")

# 格式化文章
from article_generator import format_article
article = format_article(task, result)
logger.info(f"文章标题: {article['title']}")

# 查找对应歌词记录
lyrics_list = db.get_random_unused_lyrics(limit=20)
lyrics_id = None
for l in lyrics_list:
    if l.get('song_name') == task.get('song_name'):
        lyrics_id = l['id']
        break

if not lyrics_id:
    # 如果没找到，取第一个
    all_lyrics = db.get_random_unused_lyrics(limit=1)
    if all_lyrics:
        lyrics_id = all_lyrics[0]['id']
    else:
        logger.error("找不到对应歌词记录")
        sys.exit(1)

# 存库
article_id = db.add_article(
    lyrics_id=lyrics_id,
    article_title=article['title'],
    article_content=article['content'],
    status='draft'
)
article['article_id'] = article_id
logger.info(f"文章已存库: ID={article_id}")

# 打印文章内容预览
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
print("\n" + "="*60)
print("【文章内容预览】")
print("="*60)
print(article['content'])
print("="*60)

# 发布到微信公众号
from wechat_publisher import publish_article_to_wechat
success = publish_article_to_wechat(article_id)
if success:
    logger.info("文章发布到微信公众号草稿箱成功")
else:
    logger.warning("微信发布失败（可能未配置 AppID），文章已保存为草稿状态")

logger.info("每日任务完成")
