import sqlite3, json

conn = sqlite3.connect(r'c:\Users\Admin\WorkBuddy\Claw\anime-lyrics-publisher\data\anime_lyrics.db')
cur = conn.cursor()

cur.execute("SELECT id, task_type, status, message, created_at FROM task_logs ORDER BY id DESC LIMIT 5")
rows = cur.fetchall()
with open(r'c:\Users\Admin\WorkBuddy\Claw\anime-lyrics-publisher\data\check_result.txt', 'w', encoding='utf-8') as f:
    f.write("=== task_logs ===\n")
    for r in rows:
        f.write(str(r) + "\n")
    
    cur.execute("SELECT id, anime_name, song_name, media_id, created_at FROM articles ORDER BY id DESC LIMIT 3")
    rows2 = cur.fetchall()
    f.write("=== articles ===\n")
    for r in rows2:
        f.write(str(r) + "\n")

conn.close()
print("done")
