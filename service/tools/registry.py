# service/tools/registry.py
"""
面试 Agent 工具集

get_interview_tools(db)                  — 面试流程专用
get_assistant_tools(db, knowledge_store) — AI 助手专用（含搜索）
get_tools(db, knowledge_store)           — 兼容旧接口
"""
import json
import os
import random
from typing import Optional

import requests
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

# ── Wikipedia ─────────────────────────────────────────────────────────────────
try:
    from langchain_community.tools import WikipediaQueryRun
    from langchain_community.utilities import WikipediaAPIWrapper
    _WIKI_OK = True
except ImportError:
    _WIKI_OK = False


# ═══════════════════════════════════════════════════════════════════
# ① 学生历史记录
# ═══════════════════════════════════════════════════════════════════

class StudentHistoryInput(BaseModel):
    student_id: int = Field(..., description="学生的唯一 ID")

def create_history_tool(db):
    @tool(args_schema=StudentHistoryInput)
    def get_student_interview_history(student_id: int) -> str:
        """查询指定学生的历史面试记录，包含各次面试的岗位、得分和时间。"""
        rows = db.fetchall(
            """SELECT s.name, jp.name, iss.started_at, iss.overall_score, iss.status
               FROM interview_session iss
               JOIN student s ON iss.student_id = s.id
               JOIN job_position jp ON iss.job_position_id = jp.id
               WHERE iss.student_id = ?
               ORDER BY iss.started_at DESC""",
            (student_id,),
        )
        if not rows:
            return f"学生 ID={student_id} 暂无面试记录。"
        lines = [f"学生「{rows[0][0]}」历史面试记录（共 {len(rows)} 次）："]
        for _, job_name, started_at, score, status in rows:
            score_str = f"{score:.1f}/10" if score else "未完成"
            lines.append(f"  - 岗位：{job_name}  得分：{score_str}  时间：{started_at[:10]}  状态：{status}")
        return "\n".join(lines)

    return get_student_interview_history


# ═══════════════════════════════════════════════════════════════════
# ② 岗位信息
# ═══════════════════════════════════════════════════════════════════

class JobInfoInput(BaseModel):
    job_position_id: Optional[int] = Field(default=None, description="岗位 ID，不传则列出所有")

def create_job_info_tool(db):
    @tool(args_schema=JobInfoInput)
    def get_job_position_info(job_position_id: Optional[int] = None) -> str:
        """查询岗位信息。不传 ID 则列出所有岗位；传入 ID 则返回详细技术栈。"""
        if job_position_id is None:
            rows = db.fetchall("SELECT id, name, description FROM job_position")
            if not rows:
                return "暂无岗位信息。"
            lines = ["当前支持的面试岗位："]
            for jid, name, desc in rows:
                lines.append(f"  [{jid}] {name}：{desc or '无描述'}")
            return "\n".join(lines)
        row = db.fetchone(
            "SELECT name, description, tech_stack FROM job_position WHERE id=?",
            (job_position_id,),
        )
        if not row:
            return f"未找到岗位 ID={job_position_id}"
        name, desc, tech_json = row
        tech = json.loads(tech_json)
        return f"岗位：{name}\n描述：{desc}\n核心技术栈：{', '.join(tech)}"

    return get_job_position_info


# ═══════════════════════════════════════════════════════════════════
# ③ 随机抽题
# ═══════════════════════════════════════════════════════════════════

class QuizDrawInput(BaseModel):
    classify: str = Field(default="", description="题目分类，如 'Java基础'、'MySQL'，留空不限")
    level:    str = Field(default="", description="难度：初级/中级/高级，留空不限")
    count:    int = Field(default=5,  description="抽题数量，默认 5 题，最多 20", ge=1, le=20)

def create_quiz_draw_tool(db):
    @tool(args_schema=QuizDrawInput)
    def draw_questions_from_bank(classify: str = "", level: str = "", count: int = 5) -> str:
        """从题库按分类和难度随机抽题，适合生成模拟面试试卷或日常练习。"""
        count = min(count, 20)
        sql, params = "SELECT id, classify, level, content FROM question_bank WHERE 1=1", []
        if classify:
            sql += " AND classify=?"; params.append(classify)
        if level:
            sql += " AND level=?";    params.append(level)
        rows = db.fetchall(sql, tuple(params))
        if not rows:
            return f"未找到符合条件的题目（分类={classify or '不限'}，难度={level or '不限'}）。"
        selected = random.sample(rows, min(count, len(rows)))
        lines = [f"📚 已从题库抽取 {len(selected)} 道题目：\n"]
        for i, (_, cls, lvl, content) in enumerate(selected, 1):
            lines.append(f"**Q{i}** [{cls} · {lvl}]\n{content}\n")
        return "\n".join(lines)

    return draw_questions_from_bank


