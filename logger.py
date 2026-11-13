import logging
from datetime import datetime, timedelta, timezone

def setup_logging(logfile: str = 'history.log'):
    class TimezoneFormatter(logging.Formatter):
        def __init__(self, fmt=None, datefmt=None, tz_offset=0):
            super().__init__(fmt=fmt, datefmt=datefmt)
            self.tz = timezone(timedelta(hours=tz_offset))
        def formatTime(self, record, datefmt=None):
            dt = datetime.fromtimestamp(record.created, self.tz)
            if datefmt:
                return dt.strftime(datefmt)
            return dt.strftime('%Y-%m-%d %H:%M:%S %z')
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    formatter = TimezoneFormatter(fmt='%(asctime)s - %(levelname)s - %(message)s', tz_offset=8)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    file_handler = logging.FileHandler(logfile,'w', encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger

logger = setup_logging()


logger.info('这是一条info日志')
logger.debug('这是一条debug日志')
logger.error('这是一条error日志')
logger.critical('这是一条critical日志')
