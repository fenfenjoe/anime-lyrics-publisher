# -*- coding: utf-8 -*-
"""
anime_discovery.py — 自动发现新动漫并补充到动画池

策略：
1. 调用 AniList GraphQL API（免费、无需 API Key）获取近年热门日本动画 Top 50
2. 将返回结果与本地 ANIME_SONG_CONFIG 做模糊匹配
3. 匹配成功 → 自动加入数据库 pending 队列（等待下周爬取）
4. 匹配失败 → 记录到 data/undiscovered_anime.json（供日后手动配置歌曲）
5. 网络不可用时，静默降级，不影响主流程

AniList API 端点：https://graphql.anilist.co
文档：https://anilist.gitbook.io/anilist-apiv2-docs/
"""

import json
import logging
import os
from typing import List, Dict, Optional, Tuple

import requests

import config
from database import db

logger = logging.getLogger(__name__)

# AniList GraphQL 端点
ANILIST_API = "https://graphql.anilist.co"

# 未匹配动画的记录文件（供日后参考，手动补充歌曲配置）
UNDISCOVERED_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "data", "undiscovered_anime.json"
)

# AniList 请求超时（秒）
REQUEST_TIMEOUT = 15

# ─── AniList GraphQL 查询 ─────────────────────────────────────────────────────

_QUERY_POPULAR = """
query ($page: Int, $perPage: Int, $season: MediaSeason, $year: Int) {
  Page(page: $page, perPage: $perPage) {
    media(
      type: ANIME
      format_in: [TV, MOVIE, OVA, ONA]
      countryOfOrigin: JP
      season: $season
      seasonYear: $year
      sort: [POPULARITY_DESC]
    ) {
      id
      title {
        romaji
        english
        native
      }
      startDate { year }
      popularity
      averageScore
    }
  }
}
"""

_QUERY_ALL_TIME_POPULAR = """
query ($page: Int, $perPage: Int) {
  Page(page: $page, perPage: $perPage) {
    media(
      type: ANIME
      format_in: [TV, MOVIE, OVA, ONA]
      countryOfOrigin: JP
      sort: [POPULARITY_DESC]
    ) {
      id
      title {
        romaji
        english
        native
      }
      startDate { year }
      popularity
      averageScore
    }
  }
}
"""


def _anilist_request(query: str, variables: dict) -> Optional[dict]:
    """向 AniList API 发送 GraphQL 请求，失败时返回 None（静默降级）"""
    try:
        session = requests.Session()
        session.trust_env = False  # 绕过无效系统代理
        resp = session.post(
            ANILIST_API,
            json={"query": query, "variables": variables},
            timeout=REQUEST_TIMEOUT,
        )
        if resp.status_code == 200:
            return resp.json()
        logger.warning(f"AniList API 返回 HTTP {resp.status_code}")
        return None
    except Exception as e:
        logger.warning(f"AniList API 请求失败（网络问题，静默降级）: {e}")
        return None


def fetch_popular_anime(pages: int = 2, per_page: int = 25) -> List[Dict]:
    """
    从 AniList 获取历史热门日本动画列表。

    Args:
        pages: 查询页数，每页 per_page 条
        per_page: 每页条数（AniList 最大 50）

    Returns:
        动画信息列表，每项包含 name/name_jp/name_en/year/popularity/score
    """
    results = []
    for page in range(1, pages + 1):
        data = _anilist_request(_QUERY_ALL_TIME_POPULAR, {"page": page, "perPage": per_page})
        if not data:
            break
        media_list = data.get("data", {}).get("Page", {}).get("media", [])
        if not media_list:
            break
        for m in media_list:
            titles = m.get("title", {})
            start  = m.get("startDate", {}) or {}
            results.append({
                "name_romaji": titles.get("romaji") or "",
                "name_en":     titles.get("english") or "",
                "name_jp":     titles.get("native") or "",
                "year":        start.get("year"),
                "popularity":  m.get("popularity", 0),
                "score":       m.get("averageScore", 0),
                "anilist_id":  m.get("id"),
            })
    logger.info(f"AniList 返回 {len(results)} 部热门动画")
    return results


