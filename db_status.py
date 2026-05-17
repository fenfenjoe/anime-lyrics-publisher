# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, 'c:/Users/Admin/WorkBuddy/Claw/anime-lyrics-publisher')
from database import db

print("=" * 55)
print("  动漫歌词数据库 - 当前状态汇总")
print("=" * 55)

anime_list = db.get_all_anime()
print(f"\n【动画列表】共 {len(anime_list)} 部：")
print(f"  {'ID':>3}  {'名称':<16} {'日文名':<25} {'年份':<6} {'状态'}")
print("  " + "-" * 65)
for a in anime_list:
    print(f"  {a['id']:>3}  {a['name']:<16} {str(a.get('name_jp','')):<25} {str(a.get('year','')):<6} {a['status']}")

total_lyrics = 0
print(f"\n【歌词列表】")
for a in anime_list:
    songs = db.get_lyrics_by_anime(a['id'])
    if songs:
        print(f"\n  >> {a['name']}({a.get('name_jp','')})")
        for s in songs:
            print(f"    [{s['song_type']:>2}] {s['song_name']}  /  {s.get('singer','未知歌手')}  ({s['language']})")
        total_lyrics += len(songs)

logs = db.get_recent_task_logs(task_type='weekly_crawl', limit=5)
print(f"\n【最近任务日志】")
for log in logs:
    print(f"  [{log['status']:>8}] {log['created_at']}  {log['message']}")

print(f"\n{'=' * 55}")
print(f"  合计：{len(anime_list)} 部动画 / {total_lyrics} 首歌词")
print(f"{'=' * 55}")
