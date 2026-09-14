#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import base64
import json
import os
import re
from urllib.parse import quote, urlencode
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from ruamel.yaml import YAML

# ========== Config / Debug toggles ==========
DEBUG_GITHUB_FAIL = False              # 打开后会打印无法解析的原始内联块（默认关）
DEBUG_GITHUB_FAIL_TO_FILE = False      # 是否把失败块追加到文件（默认关）
DEBUG_GITHUB_FAIL_FILE = "gh_failed_blocks.log"

# ========== Constants ==========
# All supported URI schemes for parsing plaintext formats
SUPPORTED_SCHEMES = (
    'ss://', 'ssr://', 'vmess://', 'vless://', 'trojan://', 'trojan-go://',
    'http://', 'https://', 'socks4://', 'socks5://', 'naive://', 'ssh://',
    'brook://', 'gost://', 'kcptun://', 'hysteria://', 'hysteria2://',
    'wg://', 'openvpn://', 'data:application/wireguard;base64,',
    'data:application/x-openvpn-profile;base64,'
)

def log(msg):
    """通用日志打印函数"""
    print(msg)

# ========== requests session with retry/backoff ==========
session = requests.Session()
retries = Retry(total=3, backoff_factor=0.8, status_forcelist=(429, 500, 502, 503, 504))
session.mount("http://", HTTPAdapter(max_retries=retries))
session.mount("https://", HTTPAdapter(max_retries=retries))

def fetch_url(url):
    """获取指定 URL 的内容"""
    try:
        resp = session.get(url, timeout=(5, 20), headers={"User-Agent": "sub-merge/1.0"})
        resp.raise_for_status()
        # 使用 resp.content.decode('utf-8', errors='ignore') 避免 BOM 头和编码问题
        return resp.content.decode('utf-8', errors='ignore')
    except Exception as e:
        log(f"[错误] 请求失败: {url} -> {e}")
        return None

# ========== Base64 helpers ==========
def b64_decode_any(s: str) -> str | None:
    """尝试用标准和 URL-safe 两种方式解码 Base64"""
    s = s.strip()
    def pad(x): return x + "=" * (-len(x) % 4)
    for decoder in (base64.b64decode, base64.urlsafe_b64decode):
        try:
            return decoder(pad(s)).decode("utf-8", errors="ignore")
        except Exception:
            continue
    return None

# ========== Balanced inline extractor (generic) ==========
# (这部分函数来自原始代码，用于处理不规范的 YAML 文件，保持不变)
def find_inline_json_candidates_balanced(text: str):
    candidates, i, n = [], 0, len(text)
    while i < n:
        if text.startswith("- {", i):
            start, i, brace_depth, in_string, esc, j = i, i + 2, 0, False, False, i + 2
            if j < n and text[j] == "{":
                brace_depth, j = 1, j + 1
                while j < n and brace_depth > 0:
                    ch = text[j]
                    if in_string:
                        if esc:
                            esc = False
                        elif ch == "\\":
                            esc = True
                        elif ch == '"':
                            in_string = False
                    else:
                        if ch == '"':
                            in_string = True
                        elif ch == "{":
                            brace_depth += 1
                        elif ch == "}":
                            brace_depth -= 1
                    j += 1
                candidates.append(text[start:j])
                i = j
                continue
        i += 1
    return candidates

def parse_json_blocks_to_proxies(candidates):
    proxies = []
    for block in candidates:
        json_like = block.lstrip("-").strip()
        obj = None
        candidate = json_like.replace("'", '"')
        try:
            obj = json.loads(candidate)
        except Exception:
            pass
        if obj is None:
            fixed_keys = re.sub(r'(\b[a-zA-Z0-9_\-]+)\s*:', r'"\1":', candidate)
            try:
                obj = json.loads(fixed_keys)
            except Exception:
                pass
        if obj is None:
            fixed_vals = re.sub(r'(:\s*)([A-Za-z0-9._:-]+)(\s*[,\}])', r'\1"\2"\3', fixed_keys)
            try:
                obj = json.loads(fixed_vals)
            except Exception:
                continue
        if "id" in obj and "uuid" not in obj:
            obj["uuid"] = obj.pop("id")
        if "method" in obj and "cipher" not in obj:
            obj["cipher"] = obj.pop("method")
        try:
            port = int(obj.get("port", 0))
            if port <= 0 or port > 65535:
                continue
            obj["port"] = port
        except Exception:
            continue
        if not obj.get("server"):
            continue
        t = obj.get("type")
        if t not in ("ss", "ssr", "trojan", "vmess", "vless", "http", "https", "socks5", "hysteria", "hysteria2"):
            if obj.get("uuid"):
                obj["type"] = "vmess"
            elif obj.get("cipher") and obj.get("password"):
                obj["type"] = "ss"
            else:
                continue
        proxies.append(obj)
    return proxies

