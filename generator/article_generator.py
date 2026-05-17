# -*- coding: utf-8 -*-
"""
文章生成器模块 - 生成微信公众号文章内容

工作流程:
1. 从数据库取歌词，写入 data/pending_analysis.json（等待 AI 分析）
2. WorkBuddy AI 读取该文件，分析歌词后写入 data/analysis_result.json
3. 本脚本读取分析结果，格式化为微信公众号文章并存库
"""

import os
import json
import re
import logging
import time
from typing import List, Dict, Optional
from datetime import datetime

from anime_lyrics_publisher import config
from anime_lyrics_publisher.database import db

logging.basicConfig(level=getattr(logging, config.LOG_LEVEL))
logger = logging.getLogger(__name__)

# AI 交换文件路径
PENDING_FILE = os.path.join(config.DATA_DIR, 'pending_analysis.json')
RESULT_FILE  = os.path.join(config.DATA_DIR, 'analysis_result.json')


# ──────────────────────────────────────────────
#  工具函数
# ──────────────────────────────────────────────

def _is_pure_kana(s: str) -> bool:
    """
    判断字符串是否全为平/片假名（不含任何汉字）。
    用于检测旧格式 furigana（纯读音串），以便 fallback 到原文显示。
    """
    return bool(s) and not bool(re.search(r'[\u4E00-\u9FFF\u3400-\u4DBF]', s))


def detect_language(text: str) -> str:
    """检测歌词语言"""
    hiragana = re.compile(r'[\u3040-\u309F]')
    ja_chars  = re.compile(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]')
    total = max(len(text), 1)

    if (len(ja_chars.findall(text)) + len(hiragana.findall(text))) / total > 0.3:
        return 'ja'
    if re.search(r'\b(the|a|is|to|you|and|i|my)\b', text, re.I):
        return 'en'
    if re.search(r'[\uAC00-\uD7AF]', text):
        return 'ko'
    if re.search(r'[\u4E00-\u9FAF]', text):
        return 'zh'
    return 'unknown'


def parse_lyrics_lines(lyrics_text: str, max_lines: int = None) -> List[str]:
    """将歌词文本解析为行列表"""
    if not lyrics_text:
        return []
    lines = [l.strip() for l in lyrics_text.split('\n') if l.strip() and len(l.strip()) > 1]
    limit = max_lines if max_lines is not None else config.DAILY_LYRICS_COUNT
    if limit:
        lines = lines[:limit]
    return lines


# ──────────────────────────────────────────────
#  Step 1：准备待分析任务文件
# ──────────────────────────────────────────────

def prepare_analysis_task(lyrics_data: Dict) -> bool:
    """
    把歌词信息写入 pending_analysis.json，等待 WorkBuddy AI 处理。
    返回 True 表示写入成功。
    """
    lyrics_text = lyrics_data.get('lyrics_text', '')
    language    = detect_language(lyrics_text)
    lines       = parse_lyrics_lines(lyrics_text)

    if not lines:
        logger.error("歌词内容为空，无法准备分析任务")
        return False

    task = {
        "task_id":       f"task_{int(time.time())}",
        "created_at":    datetime.now().isoformat(),
        "status":        "pending",          # pending → done
        "anime_name":    lyrics_data.get('anime_name', '未知动画'),
        "anime_name_jp": lyrics_data.get('anime_name_jp', ''),
        "song_name":     lyrics_data.get('song_name', '未知歌曲'),
        "song_type":     lyrics_data.get('song_type', 'TM'),
        "singer":        lyrics_data.get('singer', ''),
        "language":      language,
        "lyrics_lines":  lines,
        "result":        []   # 由 AI 填写
    }

    with open(PENDING_FILE, 'w', encoding='utf-8') as f:
        json.dump(task, f, ensure_ascii=False, indent=2)

    # 清空上次结果文件，避免误读旧数据
    if os.path.exists(RESULT_FILE):
        os.remove(RESULT_FILE)

    logger.info(f"分析任务已写入: {PENDING_FILE}  (共 {len(lines)} 行歌词)")
    return True


# ──────────────────────────────────────────────
#  Step 2：等待 AI 写回结果
# ──────────────────────────────────────────────

