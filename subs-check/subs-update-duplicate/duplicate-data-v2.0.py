import os
# python -m pip install pyyaml
#import yaml
# python -m pip install ruamel.yaml
from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import DoubleQuotedScalarString

'''功能说明
有一组数据，希望保持每行的独立性，但是又想将每行的数据合到一起整体去重，再将数据原本的位置还原回每行的位置，并覆盖写入到 result.yaml 中的 sub-urls: 下
比如
"url": "https://a.txt|https://b.txt|https://c.txt",
"url": "https://d.txt|httpx://a.txt|https://a.txt|https://e.txt",
"url": "https://f.txt|httpx://g.txt|https://b.txt",

比如 result.yaml 文件内容如下
other1:
  - '21'
  - '121'
other2:
  - '21'
  - '121'
  - '121'
  - '121'
other3:
  - '121'
  - '121'
  - '121'
sub-urls:
  - http://192.168.255.150:8001/sub_merge.txt
other4:
  - '121'
  - '121'
去重之后效果就是 result.yaml 文件中的 sub-urls: 下
other1:
  - '21'
  - '121'
other2:
  - '21'
  - '121'
  - '121'
  - '121'
other3:
  - '121'
  - '121'
  - '121'
sub-urls:
  - "https://a.txt"
  - "httpx://b.txt"
  - "https://c.txt"
  - "https://d.txt"
  - "httpx://a.txt"
  - "https://e.txt"
  - "https://f.txt"
  - "httpx://g.txt"
other4:
  - '121'
  - '121'
'''

# -------------------------------
# 第一步：定义原始数据，并提取全局去重后的 URL 列表
# 原始数据（每行遵循 "url": "内容", 格式）
# -------------------------------
data = [
'"url": "https://a.txt|https://b.txt|https://c.txt",',
'"url": "https://d.txt|httpx://a.txt|https://a.txt|https://e.txt",',
'"url": "https://f.txt|httpx://g.txt|https://b.txt",',
]

seen = set()
unique_urls = []

for line in data:
    try:
        # 假定每行格式固定为： "url": "内容",
        parts = line.split('"')
        url_str = parts[3].strip()
    except IndexError:
        print("数据格式错误：", line)
        continue

    # 用 "|" 分割出各单独 URL
    urls = url_str.split("|")
    for url in urls:
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)

# -------------------------------
# 第二步：加载 result.yaml 文件，并仅更新 sub-urls 节点
# -------------------------------

# 获取当前脚本所在目录，确保 result.yaml 在同一目录下
script_dir = os.path.dirname(os.path.abspath(__file__))
yaml_file_path = os.path.join(script_dir, "result.yaml")

# 使用 ruamel.yaml 的 round-trip 类型加载 YAML 内容，保留原有格式、顺序及注释
yaml_rt = YAML(typ='rt')
yaml_rt.preserve_quotes = True
yaml_rt.indent(mapping=2, sequence=4, offset=2)

# 加载 YAML 数据（如果文件不存在，则初始化一个空字典）
try:
    with open(yaml_file_path, "r", encoding="utf-8") as f:
        yaml_data = yaml_rt.load(f)
        if yaml_data is None:
            yaml_data = {}
except FileNotFoundError:
    print(f"文件 {yaml_file_path} 不存在，将创建一个新的文件。")
    yaml_data = {}

# 仅更新 "sub-urls" 键，使用 DoubleQuotedScalarString 确保每个 URL 都被双引号包裹
yaml_data["sub-urls"] = [DoubleQuotedScalarString(url) for url in unique_urls]

# -------------------------------
# 第三步：写回 YAML 文件
# -------------------------------
with open(yaml_file_path, "w", encoding="utf-8") as f:
    yaml_rt.dump(yaml_data, f)

print("成功更新 result.yaml 文件中的 sub-urls 节点！")
