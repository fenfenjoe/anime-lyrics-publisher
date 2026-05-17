import json

with open(r'data/analysis_result_hotaru.json', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace Chinese curly double quotes with book-title marks (safe in JSON)
content_fixed = content.replace('\u201c', '\u300e').replace('\u201d', '\u300f')

try:
    data = json.loads(content_fixed)
    print('Parsed OK, result count:', len(data['result']))
    with open(r'data/analysis_result_hotaru.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print('Written successfully')
except Exception as e:
    print('Error:', e)
    # Find problematic line
    lines = content_fixed.split('\n')
    for i, line in enumerate(lines):
        if '"' in line or '"' in line:
            print(f'Line {i+1}: {line[:100]}')
