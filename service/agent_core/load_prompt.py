from pathlib import Path


def load_prompt(relative_path: str) -> str:
    """
    加载提示词文件内容
    :param relative_path: 相对于项目根目录的路径，例如 'prompt/interview/interview_system.md'
    :return: 文件内容字符串
    """
    # 项目根目录 = service/agent_core/ 的父目录的父目录
    base_dir = Path(__file__).resolve().parent.parent.parent

    # 拼接完整路径
    file_path = base_dir / relative_path

    if not file_path.exists():
        raise FileNotFoundError(f"提示词文件未找到：{file_path}")

    # 读取内容 (utf-8 编码) 并去除首尾多余空白
    return file_path.read_text(encoding="utf-8").strip()
