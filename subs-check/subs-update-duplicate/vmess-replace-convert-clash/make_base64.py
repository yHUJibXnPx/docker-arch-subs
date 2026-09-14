"""
subs-fix.py
===========
读取 vmess.txt，对支持 CFNAT 的节点（WS 传输，走 CF CDN）追加一个替换了
host:port 的副本，输出 vmess_all.txt 和 vmess_all_base64.txt。

支持协议：
  vmess://  —— net=ws 时追加 CFNAT 副本
  vless://  —— type=ws 时追加 CFNAT 副本（host 参数/SNI 保留）
  trojan:// —— type=ws 时追加 CFNAT 副本（host 参数/SNI 保留）
  其余协议  —— 原样保留，不追加副本

不适合 CFNAT（直接跳过不追加副本）：
  vless+reality、hysteria2、tuic、ss、ssr 等直连协议
"""

import base64
import json
import sys
from pathlib import Path
from urllib.parse import (
    urlparse, parse_qs, urlencode, urlunparse,
    quote, unquote,
)

# ── 配置区（按需修改） ────────────────────────────────────────────
CFNAT_HOST   = "192.168.255.252"   # CFNAT 本地监听地址
CFNAT_PORT   = "1234"              # CFNAT 本地监听端口
CFNAT_SUFFIX = "-cfnat"            # 追加节点名后缀
INPUT_FILE   = Path("vmess.txt")
OUTPUT_FILE  = Path("vmess_all.txt")
OUTPUT_B64   = Path("vmess_all_base64.txt")
# ─────────────────────────────────────────────────────────────────


# ── vmess 编解码 ──────────────────────────────────────────────────

def decode_vmess(link: str) -> dict:
    data = link[len("vmess://"):]
    data += "=" * (-len(data) % 4)
    return json.loads(base64.b64decode(data).decode("utf-8"))


def encode_vmess(node: dict) -> str:
    raw = json.dumps(node, ensure_ascii=False, separators=(",", ":"))
    return "vmess://" + base64.b64encode(raw.encode()).decode()


# ── URI 协议（vless / trojan）工具 ───────────────────────────────

def _get_transport(params: dict) -> str:
    """从查询参数中读取传输类型，兼容 type= 和 network= 两种写法"""
    return (params.get("type", [""])[0]
            or params.get("network", [""])[0]).lower()


def is_ws_uri(params: dict) -> bool:
    return _get_transport(params) == "ws"


def replace_uri_address(link: str) -> str:
    """
    将 vless:// / trojan:// 链接中的 host:port 替换为 CFNAT 地址，
    保留 userinfo（uuid/密码）、所有查询参数（含 SNI 的 host=）和路径。
    """
    parsed = urlparse(link)

    # 节点名（fragment）
    old_name = unquote(parsed.fragment) if parsed.fragment else ""
    new_name = old_name + CFNAT_SUFFIX

    # 重建 netloc：userinfo 不变，只换 host:port
    userinfo = parsed.username or ""
    if parsed.password:
        userinfo = f"{userinfo}:{parsed.password}"
    new_netloc = f"{userinfo}@{CFNAT_HOST}:{CFNAT_PORT}"

    new_parsed = parsed._replace(
        netloc=new_netloc,
        fragment=quote(new_name, safe=""),
    )
    return urlunparse(new_parsed)


# ── 单条链接处理 ─────────────────────────────────────────────────

def process_link(link: str) -> list[str]:
    """
    返回处理后的链接列表：
      - 原始节点总是在第一位
      - 若协议+传输支持 CFNAT，追加一个替换地址的副本
    """

    # ── vmess ────────────────────────────────────────────────────
    if link.startswith("vmess://"):
        try:
            node = decode_vmess(link)
        except Exception as e:
            print(f"  [WARN] 无效 vmess，跳过: {e}", file=sys.stderr)
            return []

        result = [encode_vmess(node)]

        if node.get("net", "").lower() == "ws":
            cfnat_node = {
                **node,
                "add": CFNAT_HOST,
                "port": CFNAT_PORT,
                "ps": node.get("ps", "vmess") + CFNAT_SUFFIX,
            }
            result.append(encode_vmess(cfnat_node))

        return result

    # ── vless / trojan ───────────────────────────────────────────
    if link.startswith("vless://") or link.startswith("trojan://"):
        try:
            parsed = urlparse(link)
            params = parse_qs(parsed.query)
        except Exception as e:
            print(f"  [WARN] 无效 URI，保留原样: {e}", file=sys.stderr)
            return [link]

        result = [link]

        if is_ws_uri(params):
            result.append(replace_uri_address(link))

        return result

    # ── 其他协议原样保留 ─────────────────────────────────────────
    return [link]


# ── 主流程 ───────────────────────────────────────────────────────

def main():
    if not INPUT_FILE.exists():
        sys.exit(f"[ERROR] 找不到输入文件: {INPUT_FILE}")

    raw_links = [
        line.strip()
        for line in INPUT_FILE.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    all_links: list[str] = []
    counts = {"vmess_ws": 0, "vless_ws": 0, "trojan_ws": 0,
              "other": 0, "skipped": 0}

    for link in raw_links:
        processed = process_link(link)

        if not processed:
            counts["skipped"] += 1
            continue

        all_links.extend(processed)

        # 统计追加了多少 CFNAT 副本
        added = len(processed) - 1
        if added:
            if link.startswith("vmess://"):
                counts["vmess_ws"] += 1
            elif link.startswith("vless://"):
                counts["vless_ws"] += 1
            elif link.startswith("trojan://"):
                counts["trojan_ws"] += 1
        else:
            counts["other"] += 1

    # 输出纯文本
    content = "\n".join(all_links)
    OUTPUT_FILE.write_text(content, encoding="utf-8")

    # 输出 base64
    b64 = base64.b64encode(content.encode("utf-8")).decode("utf-8")
    OUTPUT_B64.write_text(b64, encoding="utf-8")

    # 汇报
    print(f"\n✓ 处理完成")
    print(f"   输入节点数 : {len(raw_links)}")
    print(f"   输出节点数 : {len(all_links)}")
    print(f"   追加 CFNAT 副本:")
    print(f"     vmess-ws  : {counts['vmess_ws']}")
    print(f"     vless-ws  : {counts['vless_ws']}")
    print(f"     trojan-ws : {counts['trojan_ws']}")
    print(f"   跳过无效   : {counts['skipped']}")
    print(f"   原样保留   : {counts['other']}")
    print(f"\n   → {OUTPUT_FILE}")
    print(f"   → {OUTPUT_B64}")


if __name__ == "__main__":
    main()