def wait_for_analysis(timeout: int = 300, poll_interval: int = 5) -> Optional[Dict]:
    """
    轮询等待 analysis_result.json 出现且 status == 'done'。
    timeout: 最多等待秒数（默认 5 分钟）
    """
    deadline = time.time() + timeout
    logger.info(f"等待 AI 分析结果（最多 {timeout} 秒）...")

    while time.time() < deadline:
        if os.path.exists(RESULT_FILE):
            try:
                with open(RESULT_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if data.get('status') == 'done' and data.get('result'):
                    logger.info("AI 分析结果已就绪")
                    return data
            except (json.JSONDecodeError, IOError):
                pass  # 文件可能还在写，忽略
        time.sleep(poll_interval)

    logger.error("等待 AI 分析超时")
    return None


# ──────────────────────────────────────────────
#  Step 3：格式化文章
# ──────────────────────────────────────────────

def format_article(task: Dict, result: Dict, article_images: List[str] = None, qq_player_html: str = None) -> Dict:
    """将 AI 分析结果格式化为微信公众号文章"""

    anime_name    = task.get('anime_name', '未知动画')
    anime_name_jp = task.get('anime_name_jp', '')
    song_name     = task.get('song_name', '未知歌曲')
    song_type     = task.get('song_type', 'TM')
    language      = task.get('language', 'ja')
    analyzed      = result.get('result', [])
    article_images = article_images or []

    title = config.ARTICLE_TITLE_TEMPLATE.format(
        anime_name=anime_name,
        song_type=song_type,
        song_name=song_name
    )

    parts = []
    parts.append(f"# {anime_name}")
    if anime_name_jp:
        parts.append(f"*{anime_name_jp}*")
    parts.append("")
    singer = task.get('singer', '')
    if singer:
        parts.append(f"**{song_type} · {song_name}（{singer}）**")
    else:
        parts.append(f"**{song_type} · {song_name}**")
    parts.append("")

    # 在歌曲标题下方插入 QQ 音乐播放器
    if qq_player_html:
        parts.append(qq_player_html)
        parts.append("")

    parts.append("---")
    parts.append("")

    # 曲目介绍：优先使用 AI 生成的 song_intro，否则不显示
    song_intro = result.get('song_intro', '').strip()
    if song_intro:
        parts.append(song_intro)
        parts.append("")

    # 开头插入第一张配图（封面风格题图）
    if len(article_images) > 0:
        parts.append(f'<img src="{article_images[0]}" style="width:100%;border-radius:8px;" />')
        parts.append("")

    parts.append("## 歌词解析")
    parts.append("")

    # 每5条歌词插一张配图，第0张已在开头用了
    INSERT_IMG_EVERY = 5
    img_idx = 1

    for i, item in enumerate(analyzed, 1):
        # 兼容 'original' 和旧版 'line' 字段名
        original    = item.get('original', '') or item.get('line', '')
        furigana    = item.get('furigana', '')   # 汉字注音（如有）
        translation = item.get('translation', '')
        grammar     = item.get('grammar', '')

        # 序号行：
        # - furigana 为"保留汉字+括注读音"格式（如 人類（じんるい）は思（おも）い出（だ）した）
        # - 若 furigana 有内容且与 original 不同，且包含汉字（非旧格式纯假名），则使用 furigana
        # - 否则 fallback 到 original
        if furigana and furigana != original and not _is_pure_kana(furigana):
            display = furigana   # 新格式：汉字+括注，直接显示
        else:
            display = original   # fallback：直接显示原文
        parts.append(f"**{i}. {display}**")
        parts.append("")
        parts.append(f"中文翻译：{translation}")
        parts.append("")
        if language == 'ja' and grammar:
            parts.append(f"语法要点：{grammar}")
            parts.append("")
        parts.append("")

        # 每5条歌词插入一张配图
        if img_idx < len(article_images) and i % INSERT_IMG_EVERY == 0:
            parts.append(f'<img src="{article_images[img_idx]}" style="width:100%;border-radius:8px;" />')
            parts.append("")
            img_idx += 1

    parts.append("---")
    parts.append("")
    parts.append("> 每天学习一句，让日语进步一点点！")
    parts.append("")
    parts.append("---")
    parts.append("*本文涉及的作品相关权利归原著作权人所有*")

    return {
        'title':   title,
        'content': '\n'.join(parts),
        'language': language
    }


# ──────────────────────────────────────────────
#  主流程
# ──────────────────────────────────────────────

class ArticleGenerator:

    def generate_article_for_daily(self) -> Optional[Dict]:
        """每日文章生成：准备任务 → 等待 AI → 格式化"""

        # 1. 取歌词
        lyrics_list = db.get_random_unused_lyrics(limit=1)
        if not lyrics_list:
            logger.warning("没有可用的歌词数据")
            return None

        lyrics = lyrics_list[0]
        # get_random_unused_lyrics 已通过 JOIN 带出 anime_name / anime_name_jp

        # 2. 写任务文件
        if not prepare_analysis_task(lyrics):
            return None

        # 3. 等待 AI 写回结果（WorkBuddy Automation 会触发 ai_analyzer.py）
        result = wait_for_analysis(timeout=300)
        if not result:
            return None

        # 4. 读取原始任务信息（task 字段由 ai_analyzer 原样回写）
        task = result.get('task', {})

        # 5. 格式化文章
        article = format_article(task, result)

        # 6. 存库
        article_id = db.add_article(
            lyrics_id=lyrics['id'],
            article_title=article['title'],
            article_content=article['content'],
            status='draft'
        )
        article['article_id'] = article_id
        logger.info(f"文章已生成: {article['title']} (ID: {article_id})")
        return article


def generate_daily_article() -> Optional[Dict]:
    logger.info("=== 开始每日文章生成任务 ===")
    log_id = db.add_task_log('daily_publish', 'running', '开始生成文章')
    try:
        article = ArticleGenerator().generate_article_for_daily()
        if article:
            db.update_task_log(log_id, 'success', f'生成文章: {article["title"]}')
        else:
            db.update_task_log(log_id, 'success', '没有可用歌词')
        return article
    except Exception as e:
        logger.error(f"每日文章生成失败: {e}")
        db.update_task_log(log_id, 'failed', str(e))
        return None
