# modules/context/context.py
from datetime import datetime as dt

class Context:
    def __init__(self):
        self.reports: dict = {}       # 보고서 저장용:    에이전트가 생성하고 읽을 중요한 정보를 저장
        self.translations = {}  # 번역 저장용:      사용자에게 한국어로 출력할 번역된 문자열 저장
        self.config = {}        # 설정 저장용:      에이전트의 동작이나 api키 등을 저장
        self.cache = {}         # 캐시 저장용:      에이전트끼리 공유할 임시 데이터 저장
        self.logs = []          # 로그 저장용:      에이전트의 동작 기록 저장



    def set_report(self, ticker: str, date: str, task: str, report: str):
        date = dt.strptime(date, "%Y%m%dT%H%M").strftime("%Y%m%dT%H")
        self.reports[ticker] = self.reports.get(ticker, {})
        self.reports[ticker][date] = self.reports[ticker].get(date, {})
        self.reports[ticker][date][task] = report

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

    def get_translation(self, key: str) -> str:
        return self.translations.get(key, f"No translation found for key: {key}")
    
    def set_config(self, **kwargs):
        for key, value in kwargs.items():
            self.config[key] = value
    
    def get_config(self, key: str, default=None):
        return self.config.get(key, default)
    
    def set_cache(self, **kwargs):
        for key, value in kwargs.items():
            self.cache[key] = value

    def get_cache(self, key: str, default=None):
        return self.cache.get(key, default)
    
    def add_log(self, log: str):
        self.logs.append(log)
