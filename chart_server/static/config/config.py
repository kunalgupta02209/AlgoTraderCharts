mongodb_url = ""
from pathlib import Path
config_file = Path('db.conf')
with open(config_file) as f:
    mongodb_url = f.readline().strip()
timezone = 'Asia/Calcutta'
