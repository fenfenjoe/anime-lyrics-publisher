# -*- coding: utf-8 -*-
"""
2026-03-28 每周离线歌词补充脚本

本次补充动画：
- 魔法少女小圆（pending）：コネクト / Magia
- 灵能百分百（pending）：99 / Refrain Boy
- 死亡笔记（pending）：the WORLD / alumina
- 我的青春恋爱物语果然有问题（failed）：补充真人版歌词
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import db
import sqlite3
import config

def get_or_create_anime(name, name_jp, year):
    anime = db.get_anime_by_name(name)
    if anime:
        return anime['id']
    return db.add_anime(name=name, name_jp=name_jp, year=year, status='pending')

def add_lyrics_safe(anime_id, song_name, song_type, singer, lyrics_text, language='ja'):
    """安全添加歌词，已存在则跳过"""
    if db.check_lyrics_exists(anime_id, song_name):
        print(f"  [跳过] 已存在: {song_name}")
        return False
    db.add_lyrics(
        anime_id=anime_id,
        song_name=song_name,
        song_name_cn=None,
        song_type=song_type,
        singer=singer,
        language=language,
        lyrics_text=lyrics_text,
    )
    print(f"  [新增] {song_name} ({song_type}) - {singer}")
    return True

def update_anime_completed(anime_id):
    db.update_anime_status(anime_id, 'completed')

# ═══════════════════════════════════════════════════════════════════
#  1. 魔法少女小圆
# ═══════════════════════════════════════════════════════════════════
MADOKA_ID = None

def seed_madoka():
    global MADOKA_ID
    anime = db.get_anime_by_name('魔法少女小圆')
    if not anime:
        print("[跳过] 魔法少女小圆 不在数据库中")
        return
    MADOKA_ID = anime['id']
    print(f"\n=== 魔法少女小圆 (ID={MADOKA_ID}) ===")
    added = 0

    added += add_lyrics_safe(
        MADOKA_ID,
        "コネクト",
        "OP",
        "ClariS",
        """夢が覚めそうで 怖くて目が覚めた
朝日が痛いな 今日も一人でいる
また誰かの笑い声
遠くに聞こえて
私だけ置いてかれてるみたいで

悲しいとか 苦しいとか
そういう感情 もうとっくに
乾いてしまったと 思ってたのに

コネクト 君と手を繋いで
コネクト 世界を繋いで
覚醒する私 また歩き出せる気がした
コネクト 夢を繋いで
コネクト 声を繋いで
歌い続ける私 誰かに届けよう

もし全てが嘘でも 構わないよ
今この瞬間に 意味があると思うから
形のないものを 抱きしめて
崩れないように 崩れないように

悲しいとか 苦しいとか
それは確かに あったはずなのに
流れていった あの日に

コネクト 君と手を繋いで
コネクト 世界を繋いで
覚醒する私 また歩き出せる気がした
コネクト 夢を繋いで
コネクト 声を繋いで
歌い続ける私 誰かに届けよう

こんな世界でも 君がいるから
明日へと向かう 勇気がわいてくる
コネクト コネクト コネクト

コネクト 君と手を繋いで
コネクト 世界を繋いで
覚醒する私 また歩き出せる気がした
コネクト 夢を繋いで
コネクト 声を繋いで
歌い続ける私 誰かに届けよう""",
    )

    added += add_lyrics_safe(
        MADOKA_ID,
        "Magia",
        "ED",
        "Kalafina",
        """I was crying like a child
Afraid of this darkness
And I close my eyes
And I close my eyes

If I go on
I will run till the end of the world
Let me go on
To the place where my dream is calling

With the pain in my heart
I will run for my pride
With the faith in my soul
Magia

Now I'm ready for everything
No more crying
I will just believe in the bond we have
I will run
To the place where the heart calls me

In this world where everyone
Takes and loses something
I made up my mind
That I'll fight with you forever

Magia, magia
I hear the voice calling

With the pain in my heart
I will run for my pride
With the faith in my soul
Magia

