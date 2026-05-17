#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
图片验证工具 - 列出下载的图片，方便手动验证
"""
import os
import sys
from pathlib import Path
from PIL import Image

def verify_images(image_dir: str):
    """扫描并验证图片目录中的图片"""
    image_dir = Path(image_dir)
    if not image_dir.exists():
        print(f"❌ 目录不存在: {image_dir}")
        return
    
    # 收集所有图片
    images = list(image_dir.glob("*.jpg")) + list(image_dir.glob("*.png"))
    images = sorted(images, key=lambda x: x.stat().st_mtime, reverse=True)
    
    if not images:
        print(f"❌ 目录中没有找到图片: {image_dir}")
        return
    
    print("=" * 70)
    print(f"图片验证报告 - 共找到 {len(images)} 张图片")
    print("=" * 70)
    
    mal_count = 0
    bing_count = 0
    cover_count = 0
    
    for i, img_path in enumerate(images, 1):
        # 判断图片类型
        img_type = "未知"
        if "cover" in img_path.name:
            img_type = "🖼️ 封面图"
            cover_count += 1
        elif "mal_" in img_path.name:
            img_type = "🎌 MAL官方图"
            mal_count += 1
        else:
            img_type = "🔍 Bing搜索图"
            bing_count += 1
        
        # 获取文件信息
        file_size = img_path.stat().st_size / 1024  # KB
        
        # 获取图片尺寸
        try:
            img = Image.open(img_path)
            width, height = img.size
            img_info = f"{width}x{height}, {img.mode}"
        except:
            img_info = "无法读取"
        
        print(f"\n[{i}] {img_type}")
        print(f"    文件: {img_path.name}")
        print(f"    路径: {img_path.absolute()}")
        print(f"    大小: {file_size:.1f} KB")
        print(f"    尺寸: {img_info}")
    
    print("\n" + "=" * 70)
    print(f"统计: MAL官方图={mal_count}, Bing搜索图={bing_count}, 封面图={cover_count}")
    print("=" * 70)
    
    # 生成简单的HTML预览
    generate_simple_html(images, "image_preview.html")
    
    print("\n💡 验证建议:")
    print("  1. 查看 MAL官方图（mal_ 开头）是否与动画相关")
    print("  2. 如果 MAL 图片质量更高，说明集成成功")
    print("  3. 用浏览器打开 image_preview.html 查看图片")
    print("=" * 70)

def generate_simple_html(images, output_file):
    """生成简单的HTML预览页面"""
    html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>图片预览</title>
    <style>
        body { font-family: Arial; max-width: 1200px; margin: 20px auto; padding: 20px; }
        .img-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 15px; }
        .img-card { border: 1px solid #ddd; padding: 10px; border-radius: 5px; }
        .img-card img { width: 100%; height: 200px; object-fit: cover; }
        .cover { border-left: 4px solid #4CAF50; }
        .mal { border-left: 4px solid #2196F3; }
        .bing { border-left: 4px solid #FF9800; }
    </style>
</head>
<body>
    <h1>📸 图片预览</h1>
    <div class="img-grid">
"""
    
    for img_path in images:
        css_class = "bing"
        if "cover" in img_path.name:
            css_class = "cover"
        elif "mal_" in img_path.name:
            css_class = "mal"
        
        # 使用相对路径
        try:
            rel_path = os.path.relpath(img_path, Path(output_file).parent)
            rel_path = rel_path.replace("\\", "/")
        except:
            rel_path = str(img_path)
        
        html += f'        <div class="img-card {css_class}">\n'
        html += f'            <img src="{rel_path}" alt="{img_path.name}">\n'
        html += f'            <p>{img_path.name}</p>\n'
        html += f'        </div>\n'
    
    html += """    </div>
</body>
</html>"""
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"\n✅ HTML 预览已生成: {Path(output_file).absolute()}")
    print(f"   请在浏览器中打开查看图片")

if __name__ == "__main__":
    image_dir = "data/images"
    if len(sys.argv) > 1:
        image_dir = sys.argv[1]
    
    verify_images(image_dir)
