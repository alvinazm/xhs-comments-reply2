#!/usr/bin/env python3
"""打包后的启动入口"""

import os
import sys
import json
import signal
import threading
from pathlib import Path

if getattr(sys, "frozen", False):
    bundle_dir = Path(sys._MEIPASS)
    app_dir = bundle_dir.parent
else:
    bundle_dir = Path(__file__).parent.parent
    app_dir = bundle_dir

os.environ["PYARMOR_HOME"] = str(bundle_dir / ".pyarmor")

sys.path.insert(0, str(bundle_dir))
sys.path.insert(0, str(bundle_dir / "app"))

logs_dir = app_dir.parent / "logs"
logs_dir.mkdir(exist_ok=True)

download_dir = app_dir.parent / "download"
download_dir.mkdir(exist_ok=True)

config_file = app_dir / "config.json"
if not config_file.exists():
    source_config = Path(__file__).parent.parent / "config.json"
    if source_config.exists():
        import shutil

        shutil.copy(source_config, config_file)
    else:
        default_config = {
            "chrome": {"host": "127.0.0.1", "port": 9292},
            "backend": {"host": "127.0.0.1", "port": 3030},
            "frontend": {"host": "127.0.0.1", "port": 5050},
            "flask": {"host": "0.0.0.0"},
        }
        with open(config_file, "w") as f:
            json.dump(default_config, f, indent=2)

from app.main import create_app, start_scheduler
from config import Config

app = create_app()
start_scheduler()

shutdown_flag = threading.Event()


def signal_handler(signum, frame):
    print("收到终止信号，正在关闭...")
    shutdown_flag.set()


signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

from werkzeug.serving import make_server


class ServerManager:
    def __init__(self):
        self.server = None

    def start(self):
        self.server = make_server(
            Config.FLASK_HOST, Config.FLASK_PORT, app, threaded=True, processes=1
        )
        print(f"Flask 服务启动: http://{Config.FLASK_HOST}:{Config.FLASK_PORT}")
        self.server.serve_forever()

    def stop(self):
        if self.server:
            self.server.shutdown()


manager = ServerManager()

server_thread = threading.Thread(target=manager.start, daemon=True)
server_thread.start()

try:
    while not shutdown_flag.is_set():
        shutdown_flag.wait(timeout=1)
except (KeyboardInterrupt, SystemExit):
    pass

print("正在关闭 Flask 服务...")
manager.stop()
print("服务已关闭")
