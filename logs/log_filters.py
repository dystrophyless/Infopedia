import logging

class ErrorLogFilter(logging.Filter):
    def filter(self, record) -> bool:
        return record.levelname == 'ERROR'

class CriticalLogFilter(logging.Filter):
    def filter(self, record) -> bool:
        return record.levelname == 'CRITICAL'