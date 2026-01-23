# Pushover Hook 子目录重构实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**目标:** 将 pushover hook 脚本移至独立的子目录 `pushover-hook/`，避免与其他项目的 hook 文件冲突

**架构:** 在 `.claude/hooks/` 下创建 `pushover-hook/` 子目录，更新 install.py 以支持新结构，修改 settings.json 中的命令路径

**技术栈:** Python 3, Claude Code Hooks, 跨平台兼容 (Windows/Linux/macOS)

---

## 前置检查

**确认当前工作目录是项目根目录**

Run:
```bash
# Windows
cd /d C:\WorkSpace\agent\cc-pushover-hook

# Linux/macOS
cd C:\WorkSpace\agent\cc-pushover-hook
```

Expected: 当前目录包含 `install.py` 和 `.claude/` 文件夹

---

## Task 1: 创建子目录并移动 hook 脚本

**Files:**
- Create: `.claude/hooks/pushover-hook/` (directory)
- Move: `.claude/hooks/*.py` → `.claude/hooks/pushover-hook/`
- Move: `.claude/hooks/README.md` → `.claude/hooks/pushover-hook/`
- Move: `.claude/hooks/debug.log` → `.claude/hooks/pushover-hook/` (if exists)

**Step 1: 创建 pushover-hook 子目录**

Run:
```bash
# Windows
mkdir .claude\hooks\pushover-hook

# Linux/macOS
mkdir -p .claude/hooks/pushover-hook
```

Expected: 目录创建成功，无错误

**Step 2: 移动 Python 脚本文件**

Run:
```bash
# Windows
move .claude\hooks\pushover-notify.py .claude\hooks\pushover-hook\
move .claude\hooks\test-pushover.py .claude\hooks\pushover-hook\
move .claude\hooks\test-encoding-manual.py .claude\hooks\pushover-hook\
move .claude\hooks\diagnose.py .claude\hooks\pushover-hook\

# Linux/macOS
mv .claude/hooks/pushover-notify.py .claude/hooks/pushover-hook/
mv .claude/hooks/test-pushover.py .claude/hooks/pushover-hook/
mv .claude/hooks/test-encoding-manual.py .claude/hooks/pushover-hook/
mv .claude/hooks/diagnose.py .claude/hooks/pushover-hook/
```

Expected: 所有 .py 文件已移动到 pushover-hook/ 子目录

**Step 3: 移动 README 和日志文件**

Run:
```bash
# Windows
move .claude\hooks\README.md .claude\hooks\pushover-hook\
if exist .claude\hooks\debug.log move .claude\hooks\debug.log .claude\hooks\pushover-hook\

# Linux/macOS
mv .claude/hooks/README.md .claude/hooks/pushover-hook/
[ -f .claude/hooks/debug.log ] && mv .claude/hooks/debug.log .claude/hooks/pushover-hook/
```

Expected: README.md 和 debug.log (如果存在) 已移动

**Step 4: 验证文件移动完成**

Run:
```bash
# Windows
dir .claude\hooks\pushover-hook

# Linux/macOS
ls -la .claude/hooks/pushover-hook/
```

Expected: 看到以下文件
- pushover-notify.py
- test-pushover.py
- test-encoding-manual.py
- diagnose.py
- README.md
- debug.log (可选)

**Step 5: 清理 __pycache__ 目录（如果存在）**

Run:
```bash
# Windows
if exist .claude\hooks\__pycache__ rmdir /s /q .claude\hooks\__pycache__

# Linux/macOS
rm -rf .claude/hooks/__pycache__
```

Expected: .claude/hooks/ 下只有 pushover-hook/ 子目录

**Step 6: 提交文件移动**

Run:
```bash
git add .claude/hooks/
git commit -m "refactor: move hook scripts to pushover-hook subdirectory"
```

---

## Task 2: 修改 install.py 支持子目录结构

**Files:**
- Modify: `install.py:84-99` (create_hook_directory method)

**Step 1: 阅读当前的 create_hook_directory 方法**

Read: `install.py` lines 84-99

