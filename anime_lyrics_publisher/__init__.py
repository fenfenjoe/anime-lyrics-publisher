# -*- coding: utf-8 -*-
"""
微信公众号动漫歌词日语学习文章生成器 - 核心模块
"""

from . import config
from .database import db
from .scheduler import start_scheduler, run_weekly_crawl_now, run_daily_publish_now

__all__ = ['config', 'db', 'start_scheduler', 'run_weekly_crawl_now', 'run_daily_publish_now']
