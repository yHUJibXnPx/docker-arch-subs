#!/usr/bin/env bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
# --------------------------------------------------------------
#	项目: CloudflareSpeedTest 自动更新 Hosts
#	版本: 1.0.4
#	作者: XIU2
#	项目: https://github.com/XIU2/CloudflareSpeedTest
# --------------------------------------------------------------

_CHECK() {
	while true
		do
		if [[ ! -e "nowip_hosts.txt" ]]; then
			echo -e "该脚本的作用为 CFST 测速后获取最快 IP 并替换 Hosts 中的 Cloudflare CDN IP。\n使用前请先阅读：https://github.com/XIU2/CloudflareSpeedTest/issues/42#issuecomment-768273848"
			echo -e "第一次使用，请先将 Hosts 中所有 Cloudflare CDN IP 统一改为一个 IP。"
			read -e -p "输入该 Cloudflare CDN IP 并回车（后续不再需要该步骤）：" NOWIP
			if [[ ! -z "${NOWIP}" ]]; then
				echo ${NOWIP} > nowip_hosts.txt
				break
			else
				echo "该 IP 不能是空！"
			fi
		else
			break
		fi
	done
}

_UPDATE() {
	echo -e "开始测速..."
	NOWIP=$(head -1 nowip_hosts.txt)

	# 这里可以自己添加、修改 CFST 的运行参数
	./cfst -o "result_hosts.txt"

	# 如果需要 "找不到满足条件的 IP 就一直循环测速下去"，那么可以将下面的两个 exit 0 改为 _UPDATE 即可
	[[ ! -e "result_hosts.txt" ]] && echo "CFST 测速结果 IP 数量为 0，跳过下面步骤..." && exit 0

	# 下面这行代码是 "找不到满足条件的 IP 就一直循环测速下去" 才需要的代码
	# 考虑到当指定了下载速度下限，但一个满足全部条件的 IP 都没找到时，CFST 就会输出所有 IP 结果
	# 因此当你指定 -sl 参数时，需要移除下面这段代码开头的 # 井号注释符，来做文件行数判断（比如下载测速数量：10 个，那么下面的值就设在为 11）
	#[[ $(cat result_hosts.txt|wc -l) > 11 ]] && echo "CFST 测速结果没有找到一个完全满足条件的 IP，重新测速..." && _UPDATE


	BESTIP=$(sed -n "2,1p" result_hosts.txt | awk -F, '{print $1}')
	if [[ -z "${BESTIP}" ]]; then
		echo "CFST 测速结果 IP 数量为 0，跳过下面步骤..."
		exit 0
	fi
	echo ${BESTIP} > nowip_hosts.txt
	echo -e "\n旧 IP 为 ${NOWIP}\n新 IP 为 ${BESTIP}\n"

        echo "开始备份 Hosts 文件（hosts_backup）..."
	\cp -f /etc/hosts /etc/hosts_backup

	echo -e "开始替换..."
	sed -i 's/'${NOWIP}'/'${BESTIP}'/g' /etc/hosts
	echo -e "完成..."
}