# ─── 模糊匹配：AniList 结果 ↔ ANIME_SONG_CONFIG ───────────────────────────────

def _normalize(text: str) -> str:
    """统一小写、去标点，用于模糊比对"""
    import re
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"[^\w\u3040-\u9fff]", "", text)
    return text


def _titles_of_config_key(key: str) -> List[str]:
    """
    把 ANIME_SONG_CONFIG 的 key（中文/英文/日文混合名）拆成可能的别名列表
    """
    aliases = [key]
    # 有些 key 包含"/"或空格，尝试拆分
    import re
    aliases += re.split(r"[/\s··：:]+", key)
    return [a.strip() for a in aliases if a.strip()]


def _build_config_alias_map(song_config_keys: List[str]) -> Dict[str, str]:
    """
    构建 normalize(别名) → config_key 的查找字典。

    别名来源（多层覆盖）：
    1. ANIME_SONG_CONFIG 的 key 本身（中文/英文/日文）
    2. config.ANIME_LIST + ANIME_RESERVE_LIST 中每条记录的 name_jp / name（中文）
       用于建立"日文名 → 中文 config key"的桥接
    """
    alias_map: Dict[str, str] = {}

    # ── 1. 直接用 config key 自身 ──────────────────────────────────────
    for key in song_config_keys:
        for alias in _titles_of_config_key(key):
            n = _normalize(alias)
            if n:
                alias_map[n] = key

    # ── 2. 通过 config.py 中的动画列表建立中文名 ↔ 日文名桥接 ──────────
    all_pools = list(getattr(config, "ANIME_LIST", [])) + list(getattr(config, "ANIME_RESERVE_LIST", []))
    for entry in all_pools:
        cn_name = entry.get("name", "")
        jp_name = entry.get("name_jp", "")
        # 找到这个中文名对应的 config key（可能相同，也可能大小写/标点不同）
        matched_key = None
        for key in song_config_keys:
            if _normalize(key) == _normalize(cn_name):
                matched_key = key
                break
            # 子串宽松匹配
            if _normalize(cn_name) in _normalize(key) or _normalize(key) in _normalize(cn_name):
                matched_key = key
                break
        if matched_key and jp_name:
            n = _normalize(jp_name)
            if n:
                alias_map[n] = matched_key

    return alias_map


def match_anilist_to_config(
    anilist_anime: Dict,
    song_config_keys: List[str],
) -> Optional[str]:
    """
    判断 AniList 返回的一部动画是否与某个 ANIME_SONG_CONFIG key 匹配。

    匹配规则：
    1. 用 ANIME_LIST/RESERVE_LIST 建立 "日文名 → 中文 config key" 桥接字典
    2. AniList 返回的日文名/罗马音/英文名 normalize 后，在字典中查找
    3. 子串宽松匹配（应对副标题等情况）

    Returns:
        匹配的 config key，或 None
    """
    alias_map = _build_config_alias_map(song_config_keys)

    a_jp  = _normalize(anilist_anime.get("name_jp", ""))
    a_rom = _normalize(anilist_anime.get("name_romaji", ""))
    a_en  = _normalize(anilist_anime.get("name_en", ""))

    for candidate in [a_jp, a_rom, a_en]:
        if not candidate:
            continue
        # 精确匹配
        if candidate in alias_map:
            return alias_map[candidate]
        # 子串宽松匹配（AniList 日文名可能带副标题）
        for alias_key, config_key in alias_map.items():
            if alias_key in candidate or candidate in alias_key:
                return config_key
    return None


# ─── 核心入口 ─────────────────────────────────────────────────────────────────

