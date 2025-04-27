#!/bin/sh
# deploy_allure_report.sh: 复制 Allure 报告到目标目录并修正权限。
# 假设源报告目录已包含由 Allure generate 生成的、合并了历史记录的正确 history 目录。
set -e

SRC_REPORT_DIR="$1" # 容器内生成的报告的路径 (例如, /report)
DEST_NGINX_DIR="$2" # 容器内 Nginx 目标目录的路径 (例如, /dest_nginx)

if [ -z "$SRC_REPORT_DIR" ] || [ -z "$DEST_NGINX_DIR" ]; then
  echo "错误：源报告目录或目标 Nginx 目录未提供！"
  exit 1
fi

echo "部署报告从 ${SRC_REPORT_DIR} 到 ${DEST_NGINX_DIR}"

# 1. 确保目标 Nginx 目录存在
echo "确保目标目录存在: ${DEST_NGINX_DIR}"
mkdir -p "$DEST_NGINX_DIR"
# 可选：如果希望每次都全新复制，可以在这里清空目标目录
# echo "清空目标目录 ${DEST_NGINX_DIR}..."
# rm -rf "${DEST_NGINX_DIR:?}/"*

# 2. 复制新的报告文件 (包括正确的 history 目录)
#    推荐使用 rsync，因为它更高效且能处理删除旧文件。
echo "复制新的报告文件 (包含 history)..."
if command -v rsync > /dev/null; then
    # 使用 rsync 同步目录。--delete 会删除目标目录中存在但源目录中不存在的文件。
    rsync -a --delete "${SRC_REPORT_DIR}/" "${DEST_NGINX_DIR}/"
else
    echo "警告: 未找到 rsync 命令，将使用 cp 命令。这可能较慢，并且不会清理目标目录中的旧文件。"
    # 如果没有 rsync，则使用 cp 复制。注意：这不会删除目标目录中多余的文件。
    # 为了确保完全覆盖，可以在步骤 1 中先清空目标目录。
    cp -rf "${SRC_REPORT_DIR}/"* "${DEST_NGINX_DIR}/"
fi

# 3. 为整个目标目录修正权限
#    根据需要调整权限设置。755 通常适用于 Web 服务器目录。
echo "修正目标目录 ${DEST_NGINX_DIR} 的最终权限..."
chmod -R 755 "${DEST_NGINX_DIR}"

echo "Allure 报告部署完成。"