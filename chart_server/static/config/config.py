mongodb_url = ""
from pathlib import Path
config_file = Path('./chart_server/static/config/db.conf')
with open(config_file) as f:
    mongodb_url = f.readline()
timezone = 'Asia/Calcutta'
