import sqlite3
conn = sqlite3.connect(r'data/anime_lyrics.db')
conn.row_factory = sqlite3.Row
# Check columns
cols = conn.execute("PRAGMA table_info(articles)").fetchall()
print("Columns:", [c['name'] for c in cols])
row = conn.execute('SELECT * FROM articles ORDER BY id DESC LIMIT 1').fetchone()
print("Last article:", dict(row))
conn.close()
