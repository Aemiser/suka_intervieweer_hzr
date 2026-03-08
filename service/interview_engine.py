# service/interview_engine.py
"""
面试引擎
管理一次完整的 AI 模拟面试会话：出题、追问、评分、生成报告。
使用原生 OpenAI SDK（避免 langchain_openai → transformers → torch 依赖链）
"""
import json
import os
from datetime import datetime
from typing import Optional

from openai import OpenAI

from service.evaluator import AnswerEvaluator, EvalResult
from service.knowledge_store import KnowledgeStore


_INTERVIEWER_SYSTEM = """你是一位专业、严谨的技术面试官，正在对"{job_name}"岗位的候选人进行模拟面试。

## 你的工作流程
1. 根据岗位技术栈，由浅入深地提问
2. 认真听取候选人的回答
3. 根据回答质量决定：追问细节 OR 切换下一个知识点
4. 面试结束时给出整体评价

## 出题原则
- 覆盖岗位核心技术栈：{tech_stack}
- 难度循序渐进：先考察基础概念，再深入原理和实践
- 每次只问一个问题，等候选人回答后再追问或换题
- 如果候选人回答正确且完整，追问更深层原理（如"能说说底层实现吗？"）
- 如果候选人回答有误，委婉指出并给出提示

## 语气要求
- 专业但不刻板，模拟真实面试氛围
- 候选人表现好时给予鼓励
- 回答简洁，不要做过多解释，保持面试节奏

## 重要约束
- 每次回复只包含一个问题或追问，不得一次问多个
- 不要在候选人回答前就告知答案
- 不要输出任何与面试无关的内容
"""

_REPORT_PROMPT = """请根据以下面试记录，生成一份结构化的面试评估报告。

岗位：{job_name}
候选人：{student_name}
面试题数：{turn_count} 题
各题得分：{scores_summary}

请用中文输出以下格式的报告（直接输出内容，不要 markdown 标题外的多余格式）：

【综合评价】
（2-3句话总体评价候选人表现）

【技术能力】
（评价技术知识掌握情况，指出强项和薄弱点）

【表现亮点】
（列出2-3个具体亮点）

【待提升项】
（列出2-3个需要改进的方向）

【学习建议】
（给出具体的学习资源方向或练习建议）
"""


