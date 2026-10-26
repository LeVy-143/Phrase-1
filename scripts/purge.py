"""Apply proposed 30-day session retention (also cascades assessments/traces)."""
import os
from datetime import datetime,timedelta,timezone
from pathlib import Path
from src.storage import Storage
if __name__=='__main__':
    storage=Storage(Path(os.environ.get('IELTS_DB_PATH','runtime/ielts.sqlite3')))
    print('Deleted expired traces:',storage.purge_traces((datetime.now(timezone.utc)-timedelta(days=7)).isoformat()))
    print('Deleted expired sessions:',storage.purge((datetime.now(timezone.utc)-timedelta(days=30)).isoformat()))
