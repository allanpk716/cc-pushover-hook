# 自动清理旧版本升级功能设计

**日期:** 2025-01-16
**作者:** Claude
**状态:** 设计完成

---

## 一、功能概述

为安装脚本添加自动清理功能，当用户从旧版本（脚本在 `.claude/hooks/`）升级到新版本（脚本在 `.claude/hooks/pushover-hook/`）时，自动删除旧位置的脚本文件。

### 目标

1. **无缝升级** - 用户只需重新运行 `install.py`，自动完成清理
2. **安全性** - 确保新文件就位后才删除旧文件
3. **清晰反馈** - 明确告知用户清理了哪些文件

---

## 二、架构设计

### 清理时机：方案 2（复制后清理）✅

**流程：**
```
1. 检测旧文件（记录）
2. 复制新文件到 pushover-hook/ 子目录
3. 验证复制成功
4. 删除旧文件
```

**选择理由：**
- 最安全：确保新文件就位后再删除旧文件
- 原子性更好：失败时不会破坏现有功能
- 用户体验好：即使出错，原有功能不受影响

---

## 三、实现设计

### 修改 `copy_hook_files` 方法

**位置:** `install.py` 第 101-137 行

**新增代码结构：**

```python
def copy_hook_files(self) -> None:
    """Copy hook script files to target directory and cleanup old files."""
    print("\n[Step 3/5] Copying Hook Files")
    print("-" * 60)

    source_hooks_dir = self.script_dir / ".claude" / "hooks" / "pushover-hook"

    # ============ 新增：检测并记录旧文件 ============
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

    # 检查并清理 __pycache__ 目录
    old_pycache = old_hooks_dir / "__pycache__"
    if old_pycache.exists() and old_pycache.is_dir():
        existing_old_files.append(old_pycache)
    # ================================================

    files_to_copy = [
        "pushover-notify.py",
        "test-pushover.py",
        "diagnose.py",
        "README.md",
    ]

    # 原有复制逻辑
    copied = 0
    for filename in files_to_copy:
        source = source_hooks_dir / filename
        target = self.hook_dir / filename

        if not source.exists():
            print(f"[WARN] Source file not found: {filename}")
            continue

        try:
            shutil.copy2(source, target)
            if self.platform != "Windows" and filename.endswith(".py"):
                target.chmod(0o755)
            print(f"[OK] Copied: {filename}")
            copied += 1
        except Exception as e:
            print(f"[ERROR] Failed to copy {filename}: {e}")

    # 验证复制成功
    if copied == 0:
        print("[ERROR] No files were copied!")
        print("[INFO] Old files were preserved for safety.")
        sys.exit(1)

    # ============ 新增：复制成功后清理旧文件 ============
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
    # ================================================
```

---

## 四、错误处理策略

### 1. 复制失败的处理

```python
if copied == 0:
    print("[ERROR] No files were copied!")
    print("[INFO] Old files were preserved for safety.")
    sys.exit(1)
```

- 如果复制失败，保留旧文件，退出安装
- 用户可以重试，不会丢失功能

### 2. 部分复制成功的处理

```python
expected_count = len(files_to_copy)
if copied < expected_count:
    print(f"[WARN] Only {copied}/{expected_count} files copied.")
    # 仍然尝试清理旧文件，因为至少有部分新功能可用
```

### 3. 清理失败的处理

```python
try:
    old_file.unlink()
    print(f"[OK] Removed: {old_file.name}")
except Exception as e:
    print(f"[WARN] Failed to remove {old_file.name}: {e}")
    print(f"[INFO] Please manually remove: {old_file}")
    # 继续清理其他文件，不中断安装
```

- 单个文件清理失败不应该中断整个流程
- 用户提供手动删除的指导

---

## 五、边界情况处理

| 情况 | 处理方式 |
|------|---------|
| **全新安装**（无旧文件） | `existing_old_files` 为空，跳过清理步骤 |
| **旧文件已在子目录**（用户手动迁移） | 旧文件检测失败，不会删除新文件 |
| **部分旧文件存在** | 只删除存在的文件，忽略不存在的 |
| **__pycache__ 目录** | 使用 `shutil.rmtree()` 递归删除 |
| **权限不足** | 输出警告，指导用户手动删除 |

