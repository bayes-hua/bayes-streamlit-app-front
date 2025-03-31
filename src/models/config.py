# Database configuration
from datetime import datetime, timezone, timedelta

DB_PATH = 'voting_platform.db'
# 设置时区为UTC+8
TZ = timezone(timedelta(hours=8))