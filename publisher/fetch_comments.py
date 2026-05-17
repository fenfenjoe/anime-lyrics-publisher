# -*- coding: utf-8 -*-
"""
获取"边听歌边学日语"系列最新文章的评论 - v2
策略：freepublish 无权限时，改用草稿 media_id 反查 msg_data_id
"""

import sys, os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(__file__))

import json, sqlite3, datetime
import config
from wechat_publisher import WechatPublisher

publisher = WechatPublisher()

# ── Step 1: access_token ───────────────────────────────────────────────────
token = publisher.get_access_token()
if not token:
    print("[ERROR] 无法获取 access_token")
    sys.exit(1)
print("[OK] access_token 获取成功")

# ── Step 2: 从本地 DB 取最新一篇已发布文章的 media_id ─────────────────────
conn = sqlite3.connect(config.DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()
cur.execute("""
    SELECT ar.id, ar.article_title, ar.wechat_media_id, ar.published_at
    FROM articles ar
    WHERE ar.status = 'published' AND ar.wechat_media_id IS NOT NULL
    ORDER BY ar.published_at DESC
    LIMIT 1
""")
row = cur.fetchone()
conn.close()

if not row:
    print("[ERROR] 本地数据库中没有已发布文章记录")
    sys.exit(1)

article_title  = row['article_title']
draft_media_id = row['wechat_media_id']
print(f"\n[目标文章]")
print(f"  标题    : {article_title}")
print(f"  media_id: {draft_media_id}")
print(f"  发布时间: {row['published_at']}")

# ── Step 3: 通过草稿 media_id 查询草稿详情，获取 article_id ──────────────
# 注：草稿详情接口 /cgi-bin/draft/get 中有 article_id 字段
print(f"\n[Step 3] 查询草稿详情，获取 article_id ...")
draft_get_url = "https://api.weixin.qq.com/cgi-bin/draft/get"
resp = publisher._session.post(
    draft_get_url,
    params={"access_token": token},
    data=json.dumps({"media_id": draft_media_id}, ensure_ascii=False).encode("utf-8"),
    headers={"Content-Type": "application/json; charset=utf-8"},
    timeout=15, verify=False
)
draft_data = resp.json()
print(f"  草稿详情接口 errcode={draft_data.get('errcode')}, errmsg={draft_data.get('errmsg')}")
print(f"  完整返回: {json.dumps(draft_data, ensure_ascii=False, indent=2)[:800]}")

# ── Step 4: 尝试从群发记录中查找 msg_data_id ─────────────────────────────
print(f"\n[Step 4] 尝试通过群发消息历史查询 msg_data_id ...")
# 接口：POST /cgi-bin/message/mass/get  需要 msg_id
# 另一个接口: GET /cgi-bin/message/mass/getmasssendresult  
# 还有：使用事件推送中保存的 msg_data_id（需历史记录）

# 先试：GET 群发消息列表（仅对已认证服务号开放，但可以尝试）
list_url = "https://api.weixin.qq.com/cgi-bin/message/mass/list"
list_body = {"begin": 0, "limit": 20}
r = publisher._session.post(
    list_url,
    params={"access_token": token},
    data=json.dumps(list_body).encode("utf-8"),
    headers={"Content-Type": "application/json; charset=utf-8"},
    timeout=15, verify=False
)
list_data = r.json()
print(f"  群发列表接口 errcode={list_data.get('errcode')}, errmsg={list_data.get('errmsg')}")
if list_data.get("errcode") == 0:
    items = list_data.get("list", [])
    print(f"  共 {len(items)} 条群发记录")
    for item in items[:5]:
        print(f"    msg_id={item.get('msg_id')}  type={item.get('type')}  status={item.get('status')}")
        news = item.get("content", {}).get("news_item", [])
        for n in news[:1]:
            print(f"      title={n.get('title')}  article_id={n.get('article_id')}")
else:
    print(f"  完整返回: {json.dumps(list_data, ensure_ascii=False)}")

# ── Step 5: 直接尝试用 draft media_id 当作 msg_data_id 调用评论接口 ────────
# （微信有时草稿发布后 media_id == msg_data_id，值得一试）
print(f"\n[Step 5] 直接用 draft media_id 尝试评论接口 ...")
comment_url = "https://api.weixin.qq.com/cgi-bin/comment/list"
comment_body = {
    "msg_data_id": draft_media_id,
    "index": 0,
    "begin": 0,
    "count": 50,
    "type": 0
}
c_resp = publisher._session.post(
    comment_url,
    params={"access_token": token},
    data=json.dumps(comment_body, ensure_ascii=False).encode("utf-8"),
    headers={"Content-Type": "application/json; charset=utf-8"},
    timeout=15, verify=False
)
c_data = c_resp.json()
print(f"  评论接口 errcode={c_data.get('errcode')}, errmsg={c_data.get('errmsg')}")
if c_data.get("errcode") == 0:
    comments = c_data.get("comment", [])
    print(f"  共 {len(comments)} 条评论")
    for i, c in enumerate(comments, 1):
        ts = datetime.datetime.fromtimestamp(c.get("create_time", 0)).strftime("%m-%d %H:%M")
        print(f"    {i}. [{ts}] {c.get('content', '')}")
else:
    print(f"  完整返回: {json.dumps(c_data, ensure_ascii=False)}")

print("\n[Done]")
