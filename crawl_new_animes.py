# -*- coding: utf-8 -*-
"""
批量爬取新动画歌词脚本（QQ 音乐）
目标动画：
  1. 钢之炼金术师（2003版）
  2. 钢之炼金术师FA（2009版）
  3. 笨女孩（アホガール）
  4. 机动战士高达SEED
  5. 机动战士高达00
  6. 火影忍者（前传，部分经典曲）
  7. 火影忍者疾风传（全OP+精选ED）
"""
import sys
import io
import logging
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
logging.disable(logging.CRITICAL)

import config
from database import db
from qq_music import get_lyrics_by_song
from anime_lyrics_spider import ANIME_SONG_CONFIG

# ─── 要处理的动画清单 ───────────────────────────────────────────────────────
TARGET_ANIMES = [
    {"name": "钢之炼金术师",     "name_jp": "鋼の錬金術師",              "year": 2003},
    {"name": "钢之炼金术师FA",   "name_jp": "鋼の錬金術師 BROTHERHOOD",  "year": 2009},
    {"name": "笨女孩",           "name_jp": "アホガール",                "year": 2017},
    {"name": "机动战士高达SEED", "name_jp": "機動戦士ガンダムSEED",      "year": 2002},
    {"name": "机动战士高达00",   "name_jp": "機動戦士ガンダム00",        "year": 2007},
    {"name": "火影忍者",         "name_jp": "NARUTO -ナルト-",           "year": 2002},
    {"name": "火影忍者疾风传",   "name_jp": "NARUTO-ナルト- 疾風伝",     "year": 2007},
]


def get_or_create_anime(name: str, name_jp: str, year: int) -> int:
    """获取或创建动画记录，返回 anime_id"""
    row = db.get_anime_by_name(name)
    if row:
        print(f"  [已存在] {name}  ID={row['id']}  status={row['status']}")
        return row['id']
    anime_id = db.add_anime(name=name, name_jp=name_jp, year=year, status='pending')
    print(f"  [新建]   {name}  ID={anime_id}")
    return anime_id


def lyrics_already_exists(anime_id: int, song_name: str) -> bool:
    """检查该动画下是否已存在同名歌词"""
    existing = db.get_lyrics_by_anime(anime_id)
    return any(l.get('song_name') == song_name for l in existing)


def save_lyrics(anime_id: int, anime_name: str, song_cfg: dict, lyrics_lines: list, song_info: dict):
    """将歌词保存到数据库"""
    lyrics_text = "\n".join(lyrics_lines)
    lyric_id = db.add_lyrics(
        anime_id    = anime_id,
        song_name   = song_cfg['song_name'],
        song_type   = song_cfg.get('song_type', 'OP'),
        singer      = song_cfg.get('singer', ''),
        lyrics_text = lyrics_text,
        language    = 'ja',
    )
    print(f"    ✅ 已入库: {song_cfg['song_name']}  ({len(lyrics_lines)} 句)  ID={lyric_id}")
    return lyric_id


def try_crawl_song(song_cfg: dict, anime_id: int, anime_name: str) -> bool:
    """尝试爬取单首歌曲，返回是否成功"""
    song_name = song_cfg['song_name']
    singer    = song_cfg.get('singer', '')
    hints     = song_cfg.get('search_hints', [])

    # 跳过已存在
    if lyrics_already_exists(anime_id, song_name):
        print(f"    ⏭ 已存在: {song_name}")
        return True

    # 策略1: 原始歌名 + 歌手
    result = get_lyrics_by_song(song_name, singer=singer)
    if result and result.get('lines') and len(result['lines']) >= 3:
        save_lyrics(anime_id, anime_name, song_cfg, result['lines'], result)
        return True

    # 策略2: 逐个 search_hints
    for hint in hints:
        time.sleep(0.3)
        result = get_lyrics_by_song(hint)
        if result and result.get('lines') and len(result['lines']) >= 3:
            save_lyrics(anime_id, anime_name, song_cfg, result['lines'], result)
            return True

    print(f"    ❌ 未找到: {song_name} / {singer}")
    return False


def update_anime_status(anime_id: int, status: str):
    db.update_anime_status(anime_id, status)


def main():
    print("=" * 60)
    print("批量 QQ 音乐爬取脚本")
    print("=" * 60)

    total_ok  = 0
    total_fail = 0

    for anime_info in TARGET_ANIMES:
        name    = anime_info['name']
        name_jp = anime_info['name_jp']
        year    = anime_info['year']

        songs = ANIME_SONG_CONFIG.get(name, [])
        if not songs:
            print(f"\n⚠️  {name}: ANIME_SONG_CONFIG 中无配置，跳过")
            continue

        print(f"\n{'─'*55}")
        print(f"📺 {name}（{name_jp}, {year}）  共 {len(songs)} 首")
        print(f"{'─'*55}")

        anime_id = get_or_create_anime(name, name_jp, year)
        ok_count = 0
        fail_count = 0

        for song_cfg in songs:
            time.sleep(0.5)   # 限流，避免触发QQ反爬
            success = try_crawl_song(song_cfg, anime_id, name)
            if success:
                ok_count += 1
            else:
                fail_count += 1

        total_ok   += ok_count
        total_fail += fail_count

        # 更新动画状态
        if ok_count > 0:
            update_anime_status(anime_id, 'completed')
            print(f"\n  → {name}: 成功 {ok_count} 首 / 失败 {fail_count} 首 → completed")
        else:
            update_anime_status(anime_id, 'failed')
            print(f"\n  → {name}: 全部失败 → failed")

    print(f"\n{'='*60}")
    print(f"全部完成！成功 {total_ok} 首 / 失败 {total_fail} 首")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
