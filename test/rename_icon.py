import os
import re
import sys


def batch_rename_icons(folder_path, dry_run=False):
    if not os.path.isdir(folder_path):
        print("❌ 错误：文件夹路径不存在")
        sys.exit(1)

    # 匹配逻辑：捕获 `_数字dp` 之前的所有内容
    pattern = re.compile(r'^(.+?)_\d+dp_.*\.png$', re.IGNORECASE)
    renamed_count = 0

    for filename in os.listdir(folder_path):
        if not filename.lower().endswith('.png'):
            continue

        match = pattern.match(filename)
        if not match:
            continue

        new_name = match.group(1) + '.png'
        old_path = os.path.join(folder_path, filename)
        new_path = os.path.join(folder_path, new_name)

        if old_path == new_path:
            continue
        if os.path.exists(new_path):
            print(f"⚠️ 跳过: {new_name} 已存在")
            continue

        if dry_run:
            print(f"🔍 [预览] {filename} -> {new_name}")
        else:
            os.rename(old_path, new_path)
            renamed_count += 1

    if dry_run:
        print("\n✅ 预览完成。确认无误后，请移除 `--dry-run` 参数重新运行。")
    else:
        print(f"\n✅ 批量重命名完成！共处理 {renamed_count} 个文件。")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python rename_icons.py <文件夹路径> [--dry-run]")
        sys.exit(1)

    is_dry_run = '--dry-run' in sys.argv
    target_folder = sys.argv[1]
    batch_rename_icons(target_folder, dry_run=is_dry_run)