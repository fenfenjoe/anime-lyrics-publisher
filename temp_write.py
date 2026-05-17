import sys
import json

sys.path.insert(0, r'c:\Users\Admin\WorkBuddy\Claw\anime-lyrics-publisher')
from ai_analyzer import write_result_to_file

with open(r'c:\Users\Admin\WorkBuddy\Claw\anime-lyrics-publisher\temp_result.json', encoding='utf-8') as f:
    data = json.load(f)

json_str = json.dumps(data, ensure_ascii=False, indent=2)
write_result_to_file(json_str)