# ========== Inline block stateful parser (robust) ==========
# (这部分函数来自原始代码，用于处理不规范的 YAML 文件，保持不变)
def parse_inline_block_to_dict(raw_block: str) -> dict | None:
    s = raw_block.strip()
    if not s.startswith("{"): s = "{" + s
    if not s.endswith("}"): s = s + "}"
    i, n, result = 1, len(s), {}
    while i < n - 1:
        while i < n - 1 and s[i] in " \t\r\n,": i += 1
        if i >= n - 1: break
        if s[i] == '"':
            i += 1; key_buf, esc = [], False
            while i < n - 1:
                ch = s[i]
                if esc: key_buf.append(ch); esc = False
                elif ch == "\\": esc = True
                elif ch == '"': i += 1; break
                else: key_buf.append(ch)
                i += 1
            key = "".join(key_buf).strip()
            while i < n - 1 and s[i] in " \t\r\n": i += 1
            if i < n - 1 and s[i] == ':': i += 1
        else:
            key_start = i
            while i < n - 1 and s[i] not in ": \t\r\n": i += 1
            key = s[key_start:i].strip()
            while i < n - 1 and s[i] in " \t\r\n": i += 1
            if i < n - 1 and s[i] == ':': i += 1
        while i < n - 1 and s[i] in " \t\r\n": i += 1
        if i >= n - 1: break
        if s[i] == '"':
            i += 1; val_buf, esc = [], False
            while i < n - 1:
                ch = s[i]
                if esc: val_buf.append(ch); esc = False
                elif ch == "\\": esc = True
                elif ch == '"': i += 1; break
                else: val_buf.append(ch)
                i += 1
            val = "".join(val_buf)
        elif s[i] in "{[":
            open_ch, close_ch = s[i], "}" if s[i] == "{" else "]"
            depth, val_buf = 0, []
            while i < n:
                ch = s[i]
                val_buf.append(ch)
                if ch == open_ch: depth += 1
                elif ch == close_ch:
                    depth -= 1
                    if depth == 0: i += 1; break
                i += 1
            val = "".join(val_buf)
        else:
            val_buf = []
            while i < n - 1:
                ch = s[i]
                if ch in ',}': break
                val_buf.append(ch)
                i += 1
            val = "".join(val_buf).strip()
        v = val.strip() if isinstance(val, str) else val
        if isinstance(v, str):
            if len(v) >= 2 and v[0] == '"' and v[-1] == '"': v = v[1:-1]
            if v.lower() in ("true", "false"): parsed_val = v.lower() == "true"
            else:
                try: parsed_val = int(v)
                except Exception: parsed_val = v
        else: parsed_val = v
        result[key] = parsed_val
        while i < n - 1 and s[i] in " \t\r\n,": i += 1
    return result

