
# 打开说明记录，防止忘记，你可能需要亿点点想象力
目前观察发现，某些规则或者节点文件即使代理也无法下载，可能是网络问题，可能是其他问题  
报类似 CACHE NOT EXIST: 'https://', creating new cache. 但是也无法下载  
我在想能不能尝试外部容器挂载手动下载并记录md5来弥补这个问题，但其实每次执行都挺痛苦的  
而且不同版本的docker容器怎么说呢，本质上不同的 subconverter 支持的功能都不一样  
我试了好多不同开发者的 subconverter 都不完美，这些开发者为什么不把功能都集成到一起呢，唉，太折磨人了  

0. 当前目录结构
    ```plaintext
    .
    ├── base                       # subconverter /base 目录映射
    │   └── cache                  # subconverter /base/cache 目录映射
    ├── make_cachefile.log         # crontab 自动执行配合docker容器生成日志文件
    ├── make_cachefile.sh          # 弥补手动生成 cache 文件脚本 
    └── subconverter目录相关说明.md  # 本目录使用说明文件
    ```
1. 首先修改 `make_cachefile.sh` ，确保下载的文件都是自己需要的文件  
2. 然后执行，更新生成缓存 cache 尝试修复 subconverter 相关节点或文件无法下载的问题
    ```bash
    bash make_cachefile.sh
    ```

# 参考
[github tindy2013/subconverter](https://github.com/tindy2013/subconverter)  
[github MetaCubeX/subconverter](https://github.com/MetaCubeX/subconverter)  
[github geekoutnet/SubConverter-MetaCubeX](https://github.com/geekoutnet/SubConverter-MetaCubeX)  
[hub.docker.com tindy2013/subconverter](https://hub.docker.com/r/tindy2013/subconverter)  
[hub.docker.com stilleshan/subconverter](https://hub.docker.com/r/stilleshan/subconverter)  
[hub.docker.com asdlokj1qpi23/subconverter](https://hub.docker.com/r/asdlokj1qpi23/subconverter)  