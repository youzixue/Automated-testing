#!/bin/sh
set -e # 如果任何命令失败，则立即退出
set -x # 打印执行的命令

DEVICE_SERIAL="$1"
UNLOCK_PIN="$2" # 设备解锁PIN码，可选参数

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

# ===== 设备解锁逻辑 =====
echo "--- 检查设备 $DEVICE_SERIAL 屏幕状态 ---"
SCREEN_STATE=$(adb -s "$DEVICE_SERIAL" shell dumpsys power | grep 'Display Power' | grep -oE '(ON|OFF)' || echo "UNKNOWN")
if [ "$SCREEN_STATE" != "ON" ]; then
  echo "设备 $DEVICE_SERIAL 屏幕处于关闭状态，尝试唤醒..."
  adb -s "$DEVICE_SERIAL" shell input keyevent 26  # POWER按键
  sleep 2
fi

echo "--- 检查设备 $DEVICE_SERIAL 锁屏状态 ---"
LOCKED=$(adb -s "$DEVICE_SERIAL" shell dumpsys window | grep -E 'mDreamingLockscreen=(true|false)' | grep -oE '(true|false)' || echo "UNKNOWN")

if [ "$LOCKED" = "true" ]; then
  echo "设备 $DEVICE_SERIAL 处于锁屏状态，尝试解锁..."
  # 先尝试滑动解锁
  adb -s "$DEVICE_SERIAL" shell input swipe 500 1500 500 500
  sleep 1
  
  # 再次检查锁屏状态
  LOCKED=$(adb -s "$DEVICE_SERIAL" shell dumpsys window | grep -E 'mDreamingLockscreen=(true|false)' | grep -oE '(true|false)' || echo "UNKNOWN")
  
  # 如果仍然锁屏且提供了PIN码，尝试输入PIN码
  if [ "$LOCKED" = "true" ] && [ ! -z "$UNLOCK_PIN" ]; then
    echo "尝试使用PIN码解锁设备 $DEVICE_SERIAL..."
    # 输入每个数字
    for i in $(seq 1 ${#UNLOCK_PIN}); do
      DIGIT=$(echo "$UNLOCK_PIN" | cut -c$i)
      adb -s "$DEVICE_SERIAL" shell input text "$DIGIT"
      sleep 0.2
    done
    # 点击回车确认
    adb -s "$DEVICE_SERIAL" shell input keyevent 66
    sleep 2
  fi
  
  # 最终再次检查
  LOCKED=$(adb -s "$DEVICE_SERIAL" shell dumpsys window | grep -E 'mDreamingLockscreen=(true|false)' | grep -oE '(true|false)' || echo "UNKNOWN")
  if [ "$LOCKED" = "true" ]; then
    echo "警告: 无法解锁设备 $DEVICE_SERIAL，这可能会影响后续测试！"
    # 不要在此退出，以保持测试继续进行，可能某些测试不需要解锁
    # 我们会返回退出码1，让调用脚本决定如何处理
    exit 1
  else
    echo "设备 $DEVICE_SERIAL 已成功解锁"
  fi
else
  echo "设备 $DEVICE_SERIAL 已处于解锁状态"
fi

# 最终确保设备亮屏
SCREEN_STATE=$(adb -s "$DEVICE_SERIAL" shell dumpsys power | grep 'Display Power' | grep -oE '(ON|OFF)' || echo "UNKNOWN")
if [ "$SCREEN_STATE" != "ON" ]; then
  echo "设备 $DEVICE_SERIAL 屏幕仍然关闭，再次尝试唤醒..."
  adb -s "$DEVICE_SERIAL" shell input keyevent 26
  sleep 1
fi

echo "--- 设备 $DEVICE_SERIAL 检查并解锁完成 ---"
exit 0 