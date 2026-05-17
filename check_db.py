import sqlite3, json

conn = sqlite3.connect('data/anime_lyrics.db')
cur = conn.cursor()

# Check latest task_logs
cur.execute("SELECT id, task_type, status, message, created_at FROM task_logs ORDER BY id DESC LIMIT 5")
rows = cur.fetchall()
for r in rows:
    print(r)

# Check articles
cur.execute("SELECT id, anime_name, song_name, media_id, created_at FROM articles ORDER BY id DESC LIMIT 3")
rows = cur.fetchall()
print("=== articles ===")
for r in rows:
    print(r)

conn.close()
