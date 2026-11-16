# 维护个人 pstack fork

所有 pstack 定制先在 `cbingb666/pstack` 的 `custom` 分支修改、提交并推送，再用 `npx skills` 重装。完整维护规则保存在 [.agents/AGENTS.md](.agents/AGENTS.md)，根 `AGENTS.md` 是它的符号链接。

## 区分源码与安装产物

- `~/code/pstack/skills/` 是唯一维护源。
- `~/.agents/skills/` 是 Codex 的全局安装目录，不直接修改。
- 安装锁由安装器更新，不手动编辑来源记录来替代安装。
- 用户指令、模型角色配置和其他来源的技能不放进这个公共 fork。

## 修改、提交、推送后重装

以修改体验原则为例：

```bash
cd ~/code/pstack
git switch custom
git status --short
```

修改 `skills/principle-experience-first/SKILL.md`，检查内容和差异。涉及脚本行为时，运行对应测试。维护安装流程本身的测试为：

```bash
python3 -m unittest discover -s scripts -p 'test_*.py'
```

审阅完成后，只提交本次修改：

```bash
git diff --check
git diff -- skills/principle-experience-first
git add skills/principle-experience-first
git commit -m "Describe the approved skill change"
git push origin custom
python3 scripts/reinstall_skills.py principle-experience-first
```

多个技能名用空格分隔；省略名称会重装本仓库全部顶层技能。`--check` 只检查前置条件，不执行安装。

脚本会拒绝未提交、未推送、分支错误或安装目录存在未保存编辑的状态。它实际调用 `npx skills`，用已推送提交号的 GitHub 地址安装到 Codex 全局目录，再核对文件清单、内容和安装记录。成功结果包含提交号、技能名、文件数和实际安装日志路径。

不要用复制源码或手工修改锁文件绕过脚本。遇到安装目录已有编辑时，先审阅差异，将确认要保留的修改应用到 fork，再执行正常流程。

## 单独审阅上游升级

`origin` 指向本 fork，`upstream` 指向 `backnotprop/pstack`。原始来源是 `cursor/plugins` 中的 pstack；本 fork 保留独立镜像提供的跨宿主适配和 Git 历史。

```bash
git fetch upstream
git log --oneline HEAD..upstream/main
git diff HEAD...upstream/main
```

接受上游行为变化后，在 `custom` 合并 `upstream/main`，解决冲突并执行相关检查。随后提交、推送，再运行同一个重装脚本。不直接覆盖文件，不强制推送，也不顺带升级未审阅的上游提交。
