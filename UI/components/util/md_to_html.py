# UI/components/util/md_to_html.py
"""
轻量级 Markdown → HTML 转换器。
支持表格、围栏代码块、标题、有/无序列表、加粗、斜体、行内代码、链接、分割线。
专为 QTextBrowser 的受限 HTML 渲染环境设计。
"""

import re
from UI.components.info.Theme import T


# ── 行内元素处理 ──────────────────────────────────────────────────────────────

def _inline_md(text: str) -> str:
    """处理行内 Markdown：先 HTML 转义，再替换格式标记。"""
    # HTML 转义（顺序重要：& 必须最先）
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    # 行内代码
    text = re.sub(
        r"`([^`]+)`",
        rf'<code style="background:{T.SURFACE};color:{T.SUCCESS};'
        rf'padding:1px 4px;border-radius:3px;'
        rf'font-family:{T.FONT_MONO};font-size:12px;">\1</code>',
        text,
    )
    # 加粗（** 和 __）
    text = re.sub(r"\*\*(.+?)\*\*", rf'<strong style="color:{T.TEXT};">\1</strong>', text)
    text = re.sub(r"__(.+?)__",     rf'<strong style="color:{T.TEXT};">\1</strong>', text)
    # 斜体（* 和 _，不与加粗冲突）
    text = re.sub(r"\*(.+?)\*", rf'<em style="color:{T.TEXT_DIM};">\1</em>', text)
    text = re.sub(r"_(.+?)_",   rf'<em style="color:{T.TEXT_DIM};">\1</em>', text)
    # 链接
    text = re.sub(
        r"\[(.+?)\]\((.+?)\)",
        rf'<a href="\2" style="color:{T.INFO};">\1</a>',
        text,
    )
    return text


# ── 块级渲染状态机 ────────────────────────────────────────────────────────────

def md_to_html(text: str) -> str:
    """
    将 Markdown 文本转换为带内联样式的 HTML 字符串。
    返回完整的 <html>…</html> 文档，背景透明。
    """
    lines = text.split("\n")
    html_parts: list[str] = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # ── 围栏代码块 ────────────────────────────────────────────────────────
        if line.strip().startswith("```"):
            code_lines: list[str] = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(
                    lines[i]
                    .replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                )
                i += 1
            i += 1  # 跳过结束 ```
            html_parts.append(
                f'<pre style="background:{T.SURFACE};border:1px solid {T.BORDER};'
                f'border-radius:6px;padding:10px 12px;margin:6px 0;'
                f'font-family:{T.FONT_MONO};font-size:12px;color:{T.SUCCESS};'
                f'white-space:pre-wrap;word-break:break-all;">'
                + "\n".join(code_lines)
                + "</pre>"
            )
            continue

        # ── 表格（连续以 | 开头的行） ─────────────────────────────────────────
        if "|" in line and line.strip().startswith("|"):
            table_rows: list[str] = []
            while i < len(lines) and "|" in lines[i] and lines[i].strip().startswith("|"):
                table_rows.append(lines[i])
                i += 1
            # 过滤掉分隔行（如 |---|---| ）
            data_rows = [r for r in table_rows if not re.match(r"^\|[\s\-:|]+\|", r)]
            if not data_rows:
                continue

            html_parts.append(
                f'<table style="border-collapse:collapse;width:100%;'
                f'margin:8px 0;font-size:13px;font-family:{T.FONT};">'
            )
            for row_idx, row in enumerate(data_rows):
                cells = [c.strip() for c in row.strip().strip("|").split("|")]
                tag  = "th" if row_idx == 0 else "td"
                bg   = (T.SURFACE if row_idx == 0
                        else (T.SURFACE if row_idx % 2 == 1 else T.SURFACE))
                color = T.INFO if row_idx == 0 else T.TEXT
                weight = "700" if row_idx == 0 else "400"
                html_parts.append("<tr>")
                for cell in cells:
                    html_parts.append(
                        f'<{tag} style="border:1px solid {T.BORDER};padding:6px 10px;'
                        f'background:{bg};color:{color};font-weight:{weight};">'
                        f"{_inline_md(cell)}</{tag}>"
                    )
                html_parts.append("</tr>")
            html_parts.append("</table>")
            continue

        # ── ATX 标题（# ~ ####） ──────────────────────────────────────────────
        m = re.match(r"^(#{1,4})\s+(.*)", line)
        if m:
            level   = len(m.group(1))
            size    = {1: "18px", 2: "16px", 3: "14px", 4: "13px"}.get(level, "14px")
            color   = {1: T.INFO, 2: T.INFO, 3: T.TEXT, 4: T.TEXT_DIM}.get(level, T.TEXT)
            content = _inline_md(m.group(2))
            html_parts.append(
                f'<p style="font-size:{size};font-weight:700;color:{color};'
                f'margin:10px 0 4px 0;">{content}</p>'
            )
            i += 1
            continue

        # ── 无序列表 ──────────────────────────────────────────────────────────
        if re.match(r"^[\-\*\+]\s+", line):
            html_parts.append('<ul style="margin:4px 0;padding-left:20px;">')
            while i < len(lines) and re.match(r"^[\-\*\+]\s+", lines[i]):
                item = _inline_md(lines[i][2:].strip())
                html_parts.append(
                    f'<li style="color:{T.TEXT};margin:2px 0;">{item}</li>'
                )
                i += 1
            html_parts.append("</ul>")
            continue

        # ── 有序列表 ──────────────────────────────────────────────────────────
        if re.match(r"^\d+\.\s+", line):
            html_parts.append('<ol style="margin:4px 0;padding-left:20px;">')
            while i < len(lines) and re.match(r"^\d+\.\s+", lines[i]):
                item = _inline_md(re.sub(r"^\d+\.\s+", "", lines[i]))
                html_parts.append(
                    f'<li style="color:{T.TEXT};margin:2px 0;">{item}</li>'
                )
                i += 1
            html_parts.append("</ol>")
            continue

        # ── 分割线 ────────────────────────────────────────────────────────────
        if re.match(r"^[-_\*]{3,}$", line.strip()):
            html_parts.append(
                f'<hr style="border:none;border-top:1px solid {T.BORDER};margin:8px 0;">'
            )
            i += 1
            continue

        # ── 空行 ──────────────────────────────────────────────────────────────
        if not line.strip():
            html_parts.append("<br>")
            i += 1
            continue

        # ── 普通段落 ──────────────────────────────────────────────────────────
        html_parts.append(
            f'<p style="color:{T.TEXT};font-size:14px;margin:3px 0;line-height:1.7;">'
            f"{_inline_md(line)}</p>"
        )
        i += 1

    body = "\n".join(html_parts)
    return (
        f'<html><body style="background:transparent;font-family:{T.FONT};'
        f'color:{T.TEXT};margin:0;padding:0;">{body}</body></html>'
    )