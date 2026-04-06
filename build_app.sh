#!/bin/bash
set -e

echo "=== XHS 评论助手打包脚本 ==="

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "0/5 检查并准备虚拟环境..."
if [ ! -d "venv" ]; then
    echo "  创建虚拟环境..."
    python -m venv venv
fi

echo "  激活虚拟环境..."
source venv/bin/activate

echo "  检查并安装依赖..."
pip install --upgrade pip -q
pip install -r backend/requirements.txt -q
pip install pyinstaller pyarmor -q

echo "1/5 构建前端..."
cd frontend && npm run build && cd ..

echo "2/5 复制前端文件到后端 static 目录..."
mkdir -p backend/static
cp -r frontend/dist/* backend/static/

echo "3/5 加密后端 Python 代码..."
rm -rf dist_backend
cd backend && pyarmor gen -O ../dist_backend -r app/ && cd ..

echo "3.5/5 复制 prompts 目录..."
mkdir -p dist_backend/prompts
cp -r backend/prompts/* dist_backend/prompts/

echo "4/5 运行 PyInstaller 打包..."
rm -rf dist build
PROJECT_ROOT="$SCRIPT_DIR" pyinstaller xhs_app.spec --clean

echo ""
echo "5/5 整理应用包..."
APP_DIR="$SCRIPT_DIR/dist/XHSCommentApp"
if [ -d "$APP_DIR/Contents" ]; then
    rm -rf "$SCRIPT_DIR/dist/XHSCommentApp.app"
    mv "$APP_DIR" "$SCRIPT_DIR/dist/XHSCommentApp.app"
    echo "输出目录: dist/XHSCommentApp.app/"
    echo "运行应用: open dist/XHSCommentApp.app"
else
    echo "输出目录: dist/XHSCommentApp/"
    echo "运行应用: open dist/XHSCommentApp/XHSCommentApp"
fi