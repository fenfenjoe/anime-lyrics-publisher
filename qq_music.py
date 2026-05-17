# -*- coding: utf-8 -*-
"""
QQ 音乐模块
- 搜索歌曲（smartbox 接口，无需鉴权）
- 获取 LRC 歌词并解析为纯文本行列表
- 生成外链播放器卡片 HTML，可嵌入微信公众号文章
"""

import re
import json
import base64
import logging
import time
from typing import Optional, Dict, List

import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

# ── 接口地址 ──────────────────────────────────────────────
# smartbox 搜索（不需要鉴权，返回 song/album/singer/mv）
SEARCH_URL    = "https://c.y.qq.com/splcloud/fcgi-bin/smartbox_new.fcg"
# 歌词接口（base64 LRC，retcode=0 即可用）
LYRIC_URL     = "https://c.y.qq.com/lyric/fcgi-bin/fcg_query_lyric_new.fcg"
# QQ 音乐歌曲页面（songmid 版，微信内可跳转）
SONG_PAGE_URL_TEMPLATE = "https://y.qq.com/n/yqq/song/{songmid}.html"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Referer": "https://y.qq.com/",
    "Accept": "application/json, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,ja;q=0.8",
}

# 创建全局 Session，禁用系统代理（避免无效代理导致连接失败）
_session = requests.Session()
_session.trust_env = False


def _make_request(method: str, url: str, **kwargs) -> Optional[requests.Response]:
    """统一请求入口，自动加 verify=False 和超时"""
    kwargs.setdefault("timeout", 10)
    kwargs.setdefault("verify", False)
    kwargs.setdefault("headers", HEADERS)
    try:
        return _session.request(method, url, **kwargs)
    except Exception as e:
        logger.error(f"HTTP 请求失败 {url}: {e}")
        return None


def search_song(song_name: str, singer: str = None) -> Optional[Dict]:
    """
    搜索 QQ 音乐，返回最佳匹配的歌曲信息。
    使用 smartbox_new.fcg 接口（无需鉴权，稳定可用）。
    匹配策略（优先级由高到低）：
      1. 歌名 + 歌手 均精确匹配
      2. 歌名精确匹配（取第一条）
      3. 歌名部分匹配（取第一条）
    返回格式: {"songid": str, "songmid": str, "song_name": str, "singer": str}
    """
    query = f"{singer} {song_name}" if singer else song_name
    logger.info(f"搜索 QQ 音乐: {query}")

    resp = _make_request("GET", SEARCH_URL, params={
        "is_xml": 0,
        "format": "json",
        "key": query,
    })
    if not resp or resp.status_code != 200:
        logger.warning(f"QQ 音乐搜索请求失败: {query}")
        return None

    try:
        data = resp.json()
        songs = (data.get("data") or {}).get("song", {}).get("itemlist", [])

        if not songs:
            logger.warning(f"QQ 音乐搜索无结果: {query}")
            return None

        # ── 优先级匹配 ──────────────────────────────────────────
        # 规范化：去空格/全角转半角，统一小写
        def norm(s: str) -> str:
            return s.strip().lower()

        song_name_n = norm(song_name)
        singer_n    = norm(singer) if singer else ""

        exact_with_singer = None   # 歌名+歌手均完全匹配
        exact_name        = None   # 歌名完全匹配（取第一条）
        partial_name      = None   # 歌名部分匹配（取第一条）

        for s in songs:
            name_n   = norm(s.get("name", ""))
            artist_n = norm(s.get("singer", ""))

            name_exact   = (name_n == song_name_n) or (song_name_n in name_n) or (name_n in song_name_n)
            singer_match = singer_n and singer_n in artist_n

            if name_exact and singer_match:
                exact_with_singer = s
                break
            if name_exact and exact_name is None:
                exact_name = s
            if (song_name_n in name_n or name_n in song_name_n) and partial_name is None:
                partial_name = s

        best = exact_with_singer or exact_name or partial_name or songs[0]

        result = {
            "songid":    best.get("id", ""),
            "songmid":   best.get("mid", ""),
            "song_name": best.get("name", ""),
            "singer":    best.get("singer", ""),
        }
        logger.info(f"QQ 音乐匹配: {result['singer']} - {result['song_name']}  (songmid={result['songmid']})")
        return result

    except Exception as e:
        logger.error(f"QQ 音乐搜索解析失败: {e}")
        return None


