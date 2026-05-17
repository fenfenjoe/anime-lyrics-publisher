# -*- coding: utf-8 -*-
import sqlite3, re

conn = sqlite3.connect('data/anime_lyrics.db')
cur = conn.execute('SELECT article_title, article_content, cover_image_path FROM articles WHERE id=60')
row = cur.fetchone()
title, content, cover = row

# 提取文章图片
imgs = re.findall(r'<img src="([^"]+)"', content)
print(f"文章图片: {len(imgs)}张")
for i, img in enumerate(imgs):
    print(f"  {i+1}: {img}")

# 提取前几句歌词用于预览
lyric_blocks = []
in_lyrics = False
count = 0
for line in content.split('\n'):
    if '## 歌词解析' in line:
        in_lyrics = True
        continue
    if in_lyrics and line.startswith('**'):
        m = re.match(r'\*\*(\d+)\.\s+(.+?)\*\*', line)
        if m:
            num = m.group(1)
            text = m.group(2)
            count += 1
            if count > 8:
                break
            # 找翻译和语法
            lyrics_lines = content.split('\n')
            trans = ''
            gram = ''
            for j, l in enumerate(lyrics_lines):
                if f'**{num}.' in l and j > 0:
                    # 找翻译行
                    for k in range(j, min(j+3, len(lyrics_lines))):
                        if '中文翻译' in lyrics_lines[k]:
                            trans = lyrics_lines[k+1].replace('中文翻译：', '').strip() if k+1 < len(lyrics_lines) else ''
                            break
                    break
            lyric_blocks.append({'num': num, 'text': text, 'trans': trans})

# 构建HTML
img_tags = '\n'.join([f'<img src="{img}" style="width:100%;border-radius:8px;margin:16px 0;" />' for img in imgs])

lyric_html = ''
for i, block in enumerate(lyric_blocks):
    lyric_html += f'''
<div class="lyric-block">
  <div class="lyric-num">第{block["num"]}句</div>
  <div class="lyric-text"><strong>{block["text"]}</strong></div>
  <div class="lyric-trans">翻译：{block["trans"]}</div>
</div>'''

html = f'''<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<title>{title}</title>
<style>
body {{ font-family: -apple-system, sans-serif; max-width: 680px; margin: 0 auto; padding: 20px; background: #fafafa; }}
img {{ max-width: 100%; }}
.cover {{ width: 100%; border-radius: 8px; margin-bottom: 20px; }}
.lyric-block {{ background: #fff; padding: 16px; border-radius: 8px; margin: 12px 0; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }}
.lyric-num {{ color: #ff6b9d; font-weight: bold; font-size: 13px; margin-bottom: 6px; }}
.lyric-text {{ font-size: 16px; color: #333; line-height: 1.8; }}
.lyric-trans {{ color: #888; font-size: 14px; margin-top: 6px; }}
.section-title {{ color: #555; font-size: 14px; margin: 20px 0 10px; }}
.source-tag {{ background: #2ecc71; color: #fff; font-size: 11px; padding: 2px 8px; border-radius: 10px; display: inline-block; margin-bottom: 8px; }}
</style>
</head>
<body>

<div style="background:#fff;padding:24px;border-radius:12px;margin-bottom:20px;box-shadow:0 2px 8px rgba(0,0,0,0.08);">
  <h1 style="margin:0 0 8px;font-size:20px;color:#333;">{title}</h1>
  <span class="source-tag">图片来源：MyAnimeList 官方</span>
  <p style="color:#555;font-size:13px;margin:4px 0;">article_id=60 | 2026-05-12</p>
</div>

<div style="background:#fff;padding:20px;border-radius:12px;margin-bottom:16px;box-shadow:0 2px 8px rgba(0,0,0,0.08);">
  <div style="font-size:15px;line-height:2;color:#444;">
    <span style="color:#ff6b9d;font-weight:bold;">推荐语：</span>
    《ミックスナッツ》是超人气动画《SPY×FAMILY》的开篇主题曲，由日本超人气流行摇滚乐队Official髭男dism创作演唱。这首歌以「混合坚果」为隐喻，描写了一群各自隐藏真实身份的人，在伪装中努力建立联系的微妙关系。节奏明快跳跃，旋律洗脑抓耳，歌词既有对「假面日常」的自嘲与无奈，也有「即使被现实反复煎炒碾压，也要成为打不碎的坚果壳」的温暖治愈，是一首听了就停不下来的宝藏OP！
  </div>
</div>

<h3 class="section-title">封面图</h3>
<img class="cover" src="{cover}" />

<h3 class="section-title">正文配图（共{len(imgs)}张，均来自 MyAnimeList 官方）</h3>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
  {' '.join([f'<img src="{img}" style="width:100%;border-radius:8px;" />' for img in imgs])}
</div>

<h3 class="section-title" style="margin-top:24px;">歌词解析预览（前{len(lyric_blocks)}句 / 共27句）</h3>
{lyric_html}

<p style="color:#999;font-size:13px;text-align:center;margin-top:24px;padding:16px;background:#f5f5f5;border-radius:8px;">
  全文共27句歌词 · 6张配图（封面+5张正文）<br/>
  <strong>图片来源：MyAnimeList Jikan API 官方图库</strong> · Bing搜索已完全禁用
</p>
</body>
</html>'''

with open('spy_mixnuts_preview.html', 'w', encoding='utf-8') as f:
    f.write(html)
print(f"预览文件已生成: spy_mixnuts_preview.html")
conn.close()
