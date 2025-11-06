# modules/context/context.py

class Context:
    def __init__(self):
        self.reports = {}
        self.cache = {}
        self.logs = []

    def set_report(self, key: str, report: str):
        self.reports[key] = report

    def get_report(self, key: str) -> str:
        return self.reports.get(key, f"No report found for key: {key}")
    
    def set_cache(self, **kwargs):
        for key, value in kwargs.items():
            self.cache[key] = value

    def get_cache(self, key: str, default=None):
        return self.cache.get(key, default)
    
    def add_log(self, log: str):
        self.logs.append(log)
