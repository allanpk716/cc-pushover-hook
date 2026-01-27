#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试 CLAUDE_PROJECT_DIR 环境变量是否正确设置
用于验证 hook 配置的路径是否有效
"""

import os
import sys
import json

def test_project_dir_env():
    """测试 CLAUDE_PROJECT_DIR 环境变量"""
    print("=" * 60)
    print("测试 CLAUDE_PROJECT_DIR 环境变量")
    print("=" * 60)

    project_dir = os.getenv("CLAUDE_PROJECT_DIR")

    if project_dir is None:
        print("❌ 失败: CLAUDE_PROJECT_DIR 环境变量未设置")
        print("\n这说明脚本不是由 Claude Code hook 触发的")
        return False

    print(f"✅ CLAUDE_PROJECT_DIR = {project_dir}")

    # 检查路径是否存在
    if not os.path.exists(project_dir):
        print(f"❌ 失败: 项目目录不存在: {project_dir}")
        return False

    print(f"✅ 项目目录存在")

    # 检查 settings.json 是否存在
    settings_path = os.path.join(project_dir, ".claude", "settings.json")
    if not os.path.exists(settings_path):
        print(f"❌ 失败: settings.json 不存在: {settings_path}")
        return False

    print(f"✅ settings.json 存在: {settings_path}")

    # 检查 hook 脚本是否存在
    hook_script = os.path.join(project_dir, ".claude", "hooks", "pushover-hook", "pushover-notify.py")
    if not os.path.exists(hook_script):
        print(f"❌ 失败: hook 脚本不存在: {hook_script}")
        return False

    print(f"✅ hook 脚本存在: {hook_script}")

    # 验证相对路径构建
    relative_path = ".claude\\hooks\\pushover-hook\\pushover-notify.py"
    full_path = os.path.join(project_dir, relative_path)
    normalized_path = os.path.normpath(full_path)

    print(f"\n相对路径: {relative_path}")
    print(f"完整路径: {normalized_path}")

    if os.path.exists(normalized_path):
        print(f"✅ 相对路径解析成功")
    else:
        print(f"❌ 相对路径解析失败")
        return False

    print("\n" + "=" * 60)
    print("✅ 所有测试通过! hook 配置正确")
    print("=" * 60)
    return True


def test_manual_mode():
    """手动测试模式"""
    print("\n" + "=" * 60)
    print("手动测试模式")
    print("=" * 60)

    current_dir = os.getcwd()
    print(f"当前工作目录: {current_dir}")

    # 尝试向上查找项目根目录（包含 .claude 文件夹）
    import pathlib
    path = pathlib.Path(current_dir)

    for level in range(5):  # 最多向上查找 5 层
        if (path / ".claude").exists():
            project_root = str(path)
            print(f"✅ 找到项目根目录: {project_root}")

            # 模拟设置环境变量
            os.environ["CLAUDE_PROJECT_DIR"] = project_root

            # 运行测试
            return test_project_dir_env()

        path = path.parent

    print("❌ 未找到项目根目录（包含 .claude 文件夹的目录）")
    return False


if __name__ == "__main__":
    # 如果提供了命令行参数，使用手动模式
    if len(sys.argv) > 1 and sys.argv[1] == "--manual":
        success = test_manual_mode()
    else:
        success = test_project_dir_env()

    sys.exit(0 if success else 1)
