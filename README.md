# AI 模拟面试与能力提升平台

> 锐捷网络企业命题 · 开发者协作手册
> 面向队内协作者（语音模块 & 双知识库）

---

## 目录

- [项目总览](#1-项目总览)
- [快速启动](#2-快速启动)
- [协作者任务分工](#3-协作者任务分工)
- [任务 A — 语音交互](#4-任务-a--语音交互agent_core-推送)
- [任务 B — 双知识库](#5-任务-b--双知识库-rag-扩展)
- [数据库结构](#6-数据库结构说明)
- [UI 组件规范](#7-ui-组件规范)
- [工具权限体系](#8-工具权限体系skillset)
- [提交规范](#9-开发与提交规范)
- [FAQ](#10-常见问题-faq)

---

## 1. 项目总览

### 1.1 赛题背景

本项目为锐捷网络企业命题「AI 模拟面试与能力提升软件」竞赛作品。

核心场景：
- 学生通过模拟面试，练习 Java 后端 / 前端技术岗位面试题
- AI 面试官出题 → 学生回答 → 多维度评分 → 个性化提升建议
- **（新增）** 老师上传课程资料后，学生可对课程项目进行「课程答辩式面试」

### 1.2 当前架构一览

| 层次 | 技术栈 | 说明                                          |
|------|--------|---------------------------------------------|
| UI 层 | PySide6 6.6 | 桌面端，四个主面板                                   |
| Service 层 | Python 3.11 | Agent / Engine / Evaluator / KnowledgeStore |
| 工具层 | LangChain Core + 原生 SDK | 8 类工具，按 SkillSet 权限分发                       |
| 大模型 | Qwen (DashScope) | qwen-plus / qwen3-omni-flash / qwen3-asr    |
| 知识库 | 阿里云百炼 RAG | 目前 1 个库，本次扩展为 2 个,都在百炼知识库中（见第 5 节）          |
| 存储 | SQLite (WAL 模式) | 本地单文件，结构见 `service/schema.py`               |

### 1.3 目录结构

```
ai_interview/
├── main.py                      # 启动入口
├── .env                         # 密钥配置（不提交 Git）
├── .env.example                 # 密钥模板
├── requirements.txt
├── README.md                    # 本文件
│
├── service/
│   ├── db.py                    # SQLite 连接管理（单例）
│   ├── schema.py                # 建表 & 种子数据
│   ├── agent_core.py            # Agent 框架（流式 + 工具调用）
│   ├── interview_engine.py      # 面试流程引擎
│   ├── evaluator.py             # 多维度评分
│   ├── knowledge_store.py       # 知识库检索（百炼 RAG）← 本次扩展
│   ├── voice.py                 # 语音 STT/TTS（新增，任务 A）
│   └── tools/
│       ├── __init__.py          # 统一导出
│       ├── registry.py          # 工具注册中心（懒加载）
│       ├── permissions.py       # SkillSet 权限集合定义
│       ├── db_tools.py          # 题库/历史/岗位工具（含分页）
│       ├── knowledge_tools.py   # RAG 检索工具 ← 本次扩展双库
│       └── search_tools.py      # 博查/Wikipedia 联网搜索
│
├── UI/
│   ├── components.py            # 统一组件库（Theme / ChatBubble 等）
│   ├── interview_panel.py       # 面试主界面
│   ├── quiz_panel.py            # 题库练习（含服务端分页/排序）
│   ├── history_panel.py         # 历史成长曲线
│   └── agent_panel.py           # AI 知识助手
│
└──（cloud 云上） knowledge_base/
    ├── interview/               # 面试要点知识库本地备份（对应百炼库 A）
    │   └── *.txt
    └── teaching/                # 老师教学资料（对应百炼库 B）← 新增
        └── *.pdf / *.txt / ...  # 由老师上传，不提交 Git
```

---

## 2. 快速启动

### 2.1 环境要求

| 依赖 | 版本 | 备注 |
|------|------|------|
| Python | 3.11+ | 低版本缺少 `match/case`，不兼容 |

其他直接跟着![requirements.txt](requirements.txt)来即可，pycharm有安装提示的

### 2.2 安装步骤

1. 克隆仓库
2. 配置密钥
3. 安装依赖项

### 2.3 .env 密钥说明

> ⚠️ **所有 Key 均不要提交 Git**，`.gitignore` 已包含 `.env`
> 目前的.env_example只是给出了样例实现，里面的apikey并不存在
> 你需要添加的是语音sdk需要添加的依赖项

```env
# ── 核心（必填）──────────────────────────────────────────
DASHSCOPE_API_KEY="sk-xxx"           # 所有 Qwen 模型 + 语音 API 的统一 Key

# ── 知识库（必填）────────────────────────────────────────
BAILOU_KNOWLEDGE_BASE_ID="xxx"       # 面试要点库 ID（百炼控制台获取，库 A）
BAILOU_TEACHING_KB_ID="xxx"         # 教学资料库 ID（新增，库 B）

# ── 百炼官方 SDK 模式（三件套，比 HTTP 模式更稳定）──────
BAILOU_WORKSPACE_ID="xxx"
ALIBABA_CLOUD_ACCESS_KEY_ID="xxx"
ALIBABA_CLOUD_ACCESS_KEY_SECRET="xxx"

# ── 联网搜索（可选，不填则跳过 web_search 工具）─────────
BOCHA_API_KEY="xxx"                  # https://open.bochaai.com 注册获取
```

---

## 3. 协作者任务分工

本次迭代有两个独立开发任务，可以**并行**进行，互不依赖：
多个人协同分工完成

| 任务 | 负责内容 | 关键文件 | 优先级 |
|------|----------|----------|--------|
| **任务 A** | 语音交互推送到 agent_core | `service/voice.py`（新建）<br>`UI/interview_panel.py` | P0 |
| **任务 B** | 双知识库 RAG 扩展 | `service/knowledge_store.py`<br>`service/tools/knowledge_tools.py`<br>`service/tools/permissions.py` | P0 |

---

## 4. 任务 A — 语音交互（agent_core 推送）

### 4.1 背景与目标

命题要求多模态交互。当前版本面试完全依赖文字输入，语音模块需实现：

- 🎤 **语音输入**：学生录音 → STT（语音转文字）→ 注入现有面试流程
- 🔊 **语音播报**（可选加分项）：AI 问题 → TTS → 播报给学生
- 😊 **情感分析**：实时识别学生语音情绪 → 影响表达维度评分

> ✅ **关键约定**：语音模块只需在 UI 层增加录音按钮，STT 后将文字填入现有输入框。**不改变 agent_core 的任何调用逻辑**，改动量极小。

### 4.2 推荐使用的 Qwen 语音 API

三个模型均使用同一个 `DASHSCOPE_API_KEY`，无需额外申请。

| API | 模型名 | 用途 | 接入难度 |
|-----|--------|------|----------|
| STT（录音文件） | `qwen3-asr-flash` | 完整录音 → 文字 | ⭐ 最简 |
| STT（实时流式） | `qwen3-asr-flash-realtime` | 实时识别 + 情感分析 | ⭐⭐⭐ |
| TTS（实时合成） | `qwen3-tts-flash-realtime` | AI 面试官语音播报 | ⭐⭐⭐ |

### 4.3 P0 版本：录音文件 STT（推荐先做这个）

#### Step 1 — 安装音频依赖

```bash
pip install sounddevice soundfile
# requirements.txt 里也要加上这两行
```

#### Step 2 — 新建 `service/voice.py`
样例实现不代表最终版本
```python
# service/voice.py
"""
语音录制 & STT 模块
P0 版本：录音文件 → qwen3-asr-flash → 文字
"""
import os
import tempfile
import threading

import requests
import sounddevice as sd
import soundfile as sf


def record_audio(seconds: int = 8, sample_rate: int = 16000) -> str:
    """
    录制音频，返回临时 .wav 文件路径。
    阻塞调用，录完才返回。
    """
    audio = sd.rec(
        int(seconds * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype="int16",
    )
    sd.wait()
    tmp = tempfile.mktemp(suffix=".wav")
    sf.write(tmp, audio, sample_rate)
    return tmp


def stt(audio_path: str) -> str:
    """
    调用 qwen3-asr-flash 将音频文件转换为文字。
    返回识别文本，失败时返回空字符串。
    """
    api_key = os.getenv("DASHSCOPE_API_KEY", "")
    try:
        with open(audio_path, "rb") as f:
            resp = requests.post(
                "https://dashscope.aliyuncs.com/compatible-mode/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {api_key}"},
                files={"file": ("audio.wav", f, "audio/wav")},
                data={"model": "qwen3-asr-flash"},
                timeout=30,
            )
        if resp.status_code == 200:
            return resp.json().get("text", "")
        print(f"[STT] HTTP {resp.status_code}: {resp.text[:200]}")
        return ""
    except Exception as e:
        print(f"[STT] 失败: {e}")
        return ""
    finally:
        # 清理临时文件
        try:
            os.unlink(audio_path)
        except Exception:
            pass
```

#### Step 3 — 在 `UI/interview_panel.py` 中增加录音按钮

在 `_build_footer()` 方法的 `input_row` 里追加，**不改动其他逻辑**：

```python
# interview_panel.py → _build_footer() 方法中

# 在 input_row.addWidget(self.send_btn) 之后追加：
self.voice_btn = ButtonFactory.primary("🎤", T.ACCENT, height=54)
self.voice_btn.setFixedWidth(54)
self.voice_btn.setToolTip("按住录音（5秒），松开后自动识别")
self.voice_btn.clicked.connect(self._toggle_recording)
input_row.addWidget(self.voice_btn)

# 初始状态
self._is_recording = False
```

```python
# interview_panel.py 中新增方法

def _toggle_recording(self):
    if self._is_recording:
        return  # 录音中，忽略重复点击
    self._is_recording = True
    self.voice_btn.setText("🔴")
    self.voice_btn.setEnabled(False)

    def run():
        from service.voice import record_audio, stt
        path = record_audio(seconds=8)
        text = stt(path)
        # 回主线程更新 UI（用 QTimer 或 Signal）
        if text:
            self.answer_input.setPlainText(text)
        self._is_recording = False
        self.voice_btn.setText("🎤")
        self.voice_btn.setEnabled(True)

    threading.Thread(target=run, daemon=True).start()
```

> ⚠️ `run()` 里的 UI 更新需要在主线程执行。最稳妥的方式是用一个 `Signal(str)` 信号传回文字，在槽函数里 `setPlainText`。参考 `AgentPanel` 里 `StreamSignals` 的写法。

### 4.4 P1 版本：实时流式 + 情感分析

实时识别通过 WebSocket 接入，情感分析结果可作为 `clarity_score` 的修正因子：

- 情感标签：`惊讶 / 平静 / 愉快 / 悲伤 / 厌恶 / 愤怒 / 恐惧`
- 在 `service/evaluator.py` 的 `_build_prompt()` 中追加情感字段
- 评分权重：平静/愉快 +0.5，明显紧张/颤抖 -0.5

> ℹ️ 实时方案改动较大，**建议 P0 先上线，再迭代**。P0 已足够满足命题多模态要求。

### 4.5 audio_path 字段（已预留，直接用）

`interview_turn` 表中已有 `audio_path` 字段，录音文件路径直接写进去：

```python
# interview_engine.py → submit_answer() 签名改为：
def submit_answer(self, session_id: int, answer: str, audio_path: str = "") -> dict:
    ...
    self.db.execute(
        "UPDATE interview_turn SET student_answer=?, scores=?, audio_path=? WHERE id=?",
        (answer, json.dumps(eval_result.to_dict()), audio_path, turn_id),
    )
```

---

## 5. 任务 B — 双知识库 RAG 扩展

### 5.1 背景与设计意图

> 🌟 **这是本项目最大的差异化亮点，答辩时重点宣讲！**

当前 `KnowledgeStore` 只连接一个百炼知识库。新版本需维护**两个知识库**：

| 知识库 | 环境变量 | 内容 | 维护者 | 场景 |
|--------|----------|------|--------|------|
| **库 A — 面试要点库** | `BAILOU_KNOWLEDGE_BASE_ID` | 通用面试知识（现有） | 技术团队 | 所有面试模式 |
| **库 B — 教学资料库** | `BAILOU_TEACHING_KB_ID` | 老师课程 PPT / 讲义 / 项目文档 | **老师上传** | 课程答辩模式 |

### 5.2 课程答辩模式的产品逻辑

老师把教学资料上传到「教学资料库」后，AI 可以基于这些内容对学生出题，考察学生对课程项目的掌握程度。

这等价于把「老师答辩学生项目」这一传统场景数字化：

1. 老师上传课程讲义、项目需求文档、参考实现
2. 学生进入「课程答辩」模式
3. AI 面试官从讲义中理解课程核心知识点，据此出题
4. 评分结合面试要点（库 A）+ 课程要求（库 B）双重参考
5. 所以需要做各个agent的权限管理！！！！！！

### 5.3 `knowledge_store.py` 修改方案

#### ① 新增 `KnowledgeType` 枚举

```python
# service/knowledge_store.py 顶部新增
from enum import Enum

class KnowledgeType(Enum):
    INTERVIEW = "interview"   # 面试要点库 A（默认）
    TEACHING  = "teaching"   # 教学资料库 B
```

#### ② `__init__` 中初始化两个库 ID

```python
def __init__(self, db=None, ...):
    ...
    self.knowledge_base_id = os.getenv("BAILOU_KNOWLEDGE_BASE_ID", "")  # 原有
    self.teaching_kb_id    = os.getenv("BAILOU_TEACHING_KB_ID", "")     # 新增
```

#### ③ `retrieve()` 支持按类型路由

```python
def retrieve(
    self,
    query: str,
    knowledge_type: KnowledgeType = KnowledgeType.INTERVIEW,  # 新增参数
    job_position_id: int = 0,
    top_k: int = 3,
) -> List[str]:
    # 根据 knowledge_type 选择库 ID
    if knowledge_type == KnowledgeType.TEACHING:
        kb_id = self.teaching_kb_id
        if not kb_id:
            return ["⚠️ 教学资料库未配置（BAILOU_TEACHING_KB_ID）"]
    else:
        kb_id = self.knowledge_base_id

    # 后续检索逻辑不变，只是把 self.knowledge_base_id 换成 kb_id
    # _retrieve_sdk() 和 _retrieve_http() 也需要接收 kb_id 参数
    ...
```

#### ④ 新增混合检索方法（课程答辩专用）

```python
def retrieve_combined(self, query: str, top_k: int = 3) -> str:
    """同时检索面试要点库和教学资料库，合并结果，用于课程答辩出题。"""
    interview_results = self.retrieve(query, KnowledgeType.INTERVIEW, top_k=top_k)
    teaching_results  = self.retrieve(query, KnowledgeType.TEACHING,  top_k=top_k)

    lines = []
    if interview_results and not interview_results[0].startswith("⚠️"):
        lines.append("【面试要点参考】")
        lines.extend(interview_results)
    if teaching_results and not teaching_results[0].startswith("⚠️"):
        lines.append("\n【课程资料参考】")
        lines.extend(teaching_results)

    return "\n".join(lines) if lines else ""
```

### 5.4 `knowledge_tools.py` 扩展

新增两个工具函数，加入 `permissions.py` 的 `COURSE_DEFENSE_SKILLS`：

```python
# service/tools/knowledge_tools.py 中新增

from service.knowledge_store import KnowledgeType

class TeachingKBSearchInput(BaseModel):
    query: str = Field(..., description="检索教学资料库的关键词或问题描述")
    top_k: int = Field(default=3, description="返回结果条数", ge=1, le=5)


def create_teaching_rag_tool(knowledge_store):
    @tool(args_schema=TeachingKBSearchInput)
    def search_teaching_knowledge(query: str, top_k: int = 3) -> str:
        """
        从老师教学资料库检索课程相关内容。
        用于课程答辩模式，基于老师讲义和项目文档出题和评分。
        有教学资料时优先于通用面试知识库使用。
        """
        results = knowledge_store.retrieve(
            query, knowledge_type=KnowledgeType.TEACHING, top_k=top_k
        )
        if not results or results[0].startswith("⚠️"):
            return results[0] if results else "教学资料库未找到相关内容。"
        lines = [f"📖 教学资料检索结果（{query}）：\n"]
        for i, r in enumerate(results, 1):
            lines.append(f"[{i}] {r}\n")
        return "\n".join(lines)

    return search_teaching_knowledge


class CombinedKBSearchInput(BaseModel):
    query: str = Field(..., description="检索关键词，将同时查询面试要点库和教学资料库")
    top_k: int = Field(default=3, description="每个知识库各返回的条数", ge=1, le=5)


def create_combined_rag_tool(knowledge_store):
    @tool(args_schema=CombinedKBSearchInput)
    def search_combined_knowledge(query: str, top_k: int = 3) -> str:
        """
        同时检索面试要点库（库 A）和教学资料库（库 B），合并返回结果。
        专用于课程答辩模式的出题和评分参考。
        """
        combined = knowledge_store.retrieve_combined(query, top_k=top_k)
        return combined if combined else "两个知识库均未找到相关内容。"

    return search_combined_knowledge
```

### 5.5 `permissions.py` 扩展

```python
# service/tools/permissions.py 新增

TOOL_TEACHING_RAG  = "search_teaching_knowledge"
TOOL_COMBINED_RAG  = "search_combined_knowledge"

# 课程答辩专用权限集合
COURSE_DEFENSE_SKILLS = SkillSet(
    name="course_defense",
    description="课程答辩模式：教学资料库 + 面试要点库 + 题库（双库混合）",
    tool_names=frozenset({
        TOOL_JOB_INFO,
        TOOL_QUIZ_DRAW,
        TOOL_QUIZ_STATS,
        TOOL_RAG,           # 面试要点库 A
        TOOL_TEACHING_RAG,  # 教学资料库 B
        TOOL_COMBINED_RAG,  # 双库混合检索
    }),
)

# 同时更新 ALL_SKILL_SETS
ALL_SKILL_SETS["course_defense"] = COURSE_DEFENSE_SKILLS
```

### 5.6 `registry.py` 中注册新工具

```python
# service/tools/registry.py → _TOOL_FACTORIES 列表末尾追加
from .knowledge_tools import create_teaching_rag_tool, create_combined_rag_tool

_TOOL_FACTORIES = [
    ...  # 原有工具
    ("search_teaching_knowledge", create_teaching_rag_tool, ["knowledge_store"]),
    ("search_combined_knowledge", create_combined_rag_tool, ["knowledge_store"]),
]
```

### 5.7 百炼控制台操作步骤

> ⚠️ 知识库必须在百炼控制台手动创建，代码无法自动建库
> 这个需要老师和同学提供相关资料，负责人和代码协同开发人员有需要的话手动上传做测试，其中负责人（队长）手中要有齐全的知识库版本，其他开发人员不强求。

1. 登录 [bailian.console.aliyun.com](https://bailian.console.aliyun.com)
2. 「知识库」→「新建知识库」，创建**两个**库：
   - 库 A：`ai_interview_base`，Index ID 填入 `BAILOU_KNOWLEDGE_BASE_ID`
   - 库 B：`teaching_materials`，Index ID 填入 `BAILOU_TEACHING_KB_ID`
3. 库 A：上传 `knowledge_base/interview/` 目录下所有 `.txt` 文件
4. 库 B：由老师上传课程 PPT、讲义 PDF、项目需求文档
5. 两个库状态变为「就绪」后重启应用即可

---

## 6. 数据库结构说明

### 核心表

| 表名 | 用途 | 关键字段 |
|------|------|----------|
| `job_position` | 面试岗位定义 | `id`, `name`, `tech_stack`（JSON） |
| `question_bank` | 本地种子题库 | `classify`, `level`, `content`, `answer` |
| `student` | 学生信息 | `id`, `name`, `email` |
| `interview_session` | 面试会话 | `student_id`, `job_position_id`, `status`, `overall_score`, `report` |
| `interview_turn` | 每轮问答 | `session_id`, `turn_index`, `question_text`, `student_answer`, `scores`（JSON）, **`audio_path`** |
| `knowledge_chunk` | 本地知识库分块（备用） | `job_position_id`, `source`, `chunk_text` |

### `audio_path` 字段

`interview_turn` 表已预留此字段，任务 A 完成后直接写入，**无需改表结构**。

---

## 7. UI 组件规范

> ⚠️ **强制约定**：所有新增 UI 代码必须从 `UI/components.py` 引入主题色，禁止在面板文件中硬编码颜色值。

### 可用组件

| 组件 | 用途 | 导入 |
|------|------|------|
| `Theme` (别名 `T`) | 颜色常量 | `from UI.components import Theme as T` |
| `ButtonFactory` | 按钮工厂（primary/solid/ghost/tag） | `from UI.components import ButtonFactory` |
| `ChatBubble` | 聊天气泡（支持 Markdown 渲染） | `from UI.components import ChatBubble` |
| `ScoreCardBubble` | 评分卡片（面试面板专用） | `from UI.components import ScoreCardBubble` |
| `StatBadge` | 统计徽章 | `from UI.components import StatBadge` |
| `TypingIndicator` | AI 打字等待动画 | `from UI.components import TypingIndicator` |
| `GLOBAL_QSS` | 全局样式表 | `from UI.components import GLOBAL_QSS` |

### 新增面板检查清单

- [ ] 继承 `QWidget`，不继承 `QFrame`
- [ ] `__init__` 中先调用 `self.setStyleSheet(GLOBAL_QSS + ...)`
- [ ] 颜色全部用 `T.XXX`，不写字面量 `#xxxxxx`
- [ ] 按钮全部用 `ButtonFactory.primary / solid / ghost`
- [ ] 长列表必须用服务端分页（参考 `quiz_panel.py` 的 `PaginationBar`）
- [ ] 后台耗时操作用 `threading.Thread` + `Signal` 回调，不阻塞主线程

---

## 8. 工具权限体系（SkillSet）

### 现有权限集合

| 集合 | 工具数 | 场景 | 便捷函数 |
|------|--------|------|----------|
| `INTERVIEW_SKILLS` | 3 | 面试引擎（无历史无联网） | `get_interview_tools(db)` |
| `READONLY_SKILLS` | 5 | 只读查询（题库+RAG） | `get_readonly_tools(db, ks)` |
| `ASSISTANT_SKILLS` | 8 | AI 助手全量 | `get_assistant_tools(db, ks)` |
| `ADMIN_SKILLS` | 8 | 管理员（预留） | `get_tools_for(db, ks, ADMIN_SKILLS)` |
| `COURSE_DEFENSE_SKILLS` | 6 | **课程答辩（任务 B 后新增）** | `get_tools_for(db, ks, COURSE_DEFENSE_SKILLS)` |

### 新增工具的三步流程

每次新增工具，按顺序改这 3 个文件：

1. **`db_tools.py` 或 `knowledge_tools.py`**：实现 `@tool` 函数 + Pydantic Schema
2. **`permissions.py`**：新增 `TOOL_XXX` 常量，加入对应 `SkillSet.tool_names`
3. **`registry.py`**：在 `_TOOL_FACTORIES` 末尾追加 `(工具名, 工厂函数, 参数列表)`

---

## 9. 开发与提交规范

### 分支策略

```
main              ← 保持可运行，只接受经过测试的合并
feature/voice     ← 任务 A：语音模块
feature/dual-kb   ← 任务 B：双知识库
hotfix/*          ← 紧急 Bug 修复
release_test      ← 发行前的测试版本
```

### Commit 格式

```
feat(voice): 新增 service/voice.py STT 录音转文字 ** 或者 ** 直接语音交互模式的mode（即新增一个vioce_contect_core而不是新加功能）
feat(kb): KnowledgeStore 支持双库检索
fix(quiz): 修复分页跳转越界问题
refactor(tools): 拆分 registry.py 工厂函数
docs: 更新 README 双知识库配置说明
```

### .gitignore 必须包含

```gitignore
.env
*.db
knowledge_base/teaching/    # 老师资料不提交
__pycache__/
*.pyc
```

### 提交前自检

- [ ] `pip install -r requirements.txt` 无报错
- [ ] `python main.py` 能正常打开窗口
- [ ] 完成一次完整面试流程（选岗 → 回答 → 结束 → 报告）
- [ ] 题库面板分页/排序/搜索正常
- [ ] AI 助手工具调用正常
- [ ] （任务 A）录音按钮 → STT → 文字填入输入框
- [ ] （任务 B）两个知识库均可检索返回结果

---

## 10. 常见问题 FAQ

**Q: `torch` 版本冲突怎么解决？**
先单独装：`pip install torch==2.10.0 --index-url https://download.pytorch.org/whl/cpu`，再装其余依赖。

**Q: 启动报 `BAILOU_KNOWLEDGE_BASE_ID 未配置`？**
检查 `.env` 文件是否存在且 Key 值非空，确认 `load_dotenv()` 在所有 `import service.*` 之前执行。

**Q: 面试官不出题 / 返回空字符串？**
用 `curl` 测一下 `DASHSCOPE_API_KEY` 是否有效：
```bash
curl https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions \
  -H "Authorization: Bearer $DASHSCOPE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen-plus","messages":[{"role":"user","content":"hi"}]}'
```

**Q: 录音没有声音 / `sounddevice` 报错？**
确认麦克风系统权限已开启，或 `pip install sounddevice --upgrade`。Windows 上可能还需要 `pip install pyaudio`，更精确的解决方案是把代码仓库给claude然后让他给出解决方案。

**Q: 博查搜索显示「⚠️ 未加载」？**
`BOCHA_API_KEY` 未配置是正常现象，联网搜索工具会被跳过，不影响其他功能。

**Q: 知识库检索一直返回「未找到相关内容」？**
确认百炼控制台知识库状态为「就绪」，且已上传文档并完成索引（等待时间约 5-30 分钟）。

**Q: `QComboBox` 下拉列表背景变黑？**
`GLOBAL_QSS` 中已包含修复，确认每个面板的 `setStyleSheet` 调用了 `GLOBAL_QSS` 即可。

---

*如有问题，群里 @ 队长或直接提 Issue。Good luck 大家! 🚀*