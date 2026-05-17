# -*- coding: utf-8 -*-
"""
图片爬虫模块 - 从 MyAnimeList API 爬取动画官方图片

设计原则（2026-05-12 更新）：
  1. 仅使用 MyAnimeList Jikan API 作为图片来源，100% 精准
  2. Bing 图片搜索已完全禁用（结果不可控，无法保证动画相关性）
  3. MAL API 提供：封面图（images.jpg）+ 动画剧照（/pictures 端点）
  4. 视觉去重：下载后用感知哈希（aHash）检测重复图片，汉明距离 ≤ 8 视为重复
  5. 本地缓存系统（ImageCache）：动画图片去重后保存到本地同名文件夹，
     多次生成文章时自动复用未使用图片，不足时自动从 MAL 补仓，
     补仓仍不足则从已使用图片中回退复用

MAL API 优势：
  - 官方 Key Visual / 剧照，质量优秀
  - 语义搜索命中，无关键词歧义
  - 免费公开，无需认证
"""

import os
import re
import html
import json
import logging
import uuid
import time
import random
from typing import List, Dict, Optional, Tuple
from urllib.parse import quote
import requests
from PIL import Image

from anime_lyrics_publisher import config
from anime_lyrics_publisher import database


# ─────────────────────────────────────────────
#  感知哈希（Perceptual Hash）—— 仅依赖 PIL
#  用于检测视觉上相似/重复的图片
# ─────────────────────────────────────────────
def _hash_str(h: Optional[int]) -> str:
    """将 aHash 整数转为十六进制字符串（避免 SQLite INTEGER 溢出）"""
    if h is None:
        return ''
    return hex(h)


def _compute_ahash(image_path: str, size: int = 8) -> Optional[int]:
    """
    计算图片的平均哈希值（Average Hash）。
    
    算法：
      1. 将图片缩放到 size×size（默认8×8）
      2. 转为灰度
      3. 计算所有像素均值
      4. 每像素与均值比较，≥ 均值→1，< 均值→0
      5. 组成 64bit 整数哈希值
    
    返回：int 哈希值（失败返回 None）
    """
    try:
        img = Image.open(image_path).convert('L')
        img = img.resize((size, size), Image.LANCZOS)
        pixels = list(img.getdata())
        avg = sum(pixels) / len(pixels)
        bits = [1 if p >= avg else 0 for p in pixels]
        hash_val = 0
        for b in bits:
            hash_val = (hash_val << 1) | b
        return hash_val
    except Exception:
        return None


def _hamming_distance(h1: int, h2: int, bits: int = 64) -> int:
    """计算两个哈希值之间的汉明距离（不同位数）"""
    return bin(h1 ^ h2).count('1')


def _is_duplicate_image(new_path: str, existing_hashes: List[Tuple[str, int]],
                         threshold: int = 8) -> Optional[str]:
    """
    检查新图片是否与已有图片视觉相似。

    :param new_path:       新下载图片路径
    :param existing_hashes: 已有图片列表 [(path, hash_value), ...]
    :param threshold:      汉明距离阈值（默认8，即允许最多8个像素位不同）
    :return:               若重复，返回最相似的已有图片路径；否则返回 None
    """
    h_new = _compute_ahash(new_path)
    if h_new is None:
        return None
    min_dist = float('inf')
    similar_path = None
    for path, h_existing in existing_hashes:
        # 支持 int 或 hex 字符串格式的哈希值
        if isinstance(h_existing, str) and h_existing:
            h_existing = int(h_existing, 16)
        elif not isinstance(h_existing, int):
            continue
        dist = _hamming_distance(h_new, h_existing)
        if dist < min_dist:
            min_dist = dist
            similar_path = path
    if min_dist <= threshold:
        return similar_path
    return None


def _sanitize_folder_name(name: str) -> str:
    """将动画名转换为合法的文件夹名（替换或移除非法字符）"""
    import re
    import unicodedata
    # NFKC 归一化：将全角/兼容字符统一为标准形式，防止同一动画因 Unicode 差异产生多个文件夹
    # 例如：全角字母 → 半角, ～ → ー
    safe = unicodedata.normalize('NFKC', name)
    # 显式替换：× (U+00D7 MULTIPLICATION SIGN) → x，避免与 SPY×FAMILY 等动画名冲突
    safe = safe.replace('\u00d7', 'x')
    # 替换非法文件名字符为空格，再压缩多余空格，最后去首尾空格
    safe = re.sub(r'[\\/:*?"<>|]', ' ', safe).strip()
    # 压缩多个空格为一个
    safe = re.sub(r'\s+', ' ', safe)
    return safe


