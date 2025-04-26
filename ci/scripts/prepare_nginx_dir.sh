    #!/bin/sh
    # prepare_nginx_dir.sh: Creates Nginx directory and sets initial permissions.
    set -e # Exit immediately if a command exits with a non-zero status.

    NGINX_DIR="$1"

    if [ -z "$NGINX_DIR" ]; then
      echo "错误：Nginx 目录路径未提供！"
      exit 1
    fi

    echo "Preparing Nginx directory: ${NGINX_DIR}"
    mkdir -p "${NGINX_DIR}"
    mkdir -p "${NGINX_DIR}/history"
    # Set broad permissions initially, can be refined if needed
    chmod -R 777 "${NGINX_DIR}"
    # find "${NGINX_DIR}" -type d -exec chmod 755 {} \;
    # find "${NGINX_DIR}" -type f -exec chmod 644 {} \;
    echo "Nginx directory prepared."