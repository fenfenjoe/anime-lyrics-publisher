import sys
sys.path.insert(0, '.')
import logging
import os
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')

from image_spider import ImageCache, crawl_images_for_article
import database

anime_name = 'Spy x Family'
name_jp = 'スパイファミリー'

cache = ImageCache()

print('=' * 60)
print('Step 1: 清空缓存（干净测试）')
print('=' * 60)
cache.clear_cache(anime_name)

print()
print('=' * 60)
print('Step 2: crawl_and_cache 爬取 15 张（修复后：无视觉去重）')
print('=' * 60)
count = cache.crawl_and_cache(anime_name, name_jp=name_jp, batch_size=15)
stats = cache.get_cache_stats(anime_name)
print(f'新增: {count} 张, 缓存统计: {stats}')
assert stats['total'] >= 10, f'缓存数量不足: {stats}'

print()
print('=' * 60)
print('Step 3: 第1次取图（3张）')
print('=' * 60)
imgs1 = cache.get_images_for_article(anime_name, name_jp=name_jp, count=3)
print(f'取到 {len(imgs1)} 张: {[os.path.basename(p) for p in imgs1]}')
assert len(imgs1) == 3, f'应取到3张，实际{len(imgs1)}张'
stats = cache.get_cache_stats(anime_name)
print(f'取后统计: {stats}')
assert stats['unused'] == stats['total'] - 3, '未使用数应减少3张'

print()
print('=' * 60)
print('Step 4: 第2次取图（3张，应触发补仓）')
print('=' * 60)
imgs2 = cache.get_images_for_article(anime_name, name_jp=name_jp, count=3)
print(f'取到 {len(imgs2)} 张: {[os.path.basename(p) for p in imgs2]}')
assert len(imgs2) == 3, f'应取到3张，实际{len(imgs2)}张'
# 验证不重复
all_paths = set(os.path.basename(p) for p in imgs1 + imgs2)
assert len(all_paths) == 6, f'两次取图应有6个不同文件，实际{len(all_paths)}个'
print(f'两次取图合并去重: {len(all_paths)} 个 ✅')

print()
print('=' * 60)
print('Step 5: 第3次取图（触发第2次补仓）')
print('=' * 60)
stats_before = cache.get_cache_stats(anime_name)
print(f'取前统计: {stats_before}')
imgs3 = cache.get_images_for_article(anime_name, name_jp=name_jp, count=3)
print(f'取到 {len(imgs3)} 张: {[os.path.basename(p) for p in imgs3]}')
assert len(imgs3) == 3, f'应取到3张，实际{len(imgs3)}张'

print()
print('=' * 60)
print('Step 6: 测试 crawl_images_for_article 完整入口')
print('=' * 60)
result = crawl_images_for_article(anime_name, name_jp=name_jp, article_image_count=3)
print(f'封面: {os.path.basename(result["cover"]) if result["cover"] else "无"}')
print(f'配图: {len(result["article_images"])} 张')
for p in result['article_images']:
    print(f'  {os.path.basename(p)}')

print()
print('=' * 60)
print('✅ 所有测试通过！')
print('=' * 60)
