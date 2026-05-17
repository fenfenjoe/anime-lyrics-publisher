# -*- coding: utf-8 -*-
"""
发布 article_id=67 (SPY×FAMILY ミックスナッツ) 到微信公众号
流程：
  1. 从 DB 读取文章（含本地图片路径）
  2. 上传封面图和所有正文图片到微信 CDN
  3. 替换文章内容为微信 CDN URL
  4. 创建微信草稿
  5. 更新 DB 状态为 published
"""
import os
import sys
import re
import json

sys.path.insert(0, os.path.dirname(__file__))

import config
from database import db
from wechat_publisher import WechatPublisher


def extract_local_images(content: str) -> list:
    """从文章正文中提取所有本地图片路径"""
    pattern = r'<img\s+[^>]*src="([^"]+)"'
    return re.findall(pattern, content)


def replace_image_urls(content: str, url_map: dict) -> str:
    """将正文中的本地路径替换为微信 CDN URL"""
    result = content
    for local_path, cdn_url in url_map.items():
        if cdn_url:
            result = result.replace(local_path, cdn_url)
    return result


def upload_image_get_cdn_url(publisher: WechatPublisher, access_token: str, img_path: str) -> str:
    """上传图片到微信素材库，返回 CDN URL"""
    if not os.path.exists(img_path):
        print(f"  ⚠️ 图片不存在: {img_path}")
        return None

    try:
        url = "https://api.weixin.qq.com/cgi-bin/material/add_material"
        params = {'access_token': access_token, 'type': 'image'}

        with open(img_path, 'rb') as f:
            files = {'media': (os.path.basename(img_path), f, 'image/jpeg')}
            resp = publisher._session.post(url, params=params, files=files, timeout=30, verify=False)
        data = resp.json()

        if 'url' in data:
            print(f"  ✅ 上传成功: {os.path.basename(img_path)} → {data['url'][:60]}...")
            return data['url']
        else:
            print(f"  ❌ 上传失败: {data}")
            return None
    except Exception as e:
        print(f"  ❌ 上传异常: {e}")
        return None


def main():
    article_id = 67

    # 1. 读取文章
    article = db.get_article_by_id(article_id)
    if not article:
        print(f"❌ 文章不存在: article_id={article_id}")
        return

    print(f"📄 文章: {article['article_title']}")
    print(f"   状态: {article['status']}")
    print(f"   封面: {article.get('cover_image_path', '')[:80]}")

    # 2. 连接微信
    publisher = WechatPublisher()
    access_token = publisher.get_access_token()
    if not access_token:
        print("❌ 获取微信 access_token 失败，请检查 config.py 中的 WECHAT_APP_ID/WECHAT_APP_SECRET")
        return
    print("✅ 微信 access_token 获取成功")

    # 3. 上传封面图
    cover_path = article.get('cover_image_path', '')
    cover_cdn_url = None
    if cover_path and os.path.exists(cover_path):
        print(f"\n📤 上传封面图...")
        cover_cdn_url = upload_image_get_cdn_url(publisher, access_token, cover_path)
    else:
        print(f"\n⚠️ 封面图不存在: {cover_path}")

    # 4. 提取并上传所有正文图片
    content = article['article_content']
    local_images = extract_local_images(content)
    print(f"\n📤 正文包含 {len(local_images)} 张图片，开始上传...")
    url_map = {}
    for img_path in local_images:
        cdn_url = upload_image_get_cdn_url(publisher, access_token, img_path)
        url_map[img_path] = cdn_url

    # 5. 替换正文图片 URL
    new_content = replace_image_urls(content, url_map)

    # 6. 上传封面到微信素材库（获取 media_id）
    print(f"\n📤 上传封面到微信素材库（获取 media_id）...")
    cover_media_id = None
    if cover_path and os.path.exists(cover_path):
        cover_media_id = publisher.upload_image(cover_path)
    if not cover_media_id:
        print("  ⚠️ 封面 media_id 获取失败，将使用默认封面")
        cover_media_id = publisher._ensure_default_cover(access_token)

    # 7. 创建微信草稿
    print(f"\n📝 创建微信草稿...")
    import re as re2
    safe_title = article['article_title'][:64]
    plain = re2.sub(r'<[^>]+>', '', content)
    plain = re2.sub(r'\s+', ' ', plain).strip()
    safe_digest = plain[:120]

    # 将新内容（CDN URL）转为 HTML
    processed_content = publisher._md_to_html(new_content)

    article_item = {
        'title': safe_title,
        'author': '',
        'content': processed_content,
        'content_source_url': '',
        'digest': safe_digest,
        'need_open_comment': 0,
        'only_fans_can_comment': 0,
    }
    if cover_media_id:
        article_item['thumb_media_id'] = cover_media_id

    articles_body = {"articles": [article_item]}

    url = "https://api.weixin.qq.com/cgi-bin/draft/add"
    params = {'access_token': access_token}
    body_bytes = json.dumps(articles_body, ensure_ascii=False).encode('utf-8')
    resp = publisher._session.post(
        url, params=params,
        data=body_bytes,
        headers={'Content-Type': 'application/json; charset=utf-8'},
        timeout=30, verify=False
    )
    data = resp.json()

    if 'media_id' in data:
        wechat_media_id = data['media_id']
        print(f"✅ 草稿创建成功! media_id={wechat_media_id}")

        # 8. 更新 DB
        db.update_article_wechat_ids(
            article_id=article_id,
            wechat_media_id=wechat_media_id,
            status='published'
        )
        print(f"✅ 文章已发布! article_id={article_id}, status=published")
        print(f"\n🎉 请在公众号后台「草稿箱」中查看并群发！")
    else:
        print(f"❌ 草稿创建失败: {data}")


if __name__ == '__main__':
    main()
