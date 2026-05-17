import sys, os
sys.path.insert(0, r'E:\workspace\workbuddy\anime-lyrics-publisher')
os.chdir(r'E:\workspace\workbuddy\anime-lyrics-publisher')
import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

from image_spider import crawl_images_for_article

# 爬取胆大党图片
result = crawl_images_for_article(
    anime_name='胆大党',
    name_jp='ダンダダン',
    article_image_count=12,
    song_name='オトノケ',
    singer='Creepy Nuts',
)
print('封面:', result['cover'])
print('配图:', result['article_images'])
print('配图数量:', len(result['article_images']))
