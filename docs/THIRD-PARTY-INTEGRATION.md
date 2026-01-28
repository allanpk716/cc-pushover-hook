# 第三方程序集成指南

本文档专门为希望集成 cc-pushover-hook 的第三方程序开发者准备，重点说明版本管理和自动更新的关键细节。

## 目录

- [概述](#概述)
- [版本管理机制](#版本管理机制)
- [安装脚本输出格式](#安装脚本输出格式)
- [集成最佳实践](#集成最佳实践)
- [常见陷阱](#常见陷阱)
- [完整集成示例](#完整集成示例)

---

## 概述

cc-pushover-hook 可以作为 Git Hook 扩展集成到第三方应用程序中（如 ai-commit-hub）。集成程序需要管理扩展的下载、安装和更新流程。

### 集成架构

```
第三方应用 (如 ai-commit-hub)
    │
    ├─→ 下载/更新扩展仓库 (git clone/pull)
    │       └─ ~/.ai-commit-hub/extensions/cc-pushover-hook/
    │
    ├─→ 调用 install.py 安装到项目
    │       └─ <project>/.claude/hooks/pushover-hook/
    │               ├─ pushover-notify.py
    │               └─ VERSION          # 关键！版本文件
    │
    └─→ 读取 VERSION 文件判断是否需要更新
```

---

## 版本管理机制

### VERSION 文件格式

VERSION 文件是版本管理的核心，必须正确创建和解析。

**文件位置：**
```
<project-path>/.claude/hooks/pushover-hook/VERSION
```

**文件格式：**
```ini
version=<version_string>
installed_at=<iso8601_timestamp>
git_commit=<commit_hash>
```

**示例：**
```ini
version=1.0.0
installed_at=2025-01-28T10:30:00Z
git_commit=3c3fc8a
```

### 版本号来源

install.py 通过以下方式获取版本号（按优先级）：

1. **git describe --tags --always**：获取带标签的版本描述（如 `v1.0.0` 或 `v1.0.0-5-gabcdef`）
2. **git rev-parse --short HEAD**：获取短 commit hash（如 `3c3fc8a`）
3. **硬编码版本**：作为最后回退（当前为 `1.0.0`）

**重要：** install.py 必须在其所在仓库目录中执行，才能通过 `git describe` 获取正确的版本号。

### 版本比较逻辑

第三方程序通过比较两个版本来判断是否需要更新：

1. **远程版本**：从扩展仓库目录执行 `git describe --tags --always` 获取
2. **本地版本**：从项目的 VERSION 文件中读取 `version=` 行

**比较示例：**
```go
// 伪代码
remoteVersion := executeGitDescribe(extensionRepoDir)
localVersion := readVersionFile(projectDir)

if remoteVersion != localVersion {
    // 需要更新
    installLatestHook(project)
}
```

---

## 安装脚本输出格式

### 非交互模式（推荐用于自动化）

使用 `--non-interactive` 标志时，install.py 输出 JSON 格式：

**成功输出：**
```json
{
  "status": "success",
  "action": "fresh_install",
  "hook_path": "/path/to/project/.claude/hooks/pushover-hook",
  "version": "1.0.0"
}
```

**失败输出：**
```json
{
  "status": "error",
  "message": "错误描述"
}
```

### 关键命令行参数

| 参数 | 说明 | 集成建议 |
|------|------|----------|
| `--target-dir PATH` | 目标项目目录（必需） | 必须指定 |
| `--non-interactive` | 非交互模式 | 强烈推荐 |
| `--force` | 强制重新安装 | 更新时使用 |
| `--timeout SECONDS` | Hook 超时时间 | 可选，默认 15 |
| `--quiet` | 静默模式 | 可选 |
| `--skip-diagnostics` | 跳过诊断 | 集成时推荐 |

### 推荐调用方式

```bash
# 安装
python install.py --target-dir "/path/to/project" --non-interactive --skip-diagnostics

# 更新
python install.py --target-dir "/path/to/project" --non-interactive --skip-diagnostics --force
```

---

## 集成最佳实践

### 1. 确保 VERSION 文件正确创建

**问题：** VERSION 文件创建失败但被忽略

**解决方案：** install.py 现在会在 VERSION 文件创建失败时抛出异常。集成程序应：

```python
import subprocess
import json

def install_hook(project_path: str) -> dict:
    result = subprocess.run(
        ["python", "install.py",
         "--target-dir", project_path,
         "--non-interactive",
         "--skip-diagnostics"],
        capture_output=True,
        text=True,
        cwd="/path/to/cc-pushover-hook"
    )

    # 检查返回码
    if result.returncode != 0:
        return {"success": False, "error": result.stderr}

    # 解析 JSON 输出
    try:
        output = json.loads(result.stdout)
        if output.get("status") == "success":
            return {"success": True, "version": output.get("version")}
        else:
            return {"success": False, "error": output.get("message")}
    except json.JSONDecodeError:
        return {"success": False, "error": "Invalid JSON output"}
```

### 2. 正确读取 VERSION 文件

```python
import re

def get_installed_version(project_path: str) -> str:
    """读取项目已安装的 hook 版本"""
    version_file = Path(project_path) / ".claude" / "hooks" / "pushover-hook" / "VERSION"

    if not version_file.exists():
        return None  # 未安装或旧版本

    content = version_file.read_text(encoding='utf-8')
    match = re.search(r'^version=(.+)$', content, re.MULTILINE)

    if match:
        return match.group(1).strip()

    return None  # 格式错误
```

### 3. 正确获取远程版本

```python
def get_extension_version(extension_dir: str) -> str:
    """从扩展仓库获取版本号"""
    result = subprocess.run(
        ["git", "describe", "--tags", "--always"],
        capture_output=True,
        text=True,
        cwd=extension_dir
    )

    if result.returncode == 0:
        return result.stdout.strip()

    return None
```

### 4. 完整的更新检查流程

```python
def check_update_needed(project_path: str, extension_dir: str) -> bool:
    """检查是否需要更新 hook"""
    local_version = get_installed_version(project_path)
    remote_version = get_extension_version(extension_dir)

    if not local_version:
        return True  # 未安装，需要安装

    if not remote_version:
        return False  # 无法获取远程版本，跳过更新

    return local_version != remote_version
```

### 5. 版本比较注意事项

**重要：** 版本比较应该使用字符串相等比较，而不是语义化版本比较。

**原因：**
- `git describe` 可能输出 `v1.0.0-5-gabcdef` 格式
- 包含 commit hash 的版本号无法用标准语义化版本比较
- 简单的字符串比较最可靠

```python
# 正确
if local_version != remote_version:
    update_hook()

# 错误（不要这样做）
if parse_semver(local_version) < parse_semver(remote_version):
    update_hook()
```

---

## 常见陷阱

### 陷阱 1：忽略 VERSION 文件创建失败

**问题：** 旧版本 install.py 在 VERSION 文件创建失败时只打印警告，不中断安装。

**后果：** 第三方程序认为安装成功，但无法读取版本号，导致每次都提示更新。

**解决方案：** 确保 install.py 在 VERSION 文件创建失败时抛出异常（已修复）。

### 陷阱 2：在错误的目录执行 install.py

**问题：** 在非扩展仓库目录执行 install.py。

**后果：** `git describe` 无法获取版本号，VERSION 文件中的版本可能不正确。

**解决方案：** 始终在扩展仓库目录执行 install.py：

```python
subprocess.run(
    ["python", "install.py", ...],
    cwd="/path/to/cc-pushover-hook",  # 关键！
    ...
)
```

### 陷阱 3：VERSION 文件格式解析错误

**问题：** VERSION 文件包含多行，解析时没有正确处理。

**后果：** 读取到错误的版本号或 `None`。

**解决方案：** 使用正则表达式精确匹配 `version=` 行：

```python
match = re.search(r'^version=(.+)$', content, re.MULTILINE)
if match:
    version = match.group(1).strip()
```

### 陷阱 4：工作目录环境变量问题

**问题：** install.py 依赖 `self.script_dir` 来执行 git 命令。

**后果：** 如果 `script_dir` 不正确，git 命令会失败。

**解决方案：** 确保 `__file__` 路径解析正确：

```python
# install.py 中的实现
self.script_dir = Path(__file__).parent.resolve()
```

### 陷阱 5：非交互模式下未解析 JSON 输出

**问题：** 使用了 `--non-interactive` 但未解析 JSON 输出。

**后果：** 无法正确判断安装是否成功。

**解决方案：** 始终解析 JSON 输出并检查 `status` 字段。

---

## 完整集成示例

### Go 语言集成（ai-commit-hub 风格）

```go
package pushover

import (
    "encoding/json"
    "fmt"
    "os"
    "os/exec"
    "path/filepath"
    "regexp"
    "strings"
)

// InstallResult 安装结果
type InstallResult struct {
    Success  bool   `json:"success"`
    Status   string `json:"status"`
    Message  string `json:"message,omitempty"`
    HookPath string `json:"hook_path,omitempty"`
    Version  string `json:"version,omitempty"`
}

// Installer 负责安装和更新 hook
type Installer struct {
    extensionDir string
}

func NewInstaller(extensionDir string) *Installer {
    return &Installer{extensionDir: extensionDir}
}

// Install 安装 hook 到项目
func (i *Installer) Install(projectPath string, force bool) (*InstallResult, error) {
    args := []string{
        "install.py",
        "--target-dir", projectPath,
        "--non-interactive",
        "--skip-diagnostics",
    }

    if force {
        args = append(args, "--force")
    }

    cmd := exec.Command("python", args...)
    cmd.Dir = i.extensionDir // 关键：在扩展目录执行

    output, err := cmd.CombinedOutput()
    if err != nil {
        return nil, fmt.Errorf("install failed: %w\nOutput: %s", err, string(output))
    }

    var result InstallResult
    if err := json.Unmarshal(output, &result); err != nil {
        return nil, fmt.Errorf("invalid JSON output: %w", err)
    }

    if result.Status != "success" {
        return &result, fmt.Errorf("install failed: %s", result.Message)
    }

    return &result, nil
}

// GetInstalledVersion 获取项目已安装的版本
func (i *Installer) GetInstalledVersion(projectPath string) (string, error) {
    versionFile := filepath.Join(projectPath, ".claude", "hooks", "pushover-hook", "VERSION")

    data, err := os.ReadFile(versionFile)
    if err != nil {
        return "", fmt.Errorf("VERSION file not found: %w", err)
    }

    re := regexp.MustCompile(`^version=(.+)$`)
    lines := strings.Split(string(data), "\n")
    for _, line := range lines {
        line = strings.TrimSpace(line)
        if matches := re.FindStringSubmatch(line); len(matches) > 1 {
            return strings.TrimSpace(matches[1]), nil
        }
    }

    return "", fmt.Errorf("version not found in VERSION file")
}

// GetExtensionVersion 获取扩展仓库的版本
func (i *Installer) GetExtensionVersion() (string, error) {
    cmd := exec.Command("git", "describe", "--tags", "--always")
    cmd.Dir = i.extensionDir

    output, err := cmd.Output()
    if err != nil {
        return "", fmt.Errorf("git describe failed: %w", err)
    }

    return strings.TrimSpace(string(output)), nil
}

// CheckUpdateNeeded 检查是否需要更新
func (i *Installer) CheckUpdateNeeded(projectPath string) (bool, string, string, error) {
    localVersion, _ := i.GetInstalledVersion(projectPath)
    if localVersion == "" {
        return true, "", "", nil // 未安装
    }

    remoteVersion, err := i.GetExtensionVersion()
    if err != nil {
        return false, localVersion, "", err
    }

    needsUpdate := localVersion != remoteVersion
    return needsUpdate, localVersion, remoteVersion, nil
}
```

### Python 语言集成

```python
import subprocess
import json
import re
from pathlib import Path
from typing import Optional, Tuple

class PushoverHookInstaller:
    """Pushover Hook 安装管理器"""

    def __init__(self, extension_dir: str):
        self.extension_dir = Path(extension_dir)

    def install(self, project_path: str, force: bool = False) -> dict:
        """安装 hook 到项目"""
        cmd = [
            "python",
            "install.py",
            "--target-dir", project_path,
            "--non-interactive",
            "--skip-diagnostics"
        ]

        if force:
            cmd.append("--force")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(self.extension_dir)  # 关键：在扩展目录执行
        )

        if result.returncode != 0:
            return {
                "success": False,
                "error": result.stderr,
                "stdout": result.stdout
            }

        try:
            output = json.loads(result.stdout)
            return output
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"Invalid JSON: {e}",
                "stdout": result.stdout
            }

    def get_installed_version(self, project_path: str) -> Optional[str]:
        """读取项目已安装的版本"""
        version_file = Path(project_path) / ".claude" / "hooks" / "pushover-hook" / "VERSION"

        if not version_file.exists():
            return None

        content = version_file.read_text(encoding='utf-8')
        match = re.search(r'^version=(.+)$', content, re.MULTILINE)

        if match:
            return match.group(1).strip()

        return None

    def get_extension_version(self) -> Optional[str]:
        """获取扩展仓库的版本"""
        result = subprocess.run(
            ["git", "describe", "--tags", "--always"],
            capture_output=True,
            text=True,
            cwd=str(self.extension_dir)
        )

        if result.returncode == 0:
            return result.stdout.strip()

        return None

    def check_update_needed(self, project_path: str) -> Tuple[bool, str, str]:
        """检查是否需要更新"""
        local_version = self.get_installed_version(project_path)
        remote_version = self.get_extension_version()

        if local_version is None:
            return True, "", remote_version or ""

        if remote_version is None:
            return False, local_version, ""

        return (local_version != remote_version), local_version, remote_version
```

---

## 测试清单

集成完成后，请验证以下场景：

- [ ] 全新安装项目 hook
- [ ] 更新已安装的 hook
- [ ] VERSION 文件正确创建
- [ ] 版本号与扩展仓库一致
- [ ] 安装失败时正确返回错误
- [ ] 非交互模式输出正确 JSON
- [ ] 旧版本迁移到新版本
- [ ] 版本比较逻辑正确

---

## 联系方式

如有集成问题，请：
1. 查看本文档的常见陷阱部分
2. 运行诊断脚本：`python .claude/hooks/pushover-hook/diagnose.py`
3. 提交 Issue 到：https://github.com/allanpk716/cc-pushover-hook/issues
