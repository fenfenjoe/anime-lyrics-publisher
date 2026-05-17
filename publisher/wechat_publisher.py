# -*- coding: utf-8 -*-
"""
微信公众号发布模块 - 使用 Wechatpy 调用微信 API 发布文章到草稿箱
"""

import os
import json
import logging
import hashlib
import time
from typing import Dict, Optional

import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from anime_lyrics_publisher import config
from anime_lyrics_publisher.database import db

# 配置日志
logging.basicConfig(level=getattr(logging, config.LOG_LEVEL))
logger = logging.getLogger(__name__)


class WechatPublisher:
    """微信公众号发布器"""

    def __init__(self, app_id: str = None, app_secret: str = None):
        self.app_id = app_id or config.WECHAT_APP_ID
        self.app_secret = app_secret or config.WECHAT_APP_SECRET
        self.access_token = None
        self.token_expires_at = 0
        # 绕过无效系统代理
        self._session = requests.Session()
        self._session.trust_env = False

    def get_access_token(self) -> Optional[str]:
        """获取微信 access_token"""
        # 检查缓存的 token 是否有效
        if self.access_token and time.time() < self.token_expires_at:
            return self.access_token

        try:
            url = f"https://api.weixin.qq.com/cgi-bin/token"
            params = {
                'grant_type': 'client_credential',
                'appid': self.app_id,
                'secret': self.app_secret
            }
            
            response = self._session.get(url, params=params, timeout=10, verify=False)
            data = response.json()
            
            if 'access_token' in data:
                self.access_token = data['access_token']
                # 提前5分钟过期
                self.token_expires_at = time.time() + data.get('expires_in', 7200) - 300
                logger.info("获取 access_token 成功")
                return self.access_token
            else:
                logger.error(f"获取 access_token 失败: {data}")
                return None
                
        except Exception as e:
            logger.error(f"获取 access_token 异常: {e}")
            return None

    def upload_image(self, image_path: str) -> Optional[str]:
        """上传图片到微信素材库"""
        if not os.path.exists(image_path):
            logger.error(f"图片文件不存在: {image_path}")
            return None

        access_token = self.get_access_token()
        if not access_token:
            return None

        try:
            url = f"https://api.weixin.qq.com/cgi-bin/material/add_material"
            params = {'access_token': access_token, 'type': 'image'}
            
            with open(image_path, 'rb') as f:
                files = {'media': f}
                response = self._session.post(url, params=params, files=files, timeout=30, verify=False)
                data = response.json()
            
            if 'media_id' in data:
                logger.info(f"图片上传成功: {data['media_id']}")
                return data['media_id']
            else:
                logger.error(f"图片上传失败: {data}")
                return None
                
        except Exception as e:
            logger.error(f"图片上传异常: {e}")
            return None

    def create_draft_article(self, title: str, content: str,
                             author: str = "",
                             cover_image_path: str = None,
                             digest: str = None,
                             content_source_url: str = None) -> Optional[str]:
        """创建草稿箱图文消息"""
        access_token = self.get_access_token()
        if not access_token:
            return None

        try:
            # 先上传封面图片（如果有）
            thumb_media_id = None
            if cover_image_path and os.path.exists(cover_image_path):
                thumb_media_id = self.upload_image(cover_image_path)

            # 若无封面图，使用默认封面
            if not thumb_media_id:
                thumb_media_id = self._ensure_default_cover(access_token)

            # 将 Markdown 正文转为 HTML，并去除 emoji
            processed_content = self._md_to_html(content)

            # 微信草稿标题最大 64 字，digest ≤ 120 字
            import re
            safe_title = title[:64]
            plain = re.sub(r'[^\w\s\u4e00-\u9fff\u3040-\u30ff，。！？、]', '', content)
            plain = re.sub(r'\s+', ' ', plain).strip()
            safe_digest = (digest or plain)[:120]

            # 构建请求体（微信草稿箱要求包裹在 {"articles": [...]} 中）
            article_item = {
                'title': safe_title,
                'author': author,         # 空字符串规避 45110 author size limit
                'content': processed_content,
                'content_source_url': content_source_url or '',
                'digest': safe_digest,
                'need_open_comment': 0,
                'only_fans_can_comment': 0,
            }
            if thumb_media_id:
                article_item['thumb_media_id'] = thumb_media_id

            articles_body = {"articles": [article_item]}

            # 调用草稿箱创建接口
            url = "https://api.weixin.qq.com/cgi-bin/draft/add"
            params = {'access_token': access_token}
            body_bytes = json.dumps(articles_body, ensure_ascii=False).encode('utf-8')

            response = self._session.post(
                url, params=params,
                data=body_bytes,
                headers={'Content-Type': 'application/json; charset=utf-8'},
                timeout=30, verify=False
            )
            data = response.json()

            if 'media_id' in data:
                logger.info(f"草稿创建成功: {data['media_id']}")
                return data['media_id']
            else:
                logger.error(f"草稿创建失败: {data}")
                return None

        except Exception as e:
            logger.error(f"创建草稿异常: {e}")
            return None

    def _ensure_default_cover(self, access_token: str) -> Optional[str]:
        """上传默认封面图，返回 media_id"""
        cover_path = os.path.join(config.IMAGE_SAVE_DIR, 'default_cover.jpg')
        if not os.path.exists(cover_path):
            try:
                from PIL import Image
                img = Image.new('RGB', (900, 500), color=(25, 25, 50))
                img.save(cover_path, 'JPEG', quality=85)
                logger.info(f"已生成默认封面图: {cover_path}")
            except Exception as e:
                logger.warning(f"生成默认封面图失败: {e}")
                return None
        try:
            with open(cover_path, 'rb') as f:
                resp = self._session.post(
                    'https://api.weixin.qq.com/cgi-bin/material/add_material',
                    params={'access_token': access_token, 'type': 'image'},
                    files={'media': ('cover.jpg', f, 'image/jpeg')},
                    timeout=30, verify=False
                )
            data = resp.json()
            media_id = data.get('media_id')
            if media_id:
                logger.info(f"默认封面上传成功: {media_id}")
            else:
                logger.warning(f"默认封面上传失败: {data}")
            return media_id
        except Exception as e:
            logger.warning(f"上传默认封面异常: {e}")
            return None

    def _md_to_html(self, md: str) -> str:
        """将 Markdown 正文转为简单 HTML，并去除 emoji"""
        import re
        def remove_emoji(text):
            return re.sub(r'[\U00010000-\U0010ffff]', '', text, flags=re.UNICODE)

        lines = md.split('\n')
        parts = []
        for line in lines:
            line = remove_emoji(line)
            if line.startswith('<img '):
                # 直接透传 img 标签（包一层 div 居中显示）
                parts.append(f'<div style="text-align:center;margin:12px 0;">{line}</div>')
            elif line.startswith('<iframe '):
                # iframe 在微信图文中会被过滤，保留为注释占位（不影响阅读）
                pass
            elif line.startswith('<p ') or line.startswith('<p>'):
                # 已经是完整 p/div HTML（如 QQ 音乐跳转卡片），直接透传
                parts.append(line)
            elif line.startswith('# '):
                parts.append(f'<h1>{line[2:]}</h1>')
            elif line.startswith('## '):
                parts.append(f'<h2>{line[3:]}</h2>')
            elif line == '---':
                parts.append('<hr/>')
            elif line.strip() == '':
                parts.append('<br/>')
            else:
                line = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', line)
                line = re.sub(r'^\*(.+)\*$', r'<em>\1</em>', line)
                line = re.sub(r'^> (.+)', r'<blockquote>\1</blockquote>', line)
                parts.append(f'<p>{line}</p>')
        return '\n'.join(parts)

    def _process_content_images(self, content: str) -> str:
        """处理正文中的图片占位符（暂时返回原内容）"""
        return content

    def publish_article(self, article_id: int) -> bool:
        """发布文章到草稿箱"""
        # 获取文章信息
        article = db.get_article_by_id(article_id)
        if not article:
            logger.error(f"文章不存在: {article_id}")
            return False

        try:
            # 创建草稿
            wechat_media_id = self.create_draft_article(
                title=article['article_title'],
                content=article['article_content'],
                cover_image_path=article.get('cover_image_path')
            )

            if wechat_media_id:
                # 更新文章状态
                db.update_article_wechat_ids(
                    article_id=article_id,
                    wechat_media_id=wechat_media_id,
                    status='published'
                )
                logger.info(f"文章发布成功: {article['article_title']}")
                return True
            else:
                logger.error(f"文章发布失败: {article['article_title']}")
                return False

        except Exception as e:
            logger.error(f"发布文章异常: {e}")
            return False

    def upload_article_content_images(self, content: str) -> str:
        """上传正文中的所有图片并替换 URL"""
        # 简单的图片路径检测
        import re
        image_pattern = r'!\[.*?\]\((.*?)\)'
        
        def replace_image(match):
            image_path = match.group(1)
            if os.path.exists(image_path):
                media_id = self.upload_image(image_path)
                if media_id:
                    # 微信公众号图片需要使用 CDN URL
                    # 这里返回一个占位符，实际需要通过素材管理获取 URL
                    return f"![image]({media_id})"
            return match.group(0)
        
        return re.sub(image_pattern, replace_image, content)


