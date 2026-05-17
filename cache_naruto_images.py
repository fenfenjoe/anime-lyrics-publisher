#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为《火影忍者疾风传》缓存大量图片
直接使用 MAL ID 1735 (Naruto: Shippuden) 获取图片，支持分页
"""

import sys
import os
import time
import requests
import logging
import random
from urllib.parse import quote

# 添加项目路径
sys.path.insert(0, r'E:\workspace\workbuddy\anime-lyrics-publisher')

import config
import database
from image_spider import ImageCache, ImageSpider, _compute_ahash, _hash_str, logger

# 配置日志
logging.basicConfig(level=getattr(logging, config.LOG_LEVEL))


def get_mal_pictures_paginated(mal_id: int, max_pages: int = 10) -> list:
    """
    从 MAL API 获取动画的所有剧照，支持分页
    """
    image_urls = []
    
    for page in range(1, max_pages + 1):
        try:
            url = f"https://api.jikan.moe/v4/anime/{mal_id}/pictures?page={page}"
            logger.info(f"MAL API 获取第 {page} 页剧照: {url}")
            
            headers = {'User-Agent': random.choice([
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            ])}
            
            resp = requests.get(url, headers=headers, timeout=15, verify=False)
            
            if resp.status_code != 200:
                logger.warning(f"第 {page} 页请求失败: {resp.status_code}")
                break
            
            data = resp.json()
            pictures = data.get('data', [])
            
            if not pictures:
                logger.info(f"第 {page} 页无更多图片，停止")
                break
            
            for pic in pictures:
                jpg_data = pic.get('jpg', {})
                if jpg_data.get('large_image_url'):
                    image_urls.append(jpg_data['large_image_url'])
                elif jpg_data.get('image_url'):
                    image_urls.append(jpg_data['image_url'])
            
            logger.info(f"第 {page} 页获取到 {len(pictures)} 张图片，累计 {len(image_urls)} 张")
            
            # 如果返回的图片数量少于 20，说明是最后一页
            if len(pictures) < 20:
                break
            
            time.sleep(1)  # 避免请求过快
            
        except Exception as e:
            logger.error(f"获取第 {page} 页失败: {e}")
            break
    
    return image_urls


def cache_naruto_images(target_count: int = 80):
    """
    为火影忍者疾风传缓存大量图片
    
    :param target_count: 目标图片数量（50-100张）
    """
    anime_name = "火影忍者疾风传"
    mal_id = 1735  # Naruto: Shippuuden 的 MAL ID
    
    logger.info(f"=== 开始为《{anime_name}》缓存图片 ===")
    logger.info(f"MAL ID: {mal_id} (Naruto: Shippuuden)")
    logger.info(f"目标数量: {target_count} 张")
    
    spider = ImageSpider()
    
    # Step 1: 获取动画详细信息
    logger.info(f"正在获取 MAL API 数据: anime/{mal_id}")
    headers = {'User-Agent': random.choice([
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    ])}
    
    try:
        resp = requests.get(f"https://api.jikan.moe/v4/anime/{mal_id}", 
                           headers=headers, timeout=15, verify=False)
        if resp.status_code == 200:
            data = resp.json()
            anime_data = data.get('data', {})
            title = anime_data.get('title', '')
            title_jp = anime_data.get('title_japanese', '')
            logger.info(f"找到动画: {title} (ID: {mal_id})")
            logger.info(f"日文标题: {title_jp}")
        else:
            logger.error(f"MAL API 请求失败: {resp.status_code}")
            return False
    except Exception as e:
        logger.error(f"获取动画数据失败: {e}")
        return False
    
    # Step 2: 获取封面图 URL
    logger.info("正在获取封面图...")
    images = anime_data.get('images', {})
    jpg_data = images.get('jpg', {})
    
    all_urls = []
    
    # 封面大图
    if jpg_data.get('large_image_url'):
        all_urls.append(jpg_data['large_image_url'])
        logger.info(f"封面大图: {jpg_data['large_image_url'][:80]}")
    
    # 封面标准图
    if jpg_data.get('image_url'):
        all_urls.append(jpg_data['image_url'])
        logger.info(f"封面标准图: {jpg_data['image_url'][:80]}")
    
    # Step 3: 获取更多剧照 (分页获取)
    logger.info(f"正在获取动画剧照 (MAL ID: {mal_id})...")
    
    # 获取前 10 页剧照
    extra_urls = get_mal_pictures_paginated(mal_id, max_pages=10)
    
    # 去重添加
    for url in extra_urls:
        if url not in all_urls:
            all_urls.append(url)
    
    logger.info(f"共获取到 {len(all_urls)} 个唯一图片 URL")
    
    # Step 4: 下载图片到缓存
    cache = ImageCache()
    folder = cache._anime_folder(anime_name)
    os.makedirs(folder, exist_ok=True)
    
    manifest = cache._load_manifest(anime_name)
    existing_urls = {img['url'] for img in manifest.get('images', []) if img.get('url')}
    
    new_count = 0
    for i, url in enumerate(all_urls):
        if new_count >= target_count:
            logger.info(f"已达到目标数量 {target_count} 张，停止下载")
            break
        
        if url in existing_urls:
            logger.debug(f"跳过已缓存的图片: {url[:80]}")
            continue
        
        filename = f"img_{i+1:04d}_{random.randint(1000, 9999)}.jpg"
        filepath = os.path.join(folder, filename)
        
        logger.info(f"下载图片 [{new_count + 1}/{target_count}]: {url[:80]}...")
        
        path = spider.download_image(url, filename=filename, save_dir=folder)
        if not path:
            logger.warning(f"下载失败: {url[:80]}")
            continue
        
        # 计算哈希值
        h = _compute_ahash(path)
        h_str = _hash_str(h)
        
        # 添加到 manifest
        img_entry = {
            'filename': os.path.basename(path),
            'url': url,
            'path': path,
            'hash': h_str or '0',
        }
        manifest['images'].append(img_entry)
        existing_urls.add(url)
        
        new_count += 1
        logger.info(f"✓ 成功下载: {os.path.basename(path)} (总计: {new_count}/{target_count})")
        
        # 每下载 10 张保存一次 manifest
        if new_count % 10 == 0:
            cache._save_manifest(anime_name, manifest)
            logger.info(f"已保存 manifest (累计 {new_count} 张)")
        
        time.sleep(0.5)  # 避免请求过快
    
    # 最终保存 manifest
    cache._save_manifest(anime_name, manifest)
    
    logger.info(f"=== 缓存完成 ===")
    logger.info(f"新增图片: {new_count} 张")
    logger.info(f"缓存总计: {len(manifest['images'])} 张")
    logger.info(f"缓存目录: {folder}")
    
    return True


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='为火影忍者疾风传缓存图片')
    parser.add_argument('-n', '--number', type=int, default=80,
                        help='目标图片数量 (默认: 80)')
    
    args = parser.parse_args()
    
    # 确保目标数量在合理范围内
    target = max(50, min(100, args.number))
    
    print(f"开始为《火影忍者疾风传》缓存 {target} 张图片...")
    print(f"使用 MAL ID: 1735 (Naruto: Shippuuden)")
    print()
    
    success = cache_naruto_images(target)
    
    if success:
        print()
        print("✅ 图片缓存完成！")
        print(f"请查看缓存目录: data/anime_images/火影忍者疾风传")
    else:
        print()
        print("❌ 图片缓存失败，请检查日志")
        sys.exit(1)