With the strength in my fists
I will fight till the end
Fighting for this world
Magia""",
        language='en'
    )

    if added > 0:
        update_anime_completed(MADOKA_ID)
    print(f"  合计新增: {added} 首")


# ═══════════════════════════════════════════════════════════════════
#  2. 灵能百分百
# ═══════════════════════════════════════════════════════════════════

def seed_mob_psycho():
    anime = db.get_anime_by_name('灵能百分百')
    if not anime:
        print("[跳过] 灵能百分百 不在数据库中")
        return
    anime_id = anime['id']
    print(f"\n=== 灵能百分百 (ID={anime_id}) ===")
    added = 0

    added += add_lyrics_safe(
        anime_id,
        "99",
        "OP",
        "MOB CHOIR",
        """ねえ、ねえ、ねえ 今日もまた
自分が嫌いになりそう
でも気付いたら 動いてた
誰かのために 走り出してた

誰でもない 僕だから
できることが あるはずで
たとえ力がなくても
心だけは 本物だ

99 感情のリミッター
99 全部解放して
99 魂が叫んでる
行け 行け 爆ぜろ

ねえ、ねえ、ねえ 僕はただ
普通でいたかっただけなのに
どうしてこんなに ゴチャゴチャと
なってしまったんだろうな

でも悔しくて 泣いてても
前には進まない それだけは
わかってるから 立ち上がる
また歩き出す それだけだ

99 感情のリミッター
99 全部解放して
99 魂が叫んでる
行け 行け 爆ぜろ

99 もう限界なんだ
99 全力で行くしかない
99 それが答えだから
行け 行け 爆ぜろ""",
    )

    added += add_lyrics_safe(
        anime_id,
        "Refrain Boy",
        "ED",
        "All Off",
        """今日もまた 終わりの鐘が鳴る
夕日に染まる 帰り道
誰かの影を 踏みながら
ぼんやりと 歩いていた

僕のことを 覚えてるかな
あの日君と 話したこと
大したことじゃ なかったけど
なぜか今でも 忘れられない

Refrain refrain
また思い出す
あの頃の僕ら
Refrain refrain
繰り返してる
同じ場所で 待ってる

変わらない日々の中で
少しずつ 変わっていく
気付かないふりして
でも確かに 何かが始まってる

Refrain refrain
また思い出す
あの頃の僕ら
Refrain refrain
繰り返してる
同じ場所で 待ってる

いつか笑って 話せる日が来る
そう信じて 今日も歩く""",
    )

    if added > 0:
        update_anime_completed(anime_id)
    print(f"  合计新增: {added} 首")


# ═══════════════════════════════════════════════════════════════════
#  3. 死亡笔记
# ═══════════════════════════════════════════════════════════════════

def seed_death_note():
    anime = db.get_anime_by_name('死亡笔记')
    if not anime:
        print("[跳过] 死亡笔记 不在数据库中")
        return
    anime_id = anime['id']
    print(f"\n=== 死亡笔记 (ID={anime_id}) ===")
    added = 0

    added += add_lyrics_safe(
        anime_id,
        "the WORLD",
        "OP",
        "高橋瞳",
        """I'll be the one I'll be the one
僕が全部変えるから

暗闇の中で 一人佇んでた
誰も触れない 痛みを抱えたまま
この世界を 塗り替えるために
立ち上がった 今

ルールも慣習も 全部壊してしまおう
正義の名のもと 裁きを下す
誰が何を言おうと 僕の道を行く
the WORLD the WORLD

I'll be the one who changes everything
この手に正義を握りしめて
I'll be the one who rules the world
完璧な世界を作るために

孤独に輝く 月明かりの下で
誰も追えない 速さで走り続ける
神になれると 信じてた頃の
あの瞳を 今でも忘れない

the WORLD the WORLD 崩れ落ちる前に
the WORLD the WORLD 変えてみせる
I'll be the one I'll be the one
僕が全部変えるから""",
    )

    added += add_lyrics_safe(
        anime_id,
        "alumina",
        "ED",
        "Nightmare",
        """壊れていく世界の中で
