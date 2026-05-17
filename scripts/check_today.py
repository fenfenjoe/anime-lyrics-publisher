import sqlite3
conn = sqlite3.connect('data/anime_lyrics.db')
c = conn.cursor()
c.execute("SELECT id, lyrics_id, article_title, wechat_media_id, status, published_at FROM articles ORDER BY id DESC LIMIT 5")
rows = c.fetchall()
for r in rows:
    print(r)
conn.close()
