"""手动完成胆大党文章发布的脚本"""
import sys, os, json, sqlite3
sys.path.insert(0, r'E:\workspace\workbuddy\anime-lyrics-publisher')
os.chdir(r'E:\workspace\workbuddy\anime-lyrics-publisher')

import config, database, logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# ── 1. 构建 cache_manifest.json ──────────────────────
cache_dir = r'E:\workspace\workbuddy\anime_lyrics_publisher\data\anime_images\胆大党'
cache_dir = r'E:\workspace\workbuddy\anime-lyrics-publisher\data\anime_images\胆大党'
manifest_path = os.path.join(cache_dir, 'cache_manifest.json')

# 收集已下载的图片
import uuid
from image_spider import _compute_ahash, _hash_str

image_files = [f for f in os.listdir(cache_dir) if f.endswith('.jpg')]
images = []
for fname in image_files:
    fpath = os.path.join(cache_dir, fname)
    h = _compute_ahash(fpath)
    images.append({
        'filename': fname,
        'url': '',  # 未知URL（下载时中断）
        'path': fpath,
        'hash': _hash_str(h) if h else '0'
    })

manifest = {'version': 1, 'anime_name': '胆大党', 'images': images}
with open(manifest_path, 'w', encoding='utf-8') as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)
print(f'已写入 manifest，共 {len(images)} 张图片')

# ── 2. 标记这些图片为未使用 ─────────────────────────
# 清空 used_anime_images 表中胆大党的记录
db = database.db
with db.get_connection() as conn:
    conn.execute("DELETE FROM used_anime_images WHERE anime_name=?", ('胆大党',))
print('已清空 used_anime_images 记录')