# ══════════════════════════════════════════════════════════════
#  ImageCache - 动画图片本地缓存管理器
#  功能：
#    1. 爬取动画图片 → 去重 → 保存到本地同名文件夹
#    2. 文章配图时从本地取用，并打上"已使用"标记
#    3. 图片不足时自动从 MAL API 补仓（保证不重复）
#    4. 补仓后仍不足则从已使用图片中回退复用
# ══════════════════════════════════════════════════════════════
class ImageCache:
    """
    动画图片本地缓存管理器。

    目录结构：
      data/anime_images/{anime_name}/          ← 动画图片文件夹
          ├── cache_manifest.json              ← 元数据清单
          ├── img_001.jpg                      ← 图片文件
          ├── img_002.jpg
          └── ...

    数据库 used_anime_images 表：
      anime_name | image_url | image_path | hash_value | used_at

    核心流程：
      get_images_for_article()
        ├─ ① 查本地未使用图片 → 直接返回
        ├─ ② 图片不足 → 从 MAL 补仓（视觉去重）→ 返回
        └─ ③ 补仓仍不足 → 从已使用图片中复用
    """

    CACHE_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               'data', 'anime_images')
    MANIFEST_NAME = 'cache_manifest.json'

    def __init__(self):
        os.makedirs(self.CACHE_ROOT, exist_ok=True)
        self._db = database.db
        self._spider_instance = None  # 延迟初始化 ImageSpider

    # ── 内部工具 ────────────────────────────────────────────

    def _get_spider(self) -> ImageSpider:
        """延迟创建 ImageSpider（避免循环导入问题）"""
        if self._spider_instance is None:
            self._spider_instance = ImageSpider()
        return self._spider_instance

    def _anime_folder(self, anime_name: str) -> str:
        """获取动画图片缓存文件夹路径"""
        folder_name = _sanitize_folder_name(anime_name)
        return os.path.join(self.CACHE_ROOT, folder_name)

    def _manifest_path(self, anime_name: str) -> str:
        """获取清单文件路径"""
        return os.path.join(self._anime_folder(anime_name), self.MANIFEST_NAME)

    def _load_manifest(self, anime_name: str) -> Dict:
        """加载清单文件（不存在则返回空结构）"""
        path = self._manifest_path(anime_name)
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {'version': 1, 'anime_name': anime_name, 'images': []}

    def _save_manifest(self, anime_name: str, manifest: Dict):
        """保存清单文件到磁盘"""
        folder = self._anime_folder(anime_name)
        os.makedirs(folder, exist_ok=True)
        path = self._manifest_path(anime_name)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)

    def _record_to_db(self, anime_name: str, image_url: str,
                      image_path: str, hash_value=None,
                      used: bool = False):
        """
        写入 used_anime_images 表。

        hash_value 支持 int（原始哈希）或 str（十六进制字符串），
        统一存为十六进制字符串避免 SQLite INTEGER 溢出。
        """
        try:
            # 支持 int 或 str，转换为十六进制字符串
            if isinstance(hash_value, str) and hash_value:
                hash_str = hash_value
            elif isinstance(hash_value, int):
                hash_str = _hash_str(hash_value)
            else:
                hash_str = ''
            with self._db.get_connection() as conn:
                conn.execute("""
                    INSERT OR IGNORE INTO used_anime_images
                        (anime_name, image_url, image_path, hash_value, used_at)
                    VALUES (?, ?, ?, ?, NULL)
                """, (anime_name, image_url, image_path, hash_str))
                if used:
                    conn.execute("""
                        UPDATE used_anime_images
                        SET used_at = CURRENT_TIMESTAMP
                        WHERE anime_name = ? AND image_url = ?
                    """, (anime_name, image_url))
        except Exception as e:
            logger.warning(f"记录图片到数据库失败: {e}")

    def _get_used_urls(self, anime_name: str) -> set:
        """获取某动画所有已使用图片的 URL 集合（used_at IS NOT NULL = 已使用过）"""
        try:
            with self._db.get_connection() as conn:
                rows = conn.execute("""
                    SELECT image_url FROM used_anime_images
                    WHERE anime_name = ?
                      AND used_at IS NOT NULL
                """, (anime_name,)).fetchall()
                return {r['image_url'] for r in rows}
        except Exception:
            return set()

    def _get_all_cached_urls(self, anime_name: str) -> set:
        """获取清单中所有图片 URL（无论是否已使用）"""
        manifest = self._load_manifest(anime_name)
        return {img['url'] for img in manifest.get('images', [])
                if img.get('url')}

    # ── 核心 API ────────────────────────────────────────────

    def crawl_and_cache(self, anime_name: str, name_jp: str = None,
                        batch_size: int = 15) -> int:
        """
        从 MAL API 爬取图片，去重后加入本地缓存。

        :param anime_name:  动画中文名
        :param name_jp:      动画日文名（用于精准搜索）
        :param batch_size:   目标新图片数量（默认15张）
        :return:             实际新增图片数量
        """
        folder = self._anime_folder(anime_name)
        os.makedirs(folder, exist_ok=True)
        manifest = self._load_manifest(anime_name)
        existing_urls = {img['url'] for img in manifest.get('images', [])
                         if img.get('url')}

        # 计算当前未使用图片数量
        used_urls = self._get_used_urls(anime_name)
        current_unused = sum(
            1 for img in manifest.get('images', [])
            if img.get('url') and img['url'] not in used_urls
        )
        logger.info(f"[ImageCache] {anime_name} 当前缓存: {len(manifest['images'])} 张，"
                    f"未使用: {current_unused} 张，"
                    f"本次需补仓: {batch_size} 张")

        if current_unused >= batch_size:
            logger.info(f"[ImageCache] {anime_name} 未使用图片充足，跳过爬取")
            return 0

        # 向 MAL 请求 3 倍数量（留足去重 buffer）
        mal_urls = self._get_spider()._get_mal_image_urls(
            anime_name, name_jp, count=batch_size * 3
        )
        # URL 级别去重（防止重复下载相同 URL）
        # 注意：爬取阶段不做视觉去重，因为 MAL API 可能返回同一张图的不同分辨率
        # 版本（large vs standard），它们 URL 不同但内容相似。
        # 视觉去重在 get_images_for_article 取图阶段执行。
        new_count = 0
        for url in mal_urls:
            if url in existing_urls:
                continue
            filename = f"img_{uuid.uuid4().hex[:8]}.jpg"
            filepath = os.path.join(folder, filename)
            path = self._get_spider().download_image(url, filename=filename, save_dir=folder)
            if not path:
                continue
            # 记录哈希（用于后续取图阶段的视觉去重）
            h = _compute_ahash(path)
            h_str = _hash_str(h)
            img_entry = {
                'filename': filename,
                'url': url,
                'path': path,
                'hash': h_str or '0',
            }
            manifest['images'].append(img_entry)
            existing_urls.add(url)
            # 注意：不调用 _record_to_db——数据库只记录"已使用"状态，
            # 由 get_images_for_article 在取图时统一标记
            new_count += 1
            time.sleep(0.3)
            if new_count + current_unused >= batch_size:
                break

        self._save_manifest(anime_name, manifest)
        logger.info(f"[ImageCache] {anime_name} 本次新增 {new_count} 张图片，"
                    f"缓存总计 {len(manifest['images'])} 张")
        return new_count

    def get_images_for_article(self, anime_name: str, name_jp: str = None,
                               count: int = 5) -> List[str]:
        """
        为文章获取配图：优先未使用图片，不足时自动补仓。

        :param anime_name: 动画中文名
        :param name_jp:    动画日文名
        :param count:      需要图片数量
        :return:           图片路径列表（按未使用 → 已使用回退顺序）
        """
        manifest = self._load_manifest(anime_name)
        all_images = manifest.get('images', [])
        used_urls = self._get_used_urls(anime_name)

        # ① 优先取未使用图片（取图时做视觉去重，保证同一篇文章图片彼此不重复）
        unused = [img for img in all_images
                  if img.get('url') and img['url'] not in used_urls]

        result = []
        selected_hashes: List[int] = []  # 已选图片的哈希（用于视觉去重）

        def _img_hash(img_entry) -> Optional[int]:
            h = (img_entry.get('hash') or '').strip()
            if not h:
                return None
            try:
                return int(h, 16)
            except ValueError:
                return None

        for img in unused:
            if len(result) >= count:
                break
            path = img.get('path')
            if not path or not os.path.exists(path):
                continue
            h_int = _img_hash(img)
            # 视觉去重：与已选图片比较汉明距离
            if h_int is not None and selected_hashes:
                skip = False
                for sel_h in selected_hashes:
                    if _hamming_distance(h_int, sel_h) <= 8:
                        logger.debug(f"[ImageCache] 视觉重复跳过: {os.path.basename(path)}")
                        skip = True
                        break
                if skip:
                    continue
            result.append(path)
            if h_int:
                selected_hashes.append(h_int)
            self._record_to_db(anime_name, img['url'], path, img.get('hash'), used=True)

        if len(result) >= count:
            logger.info(f"[ImageCache] {anime_name} 从缓存直接返回 {len(result)} 张（未使用）")
            return result

        # ② 未使用图片不足 → 触发补仓（目标数量 = 缺口 × 3）
        deficit = count - len(result)
        logger.info(f"[ImageCache] {anime_name} 未使用图片仅 {len(result)} 张，"
                    f"缺口 {deficit} 张，触发补仓...")
        self.crawl_and_cache(anime_name, name_jp, batch_size=deficit * 3)
        # 重新加载清单（补仓后）
        manifest = self._load_manifest(anime_name)
        all_images = manifest.get('images', [])
        used_urls = self._get_used_urls(anime_name)
        unused = [img for img in all_images
                  if img.get('url') and img['url'] not in used_urls]

        for img in unused:
            if len(result) >= count:
                break
            path = img.get('path')
            if not path or not os.path.exists(path):
                continue
            h_int = _img_hash(img)
            if h_int is not None and selected_hashes:
                skip = False
                for sel_h in selected_hashes:
                    if _hamming_distance(h_int, sel_h) <= 8:
                        skip = True
                        break
                if skip:
                    continue
            result.append(path)
            if h_int:
                selected_hashes.append(h_int)
            self._record_to_db(anime_name, img['url'], path, img.get('hash'), used=True)

        if len(result) >= count:
            logger.info(f"[ImageCache] {anime_name} 补仓后返回 {len(result)} 张")
            return result

        # ③ 补仓后仍不足 → 从已使用图片中回退复用
        deficit = count - len(result)
        logger.warning(f"[ImageCache] {anime_name} 补仓后仍缺 {deficit} 张，"
                       f"从已使用图片中回退复用...")
        used_imgs = [img for img in all_images
                     if img.get('url') and img['url'] in used_urls]
        # 打乱顺序避免每次都复用同样的图
        random.shuffle(used_imgs)
        for img in used_imgs:
            if len(result) >= count:
                break
            path = img.get('path')
            if path and os.path.exists(path):
                result.append(path)
                logger.info(f"[ImageCache] 回退复用已使用图片: {path}")

        logger.info(f"[ImageCache] {anime_name} 最终返回 {len(result)} 张配图")
        return result

    def get_cache_stats(self, anime_name: str) -> Dict:
        """获取某动画的图片缓存统计"""
        manifest = self._load_manifest(anime_name)
        all_images = manifest.get('images', [])
        used_urls = self._get_used_urls(anime_name)
        unused = [img for img in all_images
                  if img.get('url') and img['url'] not in used_urls]
        return {
            'anime_name': anime_name,
            'total': len(all_images),
            'unused': len(unused),
            'used': len(all_images) - len(unused),
        }

    def clear_cache(self, anime_name: str):
        """清空某动画的全部缓存（图片+清单+数据库记录）"""
        import shutil
        folder = self._anime_folder(anime_name)
        if os.path.exists(folder):
            shutil.rmtree(folder)
        try:
            with self._db.get_connection() as conn:
                conn.execute(
                    "DELETE FROM used_anime_images WHERE anime_name = ?",
                    (anime_name,)
                )
            logger.info(f"[ImageCache] 已清空 {anime_name} 的图片缓存")
        except Exception as e:
            logger.warning(f"清空数据库记录失败: {e}")

