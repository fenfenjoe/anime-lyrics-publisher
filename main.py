# -*- coding: utf-8 -*-
"""
微信公众号动漫歌词日语学习文章生成器 - 主入口
"""

import os
import sys
import argparse
import logging

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from database import db
from anime_lyrics_spider import crawl_weekly_lyrics
from article_generator import generate_daily_article
from wechat_publisher import generate_and_publish_article
from scheduler import start_scheduler, run_weekly_crawl_now, run_daily_publish_now

# 配置日志
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(config.LOG_FILE, encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


def init_database():
    """初始化数据库"""
    logger.info("初始化数据库...")
    _ = db  # 触发数据库初始化
    logger.info(f"数据库初始化完成: {config.DB_PATH}")


def cmd_weekly_crawl(args):
    """执行每周爬取任务"""
    logger.info("=" * 50)
    logger.info("执行每周爬取任务")
    logger.info("=" * 50)
    crawl_weekly_lyrics()
    logger.info("每周爬取任务完成")


def cmd_daily_publish(args):
    """执行每日发布任务"""
    logger.info("=" * 50)
    logger.info("执行每日发布任务")
    logger.info("=" * 50)
    generate_and_publish_article()
    logger.info("每日发布任务完成")


def cmd_generate(args):
    """仅生成文章（不发布）"""
    logger.info("=" * 50)
    logger.info("仅生成文章")
    logger.info("=" * 50)
    article = generate_daily_article()
    if article:
        print(f"\n文章标题: {article['title']}")
        print(f"\n文章内容:\n{article['content']}")
    else:
        print("没有可用的歌词数据")


def cmd_status(args):
    """显示状态"""
    print("\n=== 系统状态 ===\n")
    
    # 数据库状态
    print("📊 数据库状态:")
    anime_list = db.get_all_anime()
    print(f"  - 动画总数: {len(anime_list)}")
    
    pending = sum(1 for a in anime_list if a.get('status') == 'pending')
    completed = sum(1 for a in anime_list if a.get('status') == 'completed')
    print(f"  - 待爬取: {pending}")
    print(f"  - 已完成: {completed}")
    
    # 最近任务
    print("\n📝 最近任务:")
    logs = db.get_recent_task_logs(limit=5)
    for log in logs:
        status_icon = "✅" if log['status'] == 'success' else "❌" if log['status'] == 'failed' else "⏳"
        print(f"  {status_icon} {log['task_type']}: {log['status']} - {log.get('message', '')}")
    
    # 最近文章
    print("\n📄 最近文章:")
    articles = db.get_recent_articles(limit=5)
    for article in articles:
        status_icon = "✅" if article['status'] == 'published' else "📝"
        print(f"  {status_icon} {article['article_title']} - {article['status']}")
    
    print("\n" + "=" * 30)


def cmd_scheduler(args):
    """启动定时任务调度器"""
    logger.info("启动定时任务调度器...")
    logger.info(f"  - 每周爬取: 周{config.WEEKLY_CRAWL_DAY} {config.WEEKLY_CRAWL_HOUR}:{config.WEEKLY_CRAWL_MINUTE:02d}")
    logger.info(f"  - 每日发布: {config.DAILY_PUBLISH_HOUR}:{config.DAILY_PUBLISH_MINUTE:02d}")
    start_scheduler()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='微信公众号动漫歌词日语学习文章生成器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python main.py scheduler      # 启动定时任务调度器
  python main.py weekly          # 手动执行每周爬取任务
  python main.py daily           # 手动执行每日发布任务
  python main.py generate        # 仅生成文章（不发布）
  python main.py status          # 显示系统状态
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 启动调度器
    subparsers.add_parser('scheduler', help='启动定时任务调度器')
    
    # 手动执行任务
    subparsers.add_parser('weekly', help='手动执行每周爬取任务')
    subparsers.add_parser('daily', help='手动执行每日发布任务')
    subparsers.add_parser('generate', help='仅生成文章（不发布到微信）')
    
    # 查看状态
    subparsers.add_parser('status', help='显示系统状态')
    
    args = parser.parse_args()
    
    # 初始化数据库
    init_database()
    
    # 执行对应命令
    if args.command == 'scheduler':
        cmd_scheduler(args)
    elif args.command == 'weekly':
        cmd_weekly_crawl(args)
    elif args.command == 'daily':
        cmd_daily_publish(args)
    elif args.command == 'generate':
        cmd_generate(args)
    elif args.command == 'status':
        cmd_status(args)
    else:
        # 默认显示帮助
        parser.print_help()
        print("\n" + "=" * 50)
        print("提示: 使用以下命令启动定时任务:")
        print("  python main.py scheduler")
        print("=" * 50)


if __name__ == "__main__":
    main()
