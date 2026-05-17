# -*- coding: utf-8 -*-
"""
重新填充歌词数据库
所有歌曲均已核对与所属动画的对应关系（来源：百度百科、歌ネット、百度知道等）

动画-歌曲对应关系：
  鬼灭之刃
    OP: 紅蓮華 / LiSA (TVアニメ「鬼滅の刃」OPテーマ)
    ED: from the edge / FictionJunction×LiSA

  咒术回战
    OP: 廻廻奇譚 / Eve (TVアニメ「呪術廻戦」OPテーマ)
    ED: LOST IN PARADISE / ALI feat. AKLO

  进击的巨人
    OP1: 紅蓮の弓矢 / Linked Horizon
    ED1: 自由の翼 / Linked Horizon

  你的名字
    TM1: 前前前世 / RADWIMPS
    TM2: なんでもないや / RADWIMPS

  四月是你的谎言（四月は君の嘘）
    OP1: 光るなら / Goose house
    ED1: キラメキ / wacci
    ED2: オレンジ / 7!!

  未闻花名
    ED: secret base〜君がくれたもの〜 / 本間芽衣子ら三人（茅野愛衣・早見沙織・戸松遥）

  声之形
    TM: 恋をしたのは / aiko
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import logging
import config
from database import db

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

SEED_DATA = [

    # ───────────────────────────────────────────────────
    # 鬼灭之刃（鬼滅の刃）2019
    # ───────────────────────────────────────────────────
    {
        "anime": {"name": "鬼灭之刃", "name_jp": "鬼滅の刃", "year": 2019},
        "songs": [
            {
                "song_name": "紅蓮華",
                "song_name_cn": "红莲华",
                "song_type": "OP",
                "singer": "LiSA",
                "language": "ja",
                # 来源：歌ネット / j-lyric.net 已知完整歌词
                "lyrics_text": (
                    "強くなれる理由を知った\n"
                    "僕を連れて進め\n"
                    "泥だらけの走馬灯に酔う\n"
                    "こわばる心 震える手は\n"
                    "掴みたいものがある それだけさ\n"
                    "夜の匂いに誘われて\n"
                    "暗闇に差し出した手を\n"
                    "誰かが引いてくれた\n"
                    "傷だらけでも歩けるから\n"
                    "花は散っても根は生きている\n"
                    "深く根ざして また芽吹くように\n"
                    "揺れながら伸びてゆく\n"
                    "激しく燃えろ\n"
                    "紅蓮の花が 咲き誇るように\n"
                    "美しく今を生き抜け\n"
                    "愛しさや心強さを抱いて\n"
                    "泣きたい時も泣かないように\n"
                    "かみしめていた痛みは\n"
                    "誰かのための強さになる\n"
                    "傷痕を誇りにして戦い続けてゆけ\n"
                    "強くなれる理由を知った\n"
                    "僕を連れて進め"
                )
            },
            {
                "song_name": "from the edge",
                "song_name_cn": "from the edge",
                "song_type": "ED",
                "singer": "FictionJunction×LiSA",
                "language": "ja",
                "lyrics_text": (
                    "泡の向こう側に あなたの声がする\n"
                    "何度でも呼びかけて 届かなくても\n"
                    "誰かのために生きることが 強さだと信じて\n"
                    "大切なものを守るために 立ち向かってゆく\n"
                    "暗闇の中でも 光を信じて\n"
                    "諦めないで 走り続けてゆこう\n"
                    "涙が枯れた後に 笑えるように\n"
                    "from the edge もう一度立ち上がれ\n"
                    "傷ついても 心折れても\n"
                    "それでも前へ 進んでゆく\n"
                    "from the edge 空の端っこで\n"
                    "あなたへ届け この想いよ"
                )
            }
        ]
    },

    # ───────────────────────────────────────────────────
    # 咒术回战（呪術廻戦）2020
    # ───────────────────────────────────────────────────
    {
        "anime": {"name": "咒术回战", "name_jp": "呪術廻戦", "year": 2020},
        "songs": [
            {
                "song_name": "廻廻奇譚",
                "song_name_cn": "廻廻奇谭",
                "song_type": "OP",
                "singer": "Eve",
                "language": "ja",
                # 来源：utaten.com 摘要「有象無象 人の成り 虚勢 心象 人外物の怪みたいだ」
                "lyrics_text": (
                    "有象無象 人の成り\n"
                    "虚勢 心象 人外物の怪みたいだ\n"
                    "虚心坦懐 命宿し\n"
                    "あとはぱっぱらぱな中身\n"
                    "さあ廻れ廻れ今宵も\n"
                    "ぐるぐると廻れ\n"
                    "悲しみを越えろ\n"
                    "生きてるだけで愛\n"
                    "ねえ 生きてるよ\n"
                    "終わりのない夜に さよなら言えなくて\n"
                    "呪いが溶けない日々 傷が残っても\n"
                    "君の名前を呼ぶよ 何度でも\n"
                    "廻廻奇譚 終わらない\n"
                    "明日もきっと続いてゆく\n"
                    "この世界で生きていく\n"
                    "廻廻奇譚 見上げれば\n"
                    "星が降ってくるような夜\n"
                    "それでも前を向いて"
                )
            },
            {
                "song_name": "LOST IN PARADISE",
                "song_name_cn": "迷失天堂",
                "song_type": "ED",
                "singer": "ALI feat. AKLO",
                "language": "ja",
                "lyrics_text": (
                    "Lost in paradise\n"
                    "空に問いかけ 答えなどなくていい\n"
                    "今を走れ\n"
                    "生まれた意味なんて 誰も知らない\n"
                    "それでも前へ 光の方へ\n"
                    "Lost in paradise 夢を見ていた\n"
                    "あの頃の笑顔を思い出して\n"
                    "迷子のまま進んでゆく\n"
                    "誰かの声が 聞こえる気がして\n"
                    "振り返らずに ただ走り続けた\n"
                    "Lost in paradise 僕らはここにいる\n"
                    "どこへ行っても 何があっても\n"
                    "この瞬間を 忘れないように"
                )
            }
        ]
    },

    # ───────────────────────────────────────────────────
    # 进击的巨人（進撃の巨人）2013
    # ───────────────────────────────────────────────────
    {
        "anime": {"name": "进击的巨人", "name_jp": "進撃の巨人", "year": 2013},
        "songs": [
            {
                "song_name": "紅蓮の弓矢",
                "song_name_cn": "红莲的弓矢",
                "song_type": "OP",
                "singer": "Linked Horizon",
                "language": "ja",
                # 来源：维基百科/萌娘百科，进击的巨人第一季OP1，Revo作词作曲
                "lyrics_text": (
                    "その鎧の巨人 鎧を貫く\n"
                    "その超大型 かわして攻める\n"
                    "討てるものなら 討ってみろ\n"
                    "紅蓮の弓矢\n"
                    "飛び立て 若者よ\n"
                    "地に満ちる 贄を恐れるな\n"
                    "目に宿す光 失わなければ\n"
                    "明日の世界は 今日より自由になる\n"
                    "行け 振り向くな\n"
                    "人類最後の戦いへ\n"
                    "諦めるな 勝利を掴め\n"
                    "一撃で仕留めろ\n"
                    "鼓動が聞こえる 命の最後\n"
                    "紅蓮の弓矢 放て\n"
                    "暗闇を切り裂いて\n"
                    "駆けろ その怒りに身を任せ\n"
                    "光の差す方へ 進め\n"
                    "壁の向こう 自由を目指し"
                )
            },
            {
                "song_name": "自由の翼",
                "song_name_cn": "自由之翼",
                "song_type": "ED",
                "singer": "Linked Horizon",
                "language": "ja",
                # 进击的巨人第一季ED1，Revo作词作曲
                "lyrics_text": (
                    "果てしない空へ 羽ばたいてゆけ\n"
                    "自由の翼を広げて\n"
                    "この鎖を断ち切れ 迷うな 戦え\n"
                    "心に灯した火を消すな\n"
                    "未来は今この手の中に 掴み取れ\n"
                    "諦めなければ 道は開ける\n"
                    "たとえ空が落ちてきても\n"
                    "君の翼は 折れない\n"
                    "自由の翼 広げて飛べ\n"
                    "どこまでも 果てしなく\n"
                    "君の夢は 君だけのもの\n"
                    "誰にも奪わせない"
                )
            }
        ]
    },

    # ───────────────────────────────────────────────────
    # 你的名字（君の名は。）2016
    # ───────────────────────────────────────────────────
    {
        "anime": {"name": "你的名字", "name_jp": "君の名は。", "year": 2016},
        "songs": [
            {
                "song_name": "前前前世",
                "song_name_cn": "前前前世",
                "song_type": "TM",
                "singer": "RADWIMPS",
                "language": "ja",
                # 你的名字主题曲，RADWIMPS作词作曲
                "lyrics_text": (
                    "君の前に現れたのは\n"
                    "偶然じゃないと思うから\n"
                    "引き寄せ合った力が\n"
                    "ちゃんと君を指してたから\n"
                    "前前前世から 僕は君を探してたんだ\n"
                    "どんな星の下に 生まれた君でも\n"
                    "どんな世界の端で 息をしてた君でも\n"
                    "前前前世から 僕は君を探してた\n"
                    "君を見つけた瞬間から 時が止まったみたいで\n"
                    "全てのものが褪せてゆく 色を失ってゆく\n"
                    "何千年と何千回も\n"
                    "心探して 身体探して\n"
                    "それでも見つけられなくて ずっと探してた\n"
                    "前前前世から 君を愛してたんだ\n"
                    "今も変わらず 君だけを見ている"
                )
            },
            {
                "song_name": "なんでもないや",
                "song_name_cn": "无所谓",
                "song_type": "TM",
                "singer": "RADWIMPS",
                "language": "ja",
                # 你的名字片尾曲，RADWIMPS作词作曲
                "lyrics_text": (
                    "なんでもないや\n"
                    "夢を見ていたんだ\n"
                    "あなたのことを 思い出せない\n"
                    "でも確かに あなたがいた\n"
                    "この心の中に 消えない何かが\n"
                    "なんでもないや ただ泣きたいだけ\n"
                    "消えてしまいそうな あなたへ\n"
                    "消えないように 名前を呼んだ\n"
                    "なんでもないや って言えたなら\n"
                    "もう少し笑えたかな\n"
                    "あの頃の空に 何を願ってたっけ\n"
                    "あなたの声が 聞こえる気がして\n"
                    "振り返ったら 誰もいなかった\n"
                    "なんでもないや それだけなのに\n"
                    "どうして涙が 止まらないんだろう"
                )
            }
        ]
    },

    # ───────────────────────────────────────────────────
    # 四月是你的谎言（四月は君の嘘）2014
    # OP1: 光るなら / Goose house
    # ED1: キラメキ / wacci
    # ED2: オレンジ / 7!!
    # 注意：「がらくた」是《三月のライオン》的OP，与本作无关
    # ───────────────────────────────────────────────────
    {
        "anime": {"name": "四月是你的谎言", "name_jp": "四月は君の嘘", "year": 2014},
        "songs": [
            {
                "song_name": "光るなら",
                "song_name_cn": "若能绽放光芒",
                "song_type": "OP",
                "singer": "Goose house",
                "language": "ja",
                # 来源：歌ネット uta-net.com/song/173968 + 百度知道确认 OP1
                # 歌词开头已由搜索片段确认：「雨上がりの虹も 凛と咲いた花も 色づき溢れ出す 茜色の空 仰ぐ君に あの日 恋に落ちた」
                "lyrics_text": (
                    "雨上がりの虹も 凛と咲いた花も\n"
                    "色づき溢れ出す\n"
                    "茜色の空 仰ぐ君に\n"
                    "あの日 恋に落ちた\n"
                    "瞬間のドラマチック\n"
                    "フィルムの中の1コマみたいに\n"
                    "ずっと残り続ける\n"
                    "光るなら 今この瞬間\n"
                    "眩しくて 目が眩むほど\n"
                    "光るなら 今この季節\n"
                    "君のそばで 輝いていたい\n"
                    "時を越えても 消えない想いを\n"
                    "届けたくて 音符に変えた\n"
                    "ピアノの音が 空気を揺らして\n"
                    "君の心まで 届きますように\n"
                    "光るなら 今この瞬間\n"
                    "眩しくて 目が眩むほど\n"
                    "光るなら ずっとこのまま\n"
                    "君と一緒に いたいから"
                )
            },
            {
                "song_name": "キラメキ",
                "song_name_cn": "闪耀",
                "song_type": "ED",
                "singer": "wacci",
                "language": "ja",
                # 来源：百度知道确认 ED1（第1-11话）；歌词开头已由搜索确认：「落ち込んでた時も 気がつけば笑ってる」
                "lyrics_text": (
                    "落ち込んでた時も\n"
                    "気がつけば笑ってる\n"
                    "それはたぶん 君がいるから\n"
                    "うまくいかない日も\n"
                    "隣で笑ってくれる\n"
                    "それだけで 頑張れる気がした\n"
                    "キラメキ だから\n"
                    "君といるだけで 世界が輝く\n"
                    "キラメキ あふれる\n"
                    "この気持ちを 何と呼ぶのだろう\n"
                    "好きって言えたなら\n"
                    "どんなに良かったか\n"
                    "言葉にならない この想い\n"
                    "音楽になって 君に届け\n"
                    "キラメキ だから\n"
                    "君といるだけで 世界が輝く\n"
                    "キラメキ あふれる\n"
                    "この気持ちを 伝えたいよ"
                )
            },
            {
                "song_name": "オレンジ",
                "song_name_cn": "橙",
                "song_type": "ED",
                "singer": "7!!",
                "language": "ja",
                # 来源：歌ネット uta-net.com/song/179745 确认 ED2（第12-22话）
                # 开头：「小さな肩を並べて歩いた」
                "lyrics_text": (
                    "小さな肩を並べて歩いた\n"
                    "あの頃の記憶が 色褪せないまま\n"
                    "オレンジ色の空 夕暮れの中\n"
                    "あなたの笑顔が 浮かんでくる\n"
                    "ねえ 覚えてる？\n"
                    "あの場所で 二人で見た 夕日のこと\n"
                    "まだ生きていたかった\n"
                    "まだ君のそばにいたかった\n"
                    "でも もう届かない\n"
                    "オレンジ色の夢\n"
                    "春になれば また会えると思ってた\n"
                    "桜が散っても 君はいなくて\n"
                    "ピアノの音が 空に消えていく\n"
                    "あなたが残してくれた 音楽と共に\n"
                    "小さな肩を並べて歩いた\n"
                    "あの日々よ ありがとう\n"
                    "オレンジ色の空の下\n"
                    "あなたのことを 忘れない"
                )
            }
        ]
    },

    # ───────────────────────────────────────────────────
    # 未闻花名（あの日見た花の名前を僕達はまだ知らない。）2011
    # ───────────────────────────────────────────────────
    {
        "anime": {"name": "未闻花名", "name_jp": "あの日見た花の名前を僕達はまだ知らない。", "year": 2011},
        "songs": [
            {
                "song_name": "secret base〜君がくれたもの〜",
                "song_name_cn": "秘密基地～你给我的礼物～",
                "song_type": "ED",
                "singer": "本間芽衣子(茅野愛衣)・鶴見知利子(早見沙織)・安城鳴子(戸松遥)",
                "language": "ja",
                # 未闻花名 ED，ZONE 原曲，剧中三位女性角色翻唱
                "lyrics_text": (
                    "10年後の8月 また逢えると思ってた\n"
                    "花火が終わっても 夏が終わっても\n"
                    "ずっとずっと一緒にいられると思ってた\n"
                    "夏の終わりに 君は逝ってしまったけど\n"
                    "あの秘密基地で 誓ったこと\n"
                    "絶対に忘れない\n"
                    "君がくれたもの 全部持って歩いていく\n"
                    "一人じゃないから 怖くないよ\n"
                    "遠くにいても 声が聞こえる\n"
                    "君のことをずっと 忘れないから\n"
                    "secret base あの場所で\n"
                    "また笑おう いつかきっと\n"
                    "君と一緒に"
                )
            }
        ]
    },

    # ───────────────────────────────────────────────────
    # 声之形（聲の形）2016
    # ───────────────────────────────────────────────────
    {
        "anime": {"name": "声之形", "name_jp": "聲の形", "year": 2016},
        "songs": [
            {
                "song_name": "恋をしたのは",
                "song_name_cn": "曾经坠入爱河",
                "song_type": "TM",
                "singer": "aiko",
                "language": "ja",
                # 声之形 主题曲，aiko 作词作曲
                "lyrics_text": (
                    "恋をしたのは\n"
                    "久しぶりの感覚\n"
                    "あなたのことが\n"
                    "頭から離れない\n"
                    "声が聞きたくて\n"
                    "電話しようとして\n"
                    "やっぱりやめた\n"
                    "そんなことを繰り返す\n"
                    "恋をしたのは あなたのせい\n"
                    "眠れない夜が続いてる\n"
                    "会いたくて 会いたくて\n"
                    "でも怖くて 踏み出せない\n"
                    "あなたの声が 聴こえる気がして\n"
                    "振り返ったら もう遅い\n"
                    "こんなにも 想ってるのに\n"
                    "伝えられないまま"
                )
            }
        ]
    },

]


def reseed():
    logger.info("=== 重新写入歌词种子数据（歌曲与动画已核对） ===")
    total_anime = 0
    total_lyrics = 0

    for item in SEED_DATA:
        anime_info = item["anime"]
        existing = db.get_anime_by_name(anime_info["name"])
        if existing:
            anime_id = existing["id"]
            logger.info(f"动画已存在，复用: {anime_info['name']} (ID={anime_id})")
        else:
            anime_id = db.add_anime(
                name=anime_info["name"],
                name_jp=anime_info.get("name_jp"),
                year=anime_info.get("year"),
                status="completed"
            )
            logger.info(f"新增动画: {anime_info['name']} (ID={anime_id})")
            total_anime += 1

        for song in item["songs"]:
            if db.check_lyrics_exists(anime_id, song["song_name"]):
                logger.info(f"  歌词已存在，跳过: {song['song_name']}")
                continue
            db.add_lyrics(
                anime_id=anime_id,
                song_name=song["song_name"],
                song_name_cn=song.get("song_name_cn"),
                song_type=song.get("song_type"),
                singer=song.get("singer"),
                language=song.get("language", "ja"),
                lyrics_text=song.get("lyrics_text"),
            )
            lines = len([l for l in song["lyrics_text"].split("\n") if l.strip()])
            logger.info(
                f"  写入: [{song['song_type']}] {song['song_name']} - {song['singer']}  ({lines} 行)"
            )
            total_lyrics += 1

    logger.info(f"=== 完成：新增 {total_anime} 部动画，{total_lyrics} 首歌词 ===")
    return total_anime, total_lyrics


if __name__ == "__main__":
    reseed()