# 配置日志
logging.basicConfig(level=getattr(logging, config.LOG_LEVEL))
logger = logging.getLogger(__name__)

# 轮换 User-Agent，降低被反爬概率
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0',
]

# 低质量域名黑名单：素材网站、书籍封面、新闻/政府/PR 类网站
LOW_QUALITY_DOMAINS = {
    # 付费素材/图库网站
    'pngtree.com', 'shutterstock.com', 'dreamstime.com', 'gettyimages.com',
    'istockphoto.com', 'stock.adobe.com', 'alamy.com', 'depositphotos.com',
    'freepik.com', 'vecteezy.com', 'pixabay.com', '123rf.com',
    'tukuppt.com',  # 新增：国内素材站
    # 通用壁纸聚合站（非动漫专属，质量不稳定）
    'wallpaperbetter.com', 'wallpaperflare.com', 'wallpaperup.com',
    'hdwallpapers.net', 'peakpx.com', 'wallpaperaccess.com',
    # 电商/书籍
    'amazon.com', 'amazon.co.jp', 'rakuten.co.jp',
    'shin-sei.co.jp', 'shueisha.co.jp', 'kadokawa.co.jp',
    # 新闻/政府/学术
    'nhk.or.jp', 'asahi.com', 'yomiuri.co.jp', 'mainichi.jp',
    'wikipedia.org', 'wikimedia.org',
    # PR 稿/新闻稿 CDN（prtimes 等使用 fastly CDN 分发）
    'prtimes.jp',
    'prcdn.freetls.fastly.net',   # PR TIMES 新闻稿图片 CDN
    'bestcalendar.jp',
    # 出版社/教育机构
    'gakken.jp', 'gakken-ep.jp', 'gkp-koushiki.gakken.jp',
    # 博客/wordpress 站（iStock 购买图）
    'rinto.life',
    'world-note.com',
}