# ═══════════════════════════════════════════════════════════════════
# ④ 题库搜索
# ═══════════════════════════════════════════════════════════════════

class QuizSearchInput(BaseModel):
    keyword:     str  = Field(...,          description="搜索关键词")
    show_answer: bool = Field(default=True, description="是否显示参考答案")

def create_quiz_search_tool(db):
    @tool(args_schema=QuizSearchInput)
    def search_question_bank(keyword: str, show_answer: bool = True) -> str:
        """在题库中关键词搜索题目，适合查找特定知识点的题目及参考解析。"""
        rows = db.fetchall(
            "SELECT id, classify, level, content, answer FROM question_bank "
            "WHERE content LIKE ? OR answer LIKE ? LIMIT 10",
            (f"%{keyword}%", f"%{keyword}%"),
        )
        if not rows:
            return f"题库中未找到包含「{keyword}」的题目。"
        lines = [f"🔍 搜索「{keyword}」共找到 {len(rows)} 道题目：\n"]
        for _, cls, lvl, content, answer in rows:
            lines.append(f"**[{cls} · {lvl}]** {content}")
            if show_answer:
                lines.append(f"📝 参考答案：{answer[:200]}{'...' if len(answer) > 200 else ''}")
            lines.append("")
        return "\n".join(lines)

    return search_question_bank


# ═══════════════════════════════════════════════════════════════════
# ⑤ 题库统计
# ═══════════════════════════════════════════════════════════════════

class QuizStatsInput(BaseModel):
    pass

def create_quiz_stats_tool(db):
    @tool(args_schema=QuizStatsInput)
    def get_question_bank_stats() -> str:
        """查看题库的整体统计：各分类、各难度的题目数量分布。"""
        rows = db.fetchall(
            "SELECT classify, level, COUNT(*) FROM question_bank "
            "GROUP BY classify, level ORDER BY classify, level"
        )
        if not rows:
            return "题库暂无数据。"
        total = db.fetchone("SELECT COUNT(*) FROM question_bank")[0]
        lines = [f"📊 题库统计（共 {total} 题）：\n"]
        current_cls = None
        for cls, lvl, cnt in rows:
            if cls != current_cls:
                current_cls = cls
                lines.append(f"\n**{cls}**")
            lines.append(f"  {lvl}：{cnt} 题")
        classifies = db.fetchall("SELECT DISTINCT classify FROM question_bank ORDER BY classify")
        lines.append(f"\n可用分类：{', '.join(r[0] for r in classifies)}")
        return "\n".join(lines)

    return get_question_bank_stats


# ═══════════════════════════════════════════════════════════════════
# ⑥ 知识库 RAG 检索
# ═══════════════════════════════════════════════════════════════════

class KnowledgeSearchInput(BaseModel):
    query:           str = Field(...,       description="检索关键词或问题描述")
    job_position_id: int = Field(default=0, description="岗位 ID 过滤，0=通用")

def create_rag_tool(knowledge_store):
    @tool(args_schema=KnowledgeSearchInput)
    def search_knowledge_base(query: str, job_position_id: int = 0) -> str:
        """
        从知识库检索与问题相关的技术知识。
        适合查询面试题答案、技术概念、最佳实践，优先于联网搜索使用。
        """
        results = knowledge_store.retrieve(query, job_position_id=job_position_id, top_k=3)
        if not results:
            return "知识库中未找到相关内容。"
        lines = [f"知识库检索结果（关键词：{query}）："]
        for i, r in enumerate(results, 1):
            lines.append(f"\n[{i}] {r}")
        return "\n".join(lines)

    return search_knowledge_base


# ═══════════════════════════════════════════════════════════════════
# ⑦ 博查 Web Search（国内可用，替代 Tavily）
# 申请地址：https://open.bochaai.com
# 将 API Key 写入 .env：BOCHA_API_KEY=your_key
# ═══════════════════════════════════════════════════════════════════

class WebSearchInput(BaseModel):
    query: str = Field(..., description="搜索查询词，用于查找最新技术资料、新闻或框架更新")

