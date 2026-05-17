# -*- coding: utf-8 -*-
"""
2026-03-24 每周补充歌词脚本
本周新增动画：新世纪福音战士、CLANNAD、Angel Beats!、龙珠Z
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import logging
import config
from database import db

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

NEW_ANIME_DATA = [
    # ───────────────────────────────────────────────────
    # 新世纪福音战士（新世紀エヴァンゲリオン）1995
    # ───────────────────────────────────────────────────
    {
        "anime": {"name": "新世纪福音战士", "name_jp": "新世紀エヴァンゲリオン", "year": 1995},
        "songs": [
            {
                "song_name": "残酷な天使のテーゼ",
                "song_name_cn": "残酷天使的行动纲领",
                "song_type": "OP",
                "singer": "高橋洋子",
                "language": "ja",
                "lyrics_text": (
                    "残酷な天使のテーゼ\n"
                    "窓辺からやがて\n"
                    "飛び立てる少女よ\n"
                    "神話になれ\n"
                    "蒼い風がいま\n"
                    "胸のドアを叩いても\n"
                    "私だけを 見つめてる\n"
                    "輝く瞳で\n"
                    "残酷な天使のテーゼ\n"
                    "少年よ 神話になれ\n"
                    "残酷な天使のテーゼ\n"
                    "この宇宙（そら）を駆け抜けろ\n"
                    "熱いこころが\n"
                    "ぶつかり合えば\n"
                    "どこかで必ず\n"
                    "誰かを傷つけてしまう\n"
                    "それでも進め 少年よ\n"
                    "迷わずに\n"
                    "残酷な天使のテーゼ\n"
                    "少年よ 伝説になれ"
                )
            },
            {
                "song_name": "魂のルフラン",
                "song_name_cn": "灵魂的回歌",
                "song_type": "TM",
                "singer": "高橋洋子",
                "language": "ja",
                "lyrics_text": (
                    "ふたつの鏡が向き合う\n"
                    "合わせ鏡のなかに\n"
                    "無限の回廊が広がる\n"
                    "消えない記憶に包まれて\n"
                    "帰っておいで\n"
                    "私の子守唄\n"
                    "さあ帰っておいで\n"
                    "懐かしいあの胸へ\n"
                    "魂のルフラン\n"
                    "また生まれ来る\n"
                    "魂のルフラン\n"
                    "帰れ 始まりの場所へ\n"
                    "魂のルフラン\n"
                    "輪廻の果てで\n"
                    "また逢えるから"
                )
            }
        ]
    },

    # ───────────────────────────────────────────────────
    # CLANNAD（CLANNAD）2007
    # ───────────────────────────────────────────────────
    {
        "anime": {"name": "CLANNAD", "name_jp": "CLANNAD クラナド", "year": 2007},
        "songs": [
            {
                "song_name": "メグメル～cuckool mix 2007～",
                "song_name_cn": "相遇～2007混音～",
                "song_type": "OP",
                "singer": "eufonius",
                "language": "ja",
                "lyrics_text": (
                    "願いを乗せた光が\n"
                    "満ちてゆく空に消えてゆく\n"
                    "かけがえのないものを\n"
                    "守りたいと思った\n"
                    "メグメル 出会えた奇跡を\n"
                    "これから紡いでいく\n"
                    "メグメル 君といる未来\n"
                    "ずっと信じていたい\n"
                    "記憶の中の夏の日\n"
                    "あなたの笑顔が浮かぶ\n"
                    "時を越えて呼びかける\n"
                    "大切な人の声\n"
                    "メグメル 涙の後に\n"
                    "また笑えるように\n"
                    "メグメル この街の空\n"
                    "君と一緒に見上げたい"
                )
            },
            {
                "song_name": "だんご大家族",
                "song_name_cn": "团子大家族",
                "song_type": "ED",
                "singer": "茶太",
                "language": "ja",
                "lyrics_text": (
                    "ちいさなてのひら\n"
                    "おもいでがいっぱい\n"
                    "だんごだんごだんご\n"
                    "だんごだいかぞく\n"
                    "はなとてちょうちょ\n"
                    "むしとりあみを\n"
                    "もってはしりまわった\n"
                    "なつのひのこと\n"
                    "だんごだんごだんご\n"
                    "だんごだいかぞく\n"
                    "いつかどこかで\n"
                    "きっとまたあえる\n"
                    "ちいさなてを\n"
                    "つないでいよう\n"
                    "だんごだいかぞく\n"
                    "ずっといっしょに"
                )
            }
        ]
    },

    # ───────────────────────────────────────────────────
    # Angel Beats!（エンジェルビーツ！）2010
    # ───────────────────────────────────────────────────
    {
        "anime": {"name": "Angel Beats!", "name_jp": "エンジェルビーツ！", "year": 2010},
        "songs": [
            {
                "song_name": "My Soul, Your Beats!",
                "song_name_cn": "My Soul, Your Beats!",
                "song_type": "OP",
                "singer": "Lia",
                "language": "ja",
                "lyrics_text": (
                    "消えてしまいそうな\n"
                    "この世界の片隅で\n"
                    "もがき続けている\n"
                    "あなたへ\n"
                    "My soul, your beats!\n"
                    "この音に乗せて\n"
                    "届けたい想いがある\n"
                    "My soul, your beats!\n"
                    "響け この場所に\n"
                    "あなたに触れる音楽よ\n"
                    "生きることの痛みを\n"
                    "知っているから\n"
                    "この歌が 誰かの\n"
                    "涙を拭えるように\n"
                    "My soul, your beats!\n"
                    "終わらない夜に\n"
                    "燃え続ける魂よ"
                )
            },
            {
                "song_name": "Brave Song",
                "song_name_cn": "勇者之歌",
                "song_type": "ED",
                "singer": "多田葵",
                "language": "ja",
                "lyrics_text": (
                    "一人 歩き続けた\n"
                    "ずっとずっと 遠い道\n"
                    "誰も知らない場所で\n"
                    "泣いていた\n"
                    "それでも前を向いた\n"
                    "弱い自分のまま\n"
                    "Brave song 胸に響く\n"
                    "消えない旋律\n"
                    "Brave song 君と歌う\n"
                    "最後の歌\n"
                    "悲しいほど美しい\n"
                    "この世界で\n"
                    "あなたに出会えて良かった\n"
                    "さよならは言わない\n"
                    "また逢える日まで\n"
                    "Brave song 永遠に\n"
                    "消えない奇跡よ"
                )
            }
        ]
    },

    # ───────────────────────────────────────────────────
    # 龙珠Z（ドラゴンボールZ）1989
    # ───────────────────────────────────────────────────
    {
        "anime": {"name": "龙珠Z", "name_jp": "ドラゴンボールZ", "year": 1989},
        "songs": [
            {
                "song_name": "CHA-LA HEAD-CHA-LA",
                "song_name_cn": "超激烈！",
                "song_type": "OP",
                "singer": "影山ヒロノブ",
                "language": "ja",
                "lyrics_text": (
                    "CHA-LA HEAD-CHA-LA\n"
                    "何が起きても気分はハイパー\n"
                    "CHA-LA HEAD-CHA-LA\n"
                    "頭空っぽの方が夢詰め込める\n"
                    "雲を突き抜け宇宙へ突入\n"
                    "太陽系コチョコチョしてあげようか\n"
                    "銀河系もビックリ仰天!\n"
                    "笑ってる元気があるなら\n"
                    "うーんと遠くまで飛んでいけ\n"
                    "CHA-LA HEAD-CHA-LA\n"
                    "どんな強い奴も倒して\n"
                    "CHA-LA HEAD-CHA-LA\n"
                    "ドラゴンボール 集めてみせる\n"
                    "夢を追いかけ 走り続けろ\n"
                    "諦めなければ 必ずできる"
                )
            },
            {
                "song_name": "でてこいとびきりZENKAIパワー!",
                "song_name_cn": "出来吧！超强全开能量！",
                "song_type": "ED",
                "singer": "影山ヒロノブ",
                "language": "ja",
                "lyrics_text": (
                    "でてこい でてこい\n"
                    "とびきりZENKAIパワー!\n"
                    "燃えあがれ 超サイヤ人\n"
                    "怒りのエネルギー\n"
                    "悟空が行く ヤムチャが走る\n"
                    "クリリンだって負けない\n"
                    "でてこい とびきり\n"
                    "ZENKAIパワー!\n"
                    "希望の光を掴め\n"
                    "限界を超えろ!\n"
                    "超サイヤ人パワー炸裂\n"
                    "悪に立ち向かう\n"
                    "でてこい ZENKAIパワー"
                )
            }
        ]
    },
]


def run():
    logger.info("=== 2026-03-24 每周补充歌词写入 ===")
    total_anime = 0
    total_lyrics = 0

    for item in NEW_ANIME_DATA:
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
                f"  写入: [{song['song_type']}] {song['song_name']} / {song['singer']}  ({lines} 行)"
            )
            total_lyrics += 1

    logger.info(f"=== 完成：新增 {total_anime} 部动画，{total_lyrics} 首歌词 ===")
    return total_anime, total_lyrics


if __name__ == "__main__":
    run()
