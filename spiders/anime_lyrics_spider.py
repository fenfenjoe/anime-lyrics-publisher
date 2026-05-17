# -*- coding: utf-8 -*-
"""
歌词爬虫模块 - 从 QQ 音乐获取动漫 OP/ED 歌词
策略：仅从 QQ 音乐爬取（保证歌词与动漫严格一致），不走任何外网 fallback。
"""

import re
import logging
import json
from typing import List, Dict, Optional
from urllib.parse import quote, urljoin
import requests
from bs4 import BeautifulSoup

from anime_lyrics_publisher import config
from anime_lyrics_publisher.database import db
from .qq_music import get_lyrics_by_song, search_song

# 配置日志
logging.basicConfig(level=getattr(logging, config.LOG_LEVEL))
logger = logging.getLogger(__name__)


class LyricsSpider:
    """歌词爬虫基类"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
        })

    def search_anime(self, anime_name: str) -> List[Dict]:
        """搜索动画信息（子类实现）"""
        raise NotImplementedError

    def get_lyrics_list(self, anime_id: str) -> List[Dict]:
        """获取动画的歌词列表（子类实现）"""
        raise NotImplementedError

    def get_lyrics_content(self, lyrics_url: str) -> Optional[Dict]:
        """获取歌词详细内容（子类实现）"""
        raise NotImplementedError


# ═══════════════════════════════════════════════════════════════════
#  QQ 音乐爬虫（优先级最高，可精确匹配动漫歌曲）
# ═══════════════════════════════════════════════════════════════════

# 动漫歌曲配置表：key=动漫名，value=歌曲列表
# 每首歌曲格式：{"song_name": str, "singer": str, "song_type": str}
# song_type: OP=片头曲, ED=片尾曲, IN=插曲, TM=主题曲
ANIME_SONG_CONFIG: Dict[str, List[Dict]] = {
    "鬼灭之刃": [
        {"song_name": "紅蓮華",        "singer": "LiSA",              "song_type": "OP"},
        {"song_name": "from the edge", "singer": "FictionJunction",   "song_type": "ED"},
        {"song_name": "炎",            "singer": "LiSA",              "song_type": "TM"},
    ],
    "咒术回战": [
        {"song_name": "廻廻奇譚",       "singer": "Eve",               "song_type": "OP"},
        {"song_name": "LOST IN PARADISE","singer": "ALI",             "song_type": "ED"},
    ],
    "进击的巨人": [
        {"song_name": "紅蓮の弓矢",     "singer": "Linked Horizon",    "song_type": "OP"},
        {"song_name": "自由の翼",       "singer": "Linked Horizon",    "song_type": "ED"},
        {"song_name": "心臓を捧げよ！", "singer": "Linked Horizon",    "song_type": "OP"},
    ],
    "你的名字": [
        {"song_name": "前前前世",        "singer": "RADWIMPS",         "song_type": "TM"},
        {"song_name": "なんでもないや",  "singer": "RADWIMPS",         "song_type": "ED"},
        {"song_name": "スパークル",      "singer": "RADWIMPS",         "song_type": "TM"},
    ],
    "天气之子": [
        {"song_name": "愛にできることはまだあるかい", "singer": "RADWIMPS", "song_type": "TM"},
        {"song_name": "大丈夫",          "singer": "RADWIMPS",         "song_type": "TM"},
    ],
    "四月是你的谎言": [
        {"song_name": "がらくた",        "singer": "96neko",           "song_type": "OP"},
        # 注：96neko版在QQ音乐无法精确搜到，遵循"爬不到不保存"原则，不设 search_hints 兜底
        {"song_name": "オレンジ",        "singer": "7!!",              "song_type": "ED"},
        {"song_name": "キラメキ",        "singer": "wacci",            "song_type": "ED"},
    ],
    "紫罗兰永恒花园": [
        {"song_name": "Sincerely",       "singer": "TRUE",             "song_type": "OP"},
        {"song_name": "みちしるべ",      "singer": "TRUE",             "song_type": "ED"},
    ],
    "刀剑神域": [
        {"song_name": "crossing field",  "singer": "LiSA",             "song_type": "OP"},
        {"song_name": "Catch The Moment","singer": "LiSA",             "song_type": "OP"},
    ],
    "声之形": [
        {"song_name": "恋をしたのは",    "singer": "aiko",             "song_type": "TM"},
    ],
    "未闻花名": [
        {"song_name": "secret base",     "singer": "zone",             "song_type": "ED"},
    ],
    "秒速五厘米": [
        {"song_name": "One more time, One more chance", "singer": "山崎まさよし", "song_type": "TM"},
    ],
    "千与千寻": [
        {"song_name": "いつも何度でも",  "singer": "木村弓",           "song_type": "TM"},
    ],
    "龙猫": [
        {"song_name": "となりのトトロ",  "singer": "井上あずみ",       "song_type": "TM"},
    ],
    "萤火虫之墓": [
        {"song_name": "悲しくてやりきれない", "singer": "ザ・フォーク・クルセダーズ", "song_type": "TM"},
    ],
    "fate/zero": [
        {"song_name": "oath sign",       "singer": "LiSA",             "song_type": "OP"},
        {"song_name": "To the beginning","singer": "Kalafina",         "song_type": "ED"},
    ],
    "fate/stay night": [
        {"song_name": "Disillusion",     "singer": "タイナカサチ",      "song_type": "OP",
         "search_hints": ["Disillusion タイナカサチ", "Disillusion Tainaka Sachi", "Tainaka Sachi Disillusion"]},
    ],
    # ── 新增批次 1 ──────────────────────────────────────────────────────
    "新世纪福音战士": [
        {"song_name": "残酷な天使のテーゼ", "singer": "高橋洋子",       "song_type": "OP"},
        {"song_name": "魂のルフラン",        "singer": "高橋洋子",       "song_type": "TM"},
    ],
    "CLANNAD": [
        {"song_name": "メグメル～cuckool mix 2007～", "singer": "eufonius", "song_type": "OP"},
        {"song_name": "だんご大家族",        "singer": "茶太",           "song_type": "ED"},
    ],
    "Angel Beats!": [
        {"song_name": "My Soul, Your Beats!", "singer": "Lia",           "song_type": "OP"},
        {"song_name": "Brave Song",           "singer": "多田葵",         "song_type": "ED"},
    ],
    "龙珠Z": [
        {"song_name": "CHA-LA HEAD-CHA-LA",           "singer": "影山ヒロノブ", "song_type": "OP"},
        {"song_name": "でてこいとびきりZENKAIパワー!", "singer": "影山ヒロノブ", "song_type": "ED"},
    ],
    "魔法少女小圆": [
        {"song_name": "コネクト",            "singer": "ClariS",         "song_type": "OP"},
        {"song_name": "Magia",               "singer": "Kalafina",       "song_type": "ED"},
    ],
    "凉宫春日的忧郁": [
        {"song_name": "冒険でしょでしょ？",  "singer": "平野綾",         "song_type": "OP"},
        {"song_name": "ハレ晴レユカイ",      "singer": "平野綾",         "song_type": "ED"},
    ],
    "轻音少女": [
        {"song_name": "Don't say \"lazy\"",  "singer": "放课后TEA TIME", "song_type": "ED"},
        {"song_name": "GO! GO! MANIAC",      "singer": "放课后TEA TIME", "song_type": "OP"},
    ],
    "我的青春恋爱物语果然有问题": [
        {"song_name": "My Teen Romantic Comedy SNAFU", "singer": "稲川英里", "song_type": "OP",
         "search_hints": ["My Teen Romantic Comedy SNAFU 稲川英里", "SNAFU 稲川英里", "やはり俺の青春 OP"]},
        {"song_name": "Everyday World",      "singer": "8P",              "song_type": "ED",
         "search_hints": ["Everyday World 8P", "Everyday World やはり俺の青春"]},
    ],
    "夏目友人帐": [
        {"song_name": "グリーン",            "singer": "さユり",         "song_type": "OP"},
        {"song_name": "思い出の樹",          "singer": "コアラモード",   "song_type": "ED"},
    ],
    "物语系列": [
        {"song_name": "staple stable",       "singer": "SHINOBU",        "song_type": "OP"},
        {"song_name": "恋愛サーキュレーション","singer": "花澤香菜",      "song_type": "ED"},
    ],
    "Re:从零开始的异世界生活": [
        {"song_name": "Redo",                "singer": "鈴木このみ",     "song_type": "OP"},
        {"song_name": "Stay Alive",          "singer": "鈴木このみ",     "song_type": "OP"},
        {"song_name": "メリッサ",            "singer": "ポルノグラフィティ", "song_type": "TM"},
    ],
    "约定的梦幻岛": [
        {"song_name": "Touch off",           "singer": "UVERworld",      "song_type": "OP"},
        {"song_name": "Zettai Zetsumei",     "singer": "Cö shu Nie",     "song_type": "ED"},
    ],
    "寄生兽": [
        {"song_name": "Let Me Hear",         "singer": "Fear, and Loathing in Las Vegas", "song_type": "OP"},
        {"song_name": "It's the right time", "singer": "Daichi Miura",   "song_type": "ED"},
    ],
    "灵能百分百": [
        {"song_name": "99",                  "singer": "MOB CHOIR",      "song_type": "OP"},
        {"song_name": "Refrain Boy",         "singer": "All Off",        "song_type": "ED"},
    ],
    "来自深渊": [
        {"song_name": "Deep in Abyss",       "singer": "Miyu Tomita",    "song_type": "OP"},
        {"song_name": "Hanezeve Caradhina",  "singer": "Takeshi Saito",  "song_type": "ED"},
    ],
    # ── 后备池（ANIME_RESERVE_LIST）对应的歌曲配置 ───────────────────────
    # ── 钢之炼金术师 2003 版 ─────────────────────────────────────────────
    "钢之炼金术师": [
        {"song_name": "Melissa",             "singer": "ポルノグラフィティ", "song_type": "OP",
         "search_hints": ["Melissa ポルノグラフィティ", "メリッサ ポルノグラフィティ", "Melissa 鋼の錬金術師"]},
        {"song_name": "READY STEADY GO",     "singer": "L'Arc〜en〜Ciel",   "song_type": "OP",
         "search_hints": ["READY STEADY GO L'Arc", "READY STEADY GO ラルク", "READY STEADY GO 鋼の錬金術師"]},
        {"song_name": "UNDO",                "singer": "COOL JOKE",          "song_type": "OP",
         "search_hints": ["UNDO COOL JOKE", "UNDO 鋼の錬金術師"]},
        {"song_name": "リライト",            "singer": "ASIAN KUNG-FU GENERATION", "song_type": "OP",
         "search_hints": ["リライト AKFG", "Rewrite ASIAN KUNG-FU GENERATION", "リライト 鋼の錬金術師"]},
        {"song_name": "消せない罪",          "singer": "北出菜奈",           "song_type": "ED",
         "search_hints": ["消せない罪 北出菜奈", "Kesenai Tsumi Kitade Nana"]},
        {"song_name": "扉の向こうへ",        "singer": "YeLLOW Generation",  "song_type": "ED",
         "search_hints": ["扉の向こうへ YeLLOW Generation"]},
        {"song_name": "Motherland",          "singer": "Crystal Kay",        "song_type": "ED",
         "search_hints": ["Motherland Crystal Kay", "Motherland 鋼の錬金術師"]},
        {"song_name": "I Will",              "singer": "Sowelu",             "song_type": "ED",
         "search_hints": ["I Will Sowelu", "Sowelu I Will 鋼の錬金術師"]},
    ],
    "火影忍者": [
        {"song_name": "R★O★C★K★S",          "singer": "HOUND DOG",      "song_type": "OP",
         "search_hints": ["ROCKS HOUND DOG", "R★O★C★K★S NARUTO"]},
        {"song_name": "遥か彼方",            "singer": "ASIAN KUNG-FU GENERATION", "song_type": "OP",
         "search_hints": ["遥か彼方 AKFG", "遥か彼方 NARUTO", "遥か彼方 ASIAN KUNG-FU GENERATION"]},
        {"song_name": "悲しみをやさしさに",  "singer": "little by little",  "song_type": "OP",
         "search_hints": ["悲しみをやさしさに little by little", "悲しみをやさしさに NARUTO"]},
        {"song_name": "GO!!!",               "singer": "FLOW",               "song_type": "OP",
         "search_hints": ["GO!!! FLOW", "GO FLOW NARUTO"]},
        {"song_name": "青春狂騒曲",          "singer": "サンボマスター",     "song_type": "OP",
         "search_hints": ["青春狂騒曲 サンボマスター", "青春狂騒曲 NARUTO"]},
        {"song_name": "Wind",                "singer": "Akeboshi",           "song_type": "ED",
         "search_hints": ["Wind Akeboshi", "Wind NARUTO"]},
        {"song_name": "ハルモニア",          "singer": "RYTHEM",             "song_type": "ED",
         "search_hints": ["ハルモニア RYTHEM", "Harumonia NARUTO"]},
    ],
    # ── 火影忍者疾风传 ────────────────────────────────────────────────────
    "火影忍者疾风传": [
        {"song_name": "Hero's Come Back!!",  "singer": "nobodyknows+",   "song_type": "OP",
         "search_hints": ["Hero's Come Back nobodyknows", "Heros Come Back NARUTO疾風伝"]},
        {"song_name": "distance",            "singer": "LONG SHOT PARTY","song_type": "OP",
         "search_hints": ["distance LONG SHOT PARTY", "distance NARUTO疾風伝"]},
        {"song_name": "ブルーバード",        "singer": "いきものがかり",  "song_type": "OP",
         "search_hints": ["ブルーバード いきものがかり", "Blue Bird NARUTO疾風伝", "青鸟 いきものがかり"]},
        {"song_name": "CLOSER",              "singer": "井上ジョー",      "song_type": "OP",
         "search_hints": ["CLOSER 井上ジョー", "CLOSER Joe Inoue NARUTO"]},
        {"song_name": "ホタルノヒカリ",      "singer": "いきものがかり",  "song_type": "OP",
         "search_hints": ["ホタルノヒカリ いきものがかり", "Hotaru no Hikari NARUTO"]},
        {"song_name": "Sign",                "singer": "FLOW",            "song_type": "OP",
         "search_hints": ["Sign FLOW", "Sign NARUTO疾風伝 FLOW"]},
        {"song_name": "透明だった世界",      "singer": "秦基博",          "song_type": "OP",
         "search_hints": ["透明だった世界 秦基博", "透明だった世界 NARUTO"]},
        {"song_name": "Diver",               "singer": "NICO Touches the Walls", "song_type": "OP",
         "search_hints": ["Diver NICO Touches the Walls", "Diver NARUTO疾風伝"]},
        {"song_name": "ラヴァーズ",          "singer": "7!!",             "song_type": "OP",
         "search_hints": ["ラヴァーズ 7!!", "Lovers Seven Oops NARUTO"]},
        {"song_name": "newsong",             "singer": "tacica",          "song_type": "OP",
         "search_hints": ["newsong tacica", "newsong NARUTO疾風伝"]},
        {"song_name": "突撃ロック",          "singer": "ザ・クロマニヨンズ", "song_type": "OP",
         "search_hints": ["突撃ロック クロマニヨンズ", "突撃ロック NARUTO"]},
        {"song_name": "Moshimo",             "singer": "ダイスケ",        "song_type": "OP",
         "search_hints": ["Moshimo ダイスケ", "Moshimo NARUTO疾風伝"]},
        {"song_name": "ニワカ雨ニモ負ケズ",  "singer": "NICO Touches the Walls", "song_type": "OP",
         "search_hints": ["ニワカ雨ニモ負ケズ NICO", "ニワカ雨ニモ負ケズ NARUTO"]},
        {"song_name": "月の大きさ",          "singer": "乃木坂46",        "song_type": "OP",
         "search_hints": ["月の大きさ 乃木坂46", "月の大きさ NARUTO"]},
        {"song_name": "紅蓮",                "singer": "DOES",            "song_type": "OP",
         "search_hints": ["紅蓮 DOES", "Guren DOES NARUTO疾風伝"]},
        {"song_name": "シルエット",          "singer": "KANA-BOON",       "song_type": "OP",
         "search_hints": ["シルエット KANA-BOON", "Silhouette KANA-BOON NARUTO"]},
        {"song_name": "風",                  "singer": "山猿",            "song_type": "OP",
         "search_hints": ["風 山猿", "Kaze Yamasaru NARUTO疾風伝"]},
        {"song_name": "LINE",                "singer": "スキマスイッチ",  "song_type": "OP",
         "search_hints": ["LINE スキマスイッチ", "LINE Sukima Switch NARUTO"]},
        {"song_name": "ブラッドサーキュレーター", "singer": "ASIAN KUNG-FU GENERATION", "song_type": "OP",
         "search_hints": ["ブラッドサーキュレーター AKFG", "Blood Circulator NARUTO"]},
        {"song_name": "カラノココロ",        "singer": "Anly",            "song_type": "OP",
         "search_hints": ["カラノココロ Anly", "Kara no Kokoro NARUTO疾風伝"]},
        # ── ED ────────────────────────────────────────────────────────────
        {"song_name": "流れ星～Shooting Star～", "singer": "HOME MADE 家族", "song_type": "ED",
         "search_hints": ["流れ星 HOME MADE 家族", "Shooting Star HOME MADE NARUTO"]},
        {"song_name": "道～to you all",      "singer": "aluto",           "song_type": "ED",
         "search_hints": ["道 to you all aluto", "道 aluto NARUTO疾風伝"]},
        {"song_name": "Broken Youth",        "singer": "NICO Touches the Walls", "song_type": "ED",
         "search_hints": ["Broken Youth NICO Touches the Walls", "Broken Youth NARUTO"]},
        {"song_name": "うたかた花火",        "singer": "supercell",       "song_type": "ED",
         "search_hints": ["うたかた花火 supercell", "Utakata Hanabi NARUTO疾風伝"]},
        {"song_name": "真夜中のオーケストラ","singer": "Aqua Timez",      "song_type": "ED",
         "search_hints": ["真夜中のオーケストラ Aqua Timez", "真夜中のオーケストラ NARUTO"]},
        {"song_name": "FREEDOM",             "singer": "HOME MADE 家族",  "song_type": "ED",
         "search_hints": ["FREEDOM HOME MADE 家族", "FREEDOM NARUTO疾風伝"]},
        {"song_name": "シルエット",          "singer": "KANA-BOON",       "song_type": "OP",
         "search_hints": ["シルエット KANA-BOON"]},
        {"song_name": "さよならメモリー",    "singer": "7!!",             "song_type": "ED",
         "search_hints": ["さよならメモリー 7!!", "Sayonara Memory NARUTO"]},
        {"song_name": "Spinning World",      "singer": "Diana Garnett",   "song_type": "ED",
         "search_hints": ["Spinning World Diana Garnett", "Spinning World NARUTO疾風伝"]},
        {"song_name": "ピノとアメリ",        "singer": "石崎ひゅーい",    "song_type": "ED",
         "search_hints": ["ピノとアメリ 石崎ひゅーい", "ピノとアメリ NARUTO"]},
        {"song_name": "絶絶",                "singer": "Swimy",           "song_type": "ED",
         "search_hints": ["絶絶 Swimy", "絶絶 NARUTO疾風伝"]},
    ],
    "钢之炼金术师FA": [
        {"song_name": "again",               "singer": "YUI",                "song_type": "OP",
         "search_hints": ["again YUI", "again YUI 鋼の錬金術師"]},
        {"song_name": "ホログラム",          "singer": "NICO Touches the Walls", "song_type": "OP",
         "search_hints": ["ホログラム NICO Touches the Walls", "Hologram 鋼の錬金術師"]},
        {"song_name": "ゴールデンタイムラバー","singer": "スキマスイッチ",  "song_type": "OP",
         "search_hints": ["ゴールデンタイムラバー スキマスイッチ", "Golden Time Lover 鋼の錬金術師"]},
        {"song_name": "Period",              "singer": "CHEMISTRY",          "song_type": "OP",
         "search_hints": ["Period CHEMISTRY", "Period 鋼の錬金術師"]},
        {"song_name": "レイン",              "singer": "SID",                "song_type": "OP",
         "search_hints": ["レイン SID", "Rain SID 鋼の錬金術師"]},
        {"song_name": "嘘",                  "singer": "SID",                "song_type": "ED",
         "search_hints": ["嘘 SID", "SID 嘘 鋼の錬金術師"]},
        {"song_name": "LET IT OUT",          "singer": "福原美穂",           "song_type": "ED",
         "search_hints": ["LET IT OUT 福原美穂", "LET IT OUT 鋼の錬金術師"]},
        {"song_name": "瞬間センチメンタル",  "singer": "SCANDAL",            "song_type": "ED",
         "search_hints": ["瞬間センチメンタル SCANDAL", "Shunkan Sentimental SCANDAL"]},
        {"song_name": "RAY OF LIGHT",        "singer": "中川翔子",           "song_type": "ED",
         "search_hints": ["RAY OF LIGHT 中川翔子", "RAY OF LIGHT 鋼の錬金術師 しょこたん"]},
    ],
    # ── 笨女孩（アホガール）2017 ─────────────────────────────────────────
    "笨女孩": [
        {"song_name": "全力☆Summer!",        "singer": "angela",          "song_type": "OP",
         "search_hints": ["全力Summer angela", "全力☆Summer アホガール", "全力サマー angela"]},
    ],
    # ── 机动战士高达SEED ─────────────────────────────────────────────────
    "机动战士高达SEED": [
        {"song_name": "INVOKE",              "singer": "T.M.Revolution",  "song_type": "OP",
         "search_hints": ["INVOKE T.M.Revolution", "INVOKE TMR ガンダムSEED"]},
        {"song_name": "moment",              "singer": "vivian or kazuma", "song_type": "OP",
         "search_hints": ["moment vivian or kazuma", "moment ガンダムSEED"]},
        {"song_name": "Believe",             "singer": "玉置成実",         "song_type": "OP",
         "search_hints": ["Believe 玉置成実", "Believe ガンダムSEED"]},
        {"song_name": "Realize",             "singer": "玉置成実",         "song_type": "OP",
         "search_hints": ["Realize 玉置成実", "Realize ガンダムSEED"]},
        {"song_name": "あんなに一緒だったのに", "singer": "See-Saw",        "song_type": "ED",
         "search_hints": ["あんなに一緒だったのに See-Saw", "あんなに一緒だったのに ガンダムSEED"]},
        {"song_name": "Distance",            "singer": "FictionJunction YUUKA", "song_type": "ED",
         "search_hints": ["Distance FictionJunction YUUKA", "Distance ガンダムSEED"]},
        {"song_name": "FIND THE WAY",        "singer": "中島美嘉",          "song_type": "ED",
         "search_hints": ["FIND THE WAY 中島美嘉", "FIND THE WAY ガンダムSEED"]},
    ],
    # ── 机动战士高达00 ────────────────────────────────────────────────────
    "机动战士高达00": [
        {"song_name": "DAYBREAK'S BELL",     "singer": "L'Arc〜en〜Ciel",  "song_type": "OP",
         "search_hints": ["DAYBREAK'S BELL L'Arc", "DAYBREAK'S BELL ラルク ガンダム00"]},
        {"song_name": "Ash Like Snow",       "singer": "the brilliant green", "song_type": "OP",
         "search_hints": ["Ash Like Snow the brilliant green", "Ash Like Snow ガンダム00"]},
        {"song_name": "儚くも永久のカナシ",  "singer": "UVERworld",         "song_type": "OP",
         "search_hints": ["儚くも永久のカナシ UVERworld", "儚くも永久のカナシ ガンダム00"]},
        {"song_name": "泪のムコウ",          "singer": "ステレオポニー",    "song_type": "OP",
         "search_hints": ["泪のムコウ ステレオポニー", "泪のムコウ ガンダム00 Stereopony"]},
        {"song_name": "罠",                  "singer": "THE BACK HORN",     "song_type": "ED",
         "search_hints": ["罠 THE BACK HORN", "罠 ガンダム00"]},
        {"song_name": "フレンズ",            "singer": "Stephanie",         "song_type": "ED",
         "search_hints": ["フレンズ Stephanie ガンダム00", "Friends Stephanie ガンダム00"]},
        {"song_name": "trust you",           "singer": "伊藤由奈",          "song_type": "ED",
         "search_hints": ["trust you 伊藤由奈", "trust you ガンダム00"]},
    ],
    "NANA": [
        {"song_name": "ROSE",                "singer": "Anna Tsuchiya",  "song_type": "OP"},
        {"song_name": "a little pain",       "singer": "OLIVIA",         "song_type": "ED"},
    ],
    "狼与香辛料": [
        {"song_name": "旅の途中",            "singer": "岡崎律子",       "song_type": "OP"},
        {"song_name": "太陽とリゲル",        "singer": "Rocky Chack",    "song_type": "ED"},
    ],
    "虫师": [
        {"song_name": "The Sore Feet Song",  "singer": "Ally Kerr",      "song_type": "OP"},
    ],
    "黑子的篮球": [
        {"song_name": "Can Do",              "singer": "GRANRODEO",      "song_type": "OP"},
        {"song_name": "fantastic tune",      "singer": "OLDCODEX",       "song_type": "ED"},
    ],
    "排球少年": [
        {"song_name": "ヒカリアレ",          "singer": "BURNOUT SYNDROMES", "song_type": "OP"},
        {"song_name": "はじまりの歌",        "singer": "岡崎体育",       "song_type": "ED"},
    ],
    "死亡笔记": [
        {"song_name": "the WORLD",           "singer": "高橋瞳",         "song_type": "OP",
         "search_hints": ["the WORLD 高橋瞳", "the WORLD デスノート", "高橋瞳 the WORLD"]},
        {"song_name": "alumina",             "singer": "Nightmare",      "song_type": "ED",
         "search_hints": ["alumina Nightmare", "alumina デスノート", "Nightmare alumina"]},
    ],
    "青春猪头少年不会梦到兔女郎学姐": [
        {"song_name": "Distortion!!",        "singer": "Uru",            "song_type": "OP"},
        {"song_name": "Fukashigi no Carte",  "singer": "Mai Sakurajima", "song_type": "ED"},
    ],
    "小城日常": [
        {"song_name": "Hello",               "singer": "Furui Riho",     "song_type": "OP",
         "search_hints": ["Hello Furui Riho", "Hello CITY THE ANIMATION", "フルイリホ Hello"]},
        {"song_name": "LUCKY",               "singer": "TOMOO",          "song_type": "ED",
         "search_hints": ["LUCKY TOMOO", "TOMOO LUCKY CITY", "TOMOO LUCKY 小城日常"]},
    ],
    # ── 用户新增批次 2026-05-10 ──────────────────────────────────────
    "间谍过家家": [
        {"song_name": "ミックスナッツ", "singer": "Official髭男dism", "song_type": "OP",
         "search_hints": ["ミックスナッツ Official髭男dism", "Mixed Nuts Official Hige Dan", "SPY×FAMILY OP"]},
        {"song_name": "喜劇",             "singer": "星野源",           "song_type": "ED",
         "search_hints": ["喜劇 星野源", "Kigeki Hoshino Gen SPYxFAMILY", "SPY×FAMILY ED 星野源"]},
    ],
    "齐木楠雄的灾难": [
        {"song_name": "Ψレントプリズナー", "singer": "斉木ックラバー", "song_type": "OP",
         "search_hints": ["Ψレントプリズナー", "PSI Rent Prisoner", "斉木ックラバー", "サイキクスオ プリズナー"]},
        {"song_name": "Ψ発見伝!",         "singer": "でんぱ組.inc",     "song_type": "ED",
         "search_hints": ["Ψ発見伝 でんぱ組.inc", "Psihatsuden denpagumi", "斉木楠雄のΨ難 ED"]},
    ],
    "胆大党": [
        {"song_name": "オトノケ",         "singer": "Creepy Nuts",    "song_type": "OP",
         "search_hints": ["オトノケ Creepy Nuts", "Otonoke DanDaDan OP", "ダンダダン OP Creepy Nuts"]},
        {"song_name": "TAIDADA",            "singer": "ずっと真夜中でいいのに。", "song_type": "ED",
         "search_hints": ["TAIDADA ずっと真夜中でいいのに。", "Taidada ZUTOMAYO DanDaDan ED", "ダンダダン ED"]},
    ],
}


class QQMusicSpider:
    """
    QQ 音乐歌词爬虫。
    通过 ANIME_SONG_CONFIG 配置表精确定位动漫歌曲，
    调用 qq_music 模块的接口获取完整歌词。
    """

    def get_songs_for_anime(self, anime: Dict) -> List[Dict]:
        """
        根据动漫信息返回对应的歌曲配置列表。
        依次匹配: 中文名 → 日文名 → 模糊匹配。
        """
        anime_name    = anime.get("name", "")
        anime_name_jp = anime.get("name_jp", "")

        # 精确匹配
        for key in [anime_name, anime_name_jp]:
            if key and key in ANIME_SONG_CONFIG:
                return ANIME_SONG_CONFIG[key]

        # 模糊匹配（中文名包含关系）
        for config_name, songs in ANIME_SONG_CONFIG.items():
            if (anime_name and (anime_name in config_name or config_name in anime_name)):
                return songs

        return []

    def crawl(self, anime: Dict) -> List[Dict]:
        """
        爬取指定动漫的歌词。
        返回成功入库的歌词数据列表。
        """
        anime_id   = anime["id"]
        anime_name = anime.get("name", "")
        anime_name_jp = anime.get("name_jp", anime_name)

        song_configs = self.get_songs_for_anime(anime)
        if not song_configs:
            logger.info(f"QQMusicSpider: {anime_name} 不在配置表中，跳过")
            return []

        logger.info(f"QQMusicSpider: 开始爬取 {anime_name}，配置了 {len(song_configs)} 首歌")
        results = []

        for cfg in song_configs:
            song_name = cfg["song_name"]
            singer    = cfg.get("singer")
            song_type = cfg.get("song_type", "TM")

            # 已存在则跳过
            if db.check_lyrics_exists(anime_id, song_name):
                logger.info(f"  已存在: {song_name}")
                continue

            logger.info(f"  获取歌词: {singer} - {song_name}")

            lyric_data = None

            # ── 标准搜索 ──────────────────────────────────────────────
            lyric_data = get_lyrics_by_song(
                song_name=song_name,
                singer=singer,
                anime_name=anime_name_jp or anime_name,
            )

            # ── 歌手交叉验证：如果匹配到的歌手与期望完全不一致，视为误匹配 ──
            if lyric_data and singer and lyric_data.get("lines"):
                actual_singer = (lyric_data.get("singer") or "").lower()
                expected_singer = singer.lower()
                # 拆分歌手名（支持多歌手、含特殊字符），取各段做包含匹配
                # 例："Fear, and Loathing in Las Vegas" → ["fear", "and", "loathing", "in", "las", "vegas"]
                # 例："8P" → ["8p"]
                def _split_singer(s: str):
                    # 先按常见分隔符拆，再过滤空段
                    parts = re.split(r'[/,、&×\s]+', s.strip())
                    return [p.lower() for p in parts if p.strip()]

                expected_parts = _split_singer(expected_singer)
                actual_parts   = _split_singer(actual_singer)

                singer_ok = (
                    expected_singer in actual_singer
                    or actual_singer in expected_singer
                    # 期望歌手任意一段出现在实际歌手中
                    or any(ep and ep in actual_singer for ep in expected_parts if len(ep) >= 2)
                    # 实际歌手任意一段出现在期望歌手中
                    or any(ap and ap in expected_singer for ap in actual_parts if len(ap) >= 2)
                )
                if not singer_ok:
                    logger.warning(f"  歌手不匹配（期望: {singer}，实际: {lyric_data.get('singer')}），尝试 search_hints")
                    lyric_data = None  # 丢弃误匹配结果

            # ── search_hints 备用搜索 ──────────────────────────────────
            if not lyric_data and cfg.get("search_hints"):
                for hint in cfg["search_hints"]:
                    logger.info(f"  尝试备用搜索词: {hint}")
                    lyric_data = get_lyrics_by_song(song_name=hint)
                    if lyric_data and lyric_data.get("lines"):
                        break

            if not lyric_data or not lyric_data.get("lines"):
                logger.warning(f"  QQ 音乐未找到歌词: {song_name}")
                continue

            lines      = lyric_data["lines"]

            # ── 纯音乐/无歌词检测 ────────────────────────────────────
            # QQ 音乐对纯器乐会返回一行固定占位文本，检测到则跳过不入库
            INSTRUMENTAL_MARKERS = [
                "纯音乐",
                "没有填词",
                "纯器乐",
                "本歌曲为纯音乐",
                "此歌曲为没有填词",
                "instrumental",
            ]
            joined = "\n".join(lines).lower()
            if len(lines) <= 2 and any(m.lower() in joined for m in INSTRUMENTAL_MARKERS):
                logger.warning(f"  检测到纯音乐/无歌词，跳过不入库: {song_name}")
                continue
            # ─────────────────────────────────────────────────────────
            lyrics_text = "\n".join(lines)
            actual_singer = lyric_data.get("singer") or singer or ""

            # ── 非日文歌词过滤（固定规则）────────────────────────────
            # 歌词大部分不是日文（detect_language() != 'ja'）则不入库
            # 这是为了强制保证爬到的歌词是日文动漫歌曲，适配日语学习场景
            lang = detect_language(lyrics_text)
            if lang != 'ja':
                logger.warning(
                    f"  歌词语言非日文 (detect={lang})，"
                    f"跳过不入库: {song_name}（固定规则：仅入库日文歌词）"
                )
                continue

            lyrics_record = {
                "anime_id":    anime_id,
                "song_name":   song_name,
                "song_name_cn": None,
                "song_type":   song_type,
                "singer":      actual_singer,
                "language":    lang,
                "lyrics_text": lyrics_text,
            }
            db.add_lyrics(**lyrics_record)
            results.append(lyrics_record)
            logger.info(f"  保存成功: {song_name} ({len(lines)} 行)")

        return results


class AnimeLyricsComSpider(LyricsSpider):
    """AnimeLyrics.com 爬虫"""

    BASE_URL = "https://www.animelyrics.com"

    def search_anime(self, anime_name: str) -> List[Dict]:
        """搜索动画"""
        results = []
        try:
            # 直接尝试搜索
            search_url = f"{self.BASE_URL}/search?q={quote(anime_name)}"
            response = self.session.get(search_url, timeout=15)
            soup = BeautifulSoup(response.text, 'lxml')

            # 解析搜索结果
            for link in soup.select('a[href*="/anime/"]'):
                title = link.get_text(strip=True)
                if anime_name.lower() in title.lower():
                    results.append({
                        'title': title,
                        'url': urljoin(self.BASE_URL, link.get('href', ''))
                    })
        except Exception as e:
            logger.error(f"AnimeLyrics 搜索失败: {e}")
        return results

    def get_lyrics_list(self, anime_url: str) -> List[Dict]:
        """获取动画的歌词列表"""
        lyrics_list = []
        try:
            response = self.session.get(anime_url, timeout=15)
            soup = BeautifulSoup(response.text, 'lxml')

            for link in soup.select('a[href*=".htm"]'):
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                # 判断是 OP 还是 ED
                song_type = None
                if 'opening' in href.lower() or 'op' in text.lower():
                    song_type = 'OP'
                elif 'ending' in href.lower() or 'ed' in text.lower():
                    song_type = 'ED'
                elif 'insert' in href.lower() or 'in' in text.lower():
                    song_type = 'IN'

                if song_type or 'theme' in href.lower():
                    lyrics_list.append({
                        'song_name': text,
                        'url': urljoin(anime_url, href),
                        'song_type': song_type or 'TM'
                    })
        except Exception as e:
            logger.error(f"获取歌词列表失败: {e}")
        return lyrics_list

    def get_lyrics_content(self, lyrics_url: str) -> Optional[Dict]:
        """获取歌词内容"""
        try:
            response = self.session.get(lyrics_url, timeout=15)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'lxml')

            # 获取原版歌词（日文）
            japanese_lyrics = []
            for elem in soup.select('.lyrics'):
                text = elem.get_text(strip=True)
                if text:
                    japanese_lyrics.append(text)

            # 获取罗马字/翻译歌词
            roman_lyrics = []
            translation = []
            for elem in soup.select('.romaji, .translation, .eng'):
                text = elem.get_text(strip=True)
                if text:
                    if elem.get('class', [''])[0] == 'romaji':
                        roman_lyrics.append(text)
                    else:
                        translation.append(text)

            # 获取歌曲信息
            singer = None
            song_name = None
            for elem in soup.select('.artist, .songtitle'):
                text = elem.get_text(strip=True)
                if 'artist' in elem.get('class', ['']):
                    singer = text
                else:
                    song_name = text

            return {
                'japanese': '\n'.join(japanese_lyrics),
                'roman': '\n'.join(roman_lyrics),
                'translation': '\n'.join(translation),
                'singer': singer,
                'song_name': song_name
            }
        except Exception as e:
            logger.error(f"获取歌词内容失败: {e}")
            return None


class AniDBSpider(LyricsSpider):
    """AniDB 爬虫"""

    BASE_URL = "https://anidb.net"

    def search_anime(self, anime_name: str) -> List[Dict]:
        """搜索动画"""
        results = []
        try:
            search_url = f"{self.BASE_URL}/anime/?adb.search={quote(anime_name)}&no=1"
            response = self.session.get(search_url, timeout=15)
            soup = BeautifulSoup(response.text, 'lxml')

            for link in soup.select('a[href^="/anime/"]'):
                title = link.get_text(strip=True)
                if title:
                    results.append({
                        'title': title,
                        'url': urljoin(self.BASE_URL, link.get('href', ''))
                    })
        except Exception as e:
            logger.error(f"AniDB 搜索失败: {e}")
        return results


class JpopWikiSpider(LyricsSpider):
    """JpopWiki 爬虫"""

    BASE_URL = "https://ja.wikipedia.org/wiki"

    def search_anime(self, anime_name: str) -> List[Dict]:
        """搜索动画（使用维基百科）"""
        results = []
        try:
            search_url = f"{self.BASE_URL}/w/index.php?search={quote(anime_name + ' アニメ')}&limit=10"
            response = self.session.get(search_url, timeout=15)
            soup = BeautifulSoup(response.text, 'lxml')

            for link in soup.select('.mw-search-result a'):
                results.append({
                    'title': link.get_text(strip=True),
                    'url': urljoin(self.BASE_URL, link.get('href', ''))
                })
        except Exception as e:
            logger.error(f"JpopWiki 搜索失败: {e}")
        return results


def detect_language(text: str) -> str:
    """检测歌词语言"""
    # 简单的语言检测
    japanese_chars = re.compile(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]')
    hiragana = re.compile(r'[\u3040-\u309F]')
    katakana = re.compile(r'[\u30A0-\u30FF]')
    
    japanese_count = len(japanese_chars.findall(text))
    hiragana_count = len(hiragana.findall(text))
    katakana_count = len(katakana.findall(text))
    
    if japanese_count + hiragana_count + katakana_count > len(text) * 0.3:
        return 'ja'  # 日语
    elif re.search(r'[a-zA-Z]', text):
        return 'en'  # 英语
    elif re.search(r'[\u4E00-\u9FAF]', text):
        return 'zh'  # 中文
    return 'unknown'


def parse_lyrics_to_lines(lyrics_text: str) -> List[str]:
    """将歌词文本解析为行列表"""
    if not lyrics_text:
        return []
    lines = [line.strip() for line in lyrics_text.split('\n') if line.strip()]
    return lines


class LyricsCrawler:
    """
    歌词爬虫调度器。
    策略：仅从 QQ 音乐爬取（保证歌词与动漫严格一致）。
    - 动漫在 ANIME_SONG_CONFIG 中：逐首从 QQ 音乐获取，获取失败的歌曲直接跳过，不补其他来源。
    - 动漫不在 ANIME_SONG_CONFIG 中：直接标记 failed，不尝试任何爬取。
    """

    def __init__(self):
        self.qq_spider = QQMusicSpider()

    def crawl_anime_lyrics(self, anime: Dict) -> List[Dict]:
        """
        爬取单个动画的所有歌词（仅 QQ 音乐）。

        返回成功入库的歌词列表。
        状态约定：
          - completed     : QQ 音乐至少爬到 1 首歌词
          - failed        : 动画不在 ANIME_SONG_CONFIG 配置表中（无法爬取，永久失败）
          - retry_later   : 动画有配置，但本次 QQ 音乐网络失败或搜不到结果
                            → 下次周任务 init_weekly_anime() 会重置回 pending 重试
        """
        anime_name = anime['name']
        anime_id   = anime['id']

        logger.info(f"开始爬取动画: {anime_name}")

        # 检查是否在配置表中
        song_configs = self.qq_spider.get_songs_for_anime(anime)
        if not song_configs:
            logger.warning(f"{anime_name} 不在 ANIME_SONG_CONFIG 配置表中，跳过（不走其他来源）")
            db.update_anime_status(anime_id, 'failed')
            return []

        # 仅从 QQ 音乐爬取
        qq_results = self.qq_spider.crawl(anime)
        if qq_results:
            logger.info(f"{anime_name}: QQ 音乐成功获取 {len(qq_results)} 首歌词")
            db.update_anime_status(anime_id, 'completed')
        else:
            logger.warning(
                f"{anime_name}: QQ 音乐未获取到任何歌词，标记 retry_later"
                f"（下次周任务自动重置为 pending 重试）"
            )
            db.update_anime_status(anime_id, 'retry_later')

        return qq_results


def _get_new_anime_from_pool() -> List[Dict]:
    """
    从 ANIME_LIST + ANIME_RESERVE_LIST 中找出尚未入库的动画。
    优先从主池取，主池耗尽后从后备池取。
    返回最多 ANIME_BATCH_SIZE 条待新增的动画信息。
    """
    batch_size = getattr(config, 'ANIME_BATCH_SIZE', 3)
    candidates = []

    # 先扫主池，再扫后备池
    reserve_list = getattr(config, 'ANIME_RESERVE_LIST', [])
    for pool_name, pool in [("主池", config.ANIME_LIST), ("后备池", reserve_list)]:
        for anime_info in pool:
            if not db.get_anime_by_name(anime_info['name']):
                candidates.append((pool_name, anime_info))

    if not candidates:
        return []

    import random
    selected = random.sample(candidates, min(batch_size, len(candidates)))
    result = []
    for pool_name, anime_info in selected:
        logger.info(f"[补充] 从{pool_name}发现新动画: {anime_info['name']}")
        result.append(anime_info)
    return result


def init_weekly_anime() -> int:
    """
    初始化每周待爬取的动画。

    逻辑：
    0. 先将所有 'retry_later' 状态（上次网络失败、本次重试）的动画重置为 'pending'。
    1. 从 ANIME_LIST（主池）随机取最多 ANIME_BATCH_SIZE 部，跳过已存在的。
    2. 若主池已全部入库，自动从 ANIME_RESERVE_LIST（后备池）补充。
    3. 两个池都耗尽时，调用 AniList API 自动发现，记录警告并返回 0。

    返回值：本次新加入 pending 队列的动画数量。
    """
    import random
    batch_size = getattr(config, 'ANIME_BATCH_SIZE', 3)
    added = 0

    # ── 0. 将上次 retry_later 的动画重置为 pending，纳入本次候选 ─────
    _reset_retry_later_to_pending()

    # ── 1. 先尝试主池 ──────────────────────────────────────────────
    main_pool = config.ANIME_LIST
    not_in_db = [a for a in main_pool if not db.get_anime_by_name(a['name'])]

    if not_in_db:
        selected = random.sample(not_in_db, min(batch_size, len(not_in_db)))
        for anime_info in selected:
            db.add_anime(
                name=anime_info['name'],
                name_jp=anime_info.get('name_jp'),
                year=anime_info.get('year'),
                status='pending'
            )
            logger.info(f"[主池] 新增待爬取动画: {anime_info['name']}")
            added += 1
        return added

    # ── 2. 主池已耗尽 → 切换到后备池 ──────────────────────────────
    logger.info("主动画池已全部入库，尝试从后备池补充...")
    reserve_pool = getattr(config, 'ANIME_RESERVE_LIST', [])
    not_in_db_reserve = [a for a in reserve_pool if not db.get_anime_by_name(a['name'])]

    if not_in_db_reserve:
        selected = random.sample(not_in_db_reserve, min(batch_size, len(not_in_db_reserve)))
        for anime_info in selected:
            db.add_anime(
                name=anime_info['name'],
                name_jp=anime_info.get('name_jp'),
                year=anime_info.get('year'),
                status='pending'
            )
            logger.info(f"[后备池] 新增待爬取动画: {anime_info['name']}")
            added += 1
        return added

    # ── 3. 主池 + 后备池均耗尽 → 调用 AniList 自动发现 ────────────
    logger.info("主池和后备池均已耗尽，尝试通过 AniList API 自动发现新动画...")
    try:
        from anime_discovery import auto_discover_anime
        discovered = auto_discover_anime(batch_size=batch_size)
        if discovered > 0:
            logger.info(f"[自动发现] 成功补充 {discovered} 部新动画到 pending 队列")
            return discovered
        else:
            logger.warning(
                "[自动发现] AniList 未找到新的可爬取动画（可能网络不可用，或 ANIME_SONG_CONFIG 覆盖不足）\n"
                "  → 请查看 data/undiscovered_anime.json，为热门动画手动添加 ANIME_SONG_CONFIG 配置"
            )
            return 0
    except Exception as e:
        logger.error(f"[自动发现] 调用失败，静默降级: {e}")
        return 0


def _reset_retry_later_to_pending():
    """
    将数据库中所有 'retry_later' 状态的动画重置为 'pending'，
    使它们在下次周任务中重新被纳入爬取候选。
    通常在每次 init_weekly_anime() 开始时调用。
    """
    import sqlite3 as _sqlite3
    with _sqlite3.connect(config.DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE anime SET status='pending', updated_at=CURRENT_TIMESTAMP "
            "WHERE status='retry_later'"
        )
        n = cur.rowcount
        conn.commit()
    if n > 0:
        logger.info(f"[重置] 将 {n} 部 retry_later 动画重置为 pending，纳入本次候选")


def crawl_weekly_lyrics():
    """
    每周爬取任务入口。

    流程：
    1. 调用 init_weekly_anime() 补充待爬取队列，优先级：
       主池（ANIME_LIST）→ 后备池（ANIME_RESERVE_LIST）→ AniList 自动发现
    2. 从 pending 队列随机取一部执行爬取。
       - 若 QQ 音乐全部失败，自动换下一部 pending 动画继续尝试（最多 MAX_RETRY_ANIME 部）。
       - 每次失败的动画标记为 'failed'，不会再反复消耗队列机会。
    3. 若 pending 队列仍为空（三层均无新动画），记录警告并退出。

    设计原则：保证每次周任务**至少入库一部动画的歌词**（只要队列有可用动画）。
    """
    MAX_RETRY_ANIME = 5  # 本次任务最多连续尝试的动画数
    logger.info("=== 开始每周歌词爬取任务 ===")
    log_id = db.add_task_log('weekly_crawl', 'running', '开始爬取歌词')

    try:
        # ── Step 1: 补充待爬取队列 ────────────────────────────────
        newly_added = init_weekly_anime()
        logger.info(f"本次向队列补充了 {newly_added} 部新动画")

        # ── Step 2: 循环尝试，直到成功或队列耗尽 ─────────────────
        crawler       = LyricsCrawler()
        tried_ids     = set()       # 本次任务已尝试过的动画 ID（避免重复选中）
        success_anime = None        # 成功爬取的动画
        total_lyrics  = 0
        attempt       = 0

        while attempt < MAX_RETRY_ANIME:
            anime = db.get_random_pending_anime(exclude_ids=list(tried_ids))

            if not anime:
                logger.warning(
                    "待爬取队列中没有更多可用动画"
                    + ("，已全部尝试过" if tried_ids else "（队列为空）")
                )
                break

            attempt    += 1
            anime_id    = anime["id"]
            anime_name  = anime.get("name", "")
            tried_ids.add(anime_id)

            logger.info(f"[尝试 {attempt}/{MAX_RETRY_ANIME}] 爬取动画: 《{anime_name}》")
            lyrics = crawler.crawl_anime_lyrics(anime)

            if lyrics:
                # 成功：记录结果并退出循环
                success_anime = anime
                total_lyrics  = len(lyrics)
                logger.info(f"[成功] 《{anime_name}》获取 {total_lyrics} 首歌词，任务结束")
                break
            else:
                logger.warning(
                    f"[失败] 《{anime_name}》QQ 音乐爬取失败，已标记 failed，"
                    f"尝试下一部（剩余机会 {MAX_RETRY_ANIME - attempt}）"
                )

        # ── Step 3: 汇总日志 ──────────────────────────────────────
        if success_anime:
            summary = (
                f"动画《{success_anime['name']}》：获取 {total_lyrics} 首歌词"
                + (f"；本次新增 {newly_added} 部动画到队列" if newly_added else "")
                + (f"；本次共尝试 {attempt} 部动画" if attempt > 1 else "")
            )
        elif attempt == 0:
            summary = (
                "待爬取队列为空（主池、后备池、AniList 自动发现均无新动画）\n"
                "  → 请查看 data/undiscovered_anime.json，"
                "为热门动画手动添加 ANIME_SONG_CONFIG 配置后重试"
            )
            logger.warning(summary)
        else:
            summary = (
                f"本次任务尝试了 {attempt} 部动画，均未能从 QQ 音乐获取歌词。\n"
                f"  已尝试动画 ID: {tried_ids}\n"
                f"  可能原因：QQ 音乐当前网络不可用，或这些动画的 search_hints 配置不足。\n"
                f"  建议：检查网络连接，或为对应动画补充 search_hints 配置。"
            )
            logger.warning(summary)

        logger.info(f"=== 每周歌词爬取任务完成：{summary} ===")
        db.update_task_log(log_id, 'success', summary)

    except Exception as e:
        logger.error(f"每周歌词爬取任务失败: {e}")
        db.update_task_log(log_id, 'failed', str(e))




if __name__ == "__main__":
    # 测试爬虫
    print("测试歌词爬虫...")
    
    # 先添加一个测试动画
    anime_id = db.add_anime("鬼灭之刃", "鬼滅の刃", 2019, status='pending')
    anime = {'id': anime_id, 'name': '鬼灭之刃', 'name_jp': '鬼滅の刃'}
    
    # 爬取歌词
    crawler = LyricsCrawler()
    lyrics = crawler.crawl_anime_lyrics(anime)
    
    print(f"获取到 {len(lyrics)} 首歌曲")
    for l in lyrics:
        print(f"  - {l['song_name']} ({l['song_type']})")
