import sys
import json
sys.path.insert(0, r"E:\workspace\workbuddy\anime-lyrics-publisher")
from ai_analyzer import write_result_to_file

with open(r"E:\workspace\workbuddy\anime-lyrics-publisher\rocks_analysis.json", encoding="utf-8") as f:
    data = json.load(f)

write_result_to_file(json.dumps(data, ensure_ascii=False))