def parse_github_inline_block_robust(text: str):
    proxies = []
    n, i = len(text), 0
    while i < n:
        start = text.find('{', i)
        if start == -1: break
        j, brace_depth, in_str, esc, block_chars = start, 0, False, False, []
        while j < n:
            ch = text[j]
            block_chars.append(ch)
            if in_str:
                if esc: esc = False
                elif ch == '\\': esc = True
                elif ch == '"': in_str = False
            else:
                if ch == '"': in_str = True; esc = False
                elif ch == '{': brace_depth += 1
                elif ch == '}':
                    brace_depth -= 1
                    if brace_depth == 0: j += 1; break
            j += 1
        raw_block = ''.join(block_chars)
        i = j
        d = parse_inline_block_to_dict(raw_block)
        if not isinstance(d, dict):
            fallback = re.sub(r'(\b[a-zA-Z0-9_\-]+)\s*:', r'"\1":', raw_block).replace("'", '"')
            d2 = None
            try: d2 = json.loads(fallback)
            except Exception: d2 = None
            if isinstance(d2, dict): d = d2
            else:
                if DEBUG_GITHUB_FAIL:
                    snippet = raw_block if len(raw_block) <= 2000 else raw_block[:2000] + "...[truncated]"
                    log("[DEBUG-GH] 无法解析内联块，原始内容：\n" + snippet)
                    if DEBUG_GITHUB_FAIL_TO_FILE:
                        try:
                            with open(DEBUG_GITHUB_FAIL_FILE, "a", encoding="utf-8") as fh: fh.write(snippet + "\n\n")
                        except Exception: pass
                continue
        if "id" in d and "uuid" not in d: d["uuid"] = d.pop("id")
        if "method" in d and "cipher" not in d: d["cipher"] = d.pop("method")
        try:
            port = int(d.get("port", 0))
            if port <= 0 or port > 65535: continue
            d["port"] = port
        except Exception: continue
        if not d.get("server"): continue
        t = d.get("type")
        if t not in ("ss", "ssr", "trojan", "vmess", "vless", "http", "https", "socks5", "hysteria", "hysteria2"):
            if d.get("uuid"): d["type"] = "vmess"
            elif d.get("cipher") and d.get("password"): d["type"] = "ss"
            else: continue
        proxies.append(d)
    return proxies

# ========== proxy -> URI converters ==========
def proxy_to_uri(p):
    """将 Clash proxy 字典转换为标准 URI 链接"""
    t = p.get("type")
    name = p.get("name", "")
    server = p.get("server")
    port = p.get("port")

    if not (server and port):
        return None
    name_enc = quote(name, safe="")

    try:
        if t == "ss":
            if not (p.get("cipher") and p.get("password")): return None
            userinfo = f"{p['cipher']}:{p['password']}"
            enc = base64.urlsafe_b64encode(userinfo.encode()).decode().rstrip("=")
            uri = f"ss://{enc}@{server}:{port}"
            plugin = p.get("plugin")
            if plugin:
                opts = p.get("plugin-opts", {})
                plugin_str = quote(f"{plugin};{';'.join([f'{k}={v}' for k,v in opts.items()])}")
                uri += f"?plugin={plugin_str}"
            return f"{uri}#{name_enc}"

        elif t == "trojan":
            if not p.get("password"): return None
            password = quote(p['password'], safe='')
            sni = p.get("sni", p.get("serverName", ''))
            return f"trojan://{password}@{server}:{port}?sni={quote(sni)}#{name_enc}"

        elif t == "vmess":
            if not p.get("uuid"): return None
            vmess_obj = {
                "v": "2", "ps": name, "add": server, "port": str(port),
                "id": p["uuid"], "aid": str(p.get("alterId", 0)),
                "net": p.get("network", "tcp"), "type": p.get("headerType", "none"),
                "host": p.get("ws-opts", {}).get("headers", {}).get("Host", ""),
                "path": p.get("ws-opts", {}).get("path", "/"),
                "tls": "tls" if p.get("tls") else ""
            }
            enc = base64.b64encode(json.dumps(vmess_obj, separators=(",", ":")).encode()).decode()
            return f"vmess://{enc}"

        elif t == "vless":
            if not p.get("uuid"): return None
            params = {
                "encryption": p.get("encryption", "none"),
                "security": "tls" if p.get("tls") else "none",
                "type": p.get("network", "tcp"),
                "host": p.get("servername", ""),
                "path": p.get("ws-opts", {}).get("path", ""),
                "flow": p.get("flow", ""),
                "sni": p.get("servername", "")
            }
            query = urlencode({k: v for k, v in params.items() if v})
            return f"vless://{p['uuid']}@{server}:{port}?{query}#{name_enc}"

        elif t in ("http", "https"):
            auth = ""
            if p.get("username") and p.get("password"):
                auth = f"{quote(p['username'])}:{quote(p['password'])}@"
            return f"{t}://{auth}{server}:{port}#{name_enc}"
        
        elif t == "socks5":
            auth = ""
            if p.get("username") and p.get("password"):
                auth = f"{quote(p['username'])}:{quote(p['password'])}@"
            return f"socks5://{auth}{server}:{port}#{name_enc}"

        elif t == "hysteria":
            auth = p.get("auth_str", p.get("auth-str", p.get("password", "")))
            params = { "sni": p.get("sni", "") }
            query = urlencode({k: v for k, v in params.items() if v})
            return f"hysteria://{server}:{port}?{query}&auth={quote(auth)}#{name_enc}"

        elif t == "hysteria2":
            auth = p.get("password", "")
            params = { "sni": p.get("sni", "") }
            query = urlencode({k: v for k, v in params.items() if v})
            return f"hysteria2://{auth}@{server}:{port}?{query}#{name_enc}"

        elif t == "ssr":
            # SSR 链接结构复杂，从字典反向生成不完整，这里只做基本转换
            return f"ssr://{server}:{port}#{name_enc}"
            
    except Exception:
        return None
    return None