def create_web_search_tool():
    api_key = os.getenv("BOCHA_API_KEY", "")
    if not api_key:
        raise ValueError(
            "未找到 BOCHA_API_KEY。\n"
            "请前往 https://open.bochaai.com 注册并获取 API Key，\n"
            "然后在 .env 中添加：BOCHA_API_KEY=your_key"
        )

    @tool(args_schema=WebSearchInput)
    def web_search(query: str) -> str:
        """
        通过博查搜索引擎搜索最新技术资料、新闻、框架更新等（国内可直接访问）。
        在 search_knowledge_base 无结果时使用。
        """
        try:
            resp = requests.post(
                "https://api.bochaai.com/v1/web-search",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type":  "application/json",
                },
                json={
                    "query":       query,
                    "summary":     True,   # 返回 AI 摘要
                    "count":       8,
                    "freshness":   "noLimit",
                },
                timeout=20,
            )

            if resp.status_code != 200:
                return f"博查搜索失败 HTTP {resp.status_code}：{resp.text[:200]}"

            data = resp.json()

            # 博查返回结构：
            # {
            #   "data": {
            #     "webPages": {"value": [{"name":..., "url":..., "snippet":...}]},
            #     "answer": "AI 摘要"
            #   }
            # }
            result_data = data.get("data", {})
            ai_answer   = result_data.get("answer", "")
            web_pages   = result_data.get("webPages", {}).get("value", [])

            lines = [f"🔍 搜索结果（{query}）：\n"]

            if ai_answer:
                lines.append(f"**AI 摘要：** {ai_answer}\n")

            for i, page in enumerate(web_pages[:6], 1):
                name    = page.get("name", "无标题")
                url     = page.get("url", "")
                snippet = page.get("snippet", "").strip()[:300]
                lines.append(f"[{i}] {name}")
                if url:
                    lines.append(f"   链接：{url}")
                if snippet:
                    lines.append(f"   摘要：{snippet}...")
                lines.append("")

            return "\n".join(lines) if len(lines) > 2 else "搜索未返回任何结果。"

        except requests.exceptions.Timeout:
            return "博查搜索超时，请稍后重试。"
        except Exception as e:
            return f"博查搜索失败：{type(e).__name__}: {e}"

    return web_search


# ═══════════════════════════════════════════════════════════════════
# ⑧ Wikipedia
# ═══════════════════════════════════════════════════════════════════

class WikiSearchInput(BaseModel):
    query: str = Field(..., description="技术概念名称，用于查询权威定义和背景知识")

def create_wiki_tool():
    if not _WIKI_OK:
        raise ImportError("langchain_community 未安装")
    _wiki = WikipediaQueryRun(
        api_wrapper=WikipediaAPIWrapper(lang="zh", top_k_results=2, doc_content_chars_max=800)
    )

    @tool(args_schema=WikiSearchInput)
    def search_wikipedia(query: str) -> str:
        """
        从 Wikipedia 查询技术概念的权威定义和背景知识。
        适合查询算法、数据结构、设计模式等基础知识。
        """
        try:
            return _wiki.run(query)
        except Exception as e:
            return f"Wikipedia 查询失败：{e}"

    return search_wikipedia


# ═══════════════════════════════════════════════════════════════════
# 对外接口
# ═══════════════════════════════════════════════════════════════════

def get_interview_tools(db) -> list:
    """面试流程专用工具：题库 + 历史记录。"""
    return [
        create_history_tool(db),
        create_job_info_tool(db),
        create_quiz_draw_tool(db),
        create_quiz_search_tool(db),
        create_quiz_stats_tool(db),
    ]


def get_assistant_tools(db, knowledge_store) -> list:
    """AI 知识助手工具：题库 + RAG + 联网搜索。"""
    tools = [
        create_history_tool(db),
        create_job_info_tool(db),
        create_quiz_draw_tool(db),
        create_quiz_search_tool(db),
        create_quiz_stats_tool(db),
        create_rag_tool(knowledge_store),
    ]
    for factory, name in [
        (create_web_search_tool, "web_search (博查)"),
        (create_wiki_tool,       "search_wikipedia"),
    ]:
        try:
            tools.append(factory())
            print(f"[Tools] ✅ {name} 已加载")
        except Exception as e:
            print(f"[Tools] ⚠️  {name} 未加载：{e}")
    return tools


def get_tools(db, knowledge_store) -> list:
    """兼容旧接口。"""
    return get_assistant_tools(db, knowledge_store)