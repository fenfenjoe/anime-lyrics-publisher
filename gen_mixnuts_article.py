# -*- coding: utf-8 -*-
"""
SPY×FAMILY《ミックスナッツ》文章生成脚本
直接完成：查DB → 格式化文章 → 存草稿 → 爬MAL图片 → 更新文章
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import config
from database import db
from article_generator import format_article
from image_spider import crawl_images_for_article


def main():
    # 1. 查询 SPY×FAMILY 歌词
    with db.get_connection() as conn:
        cur = conn.execute('''
            SELECT l.id, l.song_name, l.song_type, l.singer, l.language,
                   a.name, a.name_jp
            FROM lyrics l JOIN anime a ON l.anime_id = a.id
            WHERE l.song_name = 'ミックスナッツ'
            LIMIT 1
        ''')
        row = cur.fetchone()
    if not row:
        print("ERROR: 未找到 'ミックスナッツ' 歌词")
        return
    lyrics_id, song_name, song_type, singer, language, anime_name, anime_name_jp = row
    print(f"歌词: {anime_name} / {anime_name_jp} - {song_name} ({song_type}) by {singer}")

    # 2. 读取分析 JSON
    json_path = os.path.join(config.DATA_DIR, 'build_mixnuts.json')
    with open(json_path, 'r', encoding='utf-8') as f:
        analysis = json.load(f)

    # 3. 构建 task（模拟 AI 分析前的任务信息）
    task = {
        'anime_name': anime_name,
        'anime_name_jp': anime_name_jp,
        'song_name': song_name,
        'song_type': song_type,
        'singer': singer,
        'language': language,
        'lyrics_id': lyrics_id,
    }

    print("正在从 MAL API 爬取图片（仅官方图库，禁用 Bing）...")

    # 4. 计算配图数量（每5句插一张）
    line_count = len(analysis['result'])
    article_image_count = max(1, line_count // 5)
    print(f"歌词 {line_count} 句，配图 {article_image_count + 1} 张（封面+正文）")

    # 5. 爬图片（仅 MAL API）
    image_result = crawl_images_for_article(
        anime_name=anime_name,
        name_jp=anime_name_jp,
        article_image_count=article_image_count,
        song_name=song_name,
        singer=singer,
    )
    cover = image_result.get('cover')
    article_images = image_result.get('article_images', [])
    print(f"封面: {cover}")
    print(f"配图: {len(article_images)} 张 → {article_images}")

    # 6. 格式化文章
    article = format_article(task, analysis, article_images=article_images)
    print(f"\n文章标题: {article['title']}")
    print(f"内容长度: {len(article['content'])} 字符")

    # 7. 存草稿
    article_id = db.add_article(
        lyrics_id=lyrics_id,
        article_title=article['title'],
        article_content=article['content'],
        cover_image_path=cover,
        status='draft'
    )
    print(f"\n✅ 文章已存为草稿: article_id={article_id}")
    print(f"   标题: {article['title']}")
    print(f"   封面: {cover}")
    print(f"   配图: {article_images}")


if __name__ == '__main__':
    main()
