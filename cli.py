#!/usr/bin/env python3
"""멀티 트레이딩 에이전트 대시보드 CLI"""

from modules.context import Context
from cli import TradingDashboardApp


def main():
    """트레이딩 대시보드 CLI 진입점"""
    app = TradingDashboardApp(Context())
    app.run()


if __name__ == "__main__":
    main()
