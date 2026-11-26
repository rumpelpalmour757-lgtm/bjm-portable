# 版本记录

日期按台北时间（UTC+8）记。

## v1.10.1

2026-11-26。在本仓库 v1.9.1 上合入作者交来的 v1.10 新加的 `run --claude-workers`，再按复核改了几处；在本仓库里，上一版是 v1.9.1。v1.10 是作者在本仓库 v1.9.1 的发布包上做的，基线和本仓库一致，只改了 7 个文件。这一版改过它的代码、测试和说明，照本仓库的习惯（作者交来的版本在仓库里改过的，版本号加 .1）不叫 v1.10，记作 v1.10.1。协议、`SKILL.md`、`scripts/`、`tests/`、`vendor/`、检查点格式和图执行器的数据库结构与 v1.9.1 相同。

- 合并：v1.10 相对 v1.9.1 的发布包改了 `CHANGELOG.md`、`README.md`、`graph-runtime/README.md`、`graph-runtime/engine.py`、`graph-runtime/workflow.py`、`graph-runtime/tests/test_claude_cli.py` 和 `graph-runtime/tests/test_scheduling.py`，其余 284 个文件和本仓库 v1.9.1 逐字节相同。`engine.py`、`workflow.py` 的改动和两项新测试取 v1.10 的，再按下面几条改。三份说明以仓库为底，v1.10 加的用法段落照代码重写。v1.10 把封面的下载按钮换成指向 v1.9.1 的文字链接，把“获取和许可”里的下载说明换成“本包是 v1.10……”，这是站在包的角度写的，没有取，仍用仓库原来的按钮和说明，只改版本。v1.10 自带的版本记录原文照录在下面。
- `--claude-workers`（来自 v1.10）：`run` 新加可选的 `--claude-workers N`，同时最多跑 N 个 Claude Code 审查节点（`operation` 为 `claude-review` 的任务节点），仍算在 `--workers` 的总数里。到了上限，其余审查节点留在 `PENDING`，尝试次数不加，不算指纹，也不写事件；不依赖它们的本地节点照常用剩下的槽位。一个审查结束，不论成功、失败、待核还是被拒，就空出一个名额。不加这个选项时只按 `--workers` 算，和 v1.9.1 相同。上限只管这一次 `run`，不存进数据库。代码上是 `engine.py` 的 `run()` 多了只能按名字传的 `worker_limits`，按节点的 `inputs.operation` 计数，审批节点不受影响；命令行只拿它限 `claude-review`。照 v1.10 的版本记录，这个选项参考了 Google ADK v2.15.0 给 `LlmAgent` 加的 `max_parallel_workers`（转交给 ADK 原有的并行工作节点；[提交 5e4f0e1](https://github.com/google/adk-python/commit/5e4f0e18cfe869a183901192f92c86d7574881b0)）：ADK 限的是一个并行工作节点同时处理几条输入，这里限的是整次运行里同一种操作的节点数，代码按 BJM 的调度器另写。
- 按复核改的地方：
  - 报错写明参数名：`--claude-workers 0` 或负数，v1.10 报的是引擎里的 `operation worker limits must be positive integers`，命令行用户看不出说的是哪个参数。现在 `workflow.py` 调引擎以前先查，报 `--claude-workers must be a positive integer`，退出码仍是 2，库里什么也不写。引擎那道检查保留，`worker_limits` 不是映射时也报同一句错：v1.10 遇到字符串或整数，报的是和上限无关的 `dictionary update sequence…` 或 `TypeError`，遇到键值对的列表则当成映射收下，现在一律拒绝。命令行总是传映射，碰不到这一处。
  - 写明这个选项什么时候不起作用：不加 `--claude` 时也接受它，但它不起作用，这次能轮到审查节点时照旧报错要求加 `--claude`；比 `--workers` 大时，实际并发仍不超过 `--workers`。这两处只写进说明，代码没有改成报错。调度进程被强行结束以后，它启动的 Claude Code 进程还可能在跑，这些进程不算进下一次 `run` 的上限：用 SIGKILL 杀掉上限为 1 的调度进程，马上用上限 1 续跑，同时有两个模拟的 `claude` 进程。说明里写明要先确认上次的调用已经结束，再续跑。
  - 图执行器改称 v0.1.7。v1.10 包里的图执行器是 v0.1.6，是本仓库 v1.9.1 的 v0.1.5 加上 `--claude-workers`；这一版改了它的两处输入检查（见上面“报错写明参数名”一条），照 v1.8.1 和 v1.9.1 的做法不再沿用同一个版本号。调度的代码和 v1.10 包里的相同。下面 v1.10 一节原文里的“图执行器 v0.1.6”指 v1.10 包里的那一版。
  - 测试：v1.10 的命令行测试断言 `review-a` 跑完以后 `review-b` 才开跑，这依赖两份初稿谁先完成。初稿 b 先完成时上限照样守住，这条断言却失败，给初稿 a 加 0.5 秒延迟就能复现。现在按两个审查实际开跑的先后比较，并核对非法取值前后状态和事件都不变；这项测试在文件里从辅助方法中间挪到了末尾。调度测试里等本地任务的时限从 5 秒放宽到 30 秒。另加三项：受限的审查失败、待核或被拒以后照样空出名额，四个审查依次以失败、待核、被拒、成功收场，尝试次数都是 1，同时在跑的始终只有 1 个；`--workers` 和审查上限同时顶到时，按事件算，同时在跑的任务最多 2 个、审查最多 1 个；`worker_limits` 取值不对（0、负数、`True`、小数、不是字符串的键、字符串、整数、键值对列表）时，在碰库以前报错。复核时试出两种错误改法，v1.10 的 35 项都看不出：只在成功时放回名额（第一个审查失败以后，其余审查一直停在 `PENDING`，`run` 照样以 0 退出）；去掉 `--workers` 的总数检查（v1.9.1 的 33 项也看不出，标成 `RUNNING` 的节点会多于线程池实际能跑的数）。现在每一种都有测试失败。
  - 说明文字：`graph-runtime/README.md` 里，v1.10 删掉了“在哪些环境验证过、Windows 和 macOS 没有实测”一句，现在按这次实测补回；新加的用法一段挪到示例说明后面，单成一段，写明 N 须是正整数、上限不入库、什么时候不起作用、被强行结束以后怎样续跑；设计参考里 ADK 一条，v1.10 写的是把 ADK 的做法用在审查上（版本记录里写“采用”），两者机制不同，改成“参考”，写清差别，链接换成用 git 核到了的那个提交，v1.10 链的 v2.15.0 发布页这次打不开，没有放进说明。`README.md` 的版本、下载按钮指向的版本、测试数、入口表和包内组件里图执行器的版本、“可选的图执行器”里的用法一段、测试说明和署名改成这一版的；v1.10 在测试说明里去掉的“Python 3.10、Windows 和 macOS 没有实测”和“测试时命令搜索路径里只有模拟程序”两句保留；令牌一句里的“演示这次在 Python 3.13 上连续跑了 30 次”，v1.10 改成了说 v1.9.1 的演示，这一版重新跑了 30 次，仍写“这次”。`THIRD-PARTY-NOTICES.md` 写明 Google ADK 只作参考。新加 `docs/releases/v1.10.1.md`。
- 测试：`tests/` 下 53 项（BJM 36 项、匿名对照材料 12 项、收票 5 项），`graph-runtime/tests/` 下 38 项（v1.9.1 的 33 项、v1.10 的 2 项、这一版新加的 3 项）。在 Linux 上用 Python 3.11、3.12、3.13 跑：`tests/` 各跑一遍，`graph-runtime/tests/` 各连跑五遍，都通过，没有跳过的项；演示在三个版本上各跑一遍，再在 3.13 上连续跑 30 次，都通过。跑的时候命令搜索路径上找不到真的 `claude`。其余实测见 `docs/releases/v1.10.1.md`。
- 回退和兼容：图执行器的数据库结构没有变，`user_version` 仍是 1；上限不存进库里，`STARTED` 事件记的字段和 v1.9.1 一样，只有 `attempt` 和 `fingerprint`。v1.9.1 不认 `--claude-workers`，报用法错误，退出码 2，其余命令照旧能用。用同一个库在 v1.9.1 和 v1.10.1 之间交替运行（图里有两份初稿、三个审查、一个本地任务、一个审批和审批后的一个任务，Claude Code 用测试里的模拟程序）：v1.9.1 跑出一个失败的审查，v1.10.1 `retry` 它再带上限 1 运行，只补跑这一支，另两个审查沿用原结果；v1.9.1 再跑，状态不变，用 v1.10.1 发的令牌批准成功，v1.10.1 跑完下游。v1.10.1 带上限 1 运行到第一个审查时被 SIGKILL 杀掉，另两个审查这时仍是 `PENDING`、尝试次数 0；v1.9.1 续跑，被中断的那个审查（设了 `retry_on_interrupt: false`）进入 `UNCERTAIN`，另两个照常跑完；`retry` 以后 v1.10.1 补跑并发出令牌，v1.9.1 用它退回；v1.10.1 再跑，状态不变，用被退回的令牌批准被拒，改稿后只重跑那一章和它的审查，发出新令牌；v1.9.1 用新令牌批准，跑完下游。带上限被杀以后，不加 `--claude-workers` 续跑，两个审查同时开跑，说明上限确实没有存下来。不加 `--claude-workers` 时，同一串命令（`--workers 1`）在 v1.9.1 和 v1.10.1 上写出的事件逐条相同，命令结果只有随机令牌不同。
- 没有验证的：真实的 Claude Code 调用，只用了模拟程序，`--claude-workers` 对实际计费和速率限制有多大帮助也没有测；按 Ctrl-C 中断时会不会留下还在跑的 Claude Code 进程，只试了 SIGKILL；Windows、macOS，Python 3.9 和 3.10；v1.10 引的别的项目的发布页，网页这次打不开，只用 git 核了标签、提交和日期，见下面的加注。

下面 v1.10 一节是作者交来的 v1.10 包自带的版本记录，原文照录。v1.10 没有单独发布到本仓库；本仓库从 v1.9.1 直接到 v1.10.1。

## v1.10

2026-11-21。基于作者仓库的 [v1.9.1 通用发布包](https://github.com/rumpelpalmour757-lgtm/bjm-portable/releases/tag/v1.9.1)（2026-11-20，包 SHA-256 `5e620cc00f29066c7700a817c58fe16a89b5069e904caad0ff785469fc10a7d3`）。含 BJM v3.2、Agent Skills 0.6.17 和图执行器 v0.1.6。基线已包含按内容记退回及按节点就绪情况预检的修正。

- 参考 [Google ADK v2.15.0](https://github.com/google/adk-python/releases/tag/v2.15.0)（2026-11-20 台北时间，[并行代理工作限额的提交](https://github.com/google/adk-python/commit/5e4f0e18cfe869a183901192f92c86d7574881b0)），为 `run --claude` 加入可选的 `--claude-workers`。达到审查上限后，排队的审查继续待执行，独立本地任务可用剩余总槽位。运行时限额不写进数据库。
- 相同的三路审查加一路本地任务，使用三个总槽位。基线最多同时派出三路审查。设定上限为一后，最多同时派出一路审查，本地任务在首路审查结束前运行。其余两路当时仍待执行，尝试次数为零。
- 核对 [Agent Skills 0.6.17 正式版](https://github.com/addyosmani/agent-skills/releases/tag/0.6.17)（2026-11-19）和达尔文 [v3.0.2 正式版](https://github.com/alchaincyf/darwin-skill/releases/tag/v3.0.2)（2026-11-18，[提交 5a8e633a20ea5bb2bf8b9c697c6da04ad85740ba](https://github.com/alchaincyf/darwin-skill/commit/5a8e633a20ea5bb2bf8b9c697c6da04ad85740ba)）。Agent Skills 的 26 个模块、原包与许可承接基线。达尔文的采用记录见 v1.7。
- 同期查阅 [LangGraph 1.2.24](https://github.com/langchain-ai/langgraph/releases/tag/1.2.24)（2026-11-20）的消息累积和恢复修复、[Temporal 合作生态公告](https://temporal.io/blog/temporal-ai-partner-ecosystem)（2026-11-19）和 [OpenAI Agents SDK v0.25.0](https://github.com/openai/openai-agents-python/releases/tag/v0.25.0)（2026-11-18）。本轮的图执行器改动采用 ADK 的并行限额做法。
- 从最终 ZIP 解压后，在 Linux 的 Python 3.12 和 3.13 上各通过 53 项 BJM 测试、35 项图执行器测试和联审演示。用同一 SQLite 文件在 v1.9.1 和 v1.10 间交替运行，核对失败分支重试、已完成分支复用和审批续跑。Claude Code 使用本地模拟程序。真实模型调用及模型质量待验证。

以上 v1.10 一节对照本仓库的版本线，补充几点（v1.10.1 加注）：

- “2026-11-21”是 v1.10 自己记的日期。“作者仓库的 v1.9.1 通用发布包”就是本仓库 v1.9.1 的发布包 `bjm-portable-v1.9.1.zip`：复核时从发布页取到这个附件，算出的 SHA-256 和这里写的相同；用发布工作流同一条 `git archive` 命令打本仓库 v1.9.1 的提交 5715aa1，结果也相同。“基线已包含按内容记退回及按节点就绪情况预检的修正”说的是 v1.9.1 的退回按内容记、预检只看这次能轮到的节点，v1.10 没有改这两处。
- “图执行器 v0.1.6”指 v1.10 包里的那一版，是本仓库 v1.9.1 的 v0.1.5 加上 `--claude-workers`；本仓库又改了两处输入检查，叫 v0.1.7，见上面 v1.10.1 一节。
- 第一条的 Google ADK：复核时用 git 核到了 v2.15.0 标签（指向提交 802db43，提交时间 2026-11-19 22:54 UTC，即台北时间 2026-11-20 06:54，和这里的日期对得上）和提交 5e4f0e1（说明是“feat: support bounded parallel agent workers”，在 v2.15.0 的历史里）；发布页和提交的网页这次都打不开，发布时刻没有核到。那个提交给 `LlmAgent` 加的 `max_parallel_workers` 限的是一个并行工作节点同时处理几条输入，ADK 的说明写明它不管整个工作流；`--claude-workers` 限的是整次运行里所有 Claude Code 审查节点，机制不同，所以第四条说的“采用 ADK 的并行限额做法”，本仓库写成“参考”。
- 第二条说的是 `test_scheduling.py` 新加的那一项测试，和测试对得上。“基线最多同时派出三路审查”不是这项测试测的（v1.9.1 没有 `worker_limits`），复核时另用脚本在 v1.9.1 的代码上跑过，属实。
- 第三条、第四条：复核时用 git 核到了 Agent Skills 0.6.17、达尔文 v3.0.2（提交 5a8e633a…）、LangGraph 1.2.24 和 OpenAI Agents SDK v0.25.0 的标签和日期，和这里写的对得上；Temporal 那篇文章复核时取到了网页，页面上记的发布日期是 2026-11-19，没有带时区。GitHub 上的几个发布页都没打开，“正式版”没有核到。这一版没有据这几样改动，`vendor/` 没有变。
- 第五条：“53 项 BJM 测试”指 `tests/` 下全部 53 项，其中 BJM 36 项、匿名对照材料 12 项、收票 5 项。“从最终 ZIP 解压后”通过的测试和“在 v1.9.1 和 v1.10 间交替运行”是 v1.10 自己记的；本仓库这次的测试和交替运行见上面 v1.10.1 一节和 `docs/releases/v1.10.1.md`。

## v1.9.1

2026-11-20。在本仓库 v1.8.1 上合入作者交来的 v1.9 新加的两样：图执行器退回审批的 `reject` 和 Agent Skills 0.6.17，再按复核改了几处；在本仓库里，上一版是 v1.8.1。v1.9 是作者在自己的 v1.8 上做的，不含本仓库 v1.8.1 的修改，所以这一版以 v1.8.1 为底，只把 v1.9 相对 v1.8 的改动移过来，版本号接着本仓库的 v1.8.1 记作 v1.9.1。协议的规则、`SKILL.md`、`scripts/`、`tests/`、检查点格式和图执行器的数据库结构与 v1.8.1 相同；协议只改了附录 C“改编依据”里的一句说明。

- 合并：v1.9 相对 v1.8 改了 `CHANGELOG.md`、`README.md`、`graph-runtime/README.md`、`graph-runtime/engine.py`、`graph-runtime/workflow.py`、`graph-runtime/tests/test_cli.py` 和 `references/methods.md`，并把 `vendor/` 换成 Agent Skills 0.6.17。`engine.py` 和 `workflow.py` 里的 `reject`、`test_cli.py` 里的两项新测试移到本仓库的图执行器上，v1.8.1 对 `retry`、`init`、`run` 的修正都保留；两边改的地方不重叠，三方合并没有文本冲突。`graph-runtime/README.md` 以仓库为底，接上 v1.9 的“退回当前版本”一节、联审表里的一行和设计参考里的一条，再按下面几条改。`references/methods.md` 取 v1.9 的，它等于把仓库版里的 0.6.16 全部换成 0.6.17，再在“设计、实现或检查界面”下面加一行无障碍审查。`README.md` 和本文件以仓库为底：v1.9 的 `README.md` 是作者那条线上的短版本，只改了版本号和组件说明；这一版照实改了封面的版本、模块数和测试数徽章、下载按钮、两处介绍里的模块数（第一处的覆盖范围加了无障碍审查）、正文里的测试数、入口表、测试说明、令牌一句的版本（“本版起”改成“v1.8.1 起”）、“可选的图执行器”一段的 `reject` 和 `--claude` 规则、包内组件和署名。v1.9 自带的版本记录原文照录在下面。
- Agent Skills 0.6.17：删掉 `vendor/agent-skills-0.6.16/` 和 `vendor/agent-skills-0.6.16.zip`，换成 `vendor/agent-skills-0.6.17/` 和 `vendor/agent-skills-0.6.17.zip`。ZIP 取自作者的 v1.9 包，和 GitHub 上 0.6.17 标签的官方源码 ZIP 逐字节相同，SHA-256 为 `f2d2dfca1ed15b78364623c6d303c626a0518184136520644ec7b15d4ba3aeb0`，ZIP 注释记的提交是 `8c99fa36d90068c82d547f7c12a9d67a3e95f4ee`，ZIP 里记的时间是 2026-11-18 20:06:37（UTC），即台北时间 2026-11-19 04:06。发布页显示 0.6.17 指向提交 8c99fa3，标着最新版。和 0.6.16 比，模块从 25 个变成 26 个：新加 `accessibility-engineering`（审查现有界面的无障碍问题），`ci-cd-and-automation`、`code-review-and-quality`、`spec-driven-development`、`using-agent-skills` 四个模块的 `SKILL.md` 改过，没有删掉的模块；文件新增 10 个、改了 28 个、删除 0 个。`LICENSE` 和 0.6.16 的逐字节相同，仍是 MIT，版权行仍是 Copyright (c) 2025 Addy Osmani。
- 展开目录照 0.6.16 的规矩办：261 个普通文件和 ZIP 逐字节相同，原包的符号链接 `.opencode/skills` 只留在 ZIP 里；ZIP 里标成可执行的 9 个 shell 脚本保留可执行位（v1.9 包里这 9 个都记成了不可执行），比 0.6.16 多的一个是新模块的 `skills/accessibility-engineering/scripts/audit-a11y.sh`。这个脚本会用 `npx --yes` 从网上取 `@axe-core/cli@4.13.0` 和 `pa11y@9.1.1` 并执行；这次只读过，`vendor/` 下的脚本一律没有运行。
- 跟着 0.6.17 改的说明：`README.md` 的模块数和路径、`references/methods.md` 的模块表、`THIRD-PARTY-NOTICES.md` 的版本、三处路径、SHA-256、提交和可执行脚本的数目。`references/bjm-v3.2.md` 附录 C“改编依据”那句说明改成 0.6.17：表里引的 12 个上游路径在 0.6.17 里都还在，0.6.17 又改了其中 4 个（`using-agent-skills`、`spec-driven-development`、`code-review-and-quality` 三个模块的 `SKILL.md` 和 `evals/README.md`），协议正文没有据此改写；原句列了五个模块却写成“四个模块”，一并改正。旧版本各节和 `docs/releases/` 里写 0.6.16、25 个模块的地方是历史记录，没有改。
- 退回审批（来自 v1.9）：审批节点等待批准时，`reject <节点> -- <令牌>` 退回当前版本。节点记为 `REJECTED`，`error` 为 `ApprovalRejected`，令牌作废，写一条 `APPROVAL_REJECTED` 事件；依赖它的步骤一直等着，无关分支照常走；被退回的节点不接受 `approve`、`reject`、`retry` 和 `resolve`；改了上游稿件再 `run`，才发新令牌。`reject` 和 `approve` 用同一套核对。
- 按复核改的地方：
  - 退回按内容记：v1.9 只靠指纹认版本，而指纹里含修订号，所以把上游改成别的再改回原文，或者往上游加一个不影响输出的输入，都会对同一份、已经退回过的内容重新发令牌，`status` 里也看不出来。现在 `APPROVAL_REJECTED` 事件多记一项 `content_sha256`，是审批节点自己的 `inputs` 加各依赖输出的摘要，不含修订号；`run` 发令牌之前先和这个节点以前的退回对照，内容相同就保持 `REJECTED`、不发令牌，写一条 `REJECTION_KEPT` 事件，`error` 写明是在哪个修订号退回的。审阅者要重看同一份稿件时，改审批节点自己的 `inputs` 再 `run`，这会重开审批，`graph-runtime/README.md` 写明了这是有意留的做法。退回只在同一个运行里、同一个审批节点上对照；作者 v1.9 记下的退回没有 `content_sha256`，不参与对照。这种对照只在依赖节点的输出逐字节相同时起作用：审批排在 Claude Code 审查节点后面时（`examples/claude_review.json` 就是这样），上游一改，审查就重跑，每次的会话 ID 不同；排在另一个审批后面时，前一个审批的输出里有带修订号的指纹。这两种图里同一份稿件仍会再次送审，要靠审阅者自己核对，`graph-runtime/README.md` 写明了这一点；要在代码上解决，得为审查节点另定送审内容，留到以后。`approve` 在令牌核对通过以后也和以前的退回对照，内容相同就拒绝批准，库里什么也不写；只做 v1.9.1 的流程里不会遇到，因为发令牌前已经查过，这一道是给经过旧版本的库用的，见下面“回退和兼容”。
  - 批准和退回被拒时分开报错：节点已经批准、已经退回、还没发令牌或者不是审批节点时，报错写明是哪一种；只有令牌不对或过期，才报 `stale or invalid approval token`。退出码仍是 2，库里什么也不写。`approve` 也照这样报。
  - `run` 的预检分成两步。审查节点的声明照 v1.8.1 那样核对：所有还没跑的审查节点（`PENDING`，以及中断后能自动重跑的 `RUNNING`）都查，这次轮不到的也查，不合格就在任何分支开跑以前报错。要不要 `--claude`、找不找 `claude` 程序，只看这次能轮到的任务节点：排在等待批准或被退回的审批后面、或者排在停在 `FAILED`、`UNCERTAIN`、`REJECTED` 的节点后面的任务不算。以前 Claude Code 审查节点挂在被退回的审批后面时，不加 `--claude` 的 `run` 整体报错，无关分支也走不了；审批还在等待时也是这样，不是 v1.9 带来的。审查节点真的轮到时，仍要 `run --claude`。`workflow.py` 另加一道保险：没经过预检的审查节点不启动任何程序。
  - 图执行器改称 v0.1.5。v1.9 包把“v1.8 的 v0.1.3 加上 `reject`”叫作 v0.1.4，而本仓库 v1.8.1 已经把改了 `retry`、`init` 和 `run` 检查的那一版叫作 v0.1.4；这一版是两者合起来再加上面几处，不再沿用同一个版本号。下面 v1.9 一节原文里的“图执行器 v0.1.4”指 v1.9 包里的那一版。
  - 测试：v1.9 新加的两项移过来，令牌前一律加 `--`，和仓库其他测试一致；改数据库的连接用 `closing()` 关上，v1.9 的写法在 `python3 -X dev` 下报 `ResourceWarning: unclosed database`；退回事件的断言加上 `content_sha256`。另加八项：退回按内容记；几种拒绝各自的报错和事件不变；预检跳过这次轮不到的审查节点（审批在等待和被退回时都试）；退回只管做出退回的那个审批节点；新建的运行不沿用以前运行里的退回；`approve` 拒绝已经退回过的同一份内容；挂在审批后面、声明被改坏的审查节点在第一次 `run` 时就报错；中断后能自动重跑的审查节点仍要 `run --claude`，加了就真的调用。其中六项和改过断言的那一项，放在只做了三方合并、没按复核改的代码上跑都失败；另外两项（新建的运行、中断后的审查节点）在那份代码上本来就成立。复核时试出四种错误改法，原有的 28 项都看不出：查退回时不按运行过滤、不按节点过滤、预检漏掉中断后能自动重跑的节点、把等待批准的审批当成已经通过；现在每一种都有测试失败。
  - 说明文字：`graph-runtime/README.md` 的“退回当前版本”一节改写成第二条批准命令的另一种做法。v1.9 的写法接在已经用新令牌批准以后，照着做只会报令牌无效；现在还注明命令里的 `approve` 是演示图里审批节点的 ID。这一节另外写明了送审内容怎样算、哪些做法什么都不变、哪些会记 `REJECTION_KEPT`、审批排在审查节点或另一个审批后面时同一份稿件仍会再次送审、该改上游稿件而不是审批节点自己的 `inputs`、要重看同一份稿件怎么办、经过旧版本的库里的令牌怎样处理、图执行器不记退回理由。“看懂两章联审”表里输入被拒那一行写明是任务节点，`error` 以 `InputRejected` 开头，并注明 v1.8.1 以前的版本和作者的 v1.9 写的库里只有类名，没有冒号和原因；“接到实际任务时”里“命令沿用原版”的说法改成命令新增了 `reject`，并写明 `REJECTED` 有两种来源、按 `error` 区分。`THIRD-PARTY-NOTICES.md` 写明 OpenAI Agents SDK v0.25.0 和 Temporal OSCAR 只作参考。新加 `docs/releases/v1.9.1.md`。
- 测试：`tests/` 下 53 项（BJM 36 项、匿名对照材料 12 项、收票 5 项），`graph-runtime/tests/` 下 33 项（v1.8.1 的 23 项、v1.9 的 2 项、这一版新加的 8 项）。实测结果见 `docs/releases/v1.9.1.md`。
- 回退和兼容：图执行器的数据库结构没有变，`user_version` 仍是 1。v1.8.1 建的库交给 v1.9.1，能直接续跑，对 v1.8.1 发的令牌也能 `reject`，改稿后再批准、走完下游。v1.9.1 写了退回的库交给 v1.8.1：依赖被退回节点的步骤照样等着；`approve`、`retry`、`resolve` 都不接受；v1.8.1 没有 `reject` 命令，命令行报用法错误；v1.8.1 不看 `content_sha256` 和 `REJECTION_KEPT`，改了上游以后再 `run` 就发新令牌，内容和退回时相同也一样；v1.8.1 的说明把 `REJECTED` 只说成输入被拒、让人改这个节点的输入，对被退回的审批节点照做会把原稿重新送审，要改的是上游稿件。v1.8.1 这样对同一份内容发的令牌，库回到 v1.9.1 以后不能用来批准：`approve` 报这份内容在哪个修订号退回过，库里什么也不写，`reject` 照常可以用；在 v1.8.1 里已经批准了的，v1.9.1 不会改回去。作者的 v1.8 和 v1.9 也不按内容对照，经过它们的库回到 v1.9.1 时一样。作者 v1.9 的库交给 v1.9.1 也能续跑；v1.9.1 的库交给 v1.9，被退回的节点照样拦住下游。

下面 v1.9 一节是作者交来的 v1.9 包自带的版本记录，原文照录。v1.9 是在作者自己的 v1.8 上做的，没有单独发布到本仓库；本仓库从 v1.8.1 直接到 v1.9.1。

## v1.9

2026-11-20。基于 v1.8，组件为 BJM v3.2、Agent Skills 0.6.17 和图执行器 v0.1.4。

- 更新至 [Agent Skills 0.6.17 正式版](https://github.com/addyosmani/agent-skills/releases/tag/0.6.17)（2026-11-19 台北时间，[提交 8c99fa36d90068c82d547f7c12a9d67a3e95f4ee](https://github.com/addyosmani/agent-skills/commit/8c99fa36d90068c82d547f7c12a9d67a3e95f4ee)）。新增无障碍审查模块，更新 CI 回滚、代码审查、规格组织、模块索引和共享资料。26 个模块及 MIT 许可随包提供。官方标签源码 ZIP 的 SHA-256 为 `f2d2dfca1ed15b78364623c6d303c626a0518184136520644ec7b15d4ba3aeb0`。
- 图执行器新增 `reject`。拒绝绑定当前审批令牌、输入指纹和修订号，写入 SQLite 事件并拦住依赖节点。无关分支可继续。修订输入后生成新审批令牌。v1.8 遇到人工拒绝时只能继续等待或修改输入。参考 [OpenAI Agents SDK v0.25.0](https://github.com/openai/openai-agents-python/releases/tag/v0.25.0)和 [Temporal 的 OSCAR 案例](https://temporal.io/blog/building-a-reliable-ai-agent-with-oscar)，日期均为 2026-11-18。
- 查阅达尔文 [v3.0.2 正式版](https://github.com/alchaincyf/darwin-skill/releases/tag/v3.0.2)（2026-11-18，[提交 5a8e633a20ea5bb2bf8b9c697c6da04ad85740ba](https://github.com/alchaincyf/darwin-skill/commit/5a8e633a20ea5bb2bf8b9c697c6da04ad85740ba)，[MIT 许可](https://github.com/alchaincyf/darwin-skill/blob/v3.0.2/LICENSE)）。采用记录见 v1.7。该版按裁决影响选择重跑的做法依赖自动计票裁决，当前 BJM 继续使用人工采纳。
- 验收覆盖 46 项 BJM 测试、17 项图执行器测试、模拟联审、26 个上游模块原文和入口检查。v1.8 与 v1.9 可在同一 SQLite 文件续跑，回退后仍能拦住被拒稿的下游，修订后的有效令牌可批准。验证使用本地夹具和模拟 CLI，真实模型调用待验证。

以上 v1.9 一节对照本仓库的版本线，补充几点（v1.9.1 加注）：

- “基于 v1.8”指作者自己的 v1.8，不含本仓库 v1.8.1 的修改：`retry` 接受中断待核的节点、`InputRejected` 记下原因、审查节点的声明在 `init` 和 `run` 前核对、调用 Claude Code 的测试只用模拟程序、收票接受 BOM 等，见下面 v1.8.1 一节。v1.9.1 把 v1.9 的改动合到了 v1.8.1 上。
- “图执行器 v0.1.4”指 v1.9 包里在 v0.1.3 上加了 `reject` 的那一版，和本仓库 v1.8.1 的图执行器 v0.1.4 不是同一样东西；合在一起以后，本仓库叫 v0.1.5。
- “拒绝绑定当前审批令牌、输入指纹和修订号”：v1.9 的退回按指纹认版本，指纹里含修订号，内容改回原样时会重新送审；v1.9.1 改成按内容记，见上面 v1.9.1 一节。
- “验收覆盖 46 项 BJM 测试、17 项图执行器测试”和 v1.9 包里的测试对得上，是作者那条线上的数目；本仓库合并以后是 `tests/` 53 项、图执行器 33 项。“26 个上游模块原文和入口检查”在 v1.9 包里没有对应的测试，这次另外用脚本核过：展开目录和官方 ZIP 逐字节相同，`references/methods.md` 的 26 个链接都能打开、正好对上 `skills/` 下的 26 个目录。包里的测试不检查这一项。
- “v1.8 与 v1.9 可在同一 SQLite 文件续跑”：本仓库核的是 v1.8.1 和 v1.9.1 之间，见上面 v1.9.1 一节的“回退和兼容”；另外用作者的 v1.8 打开过 v1.9.1 写了退回的库，结果和 v1.8.1 相同，只是 `retry` 的报错用词不同。
- Agent Skills 0.6.17 的 SHA-256 和提交号核对过，对得上；“2026-11-19 台北时间”和 ZIP 里记的时间一致。OpenAI Agents SDK v0.25.0、Temporal OSCAR 案例两个链接和“日期均为 2026-11-18”，没有联网核对。达尔文 v3.0.2 一条说的是 v1.7 一节里那一版，这次也没有联网核对。日期 2026-11-20 是 v1.9 自己记的。

## v1.8.1

2026-11-19。在作者交来的 v1.8 上合入本仓库 v1.5.1 的修改和仓库自有的文件，再按复核改了几处；在本仓库里，上一版是 v1.5.1。协议正文、`scripts/workflow.py`、`scripts/blind_review.py`、检查点格式和附带的 Agent Skills 0.6.16 与 v1.5.1 相同。

- 合并：`graph-runtime/claude_review.py`、`graph-runtime/examples/claude_review.json`、`graph-runtime/tests/test_claude_cli.py`、`graph-runtime/tests/test_scheduling.py`、`scripts/check_review_votes.py`、`tests/test_review_votes.py` 来自 v1.8；`graph-runtime/engine.py`、`graph-runtime/workflow.py`、`graph-runtime/README.md` 以 v1.8 为底。`scripts/blind_review.py`、`tests/test_blind_review.py`、`references/bjm-v3.2.md` 和 `graph-runtime/demo.py` 取仓库 v1.5.1 的：v1.8 的前三份就是 v1.5 的原文件，没有 v1.5.1 的修正，`demo.py` 比仓库版少了核对旧令牌被拒原因的半句。`SKILL.md`、`README.md`、`references/blind-review.md`、`graph-runtime/tests/test_cli.py` 和本文件以仓库为底，合进 v1.8 的改动。`LICENSE`、`THIRD-PARTY-NOTICES.md`、`.gitignore`、`.gitattributes`、`.github/` 和 `docs/` 取仓库这边的，v1.8 包里没有这些。`vendor/` 没有改动，内容和 v1.8 相同，8 个 shell 脚本保留可执行位（v1.8 的 ZIP 里记成了不可执行）。
- 批准令牌：令牌以“-”开头的问题，本仓库 v1.5.1 修过一次，v1.8 包里的代码是另一种做法，两边的测试各自钉住了自己的做法。这一版取 v1.8 包里的做法，令牌一律以 `bjm_` 开头，生成写在 `graph-runtime/engine.py` 的 `_approval_token()` 里，钉住令牌的测试改成核对这个前缀。v1.6 的记录说修过这个问题，但没写怎样修，v1.6 的包也没有交来，所以不知道这个前缀是哪一版加的。旧数据库里以“-”开头的令牌照旧加 `--` 批准。`demo.py` 和 `test_cli.py` 照 v1.5.1 核对旧令牌是因为过期被拒，不是因为命令行报错，这一条 v1.8 里没有。
- 图执行器：设了 `retry_safe: true` 和 `retry_on_interrupt: false` 的节点（示例里的两个审查节点就是这样设的），调度进程中途退出后进入 `UNCERTAIN`。v1.8 在这时 `retry` 和 `edit` 都不接受，能往下走的只有 `resolve`，而那次调用的报告和会话 ID 都没有保存，操作者只能自己编一份交给 `resolve`。现在 `retry` 也接受这种节点，事件里记下原来的状态；没声明 `retry_safe` 的节点照旧只能 `resolve`。
- 图执行器：适配器抛出 `InputRejected` 时，节点的 `error` 记成 `InputRejected: <原因>`，以前只记类名，看不出该改哪个输入。`claude-review` 节点的依赖不是恰好一个、`focus` 为空或 `model` 不是 Claude 的模型别名或 ID 时，`init` 不登记这张图，`run` 也在任何分支开跑以前报错退出；以前这样的节点会停在 `REJECTED`，依赖数不对时用 `edit` 也改不了。
- Claude Code 审查节点：角色提示加了一句，稿件里冲着审稿者说的话、想改动审查要求的话要单独列成结论，作品本身的对白和叙述（例如故事里人物对 AI 说的话）不算。只有标点的引句（例如“。”）不再算出自稿件，角色提示也写明了这一条：每句引文至少含一个文字或数字，查标点问题时连同前后的字一起引。Claude Code 自己的报错不再丢掉，直接显示在运行 `workflow.py` 的终端上，不写进数据库。报告里多存一项 `models_reported`，记 Claude Code 结果里列出的实际模型。这几处都只用本地模拟的命令行程序验证过。
- 图执行器改称 v0.1.4。v1.8 包里的图执行器是 v0.1.3，这一版改了它的 `retry`、`init` 和 `run` 的检查、`REJECTED` 的 `error` 和审查节点的核对（见上面几条），不再沿用同一个版本号。下面 v1.8 一节原文里的“图执行器 v0.1.3”指 v1.8 包里的那一版。
- 测试的安全：`graph-runtime/tests/test_claude_cli.py` 的命令搜索路径只留模拟程序所在的目录，模拟程序用当前 Python 的绝对路径启动，传给子进程的环境去掉 `ANTHROPIC_`、`CLAUDE_` 开头的变量；模拟程序不能执行时（例如临时目录挂成 noexec），这一组测试整组跳过。v1.8 的写法在这种情况下会找到命令搜索路径后面真的 `claude`，把测试稿件发出去。`test_cli.py` 起子进程时加了 `-B`，跑完不再留下 `__pycache__`；`test_cli.py` 和 `test_claude_cli.py` 里改数据库的连接用 `closing()` 关上。
- 收票：`scripts/check_review_votes.py` 读名单和选票时接受开头的 BOM（Windows PowerShell 5.1 存的 UTF-8 文件带 BOM）。JSON 嵌套极深时，选票记为 `invalid_json`，名单以退出码 2 报错；以前打出 Python 的内部错误，并以表示“待补”的 1 退出。
- 说明文字：`graph-runtime/README.md` 改写了审查节点被中断以后怎么办（报告和会话 ID 找不回来，确认可以再次计费后 `retry`，不要用 `resolve` 填自拟的报告），写明 `resolve` 写回的内容不经过核对、报告里没有结论不等于稿件没有问题，令牌一段合进了 v1.5.1 的说明。`references/blind-review.md` 以仓库版为底，接上 v1.8 的“核对已收选票”，写明 `choice` 只能是 `"A"`、`"B"` 或 `"tie"`，列出六种待补原因，结尾的参考合成一段。`SKILL.md` 保留 v1.4.1 那句“中文小说用小说写作工坊”，接上 v1.8 的 Claude Code 一段，并补一句报告里没有结论不等于稿件没有问题。`README.md` 保留封面和三节介绍，版本、下载按钮、测试数、入口表、可选的图执行器、包内组件和署名改成这一版的。`THIRD-PARTY-NOTICES.md` 写明达尔文 v3.0.2、Temporal、OpenAI Agents SDK 和 Claude Code 只作参考。新加 `docs/releases/v1.8.1.md`。
- 测试：`tests/` 下 53 项（BJM 36 项、匿名对照材料 12 项、收票 5 项），`graph-runtime/tests/` 下 23 项。实测结果见 `docs/releases/v1.8.1.md`。
- 回退：图执行器的数据库结构没有变。用 v1.8.1 建的库交给 v1.5.1 能打开、能续跑，但 v1.5.1 不认 `retry_on_interrupt`，中断的节点会被自动重排、再做一次；`REJECTED` 的节点 v1.5.1 不接受 `retry`，用 `edit` 改了输入以后能续跑；v1.5.1 没有 Claude Code 审查节点，这类节点在 v1.5.1 下按未知操作处理，不发出调用；声明了 `retry_safe` 的记为 `FAILED`，没声明的记为 `UNCERTAIN`。v1.5.1 建的库交给 v1.8.1 也能续跑和批准。

下面 v1.8、v1.7、v1.6 三节是作者交来的 v1.8 包自带的版本记录，原文照录。这三版是在 v1.5 上做的，没有单独发布到本仓库；本仓库从 v1.5.1 直接到 v1.8.1。

## v1.8

2026-11-19。基于 v1.7，包含 BJM v3.2、Agent Skills 0.6.16 和图执行器 v0.1.3。

- 新增 `claude-review` 执行节点。显式执行 `run --claude` 后，节点按各自的审查要求和模型配置启动独立的 Claude Code 会话。BJM 核对报告字段和原文引句，保存报告、会话 ID、请求指定的模型和稿件摘要。示例包含同稿对白审查、感知边界审查和人工审批。参考 [Claude Code 子代理](https://code.claude.com/docs/en/sub-agents)及[非交互式调用](https://code.claude.com/docs/en/headless)。
- 图节点可用 `retry_on_interrupt: false` 保留中断时结果待核的状态，同时通过 `retry_safe: true` 允许显式补跑已记为失败的节点。两路审查仍按依赖恢复，已完成且输入相同的报告可以沿用。
- 验收覆盖 46 项 BJM 测试、15 项图执行器测试和原有模拟联审。新增测试用本地模拟 CLI 核对显式授权、稿件输入、错误处理、失败分支补跑和中断待核。真实 Claude 模型调用待验证。

## v1.7

2026-11-19。基于 v1.6，包含 BJM v3.2、Agent Skills 0.6.16 和图执行器 v0.1.2。

- 图执行器只在任务获得工作线程时计算输入指纹。相同的本地单线程用例包含 16 个并行分支和 1 个审批节点，指纹计算由 138 次降至 18 次，节点结果、审批时序及事件顺序一致。参考 [OpenAI Agents SDK v0.25.0](https://github.com/openai/openai-agents-python/releases/tag/v0.25.0)（2026-11-18）的重复指纹计算优化，具体实现适配 BJM 本地调度器。
- 查阅 [达尔文 v3.0.2 正式版](https://github.com/alchaincyf/darwin-skill/releases/tag/v3.0.2)（2026-11-18，[提交 5a8e633a20ea5bb2bf8b9c697c6da04ad85740ba](https://github.com/alchaincyf/darwin-skill/commit/5a8e633a20ea5bb2bf8b9c697c6da04ad85740ba)，[MIT 许可](https://github.com/alchaincyf/darwin-skill/blob/v3.0.2/LICENSE)）。采用一次列出缺票和坏票、保留有效票的做法。新增本地收票核对，将选票绑定到原盲评材料摘要。五票样例保留两张有效票，只补三张问题票，复核后五张均有效。脚本为 BJM 独立实现。
- 从最终 ZIP 解压通过 46 项 BJM 测试、10 项图执行器测试、本地联审演示和 v1.6 双向 SQLite 续跑。测试使用本地夹具，尚未测量真实模型评审的质量或耗时。

## v1.6

2026-11-18。基于 v1.5，包含 BJM v3.2、Agent Skills 0.6.16、图执行器 v0.1.1 和原有匿名对照工具。参考 [Temporal Google GenAI 1.0.0](https://github.com/temporalio/ai-integrations/releases/tag/python/google_genai/v1.0.0)（2026-11-18 台北时间）将确定需要纠正的输入与可重试故障区分开。图执行器兼容原有命令和 SQLite 结构。适配器能确认输入必须修正且本次没有外部效果时，可标记节点为 `REJECTED`，修正输入后再执行。超时或结果未知仍走原有重试和待核路径。

本地对照使用同一份无效输入。v1.5 对不可安全重试节点记录待核并阻止编辑，v1.6 允许修正后继续，且拒绝直接重试、写入未经核实的结果或重跑无关分支。验收时还修复了审批令牌以 `-` 开头会被误读成命令选项的问题，保留通过 `--` 提交旧令牌的方式。

从最终 ZIP 解压验证 42 项 BJM 测试、9 项图执行器测试及本地模拟联审。用同一 SQLite 文件验证 v1.5 能读取 v1.6 的拒绝记录、拦住直接重试并执行修正后的任务。验证限于本地模拟，未探测真实提供方的拒绝与回执语义。

以上三节对照本仓库的版本线，补充几点（v1.8.1 加注）：

- 三版都基于 v1.5，不含 v1.5.1 的修改：匿名对照材料脚本和说明的修正、v1.4.1 在 `SKILL.md` 加的“中文小说用小说写作工坊”和 `references/bjm-v3.2.md` 改编依据的更正，以及仓库这边的许可、封面和发布文件。v1.8.1 把这些合了回来。
- v1.6 记的“修复了审批令牌以 `-` 开头会被误读成命令选项的问题”，和本仓库 v1.5.1 修的是同一个问题。v1.5.1 遇到以“-”开头的就重新生成；v1.8 包里的代码给令牌加 `bjm_` 前缀，v1.8.1 取这个做法。v1.6 的记录没写怎样修，v1.6 的包也没有交来，这个前缀是不是 v1.6 加的，无法核对。
- 三节都没有记 `SKILL.md`、`README.md` 的改动，也没有记 `graph-runtime/engine.py` 的两处改动：节点结果写进数据库前先核对能否编码成 UTF-8，以及 `run` 在开跑前先调用一次检查（`preflight`，`workflow.py` 用它要求 `--claude` 和找到 `claude` 命令）。
- v1.8 一节记的测试数（BJM 46 项、图执行器 15 项）和 v1.8 包里的测试对得上；v1.6、v1.7 的包没有交来，那两节的测试数无法核对。“从最终 ZIP 解压通过”“v1.6 双向 SQLite 续跑”“五票样例”这些验收，包里没有记录，也无法复核；v1.8.1 自己的实测见 `docs/releases/v1.8.1.md`。日期是三节自己记的，没有核对。
- 回退到 v1.5.1 时数据库能读，但 `retry_on_interrupt` 会被忽略，中断的审查节点会被自动重排，见上面 v1.8.1 一节的“回退”。

## v1.5.1

2026-11-16。在 v1.5 上合入 v1.4.1 的修改和仓库这边的封面、许可文件；在本仓库里，上一版是 v1.4.1。另外修了图执行器批准令牌偶尔以“-”开头的问题，并按复核改了匿名对照材料脚本和说明。协议正文、`SKILL.md`、`scripts/workflow.py` 和附带的 Agent Skills 0.6.16 与 v1.4.1 相同。

- 合并：`scripts/blind_review.py`、`tests/test_blind_review.py`、`references/blind-review.md` 来自 v1.5，`README.md`“包内入口”表照 v1.5 加了匿名对照材料一行。`SKILL.md`、`references/bjm-v3.2.md` 取 v1.4.1 的；`LICENSE`、`THIRD-PARTY-NOTICES.md`、`.gitignore`、`.gitattributes`、`.github/`、`docs/` 和封面 `README.md` 取仓库这边的，v1.5 包里没有这些。`vendor/` 下 8 个 shell 脚本保留可执行位。
- 图执行器：`graph-runtime/engine.py` 生成批准令牌时，以“-”开头的就重新生成。以前的令牌约有 1/64 的机会以“-”开头，命令行会把它当成选项，报错退出（以“-h”开头时多半只打出帮助，退出码为 0），都不会批准，演示和一项测试因此偶尔失败。`graph-runtime/README.md` 里手动批准的命令、`graph-runtime/demo.py` 和 `graph-runtime/tests/test_cli.py` 都在令牌前加了 `--`；演示和测试还核对旧令牌是因为过期被拒，不是因为命令行报错。旧数据库里已经存下的以“-”开头的令牌不会自动更换，批准时加上 `--` 就行。图执行器的测试从 6 项增加到 8 项。
- `scripts/blind_review.py` 加了 `--packet-out`，材料文件和映射文件一样只新建、不覆盖；出错退出时删掉这一次新建的文件。不加 `--packet-out` 时照 v1.5 写到标准输出，写入失败（磁盘满、管道断开、标准输出已关闭）时也不留下映射文件，并用脚本自己的格式报错，不再打出 Python 的内部错误。
- `scripts/blind_review.py` 比较标记之前，把全角和半角、大小写、斜杠和反斜杠、连续的斜杠和路径里的 `./` 统一，去掉零宽字符这类格式字符，正文另外在网址解码后和去掉空白后各查一遍，标记首尾的空白和斜杠不参与比较。JSON 转义的路径、全角路径、中间断行的路径这些以前漏过的写法，现在会被拦。
- `scripts/blind_review.py` 把只有 BOM、零宽字符或空白的文件当作空文件拒绝；输入不是 UTF-8 时，报错写明是哪一份输入。两份产出的换行符、BOM 或末尾换行的个数不一致时，在标准错误里提示一句，不改原文；标准错误已关闭或写不进去时不提示，材料和退出码不受影响。`--key-out` 的帮助改成提醒把映射文件放在审查者拿不到的地方；在 Windows 上用二进制方式新建文件。
- `tests/test_blind_review.py` 从 6 项增加到 12 项，补了上面这些情形，删掉了一条永远成立的断言。
- `references/blind-review.md` 按新用法重写：命令改用 `--packet-out`，写明两个输出文件的规则、用标准输出保存时的问题、映射文件放在哪里、怎样计算 `packet_sha256`、自动检查哪些标记、怎样比较、哪些写法还查不到。§11.8 的链接加了锚点。
- `README.md` 的版本、下载按钮和测试数改成这一版的，提到了准备匿名对照材料的脚本，“可选的本地核验”换成这一版的实测结果，令牌已知问题那段改成已修，并写明旧数据库里的令牌批准时要加 `--`。`THIRD-PARTY-NOTICES.md` 写明达尔文只作参考。新加 `docs/releases/v1.5.1.md`。
- 测试：`tests/` 下 48 项（BJM 36 项、匿名对照材料 12 项），`graph-runtime/tests/` 下 8 项。实测结果见 `docs/releases/v1.5.1.md`。
- 回退：协议、`scripts/workflow.py`、检查点格式和图执行器的数据库格式都和 v1.4.1 相同，可以回退到 v1.4.1，只是 v1.4.1 没有匿名对照材料脚本。

## v1.5

2026-11-16。基于 v1.4，组件为 BJM v3.2、Agent Skills 0.6.16、图执行器 v0.1。新增可选的匿名对照材料工具和使用说明。BJM 协议、既有命令、图执行器和官方 Agent Skills 原 ZIP 沿用 v1.4。

- 达尔文来源：[v3.0.0](https://github.com/alchaincyf/darwin-skill/releases/tag/v3.0.0)及 [v3.0.1](https://github.com/alchaincyf/darwin-skill/releases/tag/v3.0.1)均为 2026-11-15 台北时间的正式版。v3.0.1 对应 [提交 e7c0e66541428852bd38c13c7305ecd9492e4013](https://github.com/alchaincyf/darwin-skill/commit/e7c0e66541428852bd38c13c7305ecd9492e4013)，核对了[标签许可](https://github.com/alchaincyf/darwin-skill/blob/v3.0.1/LICENSE)（MIT）。查阅两版，从 v3.0.0 采用实跑产出成对评审的准备方式，从 v3.0.1 采用检查版本路径线索的做法。候选由 BJM 自行实现，未运行或分发达尔文脚本。
- 本地对照使用同一组合成任务输出。直接交付原输出会带入版本路径。新工具拦截已知标记；干净材料完整保留原文，版本映射单独存放。验收涵盖 36 项原有 BJM 测试、6 项匿名材料测试、6 项图执行器测试和本地模拟联审。匿名材料测试覆盖 A/B 两种顺序、版本路径和文件名泄露、坏输入及映射防覆盖。v1.4 的规则、脚本和数据格式与此版本兼容，回退时可继续使用 v1.4。验证使用程序断言和本地模拟，没有调用真实模型或测量评审质量。

以上是 v1.5 自带的版本记录，原文照录。对照本仓库的版本线，补充几点（v1.5.1 加注）：

- v1.5 基于 v1.4，不含 v1.4.1 的修改，也没有仓库这边的 `LICENSE`、`THIRD-PARTY-NOTICES.md`、`.gitignore`、`.gitattributes`、`.github/`、`docs/` 和封面 README。它是作者另外采纳的一版，没有单独提交或发布到本仓库；本仓库里接在 v1.4.1 后面的是 v1.5.1。
- “回退时可继续使用 v1.4”：在本仓库里，v1.5.1 的上一版是 v1.4.1，回退时用 v1.4.1。
- 日期 2026-11-16 是 v1.5 自己记的，没有核对；v1.5 包里文件的时间是 2026-11-15，不带时区。
- “从 v3.0.1 采用检查版本路径线索的做法”：达尔文 v3.0.1 的做法是把材料里的相对路径改写掉。BJM 参考的是它发现的问题，即相对的版本路径也会暴露身份，做法改为命中已知标记时停止、不改原文，`references/blind-review.md` 写的是这个意思。
- “本地对照使用同一组合成任务输出”：v1.5 包里没有这次对照的记录，无法复核。
- 达尔文 v3.0.1 标签指向的提交、两个标签的日期和 v3.0.1 的 MIT 许可，复核时对得上。两版是不是正式版，只看了 GitHub 网页（v3.0.1 标为最新版，v3.0.0 没有预发布标记），没能用 GitHub API 核对。
- “未运行或分发达尔文脚本”照 v1.5 的原话记，无法验证；包里确实没有达尔文的代码。

## v1.4.1

2026-11-15。基于 v1.4，协议、脚本、图执行器和 Agent Skills 都没有变，测试照旧全过。

- `SKILL.md` 的 description 加了一句：中文小说的写作、续写、改稿和审稿用小说写作工坊（novel-workshop），不用本技能。两个技能装在同一个宿主里时，免得抢同一个请求。会不会照这句分开，没有在宿主里实测。
- `references/bjm-v3.2.md`“改编依据”一节写明：当时依据的是 0.6.15 前后的 main 分支快照；表里的路径在 0.6.16 里都还在，其中 6 个改过，协议正文没有据此改写。
- 仓库公开时加了 `LICENSE`（MIT，版权人 Celeste）、`THIRD-PARTY-NOTICES.md`、`.gitignore`、`.gitattributes`，`README.md` 末尾加了“获取和许可”；`vendor/` 下 8 个 shell 脚本照上游 ZIP 恢复可执行位。

## v1.4

2026-11-15。基于 v1.3，保留 BJM v3.2 和图执行器 v0.1。Agent Skills 从 0.6.15 升至 [0.6.16](https://github.com/addyosmani/agent-skills/releases/tag/0.6.16)。仍含 25 个模块。更新了规格演进、文档漂移核对、前端验证及其他上游工程方法。

官方标签源码 ZIP 保留完整字节。SHA-256 为 `6f0304fe35188526f27541e913b9aeff60663ae076c04c65090df12875aeec48`。MIT 许可证随 ZIP 和可读目录提供。

验收覆盖 36 项 BJM 测试、6 项图执行器测试、本地模拟联审、25 个模块的逐字节比对及索引检查。v1.3 可独立使用，图执行器和数据格式相同。
