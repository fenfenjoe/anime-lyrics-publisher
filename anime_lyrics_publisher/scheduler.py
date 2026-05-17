# -*- coding: utf-8 -*-
"""
定时任务调度模块 - 使用 APScheduler 实现每周/每日定时任务
"""

import logging
from datetime import datetime

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from . import config
from spiders.anime_lyrics_spider import crawl_weekly_lyrics
from generator.article_generator import generate_daily_article
from publisher.wechat_publisher import generate_and_publish_article
from .database import db

# 配置日志
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TaskScheduler:
    """定时任务调度器"""

    def __init__(self):
        self.scheduler = BlockingScheduler()
        
    def setup_jobs(self):
        """设置定时任务"""
        
        # 每周爬取任务：每周六凌晨 2:00 执行
        # CronTrigger 参数：minute, hour, day, month, day_of_week
        weekly_trigger = CronTrigger(
            day_of_week=config.WEEKLY_CRAWL_DAY,
            hour=config.WEEKLY_CRAWL_HOUR,
            minute=config.WEEKLY_CRAWL_MINUTE
        )
        
        self.scheduler.add_job(
            func=self.weekly_crawl_task,
            trigger=weekly_trigger,
            id='weekly_crawl',
            name='每周歌词爬取',
            replace_existing=True
        )
        logger.info(f"每周爬取任务已设置: 周{config.WEEKLY_CRAWL_DAY} {config.WEEKLY_CRAWL_HOUR}:{config.WEEKLY_CRAWL_MINUTE:02d}")
        
        # 每日发布任务：每天早上 7:00 执行
        daily_trigger = CronTrigger(
            hour=config.DAILY_PUBLISH_HOUR,
            minute=config.DAILY_PUBLISH_MINUTE
        )
        
        self.scheduler.add_job(
            func=self.daily_publish_task,
            trigger=daily_trigger,
            id='daily_publish',
            name='每日文章发布',
            replace_existing=True
        )
        logger.info(f"每日发布任务已设置: {config.DAILY_PUBLISH_HOUR}:{config.DAILY_PUBLISH_MINUTE:02d}")

    def weekly_crawl_task(self):
        """每周爬取任务的执行函数"""
        logger.info("=== 定时任务：开始每周歌词爬取 ===")
        try:
            crawl_weekly_lyrics()
            logger.info("=== 每周歌词爬取任务完成 ===")
        except Exception as e:
            logger.error(f"每周爬取任务执行失败: {e}")

    def daily_publish_task(self):
        """每日发布任务的执行函数"""
        logger.info("=== 定时任务：开始每日文章生成和发布 ===")
        try:
            generate_and_publish_article()
            logger.info("=== 每日文章发布任务完成 ===")
        except Exception as e:
            logger.error(f"每日发布任务执行失败: {e}")

    def run(self):
        """启动调度器"""
        logger.info("定时任务调度器启动...")
        self.setup_jobs()
        
        try:
            self.scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logger.info("定时任务调度器停止")
            self.scheduler.shutdown()

    def stop(self):
        """停止调度器"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("定时任务调度器已停止")

    def get_jobs(self):
        """获取所有任务状态"""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger)
            })
        return jobs


def start_scheduler():
    """启动调度器的入口函数"""
    scheduler = TaskScheduler()
    scheduler.run()


def run_weekly_crawl_now():
    """手动触发每周爬取任务"""
    logger.info("手动触发每周爬取任务...")
    scheduler = TaskScheduler()
    scheduler.weekly_crawl_task()


def run_daily_publish_now():
    """手动触发每日发布任务"""
    logger.info("手动触发每日发布任务...")
    scheduler = TaskScheduler()
    scheduler.daily_publish_task()


if __name__ == "__main__":
    # 测试调度器
    print("测试定时任务调度器...")
    
    # 显示任务配置
    scheduler = TaskScheduler()
    scheduler.setup_jobs()
    
    print("\n已设置的任务:")
    for job in scheduler.get_jobs():
        print(f"  - {job['name']}: {job['next_run']}")
    
    print("\n任务配置完成，使用 `python main.py` 启动定时任务")
