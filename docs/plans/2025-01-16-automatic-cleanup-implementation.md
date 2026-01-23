# 自动清理旧版本升级功能实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**目标:** 为 install.py 添加自动清理功能，升级时自动删除旧位置的脚本文件

**架构:** 在 copy_hook_files 方法中添加检测和清理逻辑，先复制新文件到 pushover-hook/ 子目录，验证成功后删除旧位置的脚本文件

**技术栈:** Python 3, pathlib, shutil

---

## 前置检查

**确认当前工作目录是项目根目录**

Run:
```bash
cd C:\WorkSpace\agent\cc-pushover-hook
```

Expected: 当前目录包含 `install.py` 和 `.claude/` 文件夹

---

## Task 1: 添加旧文件检测逻辑

**Files:**
- Modify: `install.py:101-137` (copy_hook_files method)

**Step 1: 阅读当前的 copy_hook_files 方法**

Read: `install.py` lines 101-137

Current code structure:
```python
def copy_hook_files(self) -> None:
    """Copy hook script files to target directory."""
    print("\n[Step 3/5] Copying Hook Files")
    print("-" * 60)

    source_hooks_dir = self.script_dir / ".claude" / "hooks" / "pushover-hook"
    # ... rest of method
```

**Step 2: 在方法开始处添加旧文件检测逻辑**

Edit: `install.py` line 104 (after the print("-" * 60) line)

Add after line 104:
```python
    # Detect old files from previous installation
    old_hooks_dir = self.target_dir / ".claude" / "hooks"
    old_files_to_cleanup = [
        "pushover-notify.py",
        "test-pushover.py",
        "diagnose.py",
        "README.md",
        "debug.log",
    ]

    existing_old_files = []
    for filename in old_files_to_cleanup:
        old_file = old_hooks_dir / filename
        if old_file.exists():
            existing_old_files.append(old_file)

    # Check for __pycache__ directory
    old_pycache = old_hooks_dir / "__pycache__"
    if old_pycache.exists() and old_pycache.is_dir():
        existing_old_files.append(old_pycache)

```

**Step 3: 验证代码语法正确**

Run:
```bash
python -m py_compile install.py
```

Expected: 无语法错误，无输出

**Step 4: 提交添加检测逻辑**

Run:
```bash
git add install.py
git commit -m "feat(install): add old file detection logic"
```

---

## Task 2: 添加清理逻辑

**Files:**
- Modify: `install.py` (end of copy_hook_files method)

**Step 1: 找到 copy_hook_files 方法的结尾**

Read: `install.py` lines 130-137

Current end of method:
```python
        if copied == 0:
            print("[ERROR] No files were copied!")
            sys.exit(1)
```

**Step 2: 在方法结尾添加清理逻辑**

Edit: `install.py` after line 136 (after `sys.exit(1)`)

Add:
```python

    # Cleanup old files after successful copy
    if copied > 0 and existing_old_files:
        print(f"\n[INFO] Cleaning up {len(existing_old_files)} old file(s)...")
        for old_file in existing_old_files:
            try:
                if old_file.is_dir():
                    shutil.rmtree(old_file)
                else:
                    old_file.unlink()
                print(f"[OK] Removed: {old_file.name}")
            except Exception as e:
                print(f"[WARN] Failed to remove {old_file.name}: {e}")
                print(f"[INFO] Please manually remove: {old_file}")
    elif copied > 0:
        print("\n[INFO] No old files found (fresh install or already cleaned)")

```

**Step 3: 验证代码语法正确**

Run:
```bash
python -m py_compile install.py
```

Expected: 无语法错误

**Step 4: 提交添加清理逻辑**

Run:
```bash
git add install.py
git commit -m "feat(install): add automatic cleanup of old files"
```

---

## Task 3: 更新方法文档字符串

**Files:**
- Modify: `install.py:102`

**Step 1: 更新 copy_hook_files 方法的文档字符串**

Edit: `install.py` line 102

From:
```python
"""Copy hook script files to target directory."""
```