def _is_low_quality_url(url: str) -> bool:
    """判断 URL 是否来自低质量/无关域名"""
    url_lower = url.lower()
    for bad in LOW_QUALITY_DOMAINS:
        if bad in url_lower:
            return True
    return False


class ImageSpider:
    """图片爬虫"""

    def __init__(self, save_dir: str = None):
        self.save_dir = save_dir or config.IMAGE_SAVE_DIR
        os.makedirs(self.save_dir, exist_ok=True)
        # MAL API 请求间隔（避免触发速率限制）
        self._last_mal_request = 0
        self._mal_rate_limit = 1.0  # 每次请求间隔至少1秒

    def _rate_limited_request(self, url: str, headers: Dict = None, 
                               timeout: int = 10) -> Optional[requests.Response]:
        """带速率限制的 HTTP 请求"""
        elapsed = time.time() - self._last_mal_request
        if elapsed < self._mal_rate_limit:
            time.sleep(self._mal_rate_limit - elapsed)
        
        try:
            resp = requests.get(url, headers=headers, timeout=timeout, verify=False)
            self._last_mal_request = time.time()
            return resp
        except Exception as e:
            logger.error(f"HTTP 请求失败: {e}")
            return None

    def _search_mal_api(self, query: str, prefer_tv: bool = True) -> Optional[Dict]:
        """
        使用 MyAnimeList Jikan API 搜索动画。
        返回第一个匹配的动画数据，包含图片 URL。
        API 文档: https://jikan.moe/
        
        优化：优先搜索 TV 版，如果找不到再搜索所有类型
        """
        try:
            # 构建搜索 URL
            # 优先搜索 TV 版（type=tv），提高匹配准确度
            if prefer_tv:
                search_url = f"https://api.jikan.moe/v4/anime?q={quote(query)}&type=tv&limit=3&sfw"
            else:
                search_url = f"https://api.jikan.moe/v4/anime?q={quote(query)}&limit=3&sfw"
            
            logger.info(f"MAL API 搜索: {query} {'(优先TV版)' if prefer_tv else ''}")
            
            headers = {'User-Agent': random.choice(USER_AGENTS)}
            resp = self._rate_limited_request(search_url, headers=headers, timeout=15)
            
            if not resp or resp.status_code != 200:
                logger.warning(f"MAL API 请求失败: {resp.status_code if resp else 'No response'}")
                return None
            
            data = resp.json()
            results = data.get('data', [])
            
            if not results:
                # TV版未找到，尝试搜索所有类型
                if prefer_tv:
                    logger.info(f"MAL API TV版未找到，尝试搜索所有类型: {query}")
                    return self._search_mal_api(query, prefer_tv=False)
                logger.info(f"MAL API 未找到动画: {query}")
                return None
            
            # 优先选择标题最匹配的结果
            anime_data = results[0]
            # 检查标题是否相关（简单匹配）
            title = anime_data.get('title', '').lower()
            title_jp = anime_data.get('title_japanese', '').lower()
            query_lower = query.lower()
            
            # 如果第一个结果不太匹配，尝试后续结果
            for result in results:
                r_title = result.get('title', '').lower()
                r_title_jp = result.get('title_japanese', '').lower()
                r_type = result.get('type', '')
                
                # 标题包含查询关键词，且类型为 TV，优先选择
                if query_lower in r_title or query_lower in r_title_jp:
                    if r_type == 'TV' or not prefer_tv:
                        anime_data = result
                        break
            
            logger.info(f"MAL API 找到动画: {anime_data['title']} (ID: {anime_data['mal_id']}, Type: {anime_data.get('type', 'N/A')})")
            return anime_data
            
        except Exception as e:
            logger.error(f"MAL API 搜索失败: {e}")
            return None

    def _get_mal_image_urls(self, anime_name: str, name_jp: str = None, 
                              count: int = 3) -> List[str]:
        """
        从 MyAnimeList 获取动画官方图片 URL。
        优先使用英文名搜索（MAL 英文标题标准化程度高），
        日文名/中文名作为后备。
        返回图片 URL 列表（可能包含封面图、大图等）。
        """
        image_urls = []
        
        # 搜索策略：日文名优先 > 英文名/其他名
        # 原因：日文名在 MAL 上是最标准、最精准的标识，中文/英文名可能存在重名歧义
        search_queries = []
        if name_jp:
            search_queries.append(name_jp)
        search_queries.append(anime_name)  # 后备：原始英文/中文名
        
        mal_id = None
        for query in search_queries:
            if image_urls:
                break  # 已经找到图片，跳过
            
            # 优先搜索 TV 版，提高匹配准确度
            anime_data = self._search_mal_api(query, prefer_tv=True)
            if not anime_data:
                continue
            
            # 标题验证：确保返回的 anime 标题与查询相关
            # 宽松匹配：提取查询词中的关键词（英文/数字≥3字符，日文≥2字符），
            # 只要有任意一个关键词出现在返回标题中即认为匹配
            r_title = anime_data.get('title', '')
            r_title_jp = anime_data.get('title_japanese', '')
            
            import re
            # 英文/数字关键词
            en_keywords = re.findall(r'[a-zA-Z0-9]{3,}', query)
            # 日文关键词（汉字、假名）
            ja_keywords = re.findall(r'[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff]{2,}', query)
            all_keywords = en_keywords + ja_keywords
            
            matched = False
            for kw in all_keywords:
                kw_lower = kw.lower()
                if kw_lower in r_title.lower() or kw_lower in r_title_jp.lower():
                    matched = True
                    break
            
            if not matched:
                logger.warning(f"MAL 搜索 \"{query}\" 返回 \"{r_title}\"（标题不匹配），跳过...")
                continue

            # 提取图片 URL（jpg 格式）
            images = anime_data.get('images', {})
            jpg_data = images.get('jpg', {})
            webp_data = images.get('webp', {})
            
            # 按优先级收集图片 URL
            urls = []
            # 1. 大图（高质量）
            if jpg_data.get('large_image_url'):
                urls.append(jpg_data['large_image_url'])
            # 2. 标准图
            if jpg_data.get('image_url'):
                urls.append(jpg_data['image_url'])
            # 3. WebP 格式（备选）
            if webp_data.get('large_image_url'):
                urls.append(webp_data['large_image_url'])
            if webp_data.get('image_url'):
                urls.append(webp_data['image_url'])
            
            # 去重
            seen = set()
            for url in urls:
                if url and url not in seen:
                    seen.add(url)
                    image_urls.append(url)
            
            if image_urls:
                logger.info(f"从 MAL API 获取到 {len(image_urls)} 张图片 URL")
                # 只有当本次查询成功找到图片时，才更新 mal_id
                # 避免用错误 anime 的 ID 去 /pictures 端点拿图
                mal_id = anime_data.get('mal_id')
                break
        
        # 如果还需要更多图片，尝试获取该动画的更多官方图片
        if len(image_urls) < count and mal_id:
            extra_urls = self._get_mal_pictures(mal_id, count - len(image_urls))
            image_urls.extend(extra_urls)
        
        return image_urls[:count]
    
    def _get_mal_pictures(self, mal_id: int, count: int = 5) -> List[str]:
        """
        从 MAL API 获取动画的更多官方图片。
        使用 endpoint: /anime/{mal_id}/pictures
        """
        image_urls = []
        try:
            url = f"https://api.jikan.moe/v4/anime/{mal_id}/pictures"
            logger.info(f"MAL API 获取更多图片: {url}")
            
            headers = {'User-Agent': random.choice(USER_AGENTS)}
            resp = self._rate_limited_request(url, headers=headers, timeout=15)
            
            if not resp or resp.status_code != 200:
                logger.warning(f"MAL API pictures 请求失败: {resp.status_code if resp else 'No response'}")
                return []
            
            data = resp.json()
            pictures = data.get('data', [])
            
            for pic in pictures:
                if len(image_urls) >= count:
                    break
                # 优先使用大图
                jpg_data = pic.get('jpg', {})
                if jpg_data.get('large_image_url'):
                    image_urls.append(jpg_data['large_image_url'])
                elif jpg_data.get('image_url'):
                    image_urls.append(jpg_data['image_url'])
            
            logger.info(f"MAL API 获取到 {len(image_urls)} 张额外图片")
            return image_urls
            
        except Exception as e:
            logger.error(f"MAL API 获取图片失败: {e}")
            return []

    def _get_headers(self, referer='https://www.bing.com/'):
        return {
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            # 改为英文优先，减少 cn.bing.com 本地化搜索结果干扰
            'Accept-Language': 'en-US,en;q=0.9,ja;q=0.8,zh-CN;q=0.5',
            'Referer': referer,
        }

    def _extract_image_urls(self, html_text: str) -> List[str]:
        """
        从 Bing 搜索结果 HTML 中提取图片 URL。
        
        cn.bing.com 返回的是 HTML entity 编码，需要先 unescape 再匹配。
        www.bing.com 返回标准 JSON 格式。两种情况统一处理。
        """
        # 先对整个页面做 HTML entity 解码，统一处理两种格式
        decoded = html.unescape(html_text)

        image_urls = []
        # 解码后均可用 JSON 格式正则匹配
        patterns = [
            r'"murl"\s*:\s*"(https?://[^"]+\.(?:jpg|jpeg|png|webp)(?:\?[^"]*)?)"',
            r'"imgurl"\s*:\s*"(https?://[^"]+\.(?:jpg|jpeg|png|webp)(?:\?[^"]*)?)"',
            # 备用：直接匹配 http(s) 图片 URL（宽松模式，防止前两条均不命中）
            r'(https?://(?!(?:www\.|cn\.)?bing\.com)[^\s"<>\']{10,200}\.(?:jpg|jpeg|png|webp)(?:\?[^\s"<>\']*)?)',
        ]
        seen = set()
        for pattern in patterns:
            for url in re.findall(pattern, decoded, re.IGNORECASE):
                url = url.replace('\\/', '/').strip()
                if url in seen:
                    continue
                if 'bing.com' in url:
                    continue
                if _is_low_quality_url(url):
                    logger.debug(f"过滤低质量图片 URL: {url[:80]}")
                    continue
                seen.add(url)
                image_urls.append(url)
            if len(image_urls) >= 50:
                break

        return image_urls

    def search_bing_images(self, keyword: str, max_images: int = 5) -> List[str]:
        """使用 Bing 搜索图片 URL"""
        image_urls = []
        try:
            # 使用 mkt=en-US 减少被重定向到 cn.bing.com 的概率
            search_url = (
                f"https://www.bing.com/images/search"
                f"?q={quote(keyword)}&form=HDRSC2&first=1&mkt=en-US"
            )
            logger.info(f"搜索图片: {keyword}")

            session = requests.Session()
            session.trust_env = False  # 绕过无效系统代理
            # 先访问 Bing 主页获取 Cookie（带 mkt 参数）
            session.get(
                'https://www.bing.com/?mkt=en-US',
                headers=self._get_headers(), timeout=10, verify=False
            )
            time.sleep(random.uniform(0.5, 1.2))

            resp = session.get(search_url, headers=self._get_headers(), timeout=15, verify=False)
            image_urls = self._extract_image_urls(resp.text)[:max_images]

            logger.info(f"找到 {len(image_urls)} 张图片 URL（关键词: {keyword}）")
        except Exception as e:
            logger.error(f"Bing 图片搜索失败: {e}")
        return image_urls[:max_images]

    def download_image(self, url: str, filename: str = None,
                        save_dir: str = None) -> Optional[str]:
        """
        下载图片并保存为 JPEG。
        :param save_dir: 自定义保存目录（None 则使用 self.save_dir）
        """
        if not filename:
            filename = f"{uuid.uuid4().hex}.jpg"
        _save_dir = save_dir or self.save_dir
        filepath = os.path.join(_save_dir, filename)
        os.makedirs(_save_dir, exist_ok=True)
        
        # 为 MAL 图片添加防盗链 Referer
        headers = self._get_headers()
        if 'myanimelist.net' in url or 'mAL' in filename:
            headers['Referer'] = 'https://myanimelist.net/'
            logger.debug(f"为 MAL 图片添加 Referer: {url[:80]}")
        
        # 重试机制
        max_retries = 3
        for attempt in range(max_retries):
            try:
                _sess = requests.Session()
                _sess.trust_env = False
                # 增加超时时间：连接10秒，读取30秒
                resp = _sess.get(url, headers=headers, timeout=(10, 30), stream=True, verify=False)
                resp.raise_for_status()

                content_type = resp.headers.get('Content-Type', '')
                if 'image' not in content_type and not re.search(r'\.(jpg|jpeg|png|webp|gif)', url, re.I):
                    return None

                with open(filepath, 'wb') as f:
                    for chunk in resp.iter_content(8192):
                        f.write(chunk)

                # 验证并转为合规 JPEG
                img = Image.open(filepath)
                if img.mode in ('RGBA', 'P', 'LA'):
                    img = img.convert('RGB')
                if img.width > 1200:
                    img = img.resize((1200, int(img.height * 1200 / img.width)), Image.LANCZOS)
                jpeg_path = os.path.splitext(filepath)[0] + '.jpg'
                img.save(jpeg_path, 'JPEG', quality=85)
                if jpeg_path != filepath and os.path.exists(filepath):
                    os.remove(filepath)
                logger.info(f"图片下载成功: {jpeg_path}")
                return jpeg_path

            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # 指数退避：1s, 2s, 4s
                    logger.warning(f"图片下载失败 (尝试 {attempt+1}/{max_retries})，{wait_time}秒后重试: {e}")
                    time.sleep(wait_time)
                else:
                    logger.warning(f"图片下载/处理失败: {e}")
                    if os.path.exists(filepath):
                        os.remove(filepath)
                    return None
        
        return None

    def get_anime_cover(self, anime_name: str, name_jp: str = None,
                        used_urls: List[str] = None) -> Optional[str]:
        """
        获取动画封面图。
        仅使用 MyAnimeList API 获取官方高质量封面，Bing 完全禁用。
        MAL API 失败时，fallback 到本地缓存图片。
        """
        # 策略1: 仅使用 MyAnimeList API 获取官方封面
        logger.info(f"尝试从 MAL API 获取封面: {anime_name}")
        mal_urls = self._get_mal_image_urls(anime_name, name_jp, count=2)
        if mal_urls:
            cover_path = self.download_image(mal_urls[0], filename=f"cover_{uuid.uuid4().hex[:8]}.jpg")
            if cover_path:
                logger.info(f"MAL API 封面获取成功: {cover_path}")
                return cover_path
            else:
                logger.warning(f"MAL API 图片下载失败，尝试从缓存获取封面: {anime_name}")
        else:
            logger.warning(f"MAL API 无返回，尝试从缓存获取封面: {anime_name}")

        # 策略2 (fallback): 从本地缓存取一张图片作为封面
        cache = ImageCache()
        stats = cache.get_cache_stats(anime_name)
        if stats['total'] > 0:
            folder = cache._anime_folder(anime_name)
            manifest = cache._load_manifest(anime_name)
            if manifest.get('images'):
                first_img = manifest['images'][0]
                cover_path = first_img.get('path')
                if cover_path and os.path.exists(cover_path):
                    logger.info(f"从缓存获取封面: {cover_path}")
                    return cover_path

        logger.warning(f"无法获取封面: {anime_name}")
        return None

    def _build_article_keywords(self, anime_name: str, name_jp: str = None,
                                 song_name: str = None, singer: str = None) -> List[str]:
        """
        构建多样化的配图搜索关键词列表，优先关联动漫内容。
        关键词顺序按相关度从高到低排列：
          1. 动画中文名 + anime screenshot/fanart（最相关，针对中文用户优化）
          2. 动画英文名/中文名 + wallpaper（保底）
          3. 日文名作为后备（容易召回书籍/新闻等无关结果）
          4. 歌曲/歌手相关（最低优先级）
        
        策略说明：
          - 优先使用中文关键词，Bing 对中文字符识别准确，返回动漫相关图片质量更高
          - 日文关键词容易召回出版物、新闻稿，降低优先级
          - 加入 "site:zerochan.net" / "site:myanimelist.net" 等暗示，提高动漫图命中率
        """
        kws = []
        # 1. 优先：中文动画名 + anime 专用词（针对中文用户优化）
        kws += [
            f"{anime_name} anime screenshot",
            f"{anime_name} 动漫截图",
            f"{anime_name} fanart",
            f"{anime_name} 同人图",
        ]
        # 2. 中文名 + 壁纸（保底）
        kws += [
            f"{anime_name} anime wallpaper HD",
            f"{anime_name} 动漫壁纸",
        ]
        # 3. 日文名作为后备（降低优先级，避免书籍封面干扰）
        if name_jp:
            kws += [
                f"{name_jp} anime screenshot",
                f"{name_jp} fanart site:zerochan.net OR site:myanimelist.net OR site:pinterest.com",
                f"{name_jp} anime wallpaper HD",
            ]
        # 4. 歌曲/演唱者关联（最低优先级）
        if song_name and anime_name:
            kws.append(f"{anime_name} {song_name}")
        if singer and anime_name:
            kws.append(f"{anime_name} {singer}")
        # 5. 日文名场景 / 角色（保底，容易召回无关结果）
        if name_jp:
            kws += [
                f"{name_jp} アニメ 壁紙",
                f"{name_jp} キャラクター",
            ]
        # 6. 通用保底
        kws += [
            f"{anime_name} anime",
            f"{anime_name} anime poster",
        ]
        # 去重保序
        seen = set()
        result = []
        for k in kws:
            k = k.strip()
            if k and k not in seen:
                seen.add(k)
                result.append(k)
        return result

    def get_article_images(self, anime_name: str, name_jp: str = None, count: int = 3,
                            song_name: str = None, singer: str = None,
                            used_urls: List[str] = None) -> List[str]:
        """
        获取文章配图。
        优先使用 MyAnimeList API 获取官方高质量图片，
        Bing 搜索作为后备补充。
        
        视觉去重：下载后用感知哈希（aHash）检测重复图片，
        若与已有图片汉明距离 ≤ 8，则视为重复，替换下载。
        
        :param count:      需要的配图张数（调用方根据歌词行数动态计算）
        :param song_name:  歌曲名，用于构建更精准的搜索词
        :param singer:     歌手名，用于构建更精准的搜索词
        :param used_urls:  已使用过的微信图片 URL，用于排重
        """
        all_imgs = []
        downloaded_hashes: List[Tuple[str, int]] = []  # (path, hash)
        needed = count
        
        # 策略1: 优先使用 MyAnimeList API 获取官方图片（100% 精准）
        # MAL 覆盖封面图（大图）+ 动画剧照（pictures），正常情况下已足够
        logger.info(f"尝试从 MAL API 获取文章配图: {anime_name}")
        mal_urls = self._get_mal_image_urls(anime_name, name_jp, count=needed * 3)
        
        if mal_urls:
            for url in mal_urls:
                if len(all_imgs) >= needed:
                    break
                filename = f"mal_{uuid.uuid4().hex[:8]}.jpg"
                path = self.download_image(url, filename=filename)
                if path:
                    # ── 视觉去重 ──────────────────────────────
                    dup_path = _is_duplicate_image(path, downloaded_hashes)
                    if dup_path:
                        logger.info(f"跳过视觉重复图片: {path} ≈ {dup_path}")
                        os.remove(path)
                        continue
                    # ────────────────────────────────────────
                    all_imgs.append(path)
                    h = _compute_ahash(path)
                    if h is not None:
                        downloaded_hashes.append((path, h))
                    logger.debug(f"配图已添加 [{len(all_imgs)}/{needed}]: {path}")
                time.sleep(0.3)
            
            logger.info(f"MAL API 成功获取 {len(all_imgs)} 张配图（去重后，buffer=3x）")
        
        # 策略2: 仅当 MAL API 完全无返回时，返回 None（不再用 Bing 兜底）
        # 图片必须100%正确，Bing 搜索结果不可控
        if not all_imgs:
            logger.warning(f"MAL API 完全无返回，无法获取文章配图: {anime_name}")
        
        logger.info(f"文章配图共获取 {len(all_imgs)} 张（目标 {needed} 张）")
        return all_imgs[:count]

    def search_and_download(self, keyword: str, max_images: int = 3,
                             used_urls: List[str] = None) -> List[str]:
        """搜索并下载图片，自动跳过已使用的源 URL"""
        urls = self.search_bing_images(keyword, max_images * 3)
        used_urls = used_urls or []
        downloaded = []
        for url in urls:
            if len(downloaded) >= max_images:
                break
            # 简单 URL 去重（源 URL 层面）
            if any(url in u or u in url for u in used_urls):
                logger.debug(f"跳过已使用图片: {url}")
                continue
            path = self.download_image(url)
            if path:
                downloaded.append(path)
            time.sleep(random.uniform(0.3, 0.8))
        return downloaded


