# -*- coding: utf-8 -*-
# 临时脚本：将分析结果写入 data/analysis_result.json
import sys
import json
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_analyzer import write_result_to_file

# 读取分析结果（从文件读取，避免引号问题）
result_file = 'data/analysis_temp.json'
if os.path.exists(result_file):
    with open(result_file, 'r', encoding='utf-8') as f:
        result_data = json.load(f)
    write_result_to_file(json.dumps(result_data, ensure_ascii=False))
    print(f"✅ 分析结果已写入")
    print(f"✅ 共 {len(result_data.get('result', []))} 句")
else:
    print(f"❌ 结果文件不存在: {result_file}")
    print("请先创建 analysis_temp.json")
