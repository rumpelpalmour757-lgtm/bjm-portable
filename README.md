# BJM 通用迁移包 v1.4.1

从本目录的 `SKILL.md` 开始。这个文件可以单独给 AI 用。把整个 `bjm-portable/` 目录带到新项目时，就可以查阅完整协议和使用可选脚本。

| 包内入口 | 什么时候用 |
|---|---|
| [SKILL.md](SKILL.md) | 日常任务。明确交付，做一次核对，再交结果 |
| [BJM v3.2 完整协议](references/bjm-v3.2.md) | 需要详细规则时查阅。§5 是验收，§9.7 是恢复，§11 是 AI 协作宪法，附录 A 是速查 |
| [领域方法](references/methods.md) | 软件、创作、研究、文档、数据、运营和自定义领域 |
| [脚本说明](references/runtime.md) | 需要检查证据、版本、返修次数或恢复状态时 |
| [图执行器 v0.1](graph-runtime/README.md) | 需要实际调度并行节点、保存执行状态和审批记录时 |

## 开始一个任务

把任务和 `SKILL.md` 放在一起即可。可以用下面的短句开场。

```text
用 BJM 帮我完成［交付物］。
以［当前资料］为准。［允许改动］，保留［不可改动］。
交付前核对［必要条件］。
```

材料和要求明确时，一句话也够用。复杂任务才保存检查点。Agent Skills 工程模块已经随包提供，由 BJM 按当前任务选用。项目的资料、角色、标准和权限由使用者在目标项目中提供。

## 可选的本地核验

从本目录运行。系统使用 `python3` 时，可以把 `python` 换成 `python3`。脚本只依赖 Python 标准库。

```bash
python scripts/workflow.py route --intent format --domain documents
python scripts/workflow.py evaluate examples/checkpoint.json
python -m unittest discover -s tests -v
```

示例会给出 `RECHECK`。来源换版后，需要重做保真审查，仍然有效的格式检查保留。真实任务按实际执行结果填证据。

## 可选的图执行器

从本目录运行 `python3 -B graph-runtime/demo.py`，可以试跑两章模拟联审。示例包括并行分支、单章超时后补跑、改稿使旧审批失效，以及 SQLite 保存的执行事件。完整用法见[图执行器说明](graph-runtime/README.md)。

BJM 的 `scripts/workflow.py` 继续负责判断提交的证据和验收状态。图执行器负责节点调度和检查点，两者可按任务分别运行。演示使用本地模拟生成与审查，实际模型接入需提供相应适配器。

## 包内组件

见[版本记录](CHANGELOG.md)。

- BJM 完整协议和 AI 协作宪法见 `references/bjm-v3.2.md`，通用入口为 `SKILL.md`。
- Agent Skills 的 25 个模块、共享资料、脚本和许可证见 `vendor/agent-skills-0.6.16/`。从[领域方法](references/methods.md)可直接打开对应模块。
- `vendor/agent-skills-0.6.16.zip` 是原始 ZIP，原样保留。展开目录保留全部普通文件，原包自带的一个符号链接保留在原始 ZIP 中。

- 图执行器 v0.1 的源码、中文说明和测试在 `graph-runtime/`，从本目录运行 `python3 -B -m unittest discover -s graph-runtime/tests -v` 可复核。

整个目录可以独立迁移。自动发现技能或执行上游脚本时，按实际宿主配置和任务授权处理。

## 获取和许可

- 克隆本仓库，或者从 [Releases](https://github.com/rumpelpalmour757-lgtm/bjm-portable/releases) 下载 `bjm-portable-<版本>.zip`；解压出来的 `bjm-portable/` 就是这个目录。
- 本仓库按 MIT 许可发布，版权人 Celeste，全文见 [LICENSE](LICENSE)。附带的 Agent Skills 按它自己的 MIT 许可（Copyright (c) 2025 Addy Osmani），见 [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md)。