def auto_discover_anime(batch_size: int = 3) -> int:
    """
    自动从 AniList 发现新动画并加入待爬取队列。

    流程：
    1. 调用 AniList API 获取热门动画列表（最多 50 条）
    2. 过滤掉已在数据库中的动画
    3. 在剩余候选中找出在 ANIME_SONG_CONFIG 里有配置的动画
    4. 按热度排序，取前 batch_size 部加入数据库 pending 队列
    5. 没有配置的动画记录到 undiscovered_anime.json

    Args:
        batch_size: 最多加入队列的动画数量

    Returns:
        实际新加入 pending 队列的动画数量（0 表示未发现任何新动画）
    """
    logger.info("[自动发现] 开始从 AniList 获取热门动画列表...")

    # 从 ANIME_SONG_CONFIG 导入，避免循环 import
    from anime_lyrics_spider import ANIME_SONG_CONFIG
    config_keys = list(ANIME_SONG_CONFIG.keys())

    # 1. 获取 AniList 热门列表（2 页 × 25 = 50 部）
    anilist_list = fetch_popular_anime(pages=2, per_page=25)
    if not anilist_list:
        logger.warning("[自动发现] AniList 返回数据为空，跳过")
        return 0

    added = 0
    unmatched = []

    for anime in anilist_list:
        if added >= batch_size:
            break

        jp_name = anime.get("name_jp") or anime.get("name_romaji") or ""

        # 2. 跳过已在数据库中的动画（按日文名/罗马音查）
        already_in_db = False
        for candidate_name in [jp_name, anime.get("name_romaji", ""), anime.get("name_en", "")]:
            if candidate_name and db.get_anime_by_name(candidate_name):
                already_in_db = True
                break
        if already_in_db:
            continue

        # 3. 尝试与 ANIME_SONG_CONFIG 匹配
        matched_key = match_anilist_to_config(anime, config_keys)
        if matched_key:
            # 4. 加入 pending 队列
            db.add_anime(
                name=matched_key,           # 使用配置表中的 key 作为 name（与爬虫逻辑一致）
                name_jp=anime.get("name_jp"),
                year=anime.get("year"),
                status="pending",
            )
            logger.info(
                f"[自动发现] 新增动画：{matched_key}（AniList 热度={anime['popularity']}，"
                f"评分={anime['score']}）"
            )
            added += 1
        else:
            # 5. 无配置：记录到 undiscovered 文件，供日后参考
            unmatched.append({
                "name_jp":      anime.get("name_jp"),
                "name_romaji":  anime.get("name_romaji"),
                "name_en":      anime.get("name_en"),
                "year":         anime.get("year"),
                "popularity":   anime.get("popularity"),
                "score":        anime.get("score"),
                "hint":         "需在 ANIME_SONG_CONFIG 中添加歌曲配置才能爬取",
            })

    # 写入未匹配文件（追加模式，避免覆盖历史记录）
    _save_undiscovered(unmatched)

    logger.info(f"[自动发现] 完成：新增 {added} 部动画，{len(unmatched)} 部无歌曲配置（已记录）")
    return added


def _save_undiscovered(new_entries: List[Dict]) -> None:
    """把没有 ANIME_SONG_CONFIG 配置的新动画追加写入 undiscovered_anime.json"""
    if not new_entries:
        return
    os.makedirs(os.path.dirname(UNDISCOVERED_FILE), exist_ok=True)

    existing = []
    if os.path.exists(UNDISCOVERED_FILE):
        try:
            with open(UNDISCOVERED_FILE, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            existing = []

    # 去重（按 name_jp + year）
    existing_keys = {(e.get("name_jp"), e.get("year")) for e in existing}
    to_add = [e for e in new_entries if (e.get("name_jp"), e.get("year")) not in existing_keys]

    if to_add:
        existing.extend(to_add)
        with open(UNDISCOVERED_FILE, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
        logger.info(f"[自动发现] {len(to_add)} 部无配置动画已记录到 {UNDISCOVERED_FILE}")


# ─── 命令行快速测试 ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    count = auto_discover_anime(batch_size=5)
    print(f"\n自动发现完成，新增 {count} 部动画到队列")

    # 打印 undiscovered 文件前 10 条（参考用）
    if os.path.exists(UNDISCOVERED_FILE):
        with open(UNDISCOVERED_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"\n无配置动画列表（共 {len(data)} 条，前 10 条）：")
        for item in data[:10]:
            print(f"  {item.get('name_jp') or item.get('name_romaji')}（{item.get('year')}）"
                  f"  热度={item.get('popularity')}  评分={item.get('score')}")
