# Changelog

## [Unreleased]

### Added
- **智能安装系统**：自动检测并选择最佳安装模式
  - 全新安装（Fresh Install）
  - 从旧版本迁移（Migration）
  - 备份并升级（Backup & Upgrade）
  - 智能配置合并（Smart Merge）
- **安装状态检测**：自动识别现有安装类型和版本
- **VERSION 文件**：记录版本号、安装时间和 Git commit
- **配置备份**：每次升级自动备份 settings.json
- **自动清理旧文件**：安装时自动删除旧版本的文件
- **环境检测增强**：检测 Python、BurntToast 和 Pushover 配置
- **升级路径**：支持从扁平结构迁移到子目录结构
- **命令行参数增强**：
  - `--timeout`: 自定义 hook 执行超时时间
  - `--non-interactive`: 非交互模式，适合自动化
  - `--skip-diagnostics`: 跳过安装后诊断
  - `--quiet`: 静默模式，减少输出
- **版本管理**：使用 git tags/describe 动态获取版本号
- **配置合并优化**：智能识别并替换旧 pushover hook，保留其他 hook
- 并行发送通知：Windows 本地通知立即显示，不等待 Pushover API 响应

### Changed
- Hook scripts now located in `.claude/hooks/pushover-hook/` subdirectory for better isolation
- **重构安装流程**：模块化安装动作，支持多种安装场景
- **智能路径配置**：使用 `CLAUDE_PROJECT_DIR` 环境变量实现可移植路径
- **安装脚本文档**：更新模块文档字符串，反映新的智能安装功能
- Updated `install.py` to create `pushover-hook/` subdirectory during installation
- **Installation now automatically cleans up old script files from previous versions**
- All documentation updated with new paths
- `send_notifications` 函数使用 `ThreadPoolExecutor` 并行执行

### Fixed
- 修复 Windows 路径处理问题
- 修复配置合并时的重复 hook 问题
- 修复 datetime.utcnow() 弃用警告（建议）

### Migration Notes
If you have an existing installation:
1. **推荐方式**：运行新的 `install.py` 脚本
   - 脚本会**自动检测**你的安装类型
   - **自动迁移**配置到新结构
   - **自动备份**现有配置
   - **自动清理**旧文件
2. **手动方式**（不推荐）：
   - 手动移动文件从 `.claude/hooks/` 到 `.claude/hooks/pushover-hook/`
   - 更新 `settings.json` 中的路径
3. **回滚**：如果出现问题，可以使用自动生成的备份文件 `settings.json.backup_YYYYMMDD_HHMMSS`
