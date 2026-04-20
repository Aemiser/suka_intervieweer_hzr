# main.py 顶部 imports 修改如下：

import sys
from dotenv import load_dotenv
load_dotenv()

from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout
# ✅ 删除：QTabWidget, QTabBar, QSize, QIcon 的单独导入（组件内部已处理）

from service.db import DatabaseManager
from service.schema import SchemaInitializer
from service.interview_engine_sdk.interview_engine import InterviewEngine
from service.helper_engine import HelperEngine

from UI.panel.interview_panel import InterviewPanel
from UI.panel.helper_panel import HelperPanel
from UI.panel.history_panel import HistoryPanel
from UI.panel.quiz_panel import QuizPanel
from UI.components.info import Theme as T
# ✅ 删除：Icons, IconSize 的导入（组件内部已处理）
# ✅ 新增：导入封装好的 Tab 组件
from UI.components.tab_widget import EqualWidthTabWidget

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # ── 基础服务 ──────────────────────────────────────────────────────────────
    db = DatabaseManager("interview.db")
    SchemaInitializer(db).initialize()

    # ── 引擎层 ────────────────────────────────────────────────────────────────
    interview_engine = InterviewEngine(db=db)
    helper_engine = HelperEngine(db=db)

    # ── 主窗口 ────────────────────────────────────────────────────────────────
    window = QMainWindow()
    window.setWindowTitle("AI 模拟面试与能力提升平台")
    window.resize(1340, 880)
    window.setStyleSheet(f"QMainWindow {{ background: {T.BG}; }}")

    central = QWidget()
    window.setCentralWidget(central)
    root = QHBoxLayout(central)
    root.setContentsMargins(0, 0, 0, 0)
    root.setSpacing(0)

    # ✅【简化】直接使用封装好的组件，一行创建 + 样式初始化
    tabs = EqualWidthTabWidget()
    # ── 创建面板实例 ──────────────────────────────────────────────────────────
    interview_panel = InterviewPanel(db, interview_engine)
    history_panel = HistoryPanel(db)
    quiz_panel = QuizPanel(db)
    agent_panel = HelperPanel(helper_engine)

    # ── 添加带图标的 Tab（图标着色为 T.TEXT 黑色）────────────────────────────
    # 格式：(面板实例, 图标逻辑名, 显示文本)
    tab_configs = [
        (interview_panel, "record_voice", "模拟面试"),
        (quiz_panel, "menu_book", "题库练习"),
        (history_panel, "query_stats", "历史分析"),
        (agent_panel, "smart_toy", "AI 助手"),
    ]
    tabs.add_tabs(tab_configs)
    root.addWidget(tabs)
    # ── Tab 切换时刷新历史面板 ───────────────────────────────────────────────
    tabs.currentChanged.connect(
        lambda idx: history_panel._refresh() if tabs.widget(idx) is history_panel else None
    )

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()