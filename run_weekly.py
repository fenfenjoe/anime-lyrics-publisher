# -*- coding: utf-8 -*-
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from database import db
import logging

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(config.LOG_FILE, encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

logger.info("=" * 50)
logger.info("【每周任务】开始：歌词爬取")
logger.info("=" * 50)

from anime_lyrics_spider import crawl_weekly_lyrics
crawl_weekly_lyrics()

logger.info("【每周任务】完成")
