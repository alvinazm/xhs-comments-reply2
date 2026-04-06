#!/bin/bash

# XHSCommentApp 停止脚本
# 将此脚本与 XHSCommentApp.app 放在同一目录下使用

PORT=3030

# 关闭 XHSCommentApp 应用
echo "正在关闭 XHSCommentApp..."
pkill -x XHSCommentApp 2>/dev/null

# 检查端口是否被占用
PID=$(lsof -ti:$PORT 2>/dev/null)

if [ -n "$PID" ]; then
    echo "正在关闭端口 $PORT 上的进程 (PID: $PID)..."
    kill -9 $PID 2>/dev/null
    sleep 1
    
    if lsof -ti:$PORT >/dev/null 2>&1; then
        echo "关闭失败"
    else
        echo "服务已停止"
    fi
else
    echo "端口 $PORT 未被占用，无需停止"
fi

# 延迟关闭终端窗口
osascript -e 'delay 1' -e 'tell application "Terminal" to close first window' 2>/dev/null &