To:
```python
"""Copy hook script files to target directory and cleanup old files."""
```

**Step 2: 提交文档更新**

Run:
```bash
git add install.py
git commit -m "docs(install): update method docstring for cleanup feature"
```

---

## Task 4: 测试 - 全新安装场景

**Files:**
- Test: Manual verification

**Step 1: 创建测试目录**

Run:
```bash
mkdir C:\temp\test-fresh-install
```

**Step 2: 运行安装脚本**

Run:
```bash
python install.py
```

Follow prompts:
- Enter target directory: `C:\temp\test-fresh-install`
- Complete installation

**Step 3: 验证输出**

Expected output should include:
```
[Step 3/5] Copying Hook Files
------------------------------------------------------------
[OK] Copied: pushover-notify.py
[OK] Copied: test-pushover.py
[OK] Copied: diagnose.py
[OK] Copied: README.md

[INFO] No old files found (fresh install or already cleaned)
```

**Step 4: 验证目录结构**

Run:
```bash
dir C:\temp\test-fresh-install\.claude\hooks\pushover-hook
```

Expected: 看到新文件在 pushover-hook/ 子目录中

**Step 5: 清理测试目录**

Run:
```bash
rmdir /s /q C:\temp\test-fresh-install
```

**No commit needed** - This is testing only

---

## Task 5: 测试 - 升级场景

**Files:**
- Test: Manual verification

**Step 1: 创建旧版本安装的测试目录**

Run:
```bash
mkdir C:\temp\test-upgrade\.claude\hooks
```

**Step 2: 复制旧版本文件（模拟旧安装）**

Run:
```bash
copy .claude\hooks\pushover-hook\pushover-notify.py C:\temp\test-upgrade\.claude\hooks\
copy .claude\hooks\pushover-hook\test-pushover.py C:\temp\test-upgrade\.claude\hooks\
```

**Step 3: 验证旧文件存在**

Run:
```bash
dir C:\temp\test-upgrade\.claude\hooks
```

Expected: 看到 pushover-notify.py 和 test-pushover.py 在 hooks/ 根目录

**Step 4: 运行新版本安装脚本**

Run:
```bash
python install.py
```

Follow prompts:
- Enter target directory: `C:\temp\test-upgrade`
- Complete installation

**Step 5: 验证清理输出**

Expected output should include:
```
[INFO] Cleaning up 2 old file(s)...
[OK] Removed: pushover-notify.py
[OK] Removed: test-pushover.py
```

**Step 6: 验证旧文件已删除**

Run:
```bash
dir C:\temp\test-upgrade\.claude\hooks
```

Expected: 旧文件已被删除，只有 pushover-hook/ 子目录存在

**Step 7: 验证新文件在子目录中**

Run:
```bash
dir C:\temp\test-upgrade\.claude\hooks\pushover-hook
```

Expected: 新文件在 pushover-hook/ 子目录中

**Step 8: 清理测试目录**

Run:
```bash
rmdir /s /q C:\temp\test-upgrade
```

**No commit needed** - This is testing only

---

## Task 6: 更新 CHANGELOG.md

**Files:**
- Modify: `CHANGELOG.md`

**Step 1: 读取当前 CHANGELOG.md**

Read: `CHANGELOG.md`

**Step 2: 更新 Changed 部分**

Edit: `CHANGELOG.md`

在 `### Changed` 部分添加或更新：

```markdown
### Changed
- Hook scripts now located in `.claude/hooks/pushover-hook/` subdirectory for better isolation
- Updated `install.py` to create `pushover-hook/` subdirectory during installation
- **Installation now automatically cleans up old script files from previous versions**
- All documentation updated with new paths
```

**Step 3: 更新 Migration Notes 部分**

Edit: `CHANGELOG.md`

更新为：

```markdown
### Migration Notes
If you have an existing installation:
1. Run the new `install.py` script - it will **automatically remove old files** and update your configuration
2. Or manually move files from `.claude/hooks/` to `.claude/hooks/pushover-hook/`
3. Update paths in `settings.json`
```

