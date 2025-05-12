#!/bin/sh
set -e # 如果任何命令失败，则立即退出
set -x # 打印执行的命令

DEVICE_SERIAL="$1"

if [ -z "$DEVICE_SERIAL" ]; then
  echo "错误：设备序列号未提供！"
  exit 1
fi

echo "设备序列号是: $DEVICE_SERIAL"

# 尝试重启 ADB 服务以获取最新设备列表，尤其是针对 USB 设备
# 对于网络设备，如果 adb connect 失败，后续的 adb devices 可能也无法找到它
# 但如果 adb connect 成功或已连接，重启服务通常是无害的
echo "--- 为确保 ADB 服务状态最新，尝试重启 ---"
adb kill-server
sleep 1
adb start-server
sleep 2 # 给 ADB 一点时间来完成启动和设备识别

if echo "$DEVICE_SERIAL" | grep -q ':'; then
  echo "--- 检测到可能是网络设备，尝试 ADB connect ---"
  # 对于网络设备，即使`adb start-server`之后，也需要`adb connect`
  # 如果连接失败，不要立即退出，让后续的`adb devices -l`来最终确认
  adb connect "$DEVICE_SERIAL" || echo "警告: adb connect $DEVICE_SERIAL 失败或设备已连接/无法连接。"
  sleep 3 # 等待连接操作完成
else
  echo "--- 检测到可能是 USB 设备，跳过 ADB connect ---"
  # USB 设备应该在 adb start-server 后被自动检测到
fi

echo "--- ADB devices 输出 (尝试列出所有设备) ---"
adb devices -l

echo "--- 专门检查设备状态: $DEVICE_SERIAL ---"
# 使用 grep -E 来支持扩展正则表达式，并确保序列号后跟空白和 'device'
# 我们希望设备是 'device' 状态，而不是 'offline', 'unauthorized' 等
if adb devices -l | grep -E "$DEVICE_SERIAL[[:space:]]+device"; then
  echo "设备 $DEVICE_SERIAL 状态为 'device'，检查成功！"
else
  echo "错误：设备 $DEVICE_SERIAL 未找到，或状态不是 'device'！"
  echo "再次列出所有设备以供诊断:"
  adb devices -l
  exit 1
fi

exit 0 