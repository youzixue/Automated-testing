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
echo "--- 检查设备 $DEVICE_SERIAL 锁屏状态 ---"

# 检查屏幕状态
SCREEN_STATE_1=$(adb -s "$DEVICE_SERIAL" shell dumpsys power | grep 'Display Power' | grep -oE '(ON|OFF)' || echo "")
SCREEN_STATE_2=$(adb -s "$DEVICE_SERIAL" shell dumpsys power | grep 'mWakefulness=' | grep -oE '(Awake|Asleep)' || echo "")
SCREEN_STATE_3=$(adb -s "$DEVICE_SERIAL" shell dumpsys display | grep 'mState=' | grep -oE '(ON|OFF)' || echo "")

SCREEN_ON=false
if [ "$SCREEN_STATE_1" = "ON" ] || [ "$SCREEN_STATE_2" = "Awake" ] || [ "$SCREEN_STATE_3" = "ON" ]; then
  SCREEN_ON=true
  echo "设备 $DEVICE_SERIAL 屏幕已处于点亮状态"
fi

# 检查锁屏状态 - 使用多种方法
LOCKED=true
LOCK_CHECK_1=$(adb -s "$DEVICE_SERIAL" shell dumpsys window | grep -E 'mDreamingLockscreen=(true|false)' | head -n 1 | grep -oE '(true|false)' || echo "UNKNOWN")
LOCK_CHECK_2=$(adb -s "$DEVICE_SERIAL" shell dumpsys window policy | grep -E 'isStatusBarKeyguard=(true|false)' | grep -oE '(true|false)' || echo "UNKNOWN")
LOCK_CHECK_3=$(adb -s "$DEVICE_SERIAL" shell dumpsys power | grep -E 'mHoldingWakeLockSuspendBlocker=(true|false)' | grep -oE '(true|false)' || echo "UNKNOWN")

if [ "$LOCK_CHECK_1" = "false" ] || [ "$LOCK_CHECK_2" = "false" ] || [ "$LOCK_CHECK_3" = "true" ]; then
  echo "检测到设备 $DEVICE_SERIAL 可能已处于解锁状态"
  LOCKED=false
else
  echo "设备 $DEVICE_SERIAL 可能处于锁屏状态，需要解锁"
fi

# 如果屏幕关闭，先唤醒屏幕
if [ "$SCREEN_ON" = "false" ]; then
  echo "设备 $DEVICE_SERIAL 屏幕处于关闭状态，尝试唤醒..."
  adb -s "$DEVICE_SERIAL" shell input keyevent 26  # POWER键
  sleep 2
fi

# 如果设备可能被锁定，尝试解锁
if [ "$LOCKED" = "true" ]; then
  echo "尝试解锁设备 $DEVICE_SERIAL..."
  
  # 先尝试滑动解锁 (对于简单的滑动锁屏)
  adb -s "$DEVICE_SERIAL" shell input swipe 500 1500 500 500
  sleep 1
  
  # 如果提供了PIN码，尝试输入
  if [ ! -z "$UNLOCK_PIN" ]; then
    echo "尝试使用PIN码($UNLOCK_PIN)解锁设备 $DEVICE_SERIAL..."
    
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
fi

# 最终确认设备状态 (但不执行额外操作，避免影响其他应用)
FINAL_SCREEN_STATE_1=$(adb -s "$DEVICE_SERIAL" shell dumpsys power | grep 'Display Power' | grep -oE '(ON|OFF)' || echo "")
FINAL_SCREEN_STATE_2=$(adb -s "$DEVICE_SERIAL" shell dumpsys power | grep 'mWakefulness=' | grep -oE '(Awake|Asleep)' || echo "")
FINAL_SCREEN_STATE_3=$(adb -s "$DEVICE_SERIAL" shell dumpsys display | grep 'mState=' | grep -oE '(ON|OFF)' || echo "")

if [ "$FINAL_SCREEN_STATE_1" = "ON" ] || [ "$FINAL_SCREEN_STATE_2" = "Awake" ] || [ "$FINAL_SCREEN_STATE_3" = "ON" ]; then
  echo "设备 $DEVICE_SERIAL 屏幕现在处于点亮状态"
else
  echo "警告: 设备 $DEVICE_SERIAL 屏幕可能仍然关闭，这可能会影响测试"
fi

echo "--- 设备 $DEVICE_SERIAL 检查并解锁完成 ---"
exit 0 