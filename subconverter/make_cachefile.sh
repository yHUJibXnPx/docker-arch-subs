#!/usr/bin/env bash
set -euo pipefail

# 某些规则或者节点文件即使代理也无法下载
# 报类似 CACHE NOT EXIST: 'https://', creating new cache. 但是也无法下载
# 则可以尝试，手动下载创建 subconverter cache 生成缓存文件，这样 subconverter 会直接使用缓存文件
mkdir -pv base/cache
pushd cache 2>/dev/null

# bash shell 支持模拟数组
URLS=(
    "https://github.com/juewuy/ShellCrash/raw/master/rules/ShellClash_Full_Block.ini"
    "https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/LocalAreaNetwork.list"
    "https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/UnBan.list"
    "https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/BanAD.list"
    "https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/BanProgramAD.list"
    "https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/BanEasyList.list"
    "https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/BanEasyListChina.list"
    "https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/BanEasyPrivacy.list"
    "https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Ruleset/GoogleFCM.list"
    "https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/GoogleCN.list"
    "https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Ruleset/Netflix.list"
    "https://raw.githubusercontent.com/LM-Firefly/Rules/master/Global-Services/Netflix.list"
    "https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Ruleset/DisneyPlus.list"
    "https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Ruleset/YouTube.list"
    "https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Ruleset/BilibiliHMT.list"
    "https://raw.githubusercontent.com/juewuy/ShellClash/master/rules/ai.list"
    "https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Microsoft.list"
    "https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Apple.list"
    "https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Telegram.list"
    "https://raw.githubusercontent.com/LM-Firefly/Rules/master/Game.list"
    "https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Ruleset/Bahamut.list"
    "https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/ProxyMedia.list"
    "https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/ChinaMedia.list"
    "https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Ruleset/NetEaseMusic.list"
    "https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/ProxyLite.list"
    "https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/ChinaDomain.list"
    "https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/ChinaCompanyIp.list"
    "https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Download.list"
)

export IP=192.168.255.252 H_P=7890 S_P=7890 ; export HTTP_PROXY=http://${IP}:${H_P} HTTPS_PROXY=http://${IP}:${H_P} ALL_PROXY=socks5://${IP}:${S_P} http_proxy=http://${IP}:${H_P} https_proxy=http://${IP}:${H_P} all_proxy=socks5://${IP}:${S_P}

for URI in ${URLS[@]};do
    FILE_MD5SUM=$(echo -n "${URI}" | md5sum | awk '{print $1}')
    rm -fv ${FILE_MD5SUM} ${FILE_MD5SUM}_header
    curl -sSL -D ${FILE_MD5SUM}_header -o ${FILE_MD5SUM} "${URI}"
done

popd
unset HTTP_PROXY HTTPS_PROXY ALL_PROXY http_proxy https_proxy all_proxy