---

## 六、测试策略

### 测试场景

**场景 1：全新安装测试**
```bash
mkdir C:\temp\test-new-install
python install.py
# 验证：无清理消息，文件正确安装到子目录
```

**场景 2：从旧版本升级测试**
```bash
mkdir C:\temp\test-upgrade\.claude\hooks
# 复制旧版本文件
python install.py
# 验证：新文件复制 + 旧文件删除
```

**场景 3：部分文件存在测试**
```bash
# 只有 pushover-notify.py
python install.py
# 验证：只删除存在的文件
```

**场景 4：复制失败测试**
```bash
# 模拟源文件缺失
python install.py
# 验证：退出且旧文件保留
```

### 验证函数（可选）

```python
def verify_installation(self) -> bool:
    """Verify installation was successful."""
    checks = []

    # 检查新文件存在
    for filename in ["pushover-notify.py", "test-pushover.py", "diagnose.py"]:
        if (self.hook_dir / filename).exists():
            checks.append(True)

    # 检查旧文件已清理
    old_hooks_dir = self.target_dir / ".claude" / "hooks"
    for filename in ["pushover-notify.py", "test-pushover.py"]:
        if not (old_hooks_dir / filename).exists():
            checks.append(True)

    return all(checks)
```

---

## 七、用户反馈设计

### 成功升级的输出

```
[Step 3/5] Copying Hook Files
------------------------------------------------------------
[OK] Copied: pushover-notify.py
[OK] Copied: test-pushover.py
[OK] Copied: diagnose.py
[OK] Copied: README.md

[INFO] Cleaning up 4 old file(s)...
[OK] Removed: pushover-notify.py
[OK] Removed: test-pushover.py
[OK] Removed: diagnose.py
[OK] Removed: README.md
[INFO] Old __pycache__ directory removed
```

### 全新安装的输出

```
[Step 3/5] Copying Hook Files
------------------------------------------------------------
[OK] Copied: pushover-notify.py
[OK] Copied: test-pushover.py
[OK] Copied: diagnose.py
[OK] Copied: README.md

[INFO] No old files found (fresh install or already cleaned)
```

### 清理失败的输出

```
[INFO] Cleaning up 1 old file(s)...
[WARN] Failed to remove pushover-notify.py: [Errno 13] Permission denied
[INFO] Please manually remove: C:\project\.claude\hooks\pushover-notify.py
```

---

## 八、文档更新

### 更新 CHANGELOG.md

```markdown
## [Unreleased]

### Changed
- Hook scripts now located in `.claude/hooks/pushover-hook/` subdirectory for better isolation
- Updated `install.py` to create `pushover-hook/` subdirectory during installation
- **Installation now automatically cleans up old script files from previous versions**
- All documentation updated with new paths

### Migration Notes
If you have an existing installation:
1. Run the new `install.py` script - it will **automatically remove old files** and update your configuration
2. Or manually move files from `.claude/hooks/` to `.claude/hooks/pushover-hook/`
3. Update paths in `settings.json`
```

### 更新 hooks/README.md

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

---

## 九、实施清单

- [ ] 修改 `install.py` 的 `copy_hook_files` 方法
- [ ] 添加旧文件检测逻辑
- [ ] 添加清理逻辑
- [ ] 更新用户反馈消息
- [ ] 测试全新安装场景
- [ ] 测试从旧版本升级场景
- [ ] 测试部分文件存在场景
- [ ] 测试复制失败场景
- [ ] 更新 CHANGELOG.md
- [ ] 更新 hooks/README.md
- [ ] 提交代码

---

## 十、回滚计划

如果新功能出现问题：

1. **临时禁用清理** - 注释掉清理代码段
2. **恢复旧版本** - 使用 git revert 回退相关提交
3. **用户手动清理** - 在文档中提供手动清理步骤
