# -*- coding: utf-8 -*-
import json, sys

with open(r'c:\Users\Admin\WorkBuddy\Claw\anime-lyrics-publisher\analysis_result.json', 'r', encoding='utf-8') as f:
    data_str = f.read()

try:
    data = json.loads(data_str)
    print("JSON 有效，result 条数:", len(data['result']))
except json.JSONDecodeError as e:
    print(f"JSON 错误: {e}")
    # 打印出错位置附近内容
    lines = data_str.split('\n')
    err_line = e.lineno - 1
    start = max(0, err_line - 2)
    end = min(len(lines), err_line + 3)
    for i in range(start, end):
        marker = " >>> " if i == err_line else "     "
        print(f"{marker}{i+1}: {lines[i]}")
