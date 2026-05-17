# -*- coding: utf-8 -*-
"""
离线入库脚本：小城日常 CITY THE ANIMATION
歌词来源：
  - Hello: https://www.uta-net.com/song/375904/ (歌ネット)
  - LUCKY: https://www.uta-net.com/movie/375677/ (歌ネット)
"""
import sys, io, sqlite3, logging
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
logging.disable(logging.CRITICAL)

import config

ANIME_NAME    = "小城日常"
ANIME_NAME_JP = "CITY THE ANIMATION"
ANIME_YEAR    = 2025

# ── 歌词正文（来源：歌ネット uta-net.com，已人工核实）──────────────────────
LYRICS_HELLO = """Hello, Dear my friends
夢を語って
過ごした日々を覚えてる？
大人になるって難しいんだね
隠してたもの　探しに行こうよ
散らかった
こころ脱ぎ捨て　雲は泳いで
顔あげて　飛び出して　ね！
雨は上がって　一緒に歌って
手を繋いで
わたしは笑って　君も笑って
きっとこうやって　また会いに行こう
Hello, Dear my friends
また目覚めて
新しい日々が始まるよ
大人になるって難しいけど
意外と毎日は
楽しいかもしれない
散らばった　こころ集めて
水を注いで　花は咲いて
飛び出して　ね！
雨は上がって　一緒に歌って
手を繋いで
わたしは笑って　君も笑って
きっとこうやって　前向いて行こう
散らかった　こころ脱ぎ捨て
雲は泳いで　虹渡って
飛び出して　ね！
雨は上がって　一緒に歌って
手を繋いで
わたしは笑って　君も笑って
きっとこうやって　また会いに行こう""".strip()

LYRICS_LUCKY = """ビビッときたの　すぐさま
君はぜったい面白い
気づかないのは惜しいよ
見つけたわたしはラッキー
四方八方かけてく
宝探し、つきないゲーム
たぶん平和の鍵もね
君と見つけるはずなの
ああ　ふたつ並ぶ影と
道草も伸びる頃
何回でも言いたい！
君は君がいい！
今日も　明日も　100年後も　ねえ
そゆとこさ　すきだよ
ジュース飲んだら
とろけた太陽
あー夏が行く
ぼやっとしてた！
季節は　お構いなしにとけてく
茹だる通りを徒歩でゴーイノン
夢かうつつかわかんないけど
寝坊ついでのピンチも
めくるめく欲張りもそう
恥ずかしいのも　ムキになるのも
今が食べ頃らしいの
いつもと同じフリで
去年と違う夏だ
やっかい！でも楽しい
君は君がいい！
猫も杓子も走るこの街で
君と今日もいたいの
屋根の向こうに
かくれた太陽
何回でも言いたい！
君がいてうれしい！
今日も明日も100年後も　ねえ
同じ空の下で続くおはなし
ジュース買ってこう
あー夏が行く""".strip()

SONGS = [
    {
        "song_name":    "Hello",
        "song_name_cn": "Hello",
        "song_type":    "OP",
        "singer":       "Furui Riho",
        "language":     "ja",
        "lyrics_text":  LYRICS_HELLO,
    },
    {
        "song_name":    "LUCKY",
        "song_name_cn": "LUCKY",
        "song_type":    "ED",
        "singer":       "TOMOO",
        "language":     "ja",
        "lyrics_text":  LYRICS_LUCKY,
    },
]


def main():
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # ── 1. 查或插入动画条目 ────────────────────────────────────────────────
    cur.execute("SELECT id, status FROM anime WHERE name = ?", (ANIME_NAME,))
    row = cur.fetchone()
    if row:
        anime_id = row["id"]
        print(f"[已存在] 动画《{ANIME_NAME}》ID={anime_id}，状态={row['status']}")
        if row["status"] != "completed":
            cur.execute("UPDATE anime SET status='completed', updated_at=CURRENT_TIMESTAMP WHERE id=?", (anime_id,))
            print(f"  → 状态已更新为 completed")
    else:
        cur.execute(
            "INSERT INTO anime (name, name_jp, year, status) VALUES (?,?,?,'completed')",
            (ANIME_NAME, ANIME_NAME_JP, ANIME_YEAR)
        )
        anime_id = cur.lastrowid
        print(f"[新增] 动画《{ANIME_NAME}》ID={anime_id}")

    # ── 2. 逐首写入歌词 ───────────────────────────────────────────────────
    for song in SONGS:
        # 检查是否已存在（同动画+歌名）
        cur.execute(
            "SELECT id FROM lyrics WHERE anime_id=? AND song_name=?",
            (anime_id, song["song_name"])
        )
        existing = cur.fetchone()
        if existing:
            print(f"[跳过] 《{song['song_name']}》已存在 (ID={existing['id']})")
            continue

        lines = [l for l in song["lyrics_text"].splitlines() if l.strip()]
        line_count = len(lines)
        cur.execute(
            """INSERT INTO lyrics
               (anime_id, song_name, song_name_cn, song_type, singer, language, lyrics_text)
               VALUES (?,?,?,?,?,?,?)""",
            (anime_id, song["song_name"], song["song_name_cn"],
             song["song_type"], song["singer"], song["language"], song["lyrics_text"])
        )
        lyric_id = cur.lastrowid
        print(f"[已入库] 《{song['song_name']}》({song['song_type']}) 歌手:{song['singer']} 行数:{line_count} → ID={lyric_id}")

    conn.commit()
    conn.close()

    # ── 3. 汇报最终数据库状态 ─────────────────────────────────────────────
    conn2 = sqlite3.connect(config.DB_PATH)
    conn2.row_factory = sqlite3.Row
    cur2 = conn2.cursor()
    cur2.execute("SELECT COUNT(*) as cnt FROM anime")
    total_anime = cur2.fetchone()["cnt"]
    cur2.execute("SELECT COUNT(*) as cnt FROM lyrics")
    total_lyrics = cur2.fetchone()["cnt"]
    conn2.close()
    print(f"\n=== 入库完成 ===")
    print(f"动画总数: {total_anime}")
    print(f"歌词总数: {total_lyrics}")


if __name__ == "__main__":
    main()