Current code:
```python
def create_hook_directory(self) -> None:
    """Create the .claude/hooks directory structure."""
    print("\n[Step 2/5] Creating Hook Directory")
    print("-" * 60)

    self.hook_dir = self.target_dir / ".claude" / "hooks"
    cache_dir = self.target_dir / ".claude" / "cache"

    try:
        self.hook_dir.mkdir(parents=True, exist_ok=True)
        cache_dir.mkdir(parents=True, exist_ok=True)
        print(f"[OK] Created: {self.hook_dir}")
        print(f"[OK] Created: {cache_dir}")
    except Exception as e:
        print(f"[ERROR] Failed to create directories: {e}")
        sys.exit(1)
```

**Step 2: 修改 create_hook_directory 添加子目录**

Edit: `install.py` line 89

From:
```python
self.hook_dir = self.target_dir / ".claude" / "hooks"
```

To:
```python
self.hook_dir = self.target_dir / ".claude" / "hooks" / "pushover-hook"
```

**Step 3: 更新方法文档字符串**

Edit: `install.py` line 85

From:
```python
"""Create the .claude/hooks directory structure."""
```

To:
```python
"""Create the .claude/hooks/pushover-hook directory structure."""
```

**Step 4: 验证生成的 settings.json 路径会正确更新**

由于 `self.hook_dir` 已更新，第 224 行的 `hook_script_path` 会自动变为：
- Windows: `C:\project\.claude\hooks\pushover-hook\pushover-notify.py`
- Unix: `/project/.claude/hooks/pushover-hook/pushover-notify.py`

无需额外修改。

**Step 5: 提交 install.py 修改**

Run:
```bash
git add install.py
git commit -m "refactor(install): update hook directory to pushover-hook subdirectory"
```

---

## Task 3: 更新当前项目的 settings.json

**Files:**
- Modify: `.claude/settings.json`

**Step 1: 阅读当前 settings.json**

Read: `.claude/settings.json`

**Step 2: 更新所有命令路径**

Edit: `.claude/settings.json` - 更新所有 `command` 字段

当前路径:
```
C:\WorkSpace\agent\cc-pushover-hook\.claude\hooks\pushover-notify.py
```

更新为:
```
C:\WorkSpace\agent\cc-pushover-hook\.claude\hooks\pushover-hook\pushover-notify.py
```

完整的 settings.json:
```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "set PYTHONIOENCODING=utf-8&& python \"C:\\WorkSpace\\agent\\cc-pushover-hook\\.claude\\hooks\\pushover-hook\\pushover-notify.py\""
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "set PYTHONIOENCODING=utf-8&& python \"C:\\WorkSpace\\agent\\cc-pushover-hook\\.claude\\hooks\\pushover-hook\\pushover-notify.py\""
          }
        ]
      }
    ],
    "Notification": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "set PYTHONIOENCODING=utf-8&& python \"C:\\WorkSpace\\agent\\cc-pushover-hook\\.claude\\hooks\\pushover-hook\\pushover-notify.py\""
          }
        ]
      }
    ]
  }
}
```

**Step 3: 提交 settings.json 修改**

Run:
```bash
git add .claude/settings.json
git commit -m "refactor: update settings.json with pushover-hook subdirectory paths"
```

---

## Task 4: 更新 .claude/hooks/pushover-hook/README.md

**Files:**
- Modify: `.claude/hooks/pushover-hook/README.md`

**Step 1: 阅读当前 README**

Read: `.claude/hooks/pushover-hook/README.md`

**Step 2: 更新所有路径引用**

Edit: `.claude/hooks/pushover-hook/README.md`

查找并替换:
- `.claude/hooks/diagnose.py` → `.claude/hooks/pushover-hook/diagnose.py`
- `.claude/hooks/test-pushover.py` → `.claude/hooks/pushover-hook/test-pushover.py`
- `.claude/hooks/debug.log` → `.claude/hooks/pushover-hook/debug.log`
- `.claude/cache/` → `.claude/cache/` (保持不变)

更新后的关键部分:

```markdown
# Claude Code Pushover 通知 Hook

## 问题诊断

### 快速诊断

在项目目录中运行：

```bash
python .claude/hooks/pushover-hook/diagnose.py
```

## 测试通知

运行测试脚本发送测试通知：

```bash
python .claude/hooks/pushover-hook/test-pushover.py
```

## 日志位置

- 调试日志: `.claude/hooks/pushover-hook/debug.log`
- 会话缓存: `.claude/cache/session-*.jsonl`
```