def _decode_lrc(b64_str: str) -> str:
    """将 QQ 音乐返回的 base64 编码 LRC 字符串解码为原始文本"""
    if not b64_str:
        return ""
    try:
        return base64.b64decode(b64_str).decode("utf-8")
    except Exception as e:
        logger.error(f"LRC base64 解码失败: {e}")
        return ""


def _parse_lrc_to_lines(lrc_text: str) -> List[str]:
    """
    将 LRC 格式歌词解析为纯文本行列表。
    - 去除时间标签 [mm:ss.xx]
    - 去除元数据标签 [ti:...] [ar:...] [al:...] [by:...] [offset:...] [kana:...]
    - 去除「歌名 - 歌手」首行（通常是歌曲信息重复行）
    - 去除「词：/ 曲：/ 编曲：」等版权信息行
    - 保留非空日文/英文歌词行
    """
    if not lrc_text:
        return []

    meta_pattern   = re.compile(r'^\[[a-z]+:.*\]$', re.IGNORECASE)
    time_pattern   = re.compile(r'\[\d+:\d+\.\d+\]|\[\d+:\d+\]')
    credit_pattern = re.compile(r'^(词|曲|编曲|作词|作曲|制作人|混音|录音|出版)[:：]')

    lines = []
    for raw in lrc_text.splitlines():
        raw = raw.strip()
        if not raw:
            continue
        # 跳过纯元数据行
        if meta_pattern.match(raw):
            continue
        # 去掉时间标签
        text = time_pattern.sub("", raw).strip()
        if not text:
            continue
        # 跳过版权/词曲信息行
        if credit_pattern.match(text):
            continue
        lines.append(text)

    # 去掉第一行（通常是「歌名 - 歌手」）
    if lines and " - " in lines[0]:
        lines = lines[1:]

    return lines


def get_lyrics_by_songmid(songmid: str) -> Optional[Dict]:
    """
    根据 songmid 获取歌词，返回：
    {
        "lrc_text":  原始 LRC 文本,
        "lines":     纯文本歌词行列表（已过滤元数据）,
        "trans_lrc": 翻译 LRC 文本（可能为空）,
    }
    失败返回 None。
    """
    resp = _make_request("GET", LYRIC_URL, params={
        "songmid":     songmid,
        "g_tk":        5381,
        "loginUin":    0,
        "hostUin":     0,
        "format":      "json",
        "inCharset":   "utf8",
        "outCharset":  "utf-8",
        "platform":    "yqq",
        "needNewCode": 0,
    })
    if not resp or resp.status_code != 200:
        logger.warning(f"歌词接口请求失败: songmid={songmid}")
        return None

    try:
        data = resp.json()
        if data.get("retcode", -1) != 0:
            logger.warning(f"歌词接口返回错误: retcode={data.get('retcode')}, songmid={songmid}")
            return None

        lrc_text   = _decode_lrc(data.get("lyric", ""))
        trans_text = _decode_lrc(data.get("trans", ""))
        lines      = _parse_lrc_to_lines(lrc_text)

        logger.info(f"获取歌词成功: songmid={songmid}, 共 {len(lines)} 行")
        return {
            "lrc_text":  lrc_text,
            "lines":     lines,
            "trans_lrc": trans_text,
        }
    except Exception as e:
        logger.error(f"歌词解析失败: {e}")
        return None


