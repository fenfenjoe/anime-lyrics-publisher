"""
快速查询 SQLite 数据库工具
用法:
    python db_query.py            # 查看所有歌词列表（默认）
    python db_query.py anime      # 查看动画列表
    python db_query.py lyrics     # 查看所有歌词列表
    python db_query.py lyrics 2   # 查看第 2 首歌的完整歌词文本
    python db_query.py articles   # 查看已发布的文章记录
"""

import sys
import io
import sqlite3
import os

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "anime_lyrics.db")


def separator(title=""):
    print(f"\n{'─' * 60}")
    if title:
        print(f"  {title}")
        print(f"{'─' * 60}")


def cmd_anime(conn):
    separator("动画列表")
    rows = conn.execute(
        "SELECT id, name, name_jp, year FROM anime ORDER BY id"
    ).fetchall()
    if not rows:
        print("  （无数据）")
        return
    print(f"  {'ID':<5} {'中文名':<20} {'日文名':<30} {'年份'}")
    print(f"  {'─'*5} {'─'*20} {'─'*30} {'─'*6}")
    for r in rows:
        print(f"  {r[0]:<5} {str(r[1]):<20} {str(r[2] or ''):<30} {r[3] or ''}")


def cmd_lyrics(conn, detail_id=None):
    if detail_id:
        # 显示指定歌词的完整文本
        row = conn.execute(
            """SELECT l.id, a.name, l.song_name, l.song_name_cn, l.song_type,
                      l.singer, l.language, l.lyrics_text
               FROM lyrics l JOIN anime a ON l.anime_id = a.id
               WHERE l.id = ?""",
            (detail_id,),
        ).fetchone()
        if not row:
            print(f"  歌词 ID={detail_id} 不存在")
            return
        separator(f"歌词详情  ID={row[0]}")
        print(f"  动画：{row[1]}")
        print(f"  歌名：{row[2]}  ({row[3] or '无中文名'})")
        print(f"  类型：{row[4]}  歌手：{row[5]}  语言：{row[6]}")
        print(f"  歌词全文（共 {len((row[7] or '').splitlines())} 行）：")
        print()
        for i, line in enumerate((row[7] or "").splitlines(), 1):
            print(f"    {i:>3}. {line}")
    else:
        # 显示全部歌词列表
        separator("歌词列表")
        rows = conn.execute(
            """SELECT l.id, a.name, l.song_type, l.song_name, l.singer,
                      l.language,
                      CASE WHEN l.lyrics_text IS NULL THEN 0
                           ELSE length(l.lyrics_text) - length(replace(l.lyrics_text, char(10), '')) + 1
                      END AS lines
               FROM lyrics l JOIN anime a ON l.anime_id = a.id
               ORDER BY a.id, l.id"""
        ).fetchall()
        if not rows:
            print("  （无数据）")
            return
        print(f"  {'ID':<5} {'动画':<18} {'类型':<8} {'歌名':<22} {'歌手':<20} {'语言':<6} {'行数'}")
        print(f"  {'─'*5} {'─'*18} {'─'*8} {'─'*22} {'─'*20} {'─'*6} {'─'*4}")
        for r in rows:
            print(
                f"  {r[0]:<5} {str(r[1]):<18} {str(r[2] or ''):<8} "
                f"{str(r[3]):<22} {str(r[4] or ''):<20} {r[5]:<6} {r[6]}"
            )
        print(f"\n  提示：用 python db_query.py lyrics <ID> 查看完整歌词文本")


def cmd_articles(conn):
    separator("文章发布记录")
    rows = conn.execute(
        """SELECT ar.id, a.name, l.song_name, ar.title, ar.status,
                  substr(ar.created_at, 1, 16) as created_at
           FROM articles ar
           JOIN lyrics l ON ar.lyrics_id = l.id
           JOIN anime a ON l.anime_id = a.id
           ORDER BY ar.id DESC
           LIMIT 20"""
    ).fetchall()
    if not rows:
        print("  （无文章记录）")
        return
    for r in rows:
        print(f"  [{r[0]}] {r[5]}  {r[1]} / {r[2]}")
        print(f"       标题：{r[3]}")
        print(f"       状态：{r[4]}")
        print()


def main():
    args = sys.argv[1:]
    cmd = args[0].lower() if args else "lyrics"

    if not os.path.exists(DB_PATH):
        print(f"数据库文件不存在：{DB_PATH}")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    try:
        if cmd == "anime":
            cmd_anime(conn)
        elif cmd == "lyrics":
            detail_id = int(args[1]) if len(args) > 1 else None
            cmd_lyrics(conn, detail_id)
        elif cmd == "articles":
            cmd_articles(conn)
        else:
            print(__doc__)
    finally:
        conn.close()
        print()


if __name__ == "__main__":
    main()
