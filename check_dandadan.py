import sqlite3, json, os

conn = sqlite3.connect(r'E:\workspace\workbuddy\anime-lyrics-publisher\data\anime_lyrics.db')
cur = conn.cursor()

# 读取刚入库的胆大党オトノケ
cur.execute("""
    SELECT l.id, l.song_name, l.singer, l.song_type, l.lyrics_text, a.name, a.name_jp
    FROM lyrics l JOIN anime a ON l.anime_id = a.id
    WHERE l.id = 149
""")
row = cur.fetchone()
print(row)
conn.close()

lyrics_id, song_name, singer, song_type, lyrics_text, anime_name, anime_name_jp = row

lines = [l.strip() for l in lyrics_text.split('\n') if l.strip()]
print(f'共 {len(lines)} 句歌词')
print('前3句:', lines[:3])
