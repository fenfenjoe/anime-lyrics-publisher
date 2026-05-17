# -*- coding: utf-8 -*-
"""预览 article_id=61"""
import sys, os, re
sys.path.insert(0, os.path.dirname(__file__))
from database import db

article_id = 61
with db.get_connection() as conn:
    row = conn.execute(
        "SELECT article_title, article_content, cover_image_path FROM articles WHERE id = ?",
        (article_id,)
    ).fetchone()

if not row:
    print("未找到 article_id={}".format(article_id))
else:
    title, content, cover = row
    cover_rel = os.path.basename(cover) if cover else ""
    imgs_in_content = re.findall(r'data/images/([^"]+\.jpg)', content)

    if cover_rel:
        cover_html = "<img class='cover' src='data/images/{}' />".format(cover_rel)
    else:
        cover_html = "<p>无封面图</p>"

    img_thumbs = ""
    for i, img in enumerate(imgs_in_content):
        img_thumbs += "    <div><img src='data/images/{}' /><div class='caption'>配图{}}</div></div>\n".format(img, i+1)

    total_imgs = (1 if cover_rel else 0) + len(imgs_in_content)

    html = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
  body {{ font-family: -apple-system, sans-serif; max-width: 680px; margin: 0 auto; padding: 20px; background: #f9f9f9; }}
  h1 {{ font-size: 20px; color: #333; }}
  .cover {{ width: 100%; border-radius: 8px; margin-bottom: 16px; }}
  .cover-label {{ font-size: 12px; color: #888; margin-bottom: 4px; }}
  .content {{ background: white; padding: 16px; border-radius: 8px; font-size: 15px; line-height: 1.8; color: #333; }}
  .content img {{ width: 100%; border-radius: 8px; margin: 12px 0; }}
  .img-list {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 16px; }}
  .img-list img {{ width: 100px; height: 100px; object-fit: cover; border-radius: 6px; }}
  .img-list .caption {{ font-size: 11px; color: #888; text-align: center; margin-top: 2px; }}
  .section {{ background: white; padding: 16px; border-radius: 8px; margin-top: 16px; }}
  .section h3 {{ margin: 0 0 8px; font-size: 14px; color: #555; }}
</style>
</head>
<body>
<h1>{title}</h1>

<div class="cover-label">封面图</div>
{cover_html}

<div class="section">
  <h3>文章配图（{num_imgs} 张，已去重）</h3>
  <div class="img-list">
{img_thumbs}  </div>
</div>

<div class="content">
{content}
</div>

<div class="section">
  <h3>统计</h3>
  <p>封面图：{has_cover}张<br>
  正文配图：{num_imgs} 张<br>
  总计：{total} 张</p>
</div>
</body>
</html>""".format(
        title=title,
        cover_html=cover_html,
        num_imgs=len(imgs_in_content),
        img_thumbs=img_thumbs,
        content=content,
        has_cover=1 if cover_rel else 0,
        total=total_imgs,
    )

    out_path = os.path.join(os.path.dirname(__file__), "spy_mixnuts_preview_v2.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print("预览已生成: {}".format(out_path))
