import sys, sqlite3
sys.path.insert(0, r'E:\workspace\workbuddy\anime-lyrics-publisher')

conn = sqlite3.connect(r'E:\workspace\workbuddy\anime-lyrics-publisher\data\anime_lyrics.db')
cur = conn.cursor()

# 1. Add 胆大党 anime
cur.execute("""
    INSERT INTO anime (name, name_jp, year, cover_image_url, status)
    VALUES (?, ?, ?, ?, ?)
""", ('胆大党', 'ダンダダン', 2024,
      'https://myanimelist.net/images/anime/1584/143719l.jpg',
      'pending'))
anime_id = cur.lastrowid
print(f'Added anime ID: {anime_id}')

# 2. Add オトノケ lyrics
lyrics_text = """ダンダダンダンダダンダンダダンダンダダン…
諦めの悪い輩やから
アンタらなんかじゃ束なっても敵わん
くわばらくわばらくわばら目にも止まらん速さ
くたばらん黙らん下がらん押し通す我儘
そこどきな邪魔だ 俺はもう1人の貴方
貞ちゃん伽椰ちゃんわんさか黄泉の国wonderland
御祈祷中に何だが4時44分まわったら
四尺四寸四分様がカミナッチャbang around
呼ぶ声がしたんなら 文字通りお憑かれさまやん…
ハイレタハイレタハイレタハイレタハイレタ
必死で這い出た先で霧は晴れた
デコとボコが上手く噛み合ったら
痛みが重さなったら
ココロカラダアタマ
みなぎってゆく何だか
背中に今羽が生えたならば
暗闇からおさらば
飛び立っていく彼方
ココロカラダアタマ
懐かしい暖かさ
足元に今花が咲いたならば
暗闇からおさらば
飛び立っていく彼方
何度だって生きる
お前や君の中
瞼の裏や耳の中
胸の奥に居着いてるメロディー、リズムに
ダンダダンダンダダンダンダダンダンダダン…
今日も賽の河原ど真っん中
積み上げてくtop of top
鬼とチャンバラ
the lyrical chainsaw massacre
渡る大海原
鼻歌singin' sha-la-la
祓いたいのなら末代までの札束(okay?)
誰が開いたか禁パン后ドラ 後は何があっても知らんがな
何百年待ったか超久しぶりの娑婆だ
ガキや若葉
まだコッチ来んじゃねーよバカが
今確かに目が合ったな
こーゆーことかよ…シャマラン…
ハイレタハイレタハイレタハイレタハイレタ
眠り飽きた先で君が待ってた
盾と矛が肩を抱き合ったら
怒りが消去さったら
ココロカラダアタマ
みなぎってゆく何だか
背中に今羽が生えたならば
暗闇からおさらば
飛び立っていく彼方
ココロカラダアタマ
懐かしい暖かさ
足元に今花が咲いたならば
暗闇からおさらば
飛び立っていく彼方
何度だって生きる
お前や君の中
瞼の裏や耳の中
胸の奥に居着いてるメロディー、リズムに
ダンダダンダンダダンダンダダンダンダダン…
ダンダダンダンダダンダンダダンダンダダンdandadandandadandandadandandadan…"""

line_count = len([l for l in lyrics_text.split('\n') if l.strip()])
print(f'Lyrics line count: {line_count}')

cur.execute("""
    INSERT INTO lyrics (anime_id, song_name, song_type, singer, language, lyrics_text)
    VALUES (?, ?, ?, ?, ?, ?)
""", (anime_id, 'オトノケ', 'OP', 'Creepy Nuts', 'ja', lyrics_text))
lyrics_id = cur.lastrowid
print(f'Added lyrics ID: {lyrics_id}')

conn.commit()
conn.close()
print('Done!')
