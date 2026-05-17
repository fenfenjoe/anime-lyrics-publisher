# -*- coding: utf-8 -*-
"""
数据库模块 - SQLite 操作封装
"""

import sqlite3
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

import config

# 配置日志
logging.basicConfig(level=getattr(logging, config.LOG_LEVEL))
logger = logging.getLogger(__name__)


class Database:
    """SQLite 数据库操作类"""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or config.DB_PATH
        self._init_database()

    @contextmanager
    def get_connection(self):
        """获取数据库连接的上下文管理器"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 支持列名访问
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"数据库操作失败: {e}")
            raise
        finally:
            conn.close()

    def _init_database(self):
        """初始化数据库，创建表结构"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # 执行建表 SQL
            for statement in config.DB_INIT_SQL.split(';'):
                statement = statement.strip()
                if statement:
                    cursor.execute(statement)
            logger.info(f"数据库初始化完成: {self.db_path}")

    # ==================== 动画操作 ====================

    def add_anime(self, name: str, name_jp: str = None, year: int = None, 
                  cover_image_url: str = None, status: str = 'pending') -> int:
        """添加动画记录"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO anime (name, name_jp, year, cover_image_url, status)
                VALUES (?, ?, ?, ?, ?)
            """, (name, name_jp, year, cover_image_url, status))
            anime_id = cursor.lastrowid
            logger.info(f"添加动画: {name} (ID: {anime_id})")
            return anime_id

    def get_anime_by_name(self, name: str) -> Optional[Dict]:
        """根据名称查询动画"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM anime WHERE name = ?", (name,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_random_pending_anime(self, exclude_ids: List[int] = None) -> Optional[Dict]:
        """
        获取一个待爬取的随机动画。
        :param exclude_ids: 需要排除的动画 ID 列表（本次任务中已尝试过、失败的动画）
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if exclude_ids:
                placeholders = ",".join("?" * len(exclude_ids))
                cursor.execute(f"""
                    SELECT * FROM anime
                    WHERE status = 'pending'
                      AND id NOT IN ({placeholders})
                    ORDER BY RANDOM()
                    LIMIT 1
                """, exclude_ids)
            else:
                cursor.execute("""
                    SELECT * FROM anime
                    WHERE status = 'pending'
                    ORDER BY RANDOM()
                    LIMIT 1
                """)
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_anime_status(self, anime_id: int, status: str):
        """更新动画状态"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE anime 
                SET status = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            """, (status, anime_id))
            logger.info(f"更新动画状态: ID={anime_id}, status={status}")

    def get_all_anime(self) -> List[Dict]:
        """获取所有动画"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM anime ORDER BY created_at DESC")
            return [dict(row) for row in cursor.fetchall()]

    # ==================== 歌词操作 ====================

    def add_lyrics(self, anime_id: int, song_name: str, song_name_cn: str = None,
                   song_type: str = None, singer: str = None, language: str = 'ja',
                   lyrics_text: str = None) -> int:
        """添加歌词记录"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO lyrics (anime_id, song_name, song_name_cn, song_type, 
                                   singer, language, lyrics_text)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (anime_id, song_name, song_name_cn, song_type, singer, language, lyrics_text))
            lyrics_id = cursor.lastrowid
            logger.info(f"添加歌词: {song_name} (ID: {lyrics_id})")
            return lyrics_id

    def get_lyrics_by_anime(self, anime_id: int) -> List[Dict]:
        """获取动画的所有歌词"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM lyrics WHERE anime_id = ? ORDER BY song_type
            """, (anime_id,))
            return [dict(row) for row in cursor.fetchall()]

    def get_random_unused_lyrics(self, limit: int = 1) -> List[Dict]:
        """获取随机未使用的歌词（不在已发布文章中的）"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT l.*, a.name as anime_name, a.name_jp as anime_name_jp
                FROM lyrics l
                JOIN anime a ON l.anime_id = a.id
                WHERE l.id NOT IN (
                    SELECT lyrics_id FROM articles WHERE status = 'published'
                )
                AND l.lyrics_text IS NOT NULL AND l.lyrics_text != ''
                ORDER BY RANDOM()
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def check_lyrics_exists(self, anime_id: int, song_name: str) -> bool:
        """检查歌词是否已存在"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM lyrics 
                WHERE anime_id = ? AND song_name = ?
            """, (anime_id, song_name))
            return cursor.fetchone()[0] > 0

    # ==================== 文章操作 ====================

    def add_article(self, lyrics_id: int, article_title: str, 
                    article_content: str = None, cover_image_path: str = None,
                    status: str = 'draft') -> int:
        """添加文章记录"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO articles (lyrics_id, article_title, article_content, 
                                     cover_image_path, status)
                VALUES (?, ?, ?, ?, ?)
            """, (lyrics_id, article_title, article_content, cover_image_path, status))
            article_id = cursor.lastrowid
            logger.info(f"添加文章: {article_title} (ID: {article_id})")
            return article_id

    def update_article_wechat_ids(self, article_id: int, wechat_media_id: str = None,
                                   wechat_article_id: str = None, status: str = 'published'):
        """更新文章的微信素材ID和状态"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE articles 
                SET wechat_media_id = ?, wechat_article_id = ?, status = ?,
                    published_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (wechat_media_id, wechat_article_id, status, article_id))
            logger.info(f"更新文章微信ID: article_id={article_id}, status={status}")

    def get_article_by_id(self, article_id: int) -> Optional[Dict]:
        """根据ID获取文章"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM articles WHERE id = ?", (article_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_recent_articles(self, limit: int = 10) -> List[Dict]:
        """获取最近的文章"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT ar.*, l.song_name, l.song_type, a.name as anime_name
                FROM articles ar
                JOIN lyrics l ON ar.lyrics_id = l.id
                JOIN anime a ON l.anime_id = a.id
                ORDER BY ar.created_at DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_used_wechat_image_urls(self) -> List[str]:
        """
        从所有已发布/草稿文章内容中，提取曾经使用过的微信图片 CDN URL。
        用于下次爬取配图时排除重复图片。
        返回 mmbiz.qpic.cn 图片 URL 列表（去重）。
        """
        import re as _re
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT article_content FROM articles
                WHERE article_content IS NOT NULL AND article_content != ''
            """)
            rows = cursor.fetchall()

        used_urls: List[str] = []
        pattern = _re.compile(r'<img[^>]+src="(https?://[^"]+mmbiz[^"]*)"', _re.IGNORECASE)
        for row in rows:
            content = row[0] or ''
            for url in pattern.findall(content):
                if url not in used_urls:
                    used_urls.append(url)
        logger.info(f"已使用微信图片 URL 数量: {len(used_urls)}")
        return used_urls

    # ==================== 任务日志操作 ====================

    def add_task_log(self, task_type: str, status: str = 'running', 
                     message: str = None) -> int:
        """添加任务日志"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO task_logs (task_type, status, message)
                VALUES (?, ?, ?)
            """, (task_type, status, message))
            log_id = cursor.lastrowid
            return log_id

    def update_task_log(self, log_id: int, status: str, message: str = None):
        """更新任务日志"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE task_logs 
                SET status = ?, message = ? 
                WHERE id = ?
            """, (status, message, log_id))

    def get_recent_task_logs(self, task_type: str = None, limit: int = 10) -> List[Dict]:
        """获取最近的任务日志"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if task_type:
                cursor.execute("""
                    SELECT * FROM task_logs 
                    WHERE task_type = ? 
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (task_type, limit))
            else:
                cursor.execute("""
                    SELECT * FROM task_logs 
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (limit,))
            return [dict(row) for row in cursor.fetchall()]


# 全局数据库实例
db = Database()


if __name__ == "__main__":
    # 测试数据库连接
    print("测试数据库连接...")
    print(f"数据库路径: {db.db_path}")
    
    # 测试添加动画
    anime_id = db.add_anime("测试动画", "テストアニメ", 2024, "https://example.com/cover.jpg")
    print(f"添加动画ID: {anime_id}")
    
    # 测试获取随机待爬取动画
    anime = db.get_random_pending_anime()
    print(f"随机待爬取动画: {anime}")
    
    print("数据库测试完成!")
