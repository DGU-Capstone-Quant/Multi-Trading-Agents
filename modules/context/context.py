# modules/context/context.py
from datetime import datetime as dt
import json
import os

class Context:
    def __init__(self):
        self.reports: dict = {} # 보고서 저장용:    에이전트가 생성하고 읽을 중요한 정보를 저장
        self.translations = {}  # 번역 저장용:      사용자에게 한국어로 출력할 번역된 문자열 저장
        self.config = {}        # 설정 저장용:      에이전트의 동작이나 api키 등을 저장
        self.cache = {}         # 캐시 저장용:      에이전트끼리 공유할 임시 데이터 저장
        self.logs = []          # 로그 저장용:      에이전트의 동작 기록 저장
        self.on_update = None   # 업데이트 콜백 함수
        self.load()
        self.set_default_config()
    
    def load(self):
        if not os.path.exists("./saved_context.json"):
            return
        with open("./saved_context.json", "r") as f:
            data = json.load(f)
            self.reports = data.get("reports", {})
            self.translations = data.get("translations", {})
            self.config = data.get("config", {})
            self.logs = data.get("logs", [])
    
    def save(self):
        data = {
            "reports": self.reports,
            "translations": self.translations,
            "config": self.config,
            "logs": self.logs,
        }
        with open("./saved_context.json", "w") as f:
            json.dump(data, f, indent=4)

    def _on_update(self):
        if self.on_update:
            self.on_update()


    def set_report(self, ticker: str, date: str, task: str, report: str):
        date = dt.strptime(date, "%Y%m%dT%H%M").strftime("%Y%m%dT%H")
        self.reports[ticker] = self.reports.get(ticker, {})
        self.reports[ticker][date] = self.reports[ticker].get(date, {})
        self.reports[ticker][date][task] = report
        self._on_update()

    def get_report(self, ticker: str, date: str, task: str) -> str:
        date = dt.strptime(date, "%Y%m%dT%H%M").strftime("%Y%m%dT%H")
        report = self.reports.get(ticker, {}).get(date, {}).get(task, None)
        if not report:
            return ""

        report_str = report.get("title", "") + "\n\n" +\
                    "Key Considerations:\n" + report.get("key_considerations", "") + "\n\n" +\
                    "Indicators Table:\n" + report.get("indicators_table", "") + "\n\n" +\
                    "Detailed Analysis:\n" + report.get("detailed_analysis", "") + "\n\n" +\
                    "Conclusion:\n" + report.get("conclusion", "") + "\n\n" +\
                    "Recommendation:\n" + report.get("recommendation", "")
        return report_str
    
    def set_translation(self, key: str, translation: str):
        self.translations[key] = translation
        self._on_update()

    def get_translation(self, key: str) -> str:
        return self.translations.get(key, f"No translation found for key: {key}")
    
    def set_config(self, **kwargs):
        for key, value in kwargs.items():
            self.config[key] = value
        self.save()
    
    def get_config(self, key: str, default=None):
        return self.config.get(key, default)
    
    def set_default_config(self):
        with open("./graph_config.json", "r") as f:
            default_config = json.load(f)
        self.config.update(default_config)
    
    def set_cache(self, **kwargs):
        for key, value in kwargs.items():
            self.cache[key] = value
        self._on_update()

    def get_cache(self, key: str, default=None):
        return self.cache.get(key, default)
    
    def add_log(self, summary: str, content: str = ""):
        log_entry = {
            "timestamp": dt.now().timestamp(),
            "summary": summary,
            "content": content,
        }
        self.logs.append(log_entry)
        self._on_update()
        self.save()

# log structure example
# log = {
#     "timestamp": dt.now().timestamp(),
#     "summary": "Report of AAPL on 20240101T0900 generated.",
#     "content": "Detailed log content here... Example: Report content...",
# }