# ========== NEW: Parsers for different subscription formats ==========
def parse_plaintext_subscription(text):
    """解析纯文本格式，每行一个 URI"""
    uris = [
        line.strip() for line in text.splitlines() 
        if line.strip().startswith(SUPPORTED_SCHEMES)
    ]
    return uris, "plaintext" if uris else None

def parse_json_subscription(text):
    """解析特定的 JSON 数组格式 (常见于 SS 订阅)"""
    try:
        proxies_data = json.loads(text)
        if not isinstance(proxies_data, list):
            return [], None
        
        uris = []
        for p in proxies_data:
            if not isinstance(p, dict): continue
            
            # 兼容 SS JSON 格式
            if all(k in p for k in ["server", "server_port", "password", "method"]):
                name = p.get("remarks", p.get("name", "ss_node"))
                server = p["server"]; port = p["server_port"]
                password = p["password"]; method = p["method"]
                
                userinfo_b64 = base64.urlsafe_b64encode(f"{method}:{password}".encode()).decode().rstrip("=")
                uri = f"ss://{userinfo_b64}@{server}:{port}#{quote(name)}"
                uris.append(uri)
                
        return uris, "json" if uris else None
    except json.JSONDecodeError:
        return [], None

def parse_yaml_subscription(text, source_url: str | None = None):
    """解析 YAML (Clash) 格式，包含多种兜底方案"""
    yaml = YAML(typ="safe")
    try:
        data = yaml.load(text)
        if not isinstance(data, dict):
            raise ValueError("YAML content is not a dictionary")
    except Exception as e:
        log(f"[提示] YAML 解析失败，进入兜底逻辑: {e}")
        # 兜底逻辑：尝试从不规范的文本中提取节点
        if source_url and "raw.githubusercontent.com/mfuu/v2ray/master/clash.yaml" in source_url:
            gh_proxies = parse_github_inline_block_robust(text)
            uris_gh = [u for p in gh_proxies if (u := proxy_to_uri(p))]
            log(f"[信息] GitHub Clash 内联块修复得到 {len(uris_gh)} 个节点")
            return uris_gh, "github_inline"
        candidates = find_inline_json_candidates_balanced(text)
        inline_proxies = parse_json_blocks_to_proxies(candidates)
        uris_inline = [u for p in inline_proxies if (u := proxy_to_uri(p))]
        if uris_inline:
            log(f"[信息] 内联块修复得到 {len(uris_inline)} 个节点")
            return uris_inline, "inline"
        uris_regex, _ = parse_plaintext_subscription(text) # 使用纯文本解析作为正则的替代
        if uris_regex:
            log(f"[信息] 纯文本兜底抓取得到 {len(uris_regex)} 个 URI")
            return uris_regex, "regex"
        return [], None

    # 标准 YAML 解析
    proxies = []
    for field in ("proxies", "proxy", "nodes"):
        val = data.get(field)
        if isinstance(val, list):
            proxies = val
            break
    
    uris = []
    for p in proxies:
        if not isinstance(p, dict): continue
        if p.get("type") in ("direct", "reject", "dns"): continue
        if "id" in p and "uuid" not in p: p["uuid"] = p.pop("id")
        if "method" in p and "cipher" not in p: p["cipher"] = p.pop("method")
        
        try:
            port = int(p.get("port", 0))
            if port <= 0 or port > 65535: continue
            p["port"] = port
        except (ValueError, TypeError): continue
        if not p.get("server"): continue
        
        uri = proxy_to_uri(p)
        if uri:
            uris.append(uri)
            
    return uris, "yaml" if uris else None

