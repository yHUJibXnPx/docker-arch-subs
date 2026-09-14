'''功能说明
更新json文件上某些特殊的链接，比如页面获取，日期更新这种需要时时请求更新的链接，并持续性的挂载间隔一段时间就更新
脚本指定json文件，并读取，内容如下 
[
  {
    "id": 0,
    "remarks": "v2raynews",
    "site": "https://v2raynews.org/",
    "url": "https://dlconf.clashapps.cc/yaml/8a94bb84-864a-2218-f084-8f665b080a5e.yaml|https://dlconf.clashapps.cc/yaml/8a94bb84-864a-2218-f084-8f665b080a5e.yaml",
    "update_method": "change_date",
    "enabled": true
  },
  {
    "id": 1,
    "remarks": "Fukki-Z/nodefree",
    "site": "https://nodefree.org/f/freenode|Fukki-Z/nodefree|FiFier/v2rayShare",
    "url": "https://nodefree.githubrowcontent.com/2025/09/20250925.yaml|https://nodefree.githubrowcontent.com/2025/09/20250925.txt",
    "update_method": "change_date",
    "enabled": true
  },
  {
    "id": 2,
    "remarks": "nexthiddify.github.io",
    "site": "https://nexthiddify.github.io",
    "url": "https://node.freeclashnode.com/uploads/2025/09/0-20250925.txt|https://node.freeclashnode.com/uploads/2025/09/1-20250925.txt",
    "update_method": "change_date",
    "enabled": true
  },
  {
    "id": 3,
    "remarks": "www.freev2raynode.com",
    "site": "https://www.freev2raynode.com/",
    "url": "https://node.freev2raynode.com/uploads/2025/09/0-20250925.txt|https://node.freev2raynode.com/uploads/2025/09/1-20250925.txt",
    "update_method": "change_date",
    "enabled": true
  },
  {
    "id": 4,
    "remarks": "ggborr/FREEE-VPN",
    "site": "https://github.com/ggborr/FREEE-VPN",
    "url": "https://github.com/ggborr/FREEE-VPN/raw/refs/heads/main/9cl|https://github.com/ggborr/FREEE-VPN/raw/refs/heads/main/9v2",
    "update_method": "change_date",
    "enabled": true
  },
  {
    "id": 5,
    "remarks": "gooooooooooooogle/collectSub",
    "site": "https://github.com/gooooooooooooogle/collectSub",
    "url": "https://update.glados-config.com/mihomo/543454/7b9d17e/80064/glados.yaml|https://raw.githubusercontent.com/ssrsub/ssr/master/clash.yaml",
    "update_method": "page_release",
    "enabled": true
  },
  {
    "id": 6,
    "remarks": "github.com/beck-8",
    "site": "https://github.com/beck-8/subs-check/raw/refs/heads/master/config/config.example.yaml",
    "url": "https://hub.docker.com/r/xream/sub-store|https://raw.githubusercontent.com/beck-8/sub-urls/main/%E5%B0%8F%E8%80%8C%E7%BE%8E.txt",
    "update_method": "page_release",
    "enabled": true
  },
  {
    "id": 7,
    "remarks": "yitong2333/proxy-minging",
    "site": "https://github.com/yitong2333/proxy-minging/raw/refs/heads/main/latest.yaml",
    "url": "https://chromego-sub.netlify.app/sub/merged_proxies_new.yaml|https://misub.nbee.pp.ua/wltpladlw/sub",
    "update_method": "page_release",
    "enabled": true
  },
  {
    "id": 8,
    "remarks": "beck-8/sub-urls",
    "site": "https://github.com/beck-8/sub-urls",
    "url": "https://raw.githubusercontent.com/firefoxmmx2/v2rayshare_subcription/main/subscription/clash_sub.yaml|https://raw.githubusercontent.com/Q3dlaXpoaQ/V2rayN_Clash_Node_Getter/refs/heads/main/APIs/sc0.yaml",
    "update_method": "page_release",
    "enabled": true
  }
]
然后执行这个脚本根据日期或页面更新有效链接，保持json文件时时最新
'''
#!/usr/bin/env python3
import os
import json
import re
# python -m pip install requests
import requests
import time
import logging
import argparse
from datetime import datetime
# pip install beautifulsoup4
from bs4 import BeautifulSoup

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 全局开关 & 加速源配置
ENABLE_GH_PROXY = False
GH_PROXY_PREFIX = "https://ghproxy.net/"  # 这里可以换成其他加速源

