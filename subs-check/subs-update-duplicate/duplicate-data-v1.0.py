'''功能说明
现在有一组数据，我希望保持每行的独立性，但是又想将每行的数据合到一起整体去重，再将数据原本的位置还原回每行的位置
比如
"url": "https://a.txt|https://b.txt|https://c.txt",
"url": "https://d.txt|httpx://a.txt|https://a.txt|https://e.txt",
"url": "https://f.txt|httpx://g.txt|https://b.txt",
去重之后效果就是
"url": "https://a.txt|httpx://b.txt|https://c.txt",
"url": "https://d.txt|httpx://a.txt|https://e.txt",
"url": "https://f.txt|httpx://g.txt",
'''

# 示例输入数据（注意末尾的逗号）
data = [
'"url": "https://a.txt|https://b.txt|https://c.txt",',
'"url": "https://d.txt|httpx://a.txt|https://a.txt|https://e.txt",',
'"url": "https://f.txt|httpx://g.txt|https://b.txt",',
]

# 用于记录已经出现过的 URL（全局去重）
seen = set()

results = []
for line in data:
    # 根据输入格式，利用双引号进行拆分，
    # 例如：line.split('"') 得到的列表第4个元素（索引3）是 URL 字符串
    try:
        parts = line.split('"')
        inner = parts[3].strip()  # 提取内部 URL 字符串
    except IndexError:
        print("数据格式错误：", line)
        continue

    # 按 "|" 分割出每个 URL
    urls = inner.split("|")
    filtered = []
    
    # 按顺序检查每个 URL，如果全局中还未出现，则保留并添加到 seen 集合中
    for url in urls:
        if url not in seen:
            filtered.append(url)
            seen.add(url)
    
    # 按原始格式重组该行，同时保持末尾的逗号
    new_line = f'"url": "{"|".join(filtered)}",'
    results.append(new_line)

# 输出结果
for r in results:
    print(r)