# ========== NEW: Master Parser ==========
def process_subscription_content(text, url):
    """
    主解析函数，按顺序尝试不同的解析策略
    1. Base64 -> 纯文本 URI
    2. JSON -> 特定代理格式
    3. YAML -> Clash/V2RayN 格式
    4. 纯文本 URI (作为兜底)
    """
    # 策略 1: 尝试 Base64 解码
    decoded_text = b64_decode_any(text)
    if decoded_text:
        uris, stage = parse_plaintext_subscription(decoded_text)
        if stage: return uris, "base64"

    # 策略 2: 尝试解析为 JSON
    uris, stage = parse_json_subscription(text)
    if stage: return uris, stage

    # 策略 3: 尝试解析为 YAML (包含多种兜底)
    uris, stage = parse_yaml_subscription(text, source_url=url)
    if stage: return uris, stage
        
    # 策略 4: 最后尝试直接作为纯文本处理
    uris, stage = parse_plaintext_subscription(text)
    if stage: return uris, stage

    return [], "unknown"

def export_base64(uri_list, filename="merged_base64.txt"):
    """将 URI 列表合并、去重并编码为 Base64 写入文件"""
    if not uri_list:
        log("[警告] 没有发现任何有效节点，不生成文件。")
        return
        
    seen = set()
    final_uris = []
    for u in uri_list:
        if u not in seen:
            seen.add(u)
            final_uris.append(u)
    
    log(f"[统计] 最终去重后 {len(final_uris)} 个节点")

    text = "\n".join(final_uris)
    encoded = base64.b64encode(text.encode()).decode()
    with open(filename, "w", encoding="utf-8") as f:
        f.write(encoded)
    log(f"[完成] 已生成 {filename}，共 {len(final_uris)} 个节点")

def main():
    """打印当前代理环境"""
    for k in ("http_proxy", "https_proxy", "all_proxy"):
        v = os.environ.get(k)
        log(f"{k}={v}")
    sources = [
        # 您提供的测试链接
        "https://cf-workers-sub-6g0.pages.dev/sub?token=5ddebb5f3a88500559fc417a1cb7d748",
        "https://rss.zyfx6.xyz/v2rayNG/",
        "https://ys.jiedianxielou.workers.dev"
    ]
    all_uris = []
    stats = {}
    source_details = []

    for url in sources:
        log(f"[处理] {url}")
        text = fetch_url(url)
        if not text:
            source_details.append({"url": url, "count": 0, "stage": "fetch_fail"})
            continue
        
        uris, stage = process_subscription_content(text, url)
        
        if uris:
            log(f"  -> {stage.capitalize()} 解析成功: {len(uris)} 个节点")
        else:
            log("  -> 无有效节点")

        stats[stage] = stats.get(stage, 0) + len(uris)
        source_details.append({"url": url, "count": len(uris), "stage": stage})
        all_uris.extend(uris)

    log("\n" + "---" * 10)
    log("解析统计 (按类型):")
    for stage, count in stats.items():
        if count > 0:
            log(f"- {stage.capitalize():<15}: {count}")
    
    log("\n解析详情 (按来源):")
    for s in source_details:
        log(f"- {s['stage']:<15} | {s['count']:>4} nodes | {s['url']}")
    log("---" * 10 + "\n")

    export_base64(all_uris)

if __name__ == "__main__":
    main()