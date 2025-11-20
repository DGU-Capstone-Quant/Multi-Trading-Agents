"""공통 CSS 스타일"""

# 공통 컨테이너 스타일
COMMON_CONTAINER = """
    layout: vertical;
    background: $surface;
"""

HEADER_CONTAINER = """
    height: auto;
    background: $boost;
    border: heavy $primary;
    padding: 1 2;
    margin-bottom: 1;
"""

# 공통 타이틀 스타일
TITLE_STYLE = """
    text-style: bold;
    color: $accent;
    margin-bottom: 1;
    text-align: center;
"""

INFO_STYLE = """
    color: $text;
    text-align: center;
    text-style: bold;
"""

# 공통 버튼 스타일
BACK_BUTTON = """
    width: 25;
    height: 3;
    margin: 1;
    background: $warning;
    text-style: bold;
"""

BACK_BUTTON_HOVER = """
    background: $error;
    color: $text;
"""

# 보고서 토글 공통 스타일
REPORT_TOGGLE_CONTAINER = """
    .report-toggle-container {
        layout: vertical;
        height: auto;
        background: $panel;
        border: heavy $primary;
        padding: 0;
        margin-bottom: 2;
        overflow: hidden;
    }

    .report-toggle-button {
        width: 100%;
        height: 3;
        background: $boost;
        color: $accent;
        text-align: left;
        text-style: bold;
        border: none;
        padding: 0 2;
    }

    .report-toggle-button:hover {
        background: $primary;
        color: $text;
    }

    .report-toggle-button:focus {
        background: $primary;
    }

    .content-wrapper {
        height: auto;
        width: 100%;
    }

    .report-content-container {
        height: 40;
        max-height: 40;
        margin: 0;
        padding: 2;
        background: $surface;
        border-top: solid $secondary;
        overflow-x: auto;
        overflow-y: auto;
    }

    .report-content {
        color: $text;
        padding: 1;
        background: $surface;
        border: none;
        width: 100%;
        content-align: left top;
    }
"""