**Step 3: 提交 README 修改**

Run:
```bash
git add .claude/hooks/pushover-hook/README.md
git commit -m "docs: update README with new subdirectory paths"
```

---

## Task 5: 更新项目根目录 README.md（如果存在）

**Files:**
- Modify: `README.md` (if exists at project root)

**Step 1: 检查是否存在根目录 README**

Run:
```bash
# Windows
if exist README.md echo EXISTS

# Linux/macOS
[ -f README.md ] && echo EXISTS || echo NOT_FOUND
```

**Step 2: 如果存在，更新部署说明**

If README.md exists, update the deployment section:

```markdown
## 部署到新项目

### 方法一：使用安装脚本（推荐）

1. 克隆或下载此项目
2. 运行安装脚本：`python install.py`
3. 按提示输入目标项目路径
4. 设置环境变量 `PUSHOVER_TOKEN` 和 `PUSHOVER_USER`
5. 运行诊断脚本验证配置

### 方法二：手动安装

1. 复制 `.claude/hooks/pushover-hook/` 文件夹到目标项目的 `.claude/hooks/` 目录
2. 复制 `.claude/settings.json` 中的 hooks 配置到目标项目
3. 设置环境变量 `PUSHOVER_TOKEN` 和 `PUSHOVER_USER`
```

**Step 3: 提交 README 修改（如果有）**

Run:
```bash
git add README.md
git commit -m "docs: update README with subdirectory deployment instructions"
```

---

## Task 6: 测试验证 - 诊断脚本

**Files:**
- Test: `.claude/hooks/pushover-hook/diagnose.py`

**Step 1: 运行诊断脚本**

Run:
```bash
python .claude/hooks/pushover-hook/diagnose.py
```

Expected:
- 脚本成功执行
- 报告当前配置状态
- 如果环境变量未设置，显示相应警告

**Step 2: 检查 debug.log 位置**

Run:
```bash
# Windows
dir .claude\hooks\pushover-hook\debug.log

# Linux/macOS
ls -la .claude/hooks/pushover-hook/debug.log
```

Expected: debug.log 文件在新的子目录中

---

## Task 7: 测试验证 - 安装脚本

**Files:**
- Test: `install.py`

**Step 1: 创建测试项目目录**

Run:
```bash
# Windows
mkdir C:\temp\test-pushover-project

# Linux/macOS
mkdir -p /tmp/test-pushover-project
```

**Step 2: 运行安装脚本**

Run:
```bash
python install.py
```

Follow prompts:
- Enter target directory: `C:\temp\test-pushover-project` (或 `/tmp/test-pushover-project`)
- Complete installation

**Step 3: 验证测试项目的目录结构**

Run:
```bash
# Windows
dir C:\temp\test-pushover-project\.claude\hooks\pushover-hook

# Linux/macOS
ls -la /tmp/test-pushover-project/.claude/hooks/pushover-hook/
```

Expected:
- pushover-hook/ 子目录已创建
- 所有脚本文件已复制

**Step 4: 验证测试项目的 settings.json**

Read: `C:\temp\test-pushover-project\.claude\settings.json`

Expected:
- 命令路径包含 `pushover-hook` 子目录
- 例如: `C:\temp\test-pushover-project\.claude\hooks\pushover-hook\pushover-notify.py`

**Step 5: 清理测试项目**

Run:
```bash
# Windows
rmdir /s /q C:\temp\test-pushover-project

# Linux/macOS
rm -rf /tmp/test-pushover-project
```

---

## Task 8: 测试验证 - 端到端通知

**Files:**
- Test: 完整的 hook 工作流

**Step 1: 确保环境变量已设置**

Run:
```bash
# Windows CMD
echo %PUSHOVER_TOKEN%
echo %PUSHOVER_USER%

# Windows PowerShell
echo $env:PUSHOVER_TOKEN
echo $env:PUSHOVER_USER

# Linux/macOS
echo $PUSHOVER_TOKEN
echo $PUSHOVER_USER
```