class Update:

    def __init__(self, json_file):
        self.json_file = json_file
        self.session = requests.Session()  # 创建请求会话
        # 统一为 session 设置浏览器 UA，防止被目标网站拦截
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
            ),
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        })
        self.timeout = 30  # <-- 在这里添加这行，设置超时时间
        self.load_rules() # 初始规则函数

    def normalize_github_like(self, url: str) -> str:
        """把 GitHub / Gist 的网页型链接统一规范为可直链下载的原始域名"""

        # 1) github.com/{user}/{repo}/blob/{ref}/{path}
        m = re.match(r"^https://github\.com/([^/]+)/([^/]+)/blob/([^/]+)/(.+)$", url)
        if m:
            user, repo, ref, path = m.groups()
            return f"https://raw.githubusercontent.com/{user}/{repo}/{ref}/{path}"

        # 2) github.com/{user}/{repo}/raw/{ref}/{path}
        m = re.match(r"^https://github\.com/([^/]+)/([^/]+)/raw/([^/]+)/(.+)$", url)
        if m:
            user, repo, ref, path = m.groups()
            return f"https://raw.githubusercontent.com/{user}/{repo}/{ref}/{path}"

        # 3) gist.github.com/{user}/{gist_id}/raw/{rev}/{filename}
        m = re.match(r"^https://gist\.github\.com/([^/]+)/([0-9a-fA-F]+)/raw/([0-9a-fA-F]+)/(.+)$", url)
        if m:
            user, gist_id, rev, filename = m.groups()
            return f"https://gist.githubusercontent.com/{user}/{gist_id}/raw/{rev}/{filename}"

        # 4) gist.github.com/{user}/{gist_id}（只有页面，没有文件名）
        m = re.match(r"^https://gist\.github\.com/([^/]+)/([0-9a-fA-F]+)$", url)
        if m:
            user, gist_id = m.groups()
            try:
                resp = requests.get(url, timeout=30)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")
                # 找到 gist 页面上的第一个文件名
                filename_tag = soup.select_one('strong[class*="gist-"]')
                if filename_tag:
                    filename = filename_tag.get_text(strip=True)
                    return f"https://gist.githubusercontent.com/{user}/{gist_id}/raw/{filename}"
            except requests.RequestException as e:
                logging.error(f"Failed to fetch gist page {url}: {e}")
                return url

        return url

    def rewrite_url(self, url: str) -> str:
        """
        规范化 GitHub/Gist 链接，并根据 ENABLE_GH_PROXY 决定是否应用加速前缀。
        (已按您的要求修改)
        """
        # 步骤 1: 首先处理可能存在的加速前缀，以获得一个干净的原始 URL
        # 无论开关状态如何，我们都先去除前缀，以便进行统一的规范化处理
        if url.startswith(GH_PROXY_PREFIX):
            clean_url = url[len(GH_PROXY_PREFIX):]
        else:
            clean_url = url

        # 步骤 2: 对干净的 URL 进行规范化 (此步骤现在总是执行)
        normalized_url = self.normalize_github_like(clean_url)

        # 步骤 3: 如果启用了代理，则为特定域名添加前缀
        if ENABLE_GH_PROXY:
            if normalized_url.startswith("https://raw.githubusercontent.com") or normalized_url.startswith("https://gist.githubusercontent.com"):
                return f"{GH_PROXY_PREFIX}{normalized_url}"

        # 步骤 4: 如果代理未启用，或 URL 不匹配加速域名，则返回规范化后的干净 URL
        return normalized_url

    def load_list(self, file_path):
        """加载规则文件，忽略空行和#注释"""
        if not os.path.exists(file_path):
            return []
        with open(file_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]

    def load_rules(self):
        """加载三层规则"""
        self.whitelist = set(self.load_list('whitelist.txt'))
        self.exact_blacklist = set(self.load_list('exclusion_exact.txt'))
        self.pattern_blacklist = [re.compile(p) for p in self.load_list('exclusion_patterns.txt')]

    def is_excluded(self, url):
        # 白名单优先
        if any(w in url for w in self.whitelist):
            logging.debug(f"[白名单保留] {url}")
            return False
        # 精确黑名单（包含匹配）
        if any(e in url for e in self.exact_blacklist):
            logging.debug(f"[精确拦截] {url}")
            return True
        # 正则黑名单
        for pattern in self.pattern_blacklist:
            if pattern.search(url):
                logging.debug(f"[正则拦截] {url} 规则: {pattern.pattern}")
                return True
        logging.debug(f"[保留] {url}")
        return False


    def load_json(self):
        with open(self.json_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_json(self, data):
        with open(self.json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, sort_keys=False, indent=2, ensure_ascii=False)

    def url_updated(self, url):
        """判断远程链接是否已更新（返回 True 表示请求成功）"""
        try:
            resp = self.session.get(url, timeout=30)
            resp.raise_for_status()  # 若状态码为4xx、5xx，则抛出异常
            logging.info("Status code for {}: {}".format(url, resp.status_code))
            return True
        except requests.RequestException as e:
            logging.error("Error fetching {}: {}".format(url, e))
            return False

    def get_valid_urls_joined(self, urls):
        """传入形如用 | 分隔的 URL 字符串，检查每个链接，返回用 | 拼接的有效链接字符串"""
        url_list = urls.split('|')
        valid_urls = []
        for url in url_list:
            if self.url_updated(url):
                valid_urls.append(url)
            else:
                logging.error("URL {} failed or is invalid.".format(url))
        joined_urls = '|'.join(valid_urls)
        logging.info("Valid URLs joined: {}".format(joined_urls))
        return joined_urls if valid_urls else urls

    def update_json(self):
        """加载 JSON，更新各记录的链接，并写回文件"""
        # 获取当前日期信息
        today = datetime.today()
        this_year = today.strftime('%Y')
        this_month_str = today.strftime('%m')      # 带前导零月份
        this_month_int = str(today.month)          # 去掉前导零的月份
        this_today = today.strftime('%Y%m%d')
        this_day_str = today.strftime('%d')        # 带前导零日
        this_day_int = str(today.day)            # 去掉前导零的日
        data = self.load_json()
        updated = False
        for sub in data:
            try:
                # 仅对 enabled 为 True 且 update_method 不是 'auto' 的记录进行更新
                if sub.get('enabled', False) and sub.get('update_method') != 'auto':
                    id = sub.get('id')
                    # 入口兜底：先过滤再加速
                    url_list = []
                    for u in sub.get('url').split('|'):
                        if not self.is_excluded(u):
                            url_list.append(self.rewrite_url(u))
                    current_url = '|'.join(url_list) if url_list else sub.get('url')

                    logging.info("Processing ID {}.".format(id))
                    if sub.get('update_method') == 'change_date':
                        new_url = self.change_date(id, current_url, this_year, this_month_str, this_day_str, this_month_int, this_day_int, this_today)
                    elif sub.get('update_method') == 'page_release':
                        new_url = self.find_link(id, current_url, this_year, this_month_str, this_day_str, this_month_int, this_day_int)
                    else:
                        new_url = current_url
                    if new_url != current_url:
                        sub['url'] = new_url
                        updated = True
                        logging.info("ID {} url updated to {}".format(id, new_url))
                    else:
                        sub['url'] = current_url  # 保证即使没更新，也写回加速后的
                        logging.info("No available update for ID {}".format(id))
            except KeyError as e:
                logging.error("KeyError {} for record. Please check update method settings.".format(e))
        # 出口兜底：写回前统一过滤+加速
        for sub in data:
            url_list = []
            for u in sub.get('url').split('|'):
                if not self.is_excluded(u):
                    url_list.append(self.rewrite_url(u))
            sub['url'] = '|'.join(url_list) if url_list else sub.get('url')
        if updated:
            self.save_json(data)
            logging.info("JSON file updated successfully.")
        else:
            self.save_json(data)  # 即使没更新，也保存加速后的链接
            logging.info("No updates were made to the JSON file.")

    def change_date(self, id, current_url, this_year, this_month_str, this_day_str, this_month_int, this_day_int, this_today):
        """更新 URL 地址，基于日期"""
        if id == 0:
            # 固定分类页（免费节点）
            category_url = "https://v2raynews.org/index.php/category/%e5%85%8d%e8%b4%b9%e8%8a%82%e7%82%b9/"
            # 匹配文章链接（带日期）
            article_pattern = r'https://v2raynews\.org/index\.php/\d{4}/\d{2}/\d{2}/[^\s"]+'
            latest_article = self.process_links(category_url, article_pattern)
            if latest_article:
                latest_article_url = latest_article.split('|')[0]
                logging.info(f"[分类页模式] 最新文章: {latest_article_url}")
                uuid_pattern = r'https://dlconf\.clashapps\.cc/(?:yaml|conf)/[0-9a-f\-]+\.(?:yaml|conf)'
                links = self.process_links(latest_article_url, uuid_pattern)
                if links:
                    return links
                else:
                    logging.warning("[分类页模式] 未提取到 UUID 链接，尝试回退到日期拼接模式")
            # 回退模式：按日期拼接文章 URL
            # 确保传递正确的日期变量
            date_url = f"https://v2raynews.org/index.php/{this_year}/{this_month_int}/{this_day_int}/{this_year}年{this_month_int}月{this_day_int}日免费节点推荐（每日更新）｜clash-v2ray订阅每日/"
            logging.info(f"[回退模式] 尝试访问: {date_url}")
            uuid_pattern = r'https://dlconf\.clashapps\.cc/(?:yaml|conf)/[0-9a-f\-]+\.(?:yaml|conf)'
            links = self.process_links(date_url, uuid_pattern)
            return links if links else current_url
        elif id == 1:
            new_url = f'https://nodefree.githubrowcontent.com/{this_year}/{this_month_str}/{this_today}.yaml|https://nodefree.githubrowcontent.com/{this_year}/{this_month_str}/{this_today}.txt'
        elif id == 2:
            new_url = f'https://node.freeclashnode.com/uploads/{this_year}/{this_month_str}/0-{this_today}.txt|https://node.freeclashnode.com/uploads/{this_year}/{this_month_str}/1-{this_today}.txt|https://node.freeclashnode.com/uploads/{this_year}/{this_month_str}/2-{this_today}.txt|https://node.freeclashnode.com/uploads/{this_year}/{this_month_str}/3-{this_today}.txt|https://node.freeclashnode.com/uploads/{this_year}/{this_month_str}/4-{this_today}.txt|https://node.freeclashnode.com/uploads/{this_year}/{this_month_str}/0-{this_today}.yaml|https://node.freeclashnode.com/uploads/{this_year}/{this_month_str}/1-{this_today}.yaml|https://node.freeclashnode.com/uploads/{this_year}/{this_month_str}/2-{this_today}.yaml|https://node.freeclashnode.com/uploads/{this_year}/{this_month_str}/3-{this_today}.yaml|https://node.freeclashnode.com/uploads/{this_year}/{this_month_str}/4-{this_today}.yaml'
        elif id == 3:
            new_url = f'https://node.freev2raynode.com/uploads/{this_year}/{this_month_str}/0-{this_today}.txt|https://node.freev2raynode.com/uploads/{this_year}/{this_month_str}/1-{this_today}.txt|https://node.freev2raynode.com/uploads/{this_year}/{this_month_str}/2-{this_today}.txt|https://node.freev2raynode.com/uploads/{this_year}/{this_month_str}/3-{this_today}.txt|https://node.freev2raynode.com/uploads/{this_year}/{this_month_str}/4-{this_today}.txt|https://node.freev2raynode.com/uploads/{this_year}/{this_month_str}/0-{this_today}.yaml|https://node.freev2raynode.com/uploads/{this_year}/{this_month_str}/1-{this_today}.yaml|https://node.freev2raynode.com/uploads/{this_year}/{this_month_str}/2-{this_today}.yaml|https://node.freev2raynode.com/uploads/{this_year}/{this_month_str}/3-{this_today}.yaml|https://node.freev2raynode.com/uploads/{this_year}/{this_month_str}/4-{this_today}.yaml'
        elif id == 4:
            # 尝试各种可能的命名模式
            month_int = this_month_int
            day_int = this_day_int

            # 模式1: 月份.日期 (例如: 2.2clash, 2.2v2)
            patterns_month_day = [
                f'https://github.com/ggborr/FREEE-VPN/raw/refs/heads/main/{month_int}.{day_int}clash',
                f'https://github.com/ggborr/FREEE-VPN/raw/refs/heads/main/{month_int}.{day_int}v2'
            ]
            
            # 模式2: 纯月份 (例如: 9cl, 9v2, 8CLASH, 8V2, 7JD, 7jd, 4V2ray)
            patterns_month_only = [
                f'https://github.com/ggborr/FREEE-VPN/raw/refs/heads/main/{month_int}cl',
                f'https://github.com/ggborr/FREEE-VPN/raw/refs/heads/main/{month_int}v2',
                f'https://github.com/ggborr/FREEE-VPN/raw/refs/heads/main/{month_int}clash',
                f'https://github.com/ggborr/FREEE-VPN/raw/refs/heads/main/{month_int}V2ray',
                f'https://github.com/ggborr/FREEE-VPN/raw/refs/heads/main/{month_int}JD',
                f'https://github.com/ggborr/FREEE-VPN/raw/refs/heads/main/{month_int}jd'
            ]
            
            # 组合所有可能的链接，并进行验证
            all_patterns = patterns_month_day + patterns_month_only
            valid_urls = []
            for url in all_patterns:
                # 过滤并加速/去加速
                processed_url = self.rewrite_url(url)
                if self.url_updated(processed_url):
                    valid_urls.append(processed_url)
            
            # 如果找到有效的链接，返回拼接后的字符串
            if valid_urls:
                return '|'.join(valid_urls)
            # 如果没有找到，尝试回退到上个月
            else:
                logging.warning(f"ID 4: 未找到 {month_int} 月份的有效链接，尝试回退到上个月")
                from datetime import timedelta
                last_month = datetime.today().replace(day=1) - timedelta(days=1)
                last_month_int = str(last_month.month)
                
                new_url_patterns_fallback = [
                    f'https://github.com/ggborr/FREEE-VPN/raw/refs/heads/main/{last_month_int}cl',
                    f'https://github.com/ggborr/FREEE-VPN/raw/refs/heads/main/{last_month_int}v2',
                    f'https://github.com/ggborr/FREEE-VPN/raw/refs/heads/main/{last_month_int}clash',
                    f'https://github.com/ggborr/FREEE-VPN/raw/refs/heads/main/{last_month_int}V2ray'
                ]
                valid_urls_fallback = []
                for url in new_url_patterns_fallback:
                    processed_url = self.rewrite_url(url)
                    if self.url_updated(processed_url):
                        valid_urls_fallback.append(processed_url)

                if valid_urls_fallback:
                    return '|'.join(valid_urls_fallback)
                else:
                    logging.error(f"ID 4: 上个月的链接也失效了")
                    return current_url
        elif id == 5:
            new_url = f'https://github.com/free-nodes/clashfree/raw/refs/heads/main/clash{this_year}{this_month_str}{this_day_str}.yml|https://raw.githubusercontent.com/free-nodes/v2rayfree/main/v2{this_year}{this_month_str}{this_day_str}'
        elif id == 6:
            new_url = f'https://clashgithub.com/wp-content/uploads/rss/{this_year}{this_month_str}{this_day_str}.txt|https://clashgithub.com/wp-content/uploads/rss/{this_year}{this_month_str}{this_day_str}.yml'
        else:
            new_url = current_url
        # 生成 new_url 后，先过滤
        url_list = []
        for u in new_url.split('|'):
            if not self.is_excluded(u):
                url_list.append(self.rewrite_url(u))  # 全局加速
        if not url_list:
            return current_url
        valid_urls = self.get_valid_urls_joined('|'.join(url_list))
        return valid_urls if valid_urls else current_url

    def process_links(self, url, pattern):
        """提取并处理链接"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            # 提取链接并移除双引号
            all_links = [link.replace('"', '') for link in re.findall(pattern, response.text)]
            # 根据排除规则过滤链接并附加参数
            links = []
            for link in all_links:
                if self.is_excluded(link):
                    continue
                # 过滤通过后加速
                link = self.rewrite_url(link)  # 全局加速
                if 'sub.xn--4gqvd492adjr.com' in link:  # 检查域名匹配
                    links.append(f"{link}/?flag=clash.meta")  # 添加参数
                else:
                    links.append(link)
            return "|".join(links) if links else None
        except requests.RequestException as e:
            logging.error(f"Failed to fetch links from {url}: {e}")
            return None

    def find_link(self, id, current_url, this_year, this_month_str, this_day_str, this_month_int, this_day_int):
        """根据 ID 查找更新的链接"""
        pattern = r'https?://[^\s"]+'

        # 根据 ID 确定 URL
        if id == 7:
            url = f'https://raw.githubusercontent.com/free-nodes/v2rayfree/refs/heads/main/README.md'
        if id == 8:
            url = f'https://github.com/gooooooooooooogle/collectSub/raw/refs/heads/main/sub/{this_year}/{this_month_int}/{this_month_int}-{this_day_int}.yaml'
        elif id == 9:
            url = f'https://github.com/beck-8/subs-check/raw/refs/heads/master/config/config.example.yaml'
        elif id == 10:
            url = f'https://github.com/yitong2333/proxy-minging/raw/refs/heads/main/latest.yaml'
        elif id == 11:
            # https://github.com/beck-8/sub-urls
            urls = [
                'https://github.com/beck-8/sub-urls/raw/refs/heads/main/sub.txt',
                'https://github.com/beck-8/sub-urls/raw/refs/heads/main/%E5%B0%8F%E8%80%8C%E7%BE%8E.txt',
                'https://github.com/beck-8/sub-urls/raw/refs/heads/main/%E9%9D%9EGITHUB.txt',
                'https://github.com/beck-8/sub-urls/raw/refs/heads/main/%E9%AB%98%E5%A4%A7%E5%85%A8.txt'
            ]
            all_links = []
            for u in urls:
                links = self.process_links(u, pattern)
                if links:
                    all_links.append(links)
            return "|".join(all_links) if all_links else current_url
        else:
            return current_url

        logging.info(f'{url}')
        url = self.rewrite_url(url)  # 直接加速
        links = self.process_links(url, pattern)
        return links if links else current_url


# if __name__ == '__main__':
#     parser = argparse.ArgumentParser(description="实时更新 JSON 文件中的有效链接。")
#     parser.add_argument("--json-file", required=True, help="指定待更新 JSON 文件路径")
#     parser.add_argument("--interval", type=int, default=300, help="更新间隔（秒），默认为300秒")
#     args = parser.parse_args()

#     updater = Update(json_file=args.json_file)
#     while True:
#         updater.update_json()
#         logging.info("等待 {} 秒后进行下一次更新...".format(args.interval))
#         time.sleep(args.interval)

if __name__ == '__main__':

    # 显示 debug
    logging.getLogger().setLevel(logging.DEBUG)

    """打印当前代理环境"""
    for k in ("http_proxy", "https_proxy", "all_proxy"):
        v = os.environ.get(k)
        logging.debug(f"{k}={v}")

    updater = Update(json_file='sub_list.json')
    updater.update_json()