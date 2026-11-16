# 维护个人 pstack fork

本仓库记录个人定制，并保留与 `backnotprop/pstack` 的 Git 历史。原始来源是 `cursor/plugins` 中的 pstack；本地使用独立镜像提供的跨宿主适配。

## 在 custom 分支维护定制

- `custom` 是本 fork 的默认分支，记录已批准的本地定制。
- 初始基线是当前已安装的 `f905b88ebdd877e6b36fcc791970d47f44d15a15`，本次不顺带升级技能。
- `origin` 指向 `cbingb666/pstack`，`upstream` 指向 `backnotprop/pstack`。
- `main` 保留 fork 创建时的镜像版本。原镜像中的 `upstream` 分支与本地的 `upstream` 远程不是同一概念，参见 [镜像同步说明](MIRROR.md)。

首项定制是体验原则。提示文案也必须证明其必要性；用户能够通过低风险探索理解的交互，默认不增加操作提示。

## 将已批准的技能修改提交到 Git

技能继续在 `~/.agents/skills/<技能名>/` 中维护和加载。Git 工作副本位于 `~/code/pstack`。以下只读命令直接查看安装文件相对于当前 Git 提交的差异，无需先复制文件：

```bash
git --git-dir="$HOME/code/pstack/.git" --work-tree="$HOME/.agents" diff -- skills
```

确认需要保存的修改后，将对应技能同步到工作副本，检查差异后提交。例如：

```bash
cd ~/code/pstack
git switch custom
diff -ru skills/principle-experience-first ~/.agents/skills/principle-experience-first
cp -a ~/.agents/skills/principle-experience-first/. skills/principle-experience-first/
git diff --check
git diff -- skills/principle-experience-first
git add skills/principle-experience-first
git commit -m "Describe the approved skill change"
git push origin custom
```

`diff` 发现差异时返回非零状态，这是预期结果。删除文件需要同时在工作副本中明确执行 `git rm`，复制命令不会删除文件。

只同步正在修改的技能。不要复制整个 `~/.agents/`。全局用户指令、模型角色配置、安装锁文件和其他来源的技能不属于这个公共 fork。

## 从 fork 安装

```bash
npx skills add cbingb666/pstack
```

在安装器中选择全局安装和所需技能。安装前先提交未保存的本地定制，避免安装覆盖编辑。安装后核对实际的 `~/.agents/skills/<技能名>/SKILL.md`。

## 单独审阅上游升级

```bash
cd ~/code/pstack
git switch custom
git fetch upstream
git log --oneline HEAD..upstream/main
git diff HEAD...upstream/main
```

确认接受上游的行为变化后，再执行：

```bash
git merge upstream/main
```

解决冲突时保留仍然适用的个人定制，检查受影响的技能及其检查项。随后提交、推送并重新安装本 fork。

不要将上游文件直接覆盖到 `custom`。使用普通合并保留来源和定制历史，不向上游推送个人修改，也不使用强制推送覆盖本 fork 的历史。
