# -*- coding: utf-8 -*-
"""
独立图片爬虫测试脚本 - 测试 MAL API 集成效果
"""
import sys
import logging
import os
from PIL import Image
from image_spider import crawl_images_for_article, ImageSpider

# 配置日志 - 显示详细信息
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def verify_image_relevance(img_path: str, anime_name: str) -> dict:
    """验证图片的基本信息（尺寸、文件大小等）"""
    if not os.path.exists(img_path):
        return {"valid": False, "reason": "文件不存在"}
    
    try:
        file_size = os.path.getsize(img_path)
        img = Image.open(img_path)
        width, height = img.size
        
        # 基本质量检查
        checks = {
            "file_size_kb": round(file_size / 1024, 1),
            "width": width,
            "height": height,
            "aspect_ratio": round(width / height, 2),
            "mode": img.mode
        }
        
        # 质量评估
        quality_ok = True
        reasons = []
        
        if file_size < 10 * 1024:  # 小于10KB
            quality_ok = False
            reasons.append(f"文件过小({checks['file_size_kb']}KB)")
        
        if width < 300 or height < 300:
            quality_ok = False
            reasons.append(f"分辨率过低({width}x{height})")
        
        if not (0.5 < checks['aspect_ratio'] < 3.0):
            quality_ok = False
            reasons.append(f"长宽比异常({checks['aspect_ratio']})")
        
        checks["valid"] = quality_ok
        checks["reasons"] = reasons if reasons else ["OK"]
        
        return checks
        
    except Exception as e:
        return {"valid": False, "reason": str(e)}

def test_anime_images(anime_name, name_jp=None, song_name=None, singer=None, count=3):
    """测试指定动画的图片爬取效果"""
    print(f"\n{'='*70}")
    print(f"测试动画: {anime_name} ({name_jp or '无日文名'})")
    print(f"歌曲: {song_name or '无'} / 歌手: {singer or '无'}")
    print(f"目标配图数量: {count}")
    print(f"{'='*70}\n")
    
    result = crawl_images_for_article(
        anime_name=anime_name,
        name_jp=name_jp,
        article_image_count=count,
        song_name=song_name,
        singer=singer
    )
    
    print(f"\n封面图: {result['cover']}")
    if result['cover'] and os.path.exists(result['cover']):
        info = verify_image_relevance(result['cover'], anime_name)
        print(f"   尺寸: {info['width']}x{info['height']}, 大小: {info['file_size_kb']}KB")
        status = '合格' if info['valid'] else '不合格'
        print(f"   质量: {status} ({', '.join(info['reasons'])})")
    
    print(f"\n文章配图数量: {len(result['article_images'])}")
    for i, img in enumerate(result['article_images'], 1):
        print(f"\n   [{i}] {img}")
        if os.path.exists(img):
            info = verify_image_relevance(img, anime_name)
            print(f"      尺寸: {info['width']}x{info['height']}, 大小: {info['file_size_kb']}KB")
            status = '合格' if info['valid'] else '不合格'
            print(f"      质量: {status} ({', '.join(info['reasons'])})")
        else:
            print(f"      文件不存在")
    
    return result

if __name__ == "__main__":
    print("\n" + "="*70)
    print("开始测试改进后的图片爬虫 (MAL API + Bing 后备)")
    print("="*70)
    
    # 测试用例1: Fate/Zero (有日文名，热门动画)
    test_anime_images(
        anime_name="Fate/Zero",
        name_jp="Fate/Zero",
        song_name="oath sign",
        singer="LiSA",
        count=3
    )
    
    # 测试用例2: 龙珠Z (有日文名，经典动画)
    test_anime_images(
        anime_name="龙珠Z",
        name_jp="ドラゴンボールZ",
        song_name="CHA-LA HEAD-CHA-LA",
        singer="影山ヒロノブ",
        count=3
    )
    
    # 测试用例3: 王者天下 (只有中文名)
    test_anime_images(
        anime_name="王者天下",
        name_jp=None,
        song_name=None,
        singer=None,
        count=2
    )
    
    # 测试用例4: 进击的巨人 (热门动画，测试MAL API)
    test_anime_images(
        anime_name="进击的巨人",
        name_jp="進撃の巨人",
        song_name="紅蓮の弓矢",
        singer="Linked Horizon",
        count=3
    )
    
    print("\n\n" + "="*70)
    print("所有测试完成！")
    print("请检查输出的图片路径，手动验证图片是否与动画相关。")
    print("如果图片质量满意，说明 MAL API 集成成功。")
    print("="*70 + "\n")