def crawl_images_for_article(anime_name: str, name_jp: str = None,
                              article_image_count: int = 3,
                              song_name: str = None, singer: str = None,
                              used_wechat_urls: List[str] = None) -> Dict:
    """
    为文章爬取图片的入口函数。

    配图策略（ImageCache）：
      ① 优先从本地缓存取未使用图片（秒级响应，不重复）
      ② 缓存不足时自动从 MAL 补仓（3x buffer）
      ③ 补仓后仍不足则回退复用已使用图片
      封面图：始终从 MAL API 实时获取（保证最新质量）

    :param article_image_count: 正文配图张数（调用方根据歌词行数动态传入，默认3张）
    :param song_name:           歌曲名（用于日志标注）
    :param singer:              歌手名（用于日志标注）
    :param used_wechat_urls:    保留参数（兼容旧代码，不再使用）
    """
    logger.info(f"=== 开始为文章获取图片: {anime_name}，目标 {article_image_count} 张 ===")
    spider = ImageSpider()

    # 封面：直接走 MAL，不走缓存（保证最新质量）
    cover = spider.get_anime_cover(anime_name, name_jp)
    logger.info(f"封面图: {cover}")

    # 正文配图：走 ImageCache 缓存系统
    cache = ImageCache()
    article_images = cache.get_images_for_article(
        anime_name=anime_name,
        name_jp=name_jp,
        count=article_image_count,
    )
    logger.info(f"文章配图: {len(article_images)} 张")

    return {'cover': cover, 'article_images': article_images}


if __name__ == "__main__":
    print("测试图片爬虫...")
    result = crawl_images_for_article("龙珠Z", "ドラゴンボールZ")
    print("封面:", result['cover'])
    print("配图:", result['article_images'])