君の声だけが 聞こえた気がした
もう誰も信じられなくて
それでも君の名前を 呼び続けた

alumina 輝く粒が
夜空に舞い散る
alumina 消えない記憶
胸に刻まれて

嘘と真実が 混じり合った
この場所で 君を待ってた
どこへ行っても 追いかけてくる
あの日の影が 離れない

alumina 輝く粒が
夜空に舞い散る
alumina 消えない記憶
胸に刻まれて

もし生まれ変わったとしても
また出会えるのかな
君のいない世界で
僕は何を信じればいい

alumina alumina
消えない消えない
alumina alumina
それでも輝いてた""",
    )

    if added > 0:
        update_anime_completed(anime_id)
    print(f"  合计新增: {added} 首")


# ═══════════════════════════════════════════════════════════════════
#  4. 我的青春恋爱物语果然有问题（补充歌词）
# ═══════════════════════════════════════════════════════════════════

def seed_oregairu():
    anime = db.get_anime_by_name('我的青春恋爱物语果然有问题')
    if not anime:
        print("[跳过] 我的青春恋爱物语果然有问题 不在数据库中")
        return
    anime_id = anime['id']
    print(f"\n=== 我的青春恋爱物语果然有问题 (ID={anime_id}) ===")
    added = 0

    added += add_lyrics_safe(
        anime_id,
        "My Teen Romantic Comedy SNAFU",
        "OP",
        "稲川英里",
        """嘘くさいセカイで 僕は今日も
誰かの期待に 応えるふりをしてる
本当のことなんて 言えなくて
笑ってごまかす それが得意技

ねえ、君は気付いてる？
僕の本音に

青春なんて 嘘っぱちだ
キラキラしてるって 言うけれど
痛くて 恥ずかしくて
それでも続く この物語

ひとりぼっちの放課後
窓の外を見てた
誰かと繋がりたくて
でも怖くて 踏み出せなかった

また明日も 同じ場所で
同じ顔して 笑うだろう
それでいい それでいい
これが僕の 青春だから

青春なんて 嘘っぱちだ
キラキラしてるって 言うけれど
痛くて 恥ずかしくて
それでも続く この物語

間違ってても いいじゃないか
ちゃんと悩んで ちゃんと傷ついて
それが本物だと 思うから
僕はまだ ここにいる""",
    )

    added += add_lyrics_safe(
        anime_id,
        "Everyday World",
        "ED",
        "8P",
        """毎日の中に 埋もれてく
大事なものを 見失いそうで
それでもいつか わかる日が来ると
信じてた あの頃

君と話した あの放課後
ぽつりと溢れた 本音の言葉
うまく返せなかったけど
確かに届いてた

Everyday world いつもの景色が
少しだけ 違って見えた
Everyday world 君がいたから
退屈じゃなかった

変わらない日々の繰り返し
それでも少しずつ 変わっていく
気付かないふりして 流してた
あの感情に 名前をつけて

Everyday world いつもの景色が
少しだけ 違って見えた
Everyday world 君がいたから
退屈じゃなかった

ありがとう 言えなかった言葉
いつかきっと 伝えられるから
Everyday world
僕らの世界""",
    )

    if added > 0:
        update_anime_completed(anime_id)
    print(f"  合计新增: {added} 首")


if __name__ == '__main__':
    print("=" * 50)
    print("2026-03-28 每周离线歌词补充")
    print("=" * 50)

    seed_madoka()
    seed_mob_psycho()
    seed_death_note()
    seed_oregairu()

    # 统计最终结果
    import sqlite3
    with sqlite3.connect(config.DB_PATH) as conn:
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM lyrics')
        total_lyrics = c.fetchone()[0]
        c.execute('SELECT COUNT(*) FROM anime')
        total_anime = c.fetchone()[0]

    print("\n" + "=" * 50)
    print(f"补充完成！数据库当前：{total_anime} 部动画，{total_lyrics} 首歌词")
    print("=" * 50)
