# -*- coding: utf-8 -*-
import json

with open('analysis_temp.json', 'r', encoding='utf-8') as f:
    content = f.read()

# 策略：逐字符解析，找到每个grammar字段的字符串值，替换内部双引号为单引号
result_chars = []
i = 0
while i < len(content):
    # 检测 "grammar": " 开头
    grammar_key = '"grammar": "'
    if content[i:i+len(grammar_key)] == grammar_key:
        # 写入键名和开始引号
        result_chars.append(grammar_key)
        i += len(grammar_key)
        # 读取值直到找到结束引号（非转义）
        value_chars = []
        while i < len(content):
            c = content[i]
            if c == '\\':
                # 转义字符，原样保留
                value_chars.append(c)
                i += 1
                if i < len(content):
                    value_chars.append(content[i])
                    i += 1
            elif c == '"':
                # 结束引号
                result_chars.append(''.join(value_chars))
                result_chars.append('"')
                i += 1
                break
            else:
                # 普通字符
                value_chars.append(c)
                i += 1
    else:
        result_chars.append(content[i])
        i += 1

# 这个方法太复杂，改用简单方法：
# 重新生成 JSON，手动构建每个条目

# 先用更直接的方法：找到所有的嵌套双引号并替换
# 策略：在 JSON 字符串值内部，把 "word" 改成 'word'

import re

def fix_grammar_field(text):
    """修复grammar字段中的内部双引号"""
    # 匹配 "grammar": "..." 中的值部分
    # 使用贪婪匹配，然后从末尾找最后一个 ," 或 "\n
    
    new_text = []
    pos = 0
    grammar_prefix = '"grammar": "'
    
    while pos < len(text):
        idx = text.find(grammar_prefix, pos)
        if idx == -1:
            new_text.append(text[pos:])
            break
        
        # 保留 grammar 前面的内容
        new_text.append(text[pos:idx + len(grammar_prefix)])
        
        # 从值的开始位置扫描到结束
        val_start = idx + len(grammar_prefix)
        val_chars = []
        j = val_start
        depth = 0
        while j < len(text):
            c = text[j]
            if c == '\\':
                val_chars.append(c)
                j += 1
                if j < len(text):
                    val_chars.append(text[j])
                    j += 1
                continue
            if c == '"':
                # 这是结束引号
                break
            val_chars.append(c)
            j += 1
        
        # val_chars 里可能有未转义的双引号 -> 替换为单引号
        val_str = ''.join(val_chars)
        # 替换英文双引号为单引号（在日语语法说明中出现的引用）
        val_str = val_str.replace('"', "'")
        
        new_text.append(val_str)
        new_text.append('"')  # 结束引号
        pos = j + 1  # 跳过结束引号
    
    return ''.join(new_text)

fixed = fix_grammar_field(content)

try:
    data = json.loads(fixed)
    print(f'修复成功！共 {len(data["result"])} 条记录')
    with open('analysis_temp.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print('已保存修复后的文件')
except json.JSONDecodeError as e:
    print(f'仍有错误: {e}')
    start = max(0, e.pos - 100)
    end = min(len(fixed), e.pos + 100)
    print('错误位置附近:', repr(fixed[start:end]))
