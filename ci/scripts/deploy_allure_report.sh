    #!/bin/sh
    # deploy_allure_report.sh: Handles Allure history, copies report, fixes permissions and encoding.
    set -e

    SRC_REPORT_DIR="$1" # Path to the generated report inside the container (e.g., /report)
    DEST_NGINX_DIR="$2" # Path to the Nginx directory inside the container (e.g., /dest)

    if [ -z "$SRC_REPORT_DIR" ] || [ -z "$DEST_NGINX_DIR" ]; then
      echo "错误：源报告目录或目标 Nginx 目录未提供！"
      exit 1
    fi

    HISTORY_DIR="${DEST_NGINX_DIR}/history"
    TEMP_HISTORY_BACKUP="/tmp/history_backup_$$" # Use process ID for uniqueness

    echo "Deploying report from ${SRC_REPORT_DIR} to ${DEST_NGINX_DIR}"

    # 1. Backup existing history if it exists
    if [ -d "$HISTORY_DIR" ]; then
      echo "History directory exists, backing up to ${TEMP_HISTORY_BACKUP}..."
      mkdir -p "$TEMP_HISTORY_BACKUP"
      # Use cp -a to preserve attributes, ignore errors if dir is empty
      cp -a "$HISTORY_DIR"/* "$TEMP_HISTORY_BACKUP/" 2>/dev/null || echo "No existing history files to backup."

      # Attempt to fix encoding on backup JSON files (requires iconv)
      echo "Ensuring UTF-8 encoding for backed-up JSON files..."
      if command -v iconv > /dev/null; then
        find "$TEMP_HISTORY_BACKUP" -name "*.json" -type f -exec sh -c '
          file="$1"
          temp_file=$(mktemp)
          if iconv -f utf-8 -t utf-8 -c "$file" > "$temp_file"; then
            mv "$temp_file" "$file"
          else
            echo "Warning: iconv failed for $file, keeping original."
            rm "$temp_file"
          fi
        ' sh {} \; || echo "No JSON files found in backup or iconv failed."
      else
          echo "Warning: iconv command not found. Skipping encoding fix for backup."
      fi
    else
      echo "No existing history directory found."
      # Ensure the history dir exists for the copy later
      mkdir -p "$HISTORY_DIR"
    fi

    # 2. Copy the new report files (overwriting previous report, except history)
    echo "Copying new report files..."
    # Use rsync for potentially better handling of large numbers of files
    # Exclude the history directory from the source if it exists there
    if command -v rsync > /dev/null; then
        rsync -a --delete --exclude='history/' "${SRC_REPORT_DIR}/" "${DEST_NGINX_DIR}/"
    else
        echo "Warning: rsync not found, using cp. This might be slower."
        # Copy all, then remove the new history if source had one
        cp -rf "${SRC_REPORT_DIR}/"* "${DEST_NGINX_DIR}/"
        if [ -d "${DEST_NGINX_DIR}/history" ]; then
             # If we copied a history dir from source, remove it to restore the backup
             # Check if backup exists before removing potentially good new history
             if [ -d "$TEMP_HISTORY_BACKUP" ]; then
                 echo "Removing history copied from source report..."
                 rm -rf "${DEST_NGINX_DIR}/history"
             else
                 echo "Source report contained history, but no backup exists. Keeping history from source."
             fi
        fi
    fi


    # 3. Restore the backed-up history if backup exists
    if [ -d "$TEMP_HISTORY_BACKUP" ]; then
      echo "Restoring history directory..."
      # Ensure destination history directory exists
      mkdir -p "$HISTORY_DIR"
      # Copy contents back
      cp -a "$TEMP_HISTORY_BACKUP"/* "$HISTORY_DIR/" 2>/dev/null || echo "No history files to restore."
      # Clean up backup
      rm -rf "$TEMP_HISTORY_BACKUP"
    elif [ ! -d "$HISTORY_DIR" ]; then
        # If no backup and no history dir, create default empty history files
        echo "Creating default empty history files..."
        mkdir -p "$HISTORY_DIR"
        echo "{}" > "${HISTORY_DIR}/history.json"
        echo "[]" > "${HISTORY_DIR}/history-trend.json"
        echo "[]" > "${HISTORY_DIR}/duration-trend.json"
        echo "[]" > "${HISTORY_DIR}/categories-trend.json"
        echo "[]" > "${HISTORY_DIR}/retry-trend.json"
    fi

    # 4. Fix permissions for the entire destination directory
    echo "Fixing final permissions for ${DEST_NGINX_DIR}..."
    chmod -R 755 "${DEST_NGINX_DIR}" # Or more specific if needed: find ... -exec ...

    echo "Allure report deployment complete."