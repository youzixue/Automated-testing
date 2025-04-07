#!/bin/bash
# Allure报告生成脚本
# 用于生成Allure报告并启动报告服务器

# 设置错误时退出
set -e

# 脚本帮助信息
function show_help {
    echo "用法: $0 [结果目录]"
    echo ""
    echo "生成并打开Allure测试报告。"
    echo ""
    echo "参数:"
    echo "  结果目录    Allure结果目录，默认为reports/allure-results"
    echo ""
    exit 0
}

# 检查帮助参数
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    show_help
fi

# 处理参数
RESULTS_DIR=${1:-"reports/allure-results"}
REPORT_DIR="reports/allure-report"

# 检查allure命令是否可用
if ! command -v allure &> /dev/null; then
    echo "错误: 未安装Allure命令行工具。请先安装Allure。"
    echo "  macOS: brew install allure"
    echo "  Linux: sudo apt-get install allure"
    echo "  手动安装: https://docs.qameta.io/allure/#_installing_a_commandline"
    exit 1
fi

# 检查结果目录是否存在
if [ ! -d "$RESULTS_DIR" ]; then
    echo "错误: 结果目录 '$RESULTS_DIR' 不存在或为空。"
    exit 1
fi

echo "============================================="
echo "生成Allure报告"
echo "============================================="
echo "结果目录: $RESULTS_DIR"
echo "报告目录: $REPORT_DIR"
echo "---------------------------------------------"

# 确保报告目录存在
mkdir -p "$REPORT_DIR"

# 生成报告
echo "正在生成报告..."
allure generate "$RESULTS_DIR" -o "$REPORT_DIR" --clean

echo "---------------------------------------------"
echo "报告已生成: $REPORT_DIR"
echo "---------------------------------------------"
echo "启动报告服务器..."

# 启动报告服务器
echo "按 Ctrl+C 停止服务器"
allure open "$REPORT_DIR"

echo "---------------------------------------------"
echo "报告服务已关闭"
echo "============================================="