_UPDATE2() {
        echo -e "开始测速..."
        NOWIP=$(head -1 nowip_hosts.txt)

        echo '输入延迟阈值上限，单位毫秒 (default 500):'
        read TL
        TL=${TL:-500}

        echo '输入详细测试使用的端口 (default 443):'
        read TP
        TP=${TP:-443}

        echo '输入扫描阶段最大并发数 (default 4):'
        read N
        N=${N:-4}

        echo '输入详细测试阶段最大并发数 (default 50):'
        read T
        T=${T:-50}

        #CloudflareSpeedTest v2.3.4
        #测试各个 CDN 或网站所有 IP 的延迟和速度，获取最快 IP (IPv4+IPv6)！
        #https://github.com/XIU2/CloudflareSpeedTest
        #
        #参数：
        #    -n 200
        #        延迟测速线程；越多延迟测速越快，性能弱的设备 (如路由器) 请勿太高；(默认 200 最多 1000)
        #    -t 4
        #        延迟测速次数；单个 IP 延迟测速的次数；(默认 4 次)
        #    -dn 10
        #        下载测速数量；延迟测速并排序后，从最低延迟起下载测速的数量；(默认 10 个)
        #    -dt 10
        #        下载测速时间；单个 IP 下载测速最长时间，不能太短；(默认 10 秒)
        #    -tp 443
        #        指定测速端口；延迟测速/下载测速时使用的端口；(默认 443 端口)
        #    -url https://cf.xiu2.xyz/url
        #        指定测速地址；延迟测速(HTTPing)/下载测速时使用的地址，默认地址不保证可用性，建议自建；
        #
        #    -httping
        #        切换测速模式；延迟测速模式改为 HTTP 协议，所用测试地址为 [-url] 参数；(默认 TCPing)
        #    -httping-code 200
        #        有效状态代码；HTTPing 延迟测速时网页返回的有效 HTTP 状态码，仅限一个；(默认 200 301 302)
        #    -cfcolo HKG,KHH,NRT,LAX,SEA,SJC,FRA,MAD
        #        匹配指定地区；IATA 机场地区码或国家/城市码，英文逗号分隔，仅 HTTPing 模式可用；(默认 所有地区)
        #
        #    -tl 200
        #        平均延迟上限；只输出低于指定平均延迟的 IP，各上下限条件可搭配使用；(默认 9999 ms)
        #    -tll 40
        #        平均延迟下限；只输出高于指定平均延迟的 IP；(默认 0 ms)
        #    -tlr 0.2
        #        丢包几率上限；只输出低于/等于指定丢包率的 IP，范围 0.00~1.00，0 过滤掉任何丢包的 IP；(默认 1.00)
        #    -sl 5
        #        下载速度下限；只输出高于指定下载速度的 IP，凑够指定数量 [-dn] 才会停止测速；(默认 0.00 MB/s)
        #
        #    -p 10
        #        显示结果数量；测速后直接显示指定数量的结果，为 0 时不显示结果直接退出；(默认 10 个)
        #    -f ip.txt
        #        IP段数据文件；如路径含有空格请加上引号；支持其他 CDN IP段；(默认 ip.txt)
        #    -ip 1.1.1.1,2.2.2.2/24,2606:4700::/32
        #        指定IP段数据；直接通过参数指定要测速的 IP 段数据，英文逗号分隔；(默认 空)
        #    -o result.csv
        #        写入结果文件；如路径含有空格请加上引号；值为空时不写入文件 [-o ""]；(默认 result.csv)
        #
        #    -dd
        #        禁用下载测速；禁用后测速结果会按延迟排序 (默认按下载速度排序)；(默认 启用)
        #    -allip
        #        测速全部的IP；对 IP 段中的每个 IP (仅支持 IPv4) 进行测速；(默认 每个 /24 段随机测速一个 IP)
        #
        #    -debug
        #        调试输出模式；会在一些非预期情况下输出更多日志以便判断原因；(默认 关闭)
        #
        #    -v
        #        打印程序版本 + 检查版本更新
        #    -h
        #        打印帮助说明




        # 这里可以自己添加、修改 CFST 的运行参数
        ./cfst -n ${N} -t ${T} -tp ${TP} -tl ${TL} -o "result_hosts.txt"

        # 如果需要 "找不到满足条件的 IP 就一直循环测速下去"，那么可以将下面的两个 exit 0 改为 _UPDATE 即可
        [[ ! -e "result_hosts.txt" ]] && echo "CFST 测速结果 IP 数量为 0，跳过下面步骤..." && exit 0

        # 下面这行代码是 "找不到满足条件的 IP 就一直循环测速下去" 才需要的代码
        # 考虑到当指定了下载速度下限，但一个满足全部条件的 IP 都没找到时，CFST 就会输出所有 IP 结果
        # 因此当你指定 -sl 参数时，需要移除下面这段代码开头的 # 井号注释符，来做文件行数判断（比如下载测速数量：10 个，那么下面的值就设在为 11）
        #[[ $(cat result_hosts.txt|wc -l) > 11 ]] && echo "CFST 测速结果没有找到一个完全满足条件的 IP，重新测速..." && _UPDATE


        BESTIP=$(sed -n "2,1p" result_hosts.txt | awk -F, '{print $1}')
        if [[ -z "${BESTIP}" ]]; then
                echo "CFST 测速结果 IP 数量为 0，跳过下面步骤..."
                exit 0
        fi
        echo ${BESTIP} > nowip_hosts.txt
        echo -e "\n旧 IP 为 ${NOWIP}\n新 IP 为 ${BESTIP}\n"

        echo -e "完成..."
}

#_CHECK
#_UPDATE
_UPDATE2