def get_lyrics_by_song(song_name: str, singer: str = None,
                        anime_name: str = None) -> Optional[Dict]:
    """
    对外接口：搜索歌曲并获取歌词。
    依次尝试: 歌手+歌名 → 动漫名+歌名 → 纯歌名。
    返回格式（成功时）：
    {
        "songmid":   str,
        "song_name": str,
        "singer":    str,
        "lrc_text":  str,   # 原始 LRC
        "lines":     List[str],  # 纯文本歌词行
        "trans_lrc": str,   # 翻译 LRC（可能为空）
    }
    失败返回 None。
    """
    search_result = None

    if singer:
        search_result = search_song(song_name, singer)
    if not search_result and anime_name:
        search_result = search_song(song_name, anime_name)
    if not search_result:
        search_result = search_song(song_name)

    if not search_result or not search_result.get("songmid"):
        logger.warning(f"QQ 音乐未找到歌曲: {song_name}")
        return None

    songmid = search_result["songmid"]
    lyric_data = get_lyrics_by_songmid(songmid)
    if not lyric_data:
        return None

    return {
        "songmid":   songmid,
        "song_name": search_result.get("song_name", song_name),
        "singer":    search_result.get("singer", singer or ""),
        "lrc_text":  lyric_data["lrc_text"],
        "lines":     lyric_data["lines"],
        "trans_lrc": lyric_data["trans_lrc"],
    }


def build_player_html(songmid: str, song_name: str = "", singer: str = "") -> str:
    """
    生成 QQ 音乐跳转卡片 HTML（仿微信原生音乐卡片样式）。
    微信公众号图文消息中 iframe/audio 标签会被过滤，
    此处用带样式的链接卡片替代，读者点击后在微信内打开 QQ 音乐收听。
    """
    song_url = SONG_PAGE_URL_TEMPLATE.format(songmid=songmid)
    display_song = song_name if song_name else "未知歌曲"
    display_singer = singer if singer else "未知歌手"

    # 仿微信原生音乐卡片：白底、左侧音符图标、右侧歌名歌手、底部提示
    card_html = (
        f'<p style="'
        f'display:block;margin:20px 0;padding:0;'
        f'border:1px solid #e8e8e8;border-radius:8px;'
        f'background:#fff;overflow:hidden;'
        f'">'
        f'<a href="{song_url}" style="'
        f'display:block;text-decoration:none;color:inherit;'
        f'padding:14px 16px;'
        f'">'
        f'<span style="'
        f'display:inline-block;width:42px;height:42px;line-height:42px;'
        f'border-radius:50%;background:linear-gradient(135deg,#31c27c,#1aad19);'
        f'text-align:center;font-size:20px;vertical-align:middle;'
        f'margin-right:12px;'
        f'">&#127925;</span>'
        f'<span style="display:inline-block;vertical-align:middle;">'
        f'<span style="display:block;font-size:15px;font-weight:bold;color:#1a1a1a;line-height:1.4;">{display_song}</span>'
        f'<span style="display:block;font-size:13px;color:#888;margin-top:2px;">{display_singer}</span>'
        f'</span>'
        f'<span style="float:right;font-size:12px;color:#aaa;line-height:42px;vertical-align:middle;">QQ音乐 &gt;</span>'
        f'</a>'
        f'</p>'
    )
    return card_html


def get_qq_music_player(song_name: str, singer: str = None, anime_name: str = None) -> Optional[str]:
    """
    对外接口：输入歌曲名/歌手，返回可嵌入文章的播放器 HTML 字符串；失败返回 None
    依次尝试: 歌手+歌名 → 动漫名+歌名 → 纯歌名
    """
    result = None

    if singer:
        result = search_song(song_name, singer)

    if not result and anime_name:
        result = search_song(song_name, anime_name)

    if not result:
        result = search_song(song_name)

    if not result or not result.get("songmid"):
        logger.warning(f"QQ 音乐未找到: {song_name}")
        return None

    return build_player_html(
        result["songmid"],
        result.get("song_name", song_name),
        result.get("singer", singer or ""),
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # 测试播放器卡片
    print("=== 播放器卡片 ===")
    html = get_qq_music_player("なんでもないや", "RADWIMPS", "你的名字")
    print(html or "未找到")

    # 测试歌词获取
    print("\n=== 歌词获取 ===")
    lyrics = get_lyrics_by_song("紅蓮華", "LiSA", "鬼灭之刃")
    if lyrics:
        print(f"歌曲: {lyrics['singer']} - {lyrics['song_name']}")
        print(f"共 {len(lyrics['lines'])} 行歌词")
        for i, line in enumerate(lyrics['lines'][:10], 1):
            print(f"  {i}. {line}")
        if len(lyrics['lines']) > 10:
            print(f"  ... 共 {len(lyrics['lines'])} 行")
    else:
        print("未找到歌词")