**Step 4: 提交 CHANGELOG 更新**

Run:
```bash
git add CHANGELOG.md
git commit -m "docs: update changelog with automatic cleanup feature"
```

---

## Task 7: 更新 hooks/README.md

**Files:**
- Modify: `.claude/hooks/pushover-hook/README.md`

**Step 1: 读取当前 hooks README**

Read: `.claude/hooks/pushover-hook/README.md`

**Step 2: 添加升级说明部分**

在适当位置添加（例如在"部署到新项目"部分之后）：

```markdown
## 升级说明

如果您从旧版本升级：
- 直接运行 `python install.py` 即可
- 安装脚本会自动：
  - ✅ 复制新文件到 pushover-hook/ 子目录
  - ✅ 删除旧位置的脚本文件
  - ✅ 更新 settings.json 中的路径
  - ✅ 备份现有配置（settings.json.backup_*）
```

**Step 3: 提交 hooks README 更新**

Run:
```bash
git add .claude/hooks/pushover-hook/README.md
git commit -m "docs: add upgrade instructions to hooks README"
```

---

## Task 8: 最终验证测试

**Files:**
- Test: Full end-to-end verification

**Step 1: 创建完整的测试场景**

Run:
```bash
mkdir C:\temp\test-final\.claude\hooks
```

**Step 2: 模拟完整的旧版本安装**

Run:
```bash
copy .claude\hooks\pushover-hook\pushover-notify.py C:\temp\test-final\.claude\hooks\
copy .claude\hooks\pushover-hook\test-pushover.py C:\temp\test-final\.claude\hooks\
copy .claude\hooks\pushover-hook\diagnose.py C:\temp\test-final\.claude\hooks\
copy .claude\hooks\pushover-hook\README.md C:\temp\test-final\.claude\hooks\
```

创建旧的 settings.json（模拟旧配置）：
```bash
echo {"hooks":{"Stop":[{"hooks":[{"type":"command","command":"python C:\\temp\\test-final\\.claude\\hooks\\pushover-notify.py"}]}]}} > C:\temp\test-final\.claude\settings.json
```

**Step 3: 运行完整安装**

Run:
```bash
python install.py
```

Follow prompts for `C:\temp\test-final`

**Step 4: 验证所有功能点**

检查清单：
- [ ] 新文件在 pushover-hook/ 子目录
- [ ] 旧文件已删除
- [ ] settings.json 路径已更新
- [ ] settings.json.backup_* 已创建
- [ ] 输出消息清晰

**Step 5: 运行诊断脚本验证**

Run:
```bash
python C:\temp\test-final\.claude\hooks\pushover-hook\diagnose.py
```

Expected: 诊断脚本报告新的文件路径

**Step 6: 清理测试目录**

Run:
```bash
rmdir /s /q C:\temp\test-final
```

**No commit needed** - This is testing only

---

## 验收标准

完成所有任务后，验证以下条件：

- [ ] `install.py` 包含旧文件检测逻辑
- [ ] `install.py` 包含清理逻辑
- [ ] 全新安装测试通过（无清理消息）
- [ ] 升级场景测试通过（旧文件被删除）
- [ ] CHANGELOG.md 已更新
- [ ] hooks/README.md 已更新
- [ ] 所有更改已提交到 git

---

## 回滚计划

如果需要回滚：

```bash
# 回滚最近的提交
git revert HEAD~4..HEAD

# 或者硬重置（谨慎使用）
git reset --hard HEAD~4
```

---

## 预计时间

- Task 1 (添加检测逻辑): 10 分钟
- Task 2 (添加清理逻辑): 15 分钟
- Task 3 (更新文档字符串): 5 分钟
- Task 4 (全新安装测试): 10 分钟
- Task 5 (升级场景测试): 15 分钟
- Task 6 (更新 CHANGELOG): 5 分钟
- Task 7 (更新 hooks README): 5 分钟
- Task 8 (最终验证): 15 分钟

**总计: 约 80 分钟**
