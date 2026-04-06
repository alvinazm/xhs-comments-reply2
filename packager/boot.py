#!/usr/bin/env python3
"""打包后的启动入口"""

import os
import sys
import json
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

logs_dir = app_dir / "logs"
logs_dir.mkdir(exist_ok=True)

download_dir = app_dir / "download"
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

env_file = app_dir / ".env"
if not env_file.exists():
    source_env = Path(__file__).parent.parent / ".env"
    if source_env.exists():
        import shutil

        shutil.copy(source_env, env_file)
    else:
        with open(env_file, "w") as f:
            f.write(
                "# MinMax API Key\nMINIMAX_API_KEY=your_api_key\nMINIMAX_BASE_URL=https://api.minimaxi.com/v1\n"
            )

from app.main import create_app, start_scheduler
from config import Config

app = create_app()
start_scheduler()
app.run(host=Config.FLASK_HOST, port=Config.FLASK_PORT, debug=False)
