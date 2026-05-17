# -*- coding: utf-8 -*-
"""
爬虫模块 - 从各种来源获取动漫信息和歌词
"""

from .anime_lyrics_spider import crawl_weekly_lyrics, LyricsSpider
from .image_spider import crawl_images_for_article

__all__ = ['crawl_weekly_lyrics', 'LyricsSpider', 'crawl_images_for_article']
