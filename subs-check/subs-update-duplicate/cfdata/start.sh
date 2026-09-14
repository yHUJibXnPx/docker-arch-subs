#!/usr/bin/env bash
pushd cfdata 2>/dev/null

echo '输入延迟阈值，单位毫秒 (default 500):'
read DELAY
DELAY=${DELAY:-500}

echo '输入详细测试使用的端口 (default 443):'
read PORT
PORT=${PORT:-443}

echo '输入扫描阶段最大并发数 (default 100):'
read SCAN
SCAN=${SCAN:-100}

echo '输入详细测试阶段最大并发数 (default 50):'
read TEST
TEST=${TEST:-50}

# cfdata 参数
#  -delay int
#    	延迟阈值，单位毫秒 (default 500)
#  -port int
#    	详细测试使用的端口 (default 443)
#  -scan int
#    	扫描阶段最大并发数 (default 100)
#  -test int
#    	详细测试阶段最大并发数 (default 50)
./cfdata-$(uname -s | tr A-Z a-z)-$(if [ $(uname -m) = aarch64 ];then echo arm64;else echo $(uname -m); fi) -delay ${DELAY} -port ${PORT} -scan ${SCAN} -test ${TEST}
popd
