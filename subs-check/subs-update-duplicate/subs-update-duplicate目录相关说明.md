
# 打开说明记录，防止忘记，你可能需要亿点点想象力
目前观察发现，这个结构很稳定，也比较贴近于目前流行的节点处理工具，当然我也这么了很久，唉，人生就那点时间，真是浪费生命

0. 当前目录结构
    ```plaintext
    .
    ├── subs-update-duplicate目录相关说明.md  # 本目录使用说明文件
    ├── bpb-make.py                         # 本目录生成九种类型的 bpb-*.txt 文件脚本 
    ├── bpb-*.txt                           # 生成的九种类型的 bpb-*.txt 文件
    ├── cfdata                              # 来自官方 cfdata ip优选测速工具
    │   ├── cfdata                          # 来自官方 cfdata 数据生成执行目录
    │   ├── cfdata.go                       # 来自官方 cfdata 源码
    │   └── start.sh                        # 自定义 cfdata 执行脚本
    ├── duplicate-data-v1.0.py              # 第一代数据去重脚本
    ├── duplicate-data-v2.0.py              # 第二代数据去重脚本
    ├── duplicate-data-v3.0.py              # 第三代数据去重脚本
    ├── hosts.txt                           # 生成 bpb-*.txt 文件来源
    ├── http-server.log                     # python http.server 服务日志
    ├── other.txt                           # 其他自定义本地节点文件
    ├── requestment.txt                     # python 脚本所需 pip 依赖
    ├── result.yaml                         # 去重更新测试生成文件
    ├── source.json                         # 去重更新测试源文件
    ├── sub_list.json                       # 节点源文件
    ├── sub_list.json.bak                   # 节点源文件备份，似乎没用
    ├── subs-update-duplicate.log           # crontab 自动执行配合docker容器产生的日志
    ├── subs-update-duplicate.sh            # 通过shell脚本粘合python脚本执行
    ├── other_links_merged.py               # 请求指定订阅链接生成merged_base64.txt节点集合文件
    └── update-json-v1.0.py                 # 动态更新sub_list.json节点脚本
    ```
1. 首先本地进入 `cfdata` 执行 `start.sh` 然后让它运行着
    ```bash
    bash start.sh
    ```
2. 接下来 打开FOFA网络测绘网站，通过注册登陆账号  
https://fofa.info
3. 搜索TLS站点搜索关键词：`(icon_hash="-1354027319" || body="BPB-Worker-Panel") && asn="13335" && port="443"`  
https://fofa.info/result?qbase64=KGljb25faGFzaD0iLTEzNTQwMjczMTkiIHx8IGJvZHk9IkJQQi1Xb3JrZXItUGFuZWwiKSAmJiBhc249IjEzMzM1IiAmJiBwb3J0PSI0NDMi&filter_type=last_month
4. 下载API数据，输入免费的数量即可，到个人中心下载csv
5. 复制 `host` 一栏整列数据，粘贴到 `hosts.txt`
6. 进入本地 `cfdata` 的 `start.sh` 执行完成就测速结果最快的 `ip:port` 修改替换到 `bpb-make.py` 字典值 `ADDRS[cloudflare]` 
- 也可以通过 https://locations-adw.pages.dev/ 更新 cfdata/cfdata/locations.json
  ```bash
  mv -fv cfdata/locations.json cfdata/locations.json.bak
  curl -o cfdata/locations.json 'https://locations-adw.pages.dev/'
  ```
7. 将本地 `cfnat` `ip:port` 修改替换到 `bpb-make.py` 字典值 `ADDRS[cfnat]`
8. 如果你有改优选域名的需求，那就将 `domain:port` 修改替换到 `bpb-make.py` 不支持tls的字典值 `ADDRS[visa_notls]` 和支持tls的字典值 `ADDRS[visa_tls]`  
9. 如果你想自定义共享本地节点也可以添加节点到 other.txt 这样最后本地目录共享的时候会让本地 `subs-check` 获取到找到这个文件  
10. 修改本地节点源 `sub_list.json` 中的 `"id": 23,` 中的参数默认是我本地的 `192.168.255.252:8001` 你需要全部修改为自己的本地 ip:port 方便本地 `subs-check` 获取到  
11. 完成了以上配置，即可执行 subs-update-duplicate.sh
- 这个脚本可以生成九种类型的 `bpb*.txt` 文件
- 更新 `sub_list.json` 节点
- 更新本地 `subs-check` 所需文件 `../config/config.yaml`
- 关于 `other_links_merged.py` 是用来处理 yaml 格式的订阅，有些链接 yaml 是脏数据需要清理，你可以将链接添加到脚本中的 `main()` -> `sources` 变量一同处理会生成 `merged_base64.txt` 整合文件
  - 生成的 `merged_base64.txt` 可以通过 `python3 -m http.server -b 0.0.0.0 -d . 8001` 共享出来，然后通过编辑追加到 `sub_list.json` 文件中，这样就能重新喂给 `subs-check` 容器识别，如下
    ```json
    {
    "id": 25,
    "remarks": "owner_local",
    "site": "http://192.168.255.252:8001",
    "url": "... 这里是很多很多本地节点文件 ... |http://192.168.255.252:8001/merged_base64.txt",
    "update_method": "auto",
    "enabled": true,
    "未用的notls部分": "http://192.168.255.252:8001/bpb-vless-notls-cloudflarest.txt|http://192.168.255.252:8001/bpb-vless-notls-cfnat.txt|http://192.168.255.252:8001/bpb-vless-notls.txt"
    },
    ```
- 最后关于 `subs-update-duplicate.sh` 是用来自动化处理订阅的，会开启 `python http.server` 服务 `8001` 端口共享，方便本地 `subs-check` 获取到本地生成的节点 `bpb*.txt` 文件
  - 脚本开头内置了局域代理，需要你自行注释掉或者换成自己的局域代理，比如下面的代理格式仅需替换 ip 和 port 即可。
    ```bash
    export IP=192.168.255.252 H_P=7890 S_P=7890 ; export HTTP_PROXY=http://${IP}:${H_P} HTTPS_PROXY=http://${IP}:${H_P} ALL_PROXY=socks5://${IP}:${S_P} http_proxy=http://${IP}:${H_P} https_proxy=http://${IP}:${H_P} all_proxy=socks5://${IP}:${S_P}
    ```
- 现在可以执行 `subs-update-duplicate.sh` 脚本了
    ```bash
    bash subs-update-duplicate.sh
    ```
# 参考
[github beck-8/subs-check](https://github.com/beck-8/subs-check)  
[github Kwisma/cfdata](https://github.com/Kwisma/cfdata)  
[cmliu 搜索TLS站点博文](https://cmliussss.com/p/BPBbug/)  
[cmliu 定制汇聚订阅项目](https://github.com/cmliu/CF-Workers-SUB)  