If not set, set them temporarily:
```bash
# Windows
set PUSHOVER_TOKEN=your_token
set PUSHOVER_USER=your_user

# Linux/macOS
export PUSHOVER_TOKEN=your_token
export PUSHOVER_USER=your_user
```

**Step 2: 发送测试通知**

Run:
```bash
python .claude/hooks/pushover-hook/test-pushover.py
```

Expected:
- 脚本执行成功
- 收到 Pushover 测试通知

**Step 3: 检查 debug.log**

Run:
```bash
# Windows
type .claude\hooks\pushover-hook\debug.log

# Linux/macOS
cat .claude/hooks/pushover-hook/debug.log
```

Expected: 日志记录在新的子目录中

---

## Task 9: 更新设计文档

**Files:**
- Modify: `docs/plans/2025-01-15-claude-code-pushover-notifications-design.md`

**Step 1: 更新文件结构图**

Edit: `docs/plans/2025-01-15-claude-code-pushover-notifications-design.md` lines 119-126

From:
```
.claude/
├── hooks/
│   └── pushover-notify.py
├── cache/
│   └── session-{id}.jsonl
└── settings.json
```

To:
```
.claude/
├── hooks/
│   └── pushover-hook/
│       └── pushover-notify.py
├── cache/
│   └── session-{id}.jsonl
└── settings.json
```

**Step 2: 更新安装步骤说明**

Edit: `docs/plans/2025-01-15-claude-code-pushover-notifications-design.md` line 222

From:
```
3. 创建 `.claude/hooks/` 和 `.claude/cache/` 目录
4. 添加 `pushover-notify.py` 脚本
```

To:
```
3. 创建 `.claude/hooks/pushover-hook/` 和 `.claude/cache/` 目录
4. 添加 `pushover-notify.py` 脚本到 `pushover-hook/` 子目录
```

**Step 3: 提交文档更新**

Run:
```bash
git add docs/plans/2025-01-15-claude-code-pushover-notifications-design.md
git commit -m "docs: update design doc with subdirectory structure"
```

---

## Task 10: 创建变更日志文件

**Files:**
- Create: `CHANGELOG.md`

**Step 1: 创建 CHANGELOG.md**

Write: `CHANGELOG.md`

```markdown
# Changelog

## [Unreleased]

### Changed
- Hook scripts now located in `.claude/hooks/pushover-hook/` subdirectory for better isolation
- Updated `install.py` to create `pushover-hook/` subdirectory during installation
- All documentation updated with new paths

### Migration Notes
If you have an existing installation:
1. Run the new `install.py` script - it will automatically update your configuration
2. Or manually move files from `.claude/hooks/` to `.claude/hooks/pushover-hook/`
3. Update paths in `settings.json`
```

**Step 2: 提交变更日志**

Run:
```bash
git add CHANGELOG.md
git commit -m "docs: add changelog for subdirectory refactor"
```

---

## 验收标准

完成所有任务后，验证以下条件：

- [ ] `.claude/hooks/pushover-hook/` 目录存在，包含所有 hook 脚本
- [ ] `.claude/settings.json` 中的命令路径指向 `pushover-hook/` 子目录
- [ ] `install.py` 创建 `pushover-hook/` 子目录
- [ ] 运行 `diagnose.py` 成功，日志写入 `pushover-hook/debug.log`
- [ ] 运行 `install.py` 安装到测试项目，目录结构正确
- [ ] 发送测试通知成功
- [ ] 所有文档已更新
- [ ] 所有更改已提交到 git

---

## 回滚计划

如果需要回滚：

```bash
# 回滚所有更改
git reset --hard HEAD~10

# 或者分步回滚
git revert HEAD~10..HEAD
```

---

## 预计时间

- Task 1 (文件移动): 5-10 分钟
- Task 2 (install.py): 5 分钟
- Task 3 (settings.json): 5 分钟
- Task 4 (hooks README): 5 分钟
- Task 5 (根 README): 5 分钟 (如果存在)
- Task 6-8 (测试): 15-20 分钟
- Task 9-10 (文档): 10 分钟

**总计: 约 50-60 分钟**
