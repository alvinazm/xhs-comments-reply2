#!/bin/bash

# XHSCommentApp 启动脚本
# 将此脚本与 XHSCommentApp.app 放在同一目录下使用

# 获取脚本所在目录（自动定位，无需硬编码路径）
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_PATH="$SCRIPT_DIR/XHSCommentApp.app"
PORT=3030

# 检查应用是否存在
if [ ! -d "$APP_PATH" ]; then
    echo "错误: 找不到 XHSCommentApp.app，请确保它与 start_app.command 在同一目录下"
    osascript -e 'delay 3' -e 'tell application "Terminal" to close first window' 2>/dev/null &
    exit 1
fi

# 关闭 XHSCommentApp 应用
echo "正在关闭 XHSCommentApp..."
pkill -x XHSCommentApp 2>/dev/null

# 检查端口是否被占用
PID=$(lsof -ti:$PORT 2>/dev/null)

if [ -n "$PID" ]; then
    echo "端口 $PORT 已被占用 (PID: $PID)，正在关闭..."
    kill -9 $PID 2>/dev/null
    sleep 1
fi

# 启动应用
open "$APP_PATH"

# 等待应用启动
sleep 2

# 检查是否启动成功
if lsof -ti:$PORT >/dev/null 2>&1; then
    echo "应用启动成功 (http://localhost:$PORT)"
else
    echo "应用启动失败"
fi

# 延迟关闭终端窗口
osascript -e 'delay 2' -e 'tell application "Terminal" to close first window' 2>/dev/null &