class InterviewEngine:
    MAX_TURNS = 8

    def __init__(self, db, knowledge_store: KnowledgeStore):
        self.db = db
        self.ks = knowledge_store
        self.evaluator = AnswerEvaluator()

        self._client = OpenAI(
            api_key=os.getenv("DASHSCOPE_API_KEY", ""),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        self._model = "qwen-plus"

        # session_id → list of {"role": ..., "content": ...}
        self._histories: dict[int, list[dict]] = {}

    def _chat(self, messages: list[dict], temperature: float = 0.7, max_tokens: int = 1024) -> str:
        resp = self._client.chat.completions.create(
            model=self._model,
            temperature=temperature,
            max_tokens=max_tokens,
            messages=messages,
        )
        return resp.choices[0].message.content or ""

    # ── 开始面试 ──────────────────────────────────────────────────────────────

    def start_session(self, student_id: int, job_position_id: int) -> int:
        now = datetime.now().isoformat()
        cur = self.db.execute(
            "INSERT INTO interview_session (student_id, job_position_id, status, started_at) VALUES (?,?,?,?)",
            (student_id, job_position_id, "ongoing", now),
        )
        session_id = cur.lastrowid
        self._histories[session_id] = []
        return session_id

    def get_first_question(self, session_id: int) -> str:
        job = self._get_job(session_id)
        tech_stack_str = "、".join(json.loads(job["tech_stack"]))

        system_content = _INTERVIEWER_SYSTEM.format(
            job_name=job["name"], tech_stack=tech_stack_str
        )
        history = [
            {"role": "system",  "content": system_content},
            {"role": "user",    "content": "你好，我准备好了，请开始面试。"},
        ]
        self._histories[session_id] = history

        reply = self._chat(history)
        self._histories[session_id].append({"role": "assistant", "content": reply})
        self._save_turn(session_id, question_text=reply, student_answer="")
        return reply

    # ── 提交回答 ──────────────────────────────────────────────────────────────

    def submit_answer(self, session_id: int, answer: str) -> dict:
        turn = self._get_latest_unanswered_turn(session_id)
        if not turn:
            return {"ai_reply": "面试已结束，请点击「结束面试」查看报告。", "is_finished": True}

        turn_id, question_text = turn

        job = self._get_job(session_id)
        context = self.ks.retrieve_as_context(question_text, job_position_id=job["id"]) \
            if hasattr(self.ks, "retrieve_as_context") else ""

        eval_result = self.evaluator.evaluate(
            question=question_text,
            answer=answer,
            job_name=job["name"],
            context=context,
        )

        self.db.execute(
            "UPDATE interview_turn SET student_answer=?, scores=? WHERE id=?",
            (answer, json.dumps(eval_result.to_dict()), turn_id),
        )

        finished_count = self.db.fetchone(
            "SELECT COUNT(*) FROM interview_turn WHERE session_id=? AND student_answer!=''",
            (session_id,),
        )[0]
        is_finished = finished_count >= self.MAX_TURNS

        history = self._histories.get(session_id, [])
        history.append({"role": "user", "content": answer})

        if is_finished:
            history.append({"role": "user", "content": "（面试轮数已到，请给候选人一个简短收尾语）"})

        ai_reply = self._chat(history)
        history.append({"role": "assistant", "content": ai_reply})

        if not is_finished:
            self._save_turn(session_id, question_text=ai_reply, student_answer="")

        return {
            "eval": eval_result,
            "ai_reply": ai_reply,
            "is_finished": is_finished,
        }

    # ── 结束面试 ──────────────────────────────────────────────────────────────

    def finish_session(self, session_id: int) -> str:
        turns = self.db.fetchall(
            "SELECT question_text, student_answer, scores FROM interview_turn "
            "WHERE session_id=? AND student_answer!='' ORDER BY turn_index",
            (session_id,),
        )
        if not turns:
            report_text = "本次面试未完成任何题目，无法生成报告。"
            self._close_session(session_id, overall_score=0.0, report=report_text)
            return report_text

        all_scores = []
        scores_summary_lines = []
        for i, (q, a, scores_json) in enumerate(turns, 1):
            if scores_json:
                sc = json.loads(scores_json)
                overall = sc.get("overall", 0)
                all_scores.append(overall)
                scores_summary_lines.append(
                    f"第{i}题（{q[:20]}…）: 综合 {overall}/10  "
                    f"技术{sc.get('tech',0)} 逻辑{sc.get('logic',0)} "
                    f"深度{sc.get('depth',0)} 表达{sc.get('clarity',0)}"
                )

        overall_score = round(sum(all_scores) / len(all_scores), 2) if all_scores else 0.0

        job = self._get_job(session_id)
        student = self._get_student(session_id)
        prompt = _REPORT_PROMPT.format(
            job_name=job["name"],
            student_name=student["name"],
            turn_count=len(turns),
            scores_summary="\n".join(scores_summary_lines),
        )
        try:
            report_text = self._chat(
                [{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=1500,
            )
        except Exception as e:
            report_text = f"报告生成失败: {e}\n\n各题得分：\n" + "\n".join(scores_summary_lines)

        self._close_session(session_id, overall_score=overall_score, report=report_text)
        return report_text

    # ── 内部辅助 ──────────────────────────────────────────────────────────────

    def _save_turn(self, session_id: int, question_text: str, student_answer: str):
        idx = self.db.fetchone(
            "SELECT COALESCE(MAX(turn_index)+1, 0) FROM interview_turn WHERE session_id=?",
            (session_id,),
        )[0]
        self.db.execute(
            "INSERT INTO interview_turn (session_id, turn_index, question_text, student_answer, created_at) "
            "VALUES (?,?,?,?,?)",
            (session_id, idx, question_text, student_answer, datetime.now().isoformat()),
        )

    def _get_latest_unanswered_turn(self, session_id: int):
        return self.db.fetchone(
            "SELECT id, question_text FROM interview_turn "
            "WHERE session_id=? AND student_answer='' ORDER BY turn_index DESC LIMIT 1",
            (session_id,),
        )

    def _close_session(self, session_id: int, overall_score: float, report: str):
        self.db.execute(
            "UPDATE interview_session SET status='finished', finished_at=?, overall_score=?, report=? WHERE id=?",
            (datetime.now().isoformat(), overall_score, report, session_id),
        )
        self._histories.pop(session_id, None)

    def _get_job(self, session_id: int) -> dict:
        row = self.db.fetchone(
            "SELECT jp.id, jp.name, jp.tech_stack FROM interview_session s "
            "JOIN job_position jp ON s.job_position_id=jp.id WHERE s.id=?",
            (session_id,),
        )
        return {"id": row[0], "name": row[1], "tech_stack": row[2]}

    def _get_student(self, session_id: int) -> dict:
        row = self.db.fetchone(
            "SELECT st.id, st.name FROM interview_session s "
            "JOIN student st ON s.student_id=st.id WHERE s.id=?",
            (session_id,),
        )
        return {"id": row[0], "name": row[1]}

    def get_session_turns(self, session_id: int) -> list:
        return self.db.fetchall(
            "SELECT turn_index, question_text, student_answer, scores "
            "FROM interview_turn WHERE session_id=? ORDER BY turn_index",
            (session_id,),
        )