def publish_article_to_wechat(article_id: int = None) -> bool:
    """发布文章到微信公众号的入口函数"""
    logger.info("=== 开始发布文章到微信公众号 ===")
    
    # 记录任务开始
    log_id = db.add_task_log('daily_publish', 'running', '开始发布文章')
    
    try:
        # 如果没有指定文章ID，获取最新的草稿文章
        if not article_id:
            articles = db.get_recent_articles(limit=1)
            if articles and articles[0]['status'] == 'draft':
                article_id = articles[0]['id']
        
        if not article_id:
            logger.warning("没有待发布的文章")
            db.update_task_log(log_id, 'success', '没有待发布的文章')
            return False
        
        # 发布文章
        publisher = WechatPublisher()
        success = publisher.publish_article(article_id)
        
        if success:
            logger.info("=== 文章发布成功 ===")
            db.update_task_log(log_id, 'success', '文章发布成功')
            return True
        else:
            logger.error("=== 文章发布失败 ===")
            db.update_task_log(log_id, 'failed', '文章发布失败')
            return False
            
    except Exception as e:
        logger.error(f"发布文章异常: {e}")
        db.update_task_log(log_id, 'failed', str(e))
        return False


def generate_and_publish_article() -> bool:
    """生成并发布文章的完整流程"""
    logger.info("=== 开始生成并发布文章 ===")
    
    # 1. 生成文章
    from generator.article_generator import generate_daily_article
    article = generate_daily_article()
    
    if not article:
        logger.warning("文章生成失败或没有可用歌词")
        return False
    
    # 2. 爬取配图
    from spiders.image_spider import crawl_images_for_article
    
    lyrics_data = article.get('lyrics_data', {})
    anime_name = lyrics_data.get('anime_name', '')
    anime_name_jp = lyrics_data.get('anime_name_jp')
    
    images = crawl_images_for_article(anime_name, anime_name_jp)
    
    # 3. 更新文章配图
    if images.get('cover'):
        db.update_article_wechat_ids(
            article_id=article['article_id'],
            cover_image_path=images['cover'],
            status='draft'
        )
    
    # 4. 发布到微信公众号
    return publish_article_to_wechat(article['article_id'])


if __name__ == "__main__":
    # 测试发布功能
    print("测试微信公众号发布...")
    
    # 需要先配置 AppID 和 AppSecret
    if config.WECHAT_APP_ID == "your_app_id":
        print("请先在 config.py 中配置 WECHAT_APP_ID 和 WECHAT_APP_SECRET")
    else:
        publisher = WechatPublisher()
        print(f"AppID: {publisher.app_id}")
        print("测试完成")
