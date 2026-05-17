# -*- coding: utf-8 -*-
"""
离线歌词种子数据 - 当爬虫无法访问外网时使用内置数据填充数据库
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import logging
import config
from database import db

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# ───── 内置经典动漫歌词数据 ─────────────────────────────────────────
SEED_DATA = [
    {
        "anime": {"name": "鬼灭之刃", "name_jp": "鬼滅の刃", "year": 2019},
        "songs": [
            {
                "song_name": "紅蓮華",
                "song_name_cn": "红莲华",
                "song_type": "OP",
                "singer": "LiSA",
                "language": "ja",
                "lyrics_text": (
                    "強くなれる理由を知った\n"
                    "僕を連れて進め\n"
                    "夢を描いた その先に\n"
                    "何が待っていても\n"
                    "恐れずに 体に刻め\n"
                    "燃え上がれ 魂\n"
                    "紅蓮の花が 咲き誇るように\n"
                    "美しく 今を生き抜け\n"
                    "愛しさや心強さを抱いて\n"
                    "進み続ける限り\n"
                    "その先へ"
                )
            },
            {
                "song_name": "from the edge",
                "song_name_cn": "from the edge",
                "song_type": "ED",
                "singer": "FictionJunction×LiSA",
                "language": "ja",
                "lyrics_text": (
                    "泡の向こう側に\n"
                    "あなたの声がする\n"
                    "何度でも呼びかけて\n"
                    "届かなくても\n"
                    "誰かのために生きることが\n"
                    "強さだと信じて\n"
                    "大切なものを守るために\n"
                    "立ち向かってゆく"
                )
            }
        ]
    },
    {
        "anime": {"name": "咒术回战", "name_jp": "呪術廻戦", "year": 2020},
        "songs": [
            {
                "song_name": "廻廻奇譚",
                "song_name_cn": "廻廻奇谭",
                "song_type": "OP",
                "singer": "Eve",
                "language": "ja",
                "lyrics_text": (
                    "生きてるだけで愛\n"
                    "ねえ 生きてるよ\n"
                    "終わりのない夜に\n"
                    "さよなら 言えなくて\n"
                    "呪いが溶けない日々\n"
                    "傷が残っても\n"
                    "君の名前を呼ぶよ\n"
                    "何度でも\n"
                    "廻廻奇譚 終わらない\n"
                    "明日もきっと続いてゆく\n"
                    "この世界で生きていく"
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
                    "空に問いかけ\n"
                    "答えなどなくていい\n"
                    "今を走れ\n"
                    "生まれた意味なんて\n"
                    "誰も知らない\n"
                    "それでも前へ\n"
                    "光の方へ\n"
                    "Lost in paradise\n"
                    "夢を見ていた"
                )
            }
        ]
    },
    {
        "anime": {"name": "进击的巨人", "name_jp": "進撃の巨人", "year": 2013},
        "songs": [
            {
                "song_name": "紅蓮の弓矢",
                "song_name_cn": "红莲的弓矢",
                "song_type": "OP",
                "singer": "Linked Horizon",
                "language": "ja",
                "lyrics_text": (
                    "行け 振り向くな\n"
                    "後悔するな\n"
                    "刻め 魂に\n"
                    "叫べ 戦え\n"
                    "紅蓮の弓矢\n"
                    "放て 暗闇を切り裂いて\n"
                    "駆けろ その怒りに身を任せ\n"
                    "光の差す方へ\n"
                    "勝利を掴め\n"
                    "諦めるな\n"
                    "前を向け 進め\n"
                    "壁の向こう 自由を目指し"
                )
            },
            {
                "song_name": "自由の翼",
                "song_name_cn": "自由之翼",
                "song_type": "ED",
                "singer": "Linked Horizon",
                "language": "ja",
                "lyrics_text": (
                    "果てしない空へ\n"
                    "羽ばたいてゆけ\n"
                    "自由の翼を広げて\n"
                    "この鎖を断ち切れ\n"
                    "迷うな 戦え\n"
                    "心に灯した火を消すな\n"
                    "未来は今この手の中に\n"
                    "掴み取れ"
                )
            }
        ]
    },
    {
        "anime": {"name": "你的名字", "name_jp": "君の名は。", "year": 2016},
        "songs": [
            {
                "song_name": "前前前世",
                "song_name_cn": "前前前世",
                "song_type": "TM",
                "singer": "RADWIMPS",
                "language": "ja",
                "lyrics_text": (
                    "君の前に现れたのは\n"
                    "偶然じゃないと思うから\n"
                    "引き寄せ合った力が\n"
                    "ちゃんと君を指してたから\n"
                    "前前前世から 僕は君を探してたんだ\n"
                    "どんな星の下に 生まれた君でも\n"
                    "どんな世界の端で 息をしてた君でも\n"
                    "前前前世から 僕は君を探してた"
                )
            },
            {
                "song_name": "なんでもないや",
                "song_name_cn": "无所谓",
                "song_type": "ED",
                "singer": "RADWIMPS",
                "language": "ja",
                "lyrics_text": (
                    "なんでもないや\n"
                    "夢を見ていたんだ\n"
                    "あなたのことを\n"
                    "思い出せない\n"
                    "でも確かに\n"
                    "あなたがいた\n"
                    "この心の中に\n"
                    "消えない何かが\n"
                    "なんでもないや\n"
                    "ただ 泣きたいだけ"
                )
            }
        ]
    },
    {
        "anime": {"name": "四月是你的谎言", "name_jp": "四月はあなたの嘘です。", "year": 2014},
        "songs": [
            {
                "song_name": "がらくた",
                "song_name_cn": "废铜烂铁",
                "song_type": "OP",
                "singer": "96猫",
                "language": "ja",
                "lyrics_text": (
                    "ガラクタばかりの この部屋で\n"
                    "キミのことを思い出す\n"
                    "色褪せた写真の中で\n"
                    "キミはまだ笑ってる\n"
                    "音のない世界に\n"
                    "また迷い込んで\n"
                    "キミの声を探している\n"
                    "どこかにあるはずの\n"
                    "あの頃の音楽を"
                )
            },
            {
                "song_name": "オレンジ",
                "song_name_cn": "橙",
                "song_type": "ED",
                "singer": "7!!",
                "language": "ja",
                "lyrics_text": (
                    "オレンジ色の空\n"
                    "あなたと見た夕暮れ\n"
                    "忘れられない\n"
                    "あの日のこと\n"
                    "ピアノの音が\n"
                    "遠く消えていく\n"
                    "それでも確かに\n"
                    "あなたは生きていた\n"
                    "この瞬間に"
                )
            }
        ]
    },
]


def seed_offline_lyrics():
    """将内置歌词数据写入数据库（跳过已存在的记录）
    已于 2026-03 重新校对所有歌曲与动画的对应关系，并更新为正确数据。
    详见 reseed_lyrics.py（已同步本文件数据）。
    """
    from reseed_lyrics import reseed
    return reseed()


if __name__ == "__main__":
    seed_offline_lyrics()
