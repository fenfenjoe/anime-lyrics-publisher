# -*- coding: utf-8 -*-
"""
AI 歌词分析模块 - 由 WorkBuddy AI 直接调用

本脚本是 WorkBuddy Automation 任务的执行体。
WorkBuddy AI 在每日定时任务中：
  1. 读取 data/pending_analysis.json（由 article_generator.py 写入）
  2. 对歌词进行翻译和语法分析
  3. 将结果写入 data/analysis_result.json
  4. article_generator.py 轮询到结果后继续生成文章

手动运行（测试用）：
  python ai_analyzer.py
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import List, Dict

# 确保项目根目录在 Python 路径中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from anime_lyrics_publisher import config

logging.basicConfig(level=getattr(logging, config.LOG_LEVEL),
                    format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

PENDING_FILE = os.path.join(config.DATA_DIR, 'pending_analysis.json')
RESULT_FILE  = os.path.join(config.DATA_DIR, 'analysis_result.json')


def load_pending_task() -> Dict:
    """读取待分析任务文件"""
    if not os.path.exists(PENDING_FILE):
        raise FileNotFoundError(f"未找到待分析任务文件: {PENDING_FILE}")
    with open(PENDING_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def build_analysis_prompt(task: Dict) -> str:
    """
    根据任务信息构建 prompt。
    WorkBuddy AI 在 Automation 里会直接看到并执行这段 prompt。
    """
    anime     = task.get('anime_name', '未知动画')
    song      = task.get('song_name', '未知歌曲')
    song_type = task.get('song_type', '')
    language  = task.get('language', 'ja')
    lines     = task.get('lyrics_lines', [])
    n         = len(lines)

    numbered = '\n'.join(f"{i+1}. {l}" for i, l in enumerate(lines))

    if language == 'ja':
        instruction = (
            f"你是一位热爱二次元音乐、擅长情报收集、鉴赏与推荐的女少年，同时也是专业的日语老师。\n"
            f"请对以下来自《{anime}》{song_type}《{song}》的日语歌词进行分析。\n\n"
            f"[重要约束 - 必须严格遵守]\n"
            f"- 歌词共 {n} 句，你必须对每一句都进行分析，result 数组中必须恰好有 {n} 个元素\n"
            f"- 不得省略、合并或跳过任何一句，即使某句很短或者重复\n"
            f"- 输出的 JSON 中，第 N 个元素对应第 N 句歌词，顺序不可打乱\n\n"
            f"分析要求：\n"
            f"1. 给出每句的准确中文翻译（保留歌词的诗意）\n"
            f"2. 给出每句的 furigana 注音版本（行内括注格式，规则如下）：\n"
            f"   - 保留原文中所有汉字（不替换为假名），在每个汉字或汉字词后面紧跟括号标注读音\n"
            f"   - 例：原文 君の名は → furigana：君（きみ）の名（な）は\n"
            f"   - 例：原文 夢の中で会った → furigana：夢（ゆめ）の中（なか）で会（あ）った\n"
            f"   - 例：原文 人類は思い出した → furigana：人類（じんるい）は思（おも）い出（だ）した\n"
            f"   - 如果原文全是平假名/片假名，没有汉字，则 furigana 与 original 完全相同\n"
            f"   - 【严禁】把原文全部转换成平假名/片假名作为 furigana——furigana 必须保留汉字\n"
            f"3. 分析每句中 1~3 个典型的日语语法点（助词用法、动词活用、常用句型等），用中文简明说明\n"
            f"4. 为整首歌曲写一段 50~100 字的中文简介（song_intro）：\n"
            f"   - 以热爱二次元、擅长鉴赏推荐的女少年口吻写，语气自然活泼，可以带一点个人情感和主观推荐色彩\n"
            f"   - 介绍该曲的背景、风格及在动漫中的作用，字数严格控制在 50~100 字以内\n\n"
            f"全部 {n} 句歌词如下：\n"
            f"{numbered}\n\n"
            f"请严格按以下 JSON 格式输出，不要添加任何多余内容：\n"
            f'{{\n  "song_intro": "50~100字、女少年口吻的曲目简介",\n  "result": [\n'
            f'    {{"original": "第1句原文", "furigana": "保留汉字并在汉字后括注读音的版本", "translation": "中文翻译", "grammar": "语法要点"}},\n'
            f'    {{"original": "第2句原文", "furigana": "保留汉字并在汉字后括注读音的版本", "translation": "中文翻译", "grammar": "语法要点"}}\n'
            f"  ]\n}}\n\n"
            f"re-note: result must have exactly {n} elements, one per lyric line."
        )
    else:
        lang_name = {'en': '英语', 'ko': '韩语', 'zh': '中文'}.get(language, language)
        instruction = (
            f"你是一位热爱二次元音乐、擅长情报收集、鉴赏与推荐的女少年，同时也是专业的歌词翻译者。\n"
            f"请将以下来自《{anime}》{song_type}《{song}》的{lang_name}歌词翻译成中文（保留歌词的诗意和情感）。\n\n"
            f"[重要约束 - 必须严格遵守]\n"
            f"- 歌词共 {n} 句，你必须对每一句都进行翻译，result 数组中必须恰好有 {n} 个元素\n"
            f"- 不得省略、合并或跳过任何一句\n"
            f"- 同时为整首歌曲写一段 50~100 字的中文简介（song_intro）：\n"
            f"  - 以热爱二次元、擅长鉴赏推荐的女少年口吻写，语气自然活泼，带一点个人情感和主观推荐色彩\n"
            f"  - 介绍该曲的背景、风格及在动漫中的作用，字数严格控制在 50~100 字以内\n\n"
            f"全部 {n} 句歌词如下：\n"
            f"{numbered}\n\n"
            f"请严格按以下 JSON 格式输出，不要添加任何多余内容：\n"
            f'{{\n  "song_intro": "50~100字、女少年口吻的曲目简介",\n  "result": [\n'
            f'    {{"original": "第1句原文", "translation": "中文翻译", "grammar": ""}},\n'
            f'    {{"original": "第2句原文", "translation": "中文翻译", "grammar": ""}}\n'
            f"  ]\n}}\n\n"
            f"re-note: result array must contain exactly {n} elements."
        )

    return instruction


def write_result(task: Dict, result_items: List[Dict], song_intro: str = ''):
    """将分析结果写入 result 文件，并标记 status=done"""
    output = {
        "task_id":      task.get('task_id'),
        "status":       "done",
        "completed_at": datetime.now().isoformat(),
        "task":         task,           # 原样回写，供 article_generator 读取
        "song_intro":   song_intro,     # 曲目简介
        "result":       result_items
    }
    with open(RESULT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    logger.info(f"分析结果已写入: {RESULT_FILE}")


def run_analysis_by_ai():
    """
    ══════════════════════════════════════════════════════════════
    本函数由 WorkBuddy Automation 自动调用。

    执行步骤：
      1. 读取 pending_analysis.json
      2. 打印分析 prompt（WorkBuddy AI 看到并执行）
      3. AI 将 JSON 结果写回 analysis_result.json（status = done）
    ══════════════════════════════════════════════════════════════
    """
    logger.info("=== AI 歌词分析任务启动 ===")

    # Step 1: 读取任务
    task = load_pending_task()
    logger.info(f"任务: {task.get('anime_name')} - {task.get('song_name')}  语言: {task.get('language')}")

    # Step 2: 构建 prompt 并打印（WorkBuddy AI 会看到并执行）
    prompt = build_analysis_prompt(task)

    print("\n" + "=" * 60)
    print("【WorkBuddy AI 请执行以下分析任务】")
    print("=" * 60)
    print(prompt)
    print("=" * 60)
    print("\n请将上面 JSON 格式的结果写入以下文件（status 设为 done）：")
    print(f"  {RESULT_FILE}")
    print("\n或者直接调用 write_result_to_file(result_json_string) 函数。")

    return prompt, task


def write_result_to_file(result_json_str: str, task: Dict = None):
    """
    辅助函数：接受 AI 输出的 JSON 字符串，解析后写入结果文件。
    WorkBuddy AI 在 Automation 中可以直接调用此函数。
    """
    if task is None:
        task = load_pending_task()

    # 尝试从字符串中提取 JSON
    import re
    # 处理 AI 可能包裹在 ```json ... ``` 中的情况
    match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', result_json_str)
    if match:
        result_json_str = match.group(1)

    data = json.loads(result_json_str)
    result_items = data.get('result', [])
    song_intro   = data.get('song_intro', '')

    if not result_items:
        raise ValueError("解析到的 result 为空，请检查 AI 输出格式")

    # ── 验证结果条数与歌词句数是否一致 ────────────────────────
    expected = len(task.get('lyrics_lines', []))
    actual   = len(result_items)
    if actual < expected:
        msg = (
            f"\n{'!'*60}\n"
            f"【警告】AI 返回的分析结果不完整！\n"
            f"  歌词总句数: {expected}\n"
            f"  AI 已返回: {actual}\n"
            f"  缺少: {expected - actual} 句（第 {actual+1}～{expected} 句）\n"
            f"\n请继续补全剩余歌词的分析，并将完整的 {expected} 条 JSON 重新调用本函数写入。\n"
            f"{'!'*60}"
        )
        logger.warning(msg)
        print(msg)
        raise ValueError(
            f"结果不完整: 期望 {expected} 条，实际只有 {actual} 条。"
            f"请补全第 {actual+1}～{expected} 句后重新提交。"
        )

    write_result(task, result_items, song_intro=song_intro)
    logger.info(f"成功写入 {len(result_items)} 条分析结果")
    return result_items


if __name__ == "__main__":
    """
    手动测试：
      python ai_analyzer.py
    
    此命令会：
      1. 读取 data/pending_analysis.json
      2. 打印分析 prompt
      3. 等待你（或 AI）把 JSON 结果粘贴进来，然后写入结果文件
    """
    prompt, task = run_analysis_by_ai()

    print("\n如需手动测试，请将 AI 返回的 JSON 粘贴到下方并回车（输入 END 结束）：")
    lines = []
    while True:
        try:
            line = input()
            if line.strip() == 'END':
                break
            lines.append(line)
        except EOFError:
            break

    if lines:
        raw = '\n'.join(lines)
        try:
            items = write_result_to_file(raw, task)
            print(f"\n✅ 已写入 {len(items)} 条分析结果到 {RESULT_FILE}")
        except Exception as e:
            print(f"\n❌ 写入失败: {e}")
