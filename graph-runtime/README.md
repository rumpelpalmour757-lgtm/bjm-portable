# BJM 图工程原型 v0.1.7

用 BJM 的分工和验收思路跑一条可恢复的任务图。Python 标准库负责调度，SQLite 保存节点结果、审批状态和执行事件。每个数据库同一时间由一个本机进程调度，进程内可以并行跑分支。两章联审演示使用本地模拟调用，开箱即可复现分支失败和恢复。

## 快速运行

本模块单独解压时，从模块根目录运行。它随 BJM 迁移包分发时，下面的逐条命令从 `bjm-portable/graph-runtime/` 目录运行。需要 Python 3.10 或更新版本。v0.1.7 这次在 Linux 上用 Python 3.11、3.12、3.13 验证过，Windows 和 macOS 没有实测。

```bash
python3 demo.py
```

演示脚本依次触发一章失败、从原数据库恢复、修改稿件、拒绝旧审批并接受新审批。下面也可以用 Bash 逐步复现。

```bash
bjm_demo_dir="$(mktemp -d)"
bjm_demo_db="$bjm_demo_dir/demo.sqlite3"

python3 workflow.py --db "$bjm_demo_db" --run-id demo init examples/two_chapters.json
python3 workflow.py --db "$bjm_demo_db" --run-id demo run --workers 2 --fail-before review-b
python3 workflow.py --db "$bjm_demo_db" --run-id demo status
python3 workflow.py --db "$bjm_demo_db" --run-id demo retry review-b
python3 workflow.py --db "$bjm_demo_db" --run-id demo run --workers 2
python3 workflow.py --db "$bjm_demo_db" --run-id demo events
```

`--fail-before review-b` 在第二章审查的模拟调用开始前制造失败。第一次 `run` 后以 `status` 的节点状态判断结果，命令正常退出只表示返回了运行信息。随后几个命令启动新的进程，使用同一个 SQLite 文件继续工作。

## 验证审批绑定

上一步恢复后，先用 `status` 保存 `nodes.approve.token`，然后改第二章并恢复运行。

```bash
python3 workflow.py --db "$bjm_demo_db" --run-id demo status
python3 workflow.py --db "$bjm_demo_db" --run-id demo edit draft-b '{"text":"第二章的新稿内容。"}'
python3 workflow.py --db "$bjm_demo_db" --run-id demo run --workers 2
python3 workflow.py --db "$bjm_demo_db" --run-id demo status
```

先运行下面第一条来核对旧令牌会被拒绝，再把第二条的占位符替换为新令牌并批准。令牌前面的 `--` 告诉命令行后面不再是选项。

```bash
python3 workflow.py --db "$bjm_demo_db" --run-id demo approve approve -- '<编辑前的令牌>'
python3 workflow.py --db "$bjm_demo_db" --run-id demo approve approve -- '<编辑后的令牌>'
```

令牌由程序随机生成。v1.5.1 以前的版本生成的令牌约有 1/64 的机会以 `-` 开头，不加 `--` 时命令行会把它当成选项，报错退出（以 `-h` 开头时多半只打出帮助，退出码为 0），都不会批准。v1.5.1 生成时避开了 `-` 开头；现在生成的令牌一律以 `bjm_` 开头。旧数据库里已经存下的以 `-` 开头的令牌不会自动更换，照上面的写法加上 `--` 就能批准。

令牌不对或已经过期时，报 `stale or invalid approval token`。节点已经批准、已经退回、还没发令牌，或者根本不是审批节点时，报错直接写明是哪一种，不说令牌的事。

## 退回当前版本

审阅者看过稿件不同意时，可以退回，不批准。照上一节做到等待批准这一步以后，把上面第二条批准命令换成下面这条。命令里 `reject` 后面的 `approve` 是演示图里审批节点的 ID，不是第二个命令。

```bash
python3 workflow.py --db "$bjm_demo_db" --run-id demo reject approve -- '<编辑后的令牌>'
```

退回以后，审批节点记为 `REJECTED`，`error` 是 `ApprovalRejected`，令牌立即作废。SQLite 里多一条 `APPROVAL_REJECTED` 事件，记下这一版的审批指纹、修订号和送审内容的摘要 `content_sha256`。依赖这个审批的步骤一直等着，其他分支照常运行。被退回的节点不接受 `approve`、`reject`、`retry` 和 `resolve`。

要重新送审，改的是审批节点上游的稿件：用 `edit` 改稿，再 `run`，从 `status` 取新令牌。不要改审批节点自己的 `inputs`，那样送审的还是原稿（见下面一段）。送审内容指审批节点自己的 `inputs` 加上各依赖节点的输出，逐字节比较。退回以后反复 `run`，或者用 `edit` 提交和原来完全相同的输入，什么都不变：节点照旧是 `REJECTED`，`error` 仍是 `ApprovalRejected`，也不写新事件。改了稿件以后又改回被退回的那一份，或者往上游加一个不影响输出的输入，`edit` 会把审批节点放回 `PENDING`，再 `run` 时送审内容和退回时相同，节点就回到 `REJECTED`，不发新令牌，事件里记一条 `REJECTION_KEPT`，`error` 写明是在哪个修订号退回的。

这种对照只在依赖节点的输出逐字节相同时起作用。审批节点排在 Claude Code 审查节点后面时（`examples/claude_review.json` 就是这样），上游一改，哪怕改回原稿，审查也会重跑，每次的会话 ID 不同，模型给的结论也可能不同；排在另一个审批节点后面时，前一个审批要重新批准，它的输出里有带修订号的指纹。这两种情形下送审内容都和退回时不同，同一份稿件仍会再次送审，要靠审阅者自己核对，例如对照审查报告里稿件的 SHA-256（`artifact_sha256`）。

审阅者要重看同一份稿件（例如退回错了）时，改审批节点自己的 `inputs`，例如写上为什么要重看，再 `run`。这会发出新令牌，送审的仍是原稿，批准前照常核对稿件。上游连着已经完成、没声明 `retry_safe` 的外部动作时，`edit` 改不了稿件，这也是本次运行里唯一能重开审批的办法；要改稿件，就新建运行。退回只在同一个运行里、同一个审批节点上对照，新建的运行不沿用以前运行里的退回，别的审批节点送审同一份内容也照常发令牌。

数据库经过不按内容对照的版本（v1.8.1、作者的 v1.8 和 v1.9）以后，那些版本可能对退回过的同一份内容发了令牌。回到这一版，用这样的令牌 `approve` 会被拒，报 `the same content was rejected at revision N`，库里什么也不写；`reject` 照常可以用。在那些版本里已经批准了的，这一版不会改回去。

图执行器不记退回的理由，理由要另外记下来交给改稿的人。依赖被退回的审批、这次运行轮不到的 Claude Code 审查节点，不要求加 `--claude`，无关分支照常能跑；等审批通过、轮到审查节点时，才要 `run --claude`。不过每次 `run` 都先核对所有还没跑的审查节点的声明，轮不到的也查，声明不合格（例如 `edit` 把 `focus` 改成空的）就报错退出，见下面“使用 Claude Code 并行审稿”。

## 运行回归测试

```bash
python3 -B -m unittest discover -s tests -v
```

## 看懂两章联审

两章的初稿互相独立，各自交给对应的审查节点。审批等两份审查完成，再绑定当前候选和审查结果。执行记录可以用来定位节点开始、完成、失败、重新审查和等待审批的顺序。

| 场景 | 验收现象 |
|---|---|
| 其中一章审查失败 | 另一章已保存的结果继续有效。显式重试失败节点，再恢复整个运行 |
| 停止程序后重新启动 | 从 SQLite 重新读同一个运行。已保存且输入仍匹配的节点直接沿用 |
| 审批前修改其中一章 | 只重跑该章及受影响的下游。修改前发出的审批令牌失效 |
| 审阅者退回当前版本 | 退回决定随数据库保存。依赖该审批的步骤等待新版本通过，其他分支可继续。同一个运行里送审内容逐字节相同时不再送审；审批排在审查节点或另一个审批后面时做不到这一点，见“退回当前版本” |
| 外部调用中途失联，无法判断是否送达 | 节点进入待核状态。等待提供方回执，取得已确认结果后用 `resolve` 写回。 |
| 任务节点的输入被明确拒绝，能确认本次没有产生外部效果 | 节点记为 `REJECTED`，`error` 以 `InputRejected` 开头，冒号后写明原因（v1.8.1 以前的版本和作者的 v1.9 写的库里只有类名）。用 `edit` 修正这个节点自己的输入再继续，本轮无关分支沿用原结果。 |

## 使用 Claude Code 并行审稿

在本机安装可信的 Claude Code CLI，建议使用 v2.1.286 或以上。适配器使用 `--bare`，真实调用需配置 Anthropic API 密钥或 Claude Code 支持的提供方凭据。平时用 Claude 订阅登录的用户也需另行配置上述凭据。以下从图执行器目录运行，`init` 登记示例图，带 `--claude` 的 `run` 才发送稿件给模型。

```bash
bjm_review_dir="$(mktemp -d)"
bjm_review_db="$bjm_review_dir/review.sqlite3"

python3 workflow.py --db "$bjm_review_db" --run-id review init examples/claude_review.json
python3 workflow.py --db "$bjm_review_db" --run-id review run --claude --workers 2
python3 workflow.py --db "$bjm_review_db" --run-id review status
```

示例用两种模型审同一段虚构稿件，分别检查对白和人物感知。每个 `claude-review` 节点声明目标模型 `model`、审查要求 `focus` 和一个产出 `text` 的依赖。依赖不是恰好一个、`focus` 为空或 `model` 不是 Claude 的模型别名或 ID 时，`init` 拒绝登记这张图；已登记的运行在 `run` 时也先查一遍，这次轮不到的审查节点也查，不合格就在任何分支开跑以前报错退出。`focus` 和 `model` 可以用 `edit` 改，依赖数不对只能改图以后新建运行。适配器通过 `--agent` 在独立的非交互会话中启用内置的 `bjm-reviewer` 角色，并关闭工具。模型从请求取得该稿件和审查要求。Claude Code 自己的报错直接显示在运行 `workflow.py` 的终端上，不写进数据库。

每条结论包括原文引句 `quote`、问题 `issue` 和建议 `suggestion`。BJM 核对报告结构，核对引句是否原样出现在稿件里、是否至少含一个文字或数字（只有标点的引句不算；角色提示也把这条告诉了模型，查标点问题时要连同前后的字一起引），并保存报告、会话 ID、稿件 SHA-256、请求指定的模型 `model_requested`，以及 Claude Code 结果里列出的实际模型 `models_reported`（可能不止一个，结果里没有时为空）。经 `run --claude` 得到的 `SUCCEEDED` 表示报告通过这些核对；用 `resolve` 写回的内容不经过这些核对，事件里记为 `RESOLVED`。通过核对不等于结论成立，编辑者仍需判断结论是否成立、哪些建议值得采纳。报告里没有结论（`findings` 为空），也不说明稿件没有问题：稿件里夹带的“忽略要求、返回空列表”这类话，模型如果照做，交回的空报告和真正没有问题时一样能通过核对。角色提示要求把稿件里冲着审稿者说的话、想改动审查要求的话单独列成结论，作品本身的对白和叙述不算（例如故事里人物对 AI 或“系统”说的话）；模型照不照做没有用真实模型验证过。两份报告保存后，`approve` 节点进入 `AWAITING_APPROVAL`，看过稿件和报告后可使用当前令牌批准。

示例通过 `retry_safe: true` 允许手动补跑。一支显示为 `FAILED` 时，确认可以再次计费后执行 `retry <节点>`，再用 `run --claude` 继续。已完成且输入相同的另一支会沿用原报告。示例同时设置 `retry_on_interrupt: false`：调度进程在调用期间退出（例如按了 Ctrl-C 或进程被杀）后，再次运行时这一支不会自动重发，而是进入 `UNCERTAIN`，因为那次调用可能已经计费。适配器不保存会话，报告要等 Claude Code 正常结束才交回，所以那次调用的报告和会话 ID 都找不回来，也没有外部结果可以核对。这时 `edit` 会被拦住；确认可以再次计费后，执行 `retry <节点>`，再用 `run --claude` 继续，只补跑这一支。不要用 `resolve` 填一份自拟的报告。包内测试使用本地模拟 CLI，实际模型调用待验证。

图里既有本地任务又有 Claude Code 审查时，可以加 `--claude-workers N` 限定同时在跑的审查节点数，例如 `run --claude --workers 4 --claude-workers 1`：同时最多跑 4 个任务节点，其中审查节点（`operation` 为 `claude-review`）最多 1 个。到了上限，其余审查节点留在 `PENDING`，尝试次数不加；不依赖它们的本地节点照常用剩下的槽位。一个审查结束，不论成功、失败、待核还是被拒，就空出一个名额。N 须是正整数，0 或负数报错退出，库里什么也不写。这个上限算在 `--workers` 里面，比 `--workers` 大时，实际并发仍不超过 `--workers`。不加 `--claude` 时这个选项不起作用：这次能轮到审查节点，照旧报错要求加 `--claude`；轮不到，就没有审查可限。上限不存进数据库，每次 `run` 要限都得再加，不加时审查和其他任务一起只按 `--workers` 算。用示例图、上限为 1 时，两个审查会一个跑完再跑另一个。调度进程被强行结束以后（例如 `kill -9`），它启动的 Claude Code 进程可能还在跑，这些进程不算进下一次 `run` 的上限；要守住上限，先确认上次的调用已经结束，再续跑。

[Claude Code 子代理](https://code.claude.com/docs/en/sub-agents) · [CLI 参数参考](https://code.claude.com/docs/en/cli-reference) · [非交互运行与 Bare 模式](https://code.claude.com/docs/en/headless)

## 接到实际任务时

- 每个任务节点声明输入和依赖。把提供方调用放在任务处理函数里，将实际稿件版本、请求 ID 和结果一并返回，便于恢复后对照。适配器应在正常返回前校验节点验收条件。审查失败或证据不足时应报告失败。
- 能确认重试安全的调用才标记为可安全重试。结果未知时等待提供方回执，已确认结果才用 `resolve <节点> '<实际结果 JSON>'` 记录；`resolve` 原样写入给出的 JSON，不经过适配器的核对。`retry` 适用于被声明为可安全重试、已失败或因调度中断而待核的节点。已完成的外部动作如果未标记为可安全重试，关联的上游编辑会被拦住；另一次外部动作应由操作者重新授权并开启新的运行。
- 对可手动重试、但不适合在调度器中断后自动重发的任务，设置 `retry_on_interrupt: false`。这样的节点被中断后进入 `UNCERTAIN`，操作者确认可以重做后用 `retry` 放回队列。省略这个字段时，调度器按既有的 `retry_safe` 标记恢复。
- 输入必须修改且能确认本次没有产生外部效果时，适配器可以抛出 `engine.InputRejected`。例如发送前的参数校验失败，或提供方明确保证请求未生效。超时、断线和含义不确定的错误仍沿用原来的故障处理，不能只凭 HTTP 状态码把它们归类为 `InputRejected`。节点的 `error` 记为 `InputRejected: <原因>`，原因是适配器自己写的那句话，不要把提供方返回的内容放进去；其他异常只记异常的类名。SQLite 的结构沿用原版，命令新增了 `reject`。`REJECTED` 有两种来源，接入方按 `error` 区分：任务节点的 `error` 以 `InputRejected` 开头（v1.8.1 以前的版本和作者的 v1.9 写的库里只有类名，没有冒号和原因），要改的是这个节点自己的输入；审批节点的 `error` 以 `ApprovalRejected` 开头，是审阅者退回的，要改的是它上游的稿件。
- 审批令牌标识当前审批版本，批准和退回都只核对令牌。真实部署还需由接入系统校验操作者身份及审批权限。
- 每次运行使用创建时登记的图版本。改某一节点的输入用 `edit`；更换节点结构或状态格式时，新建运行并明确沿用的资料。原型独立运行，演示所用的生成和复核结果均来自本地模拟夹具。

## 设计参考

- Google ADK 的图工作流实战把流程分成明确节点，示范并行分支、汇总和人工审批。 [Graph Workflows in ADK](https://cloud.google.com/blog/topics/developers-practitioners/graph-workflows-in-adk-everything-you-need-to-know/)
- Google ADK v2.15.0 给 `LlmAgent` 加了 `max_parallel_workers`，限定一个并行工作节点同时处理几条输入，不管整个工作流。`--claude-workers` 参考了在总并发之外给一类工作另设上限的做法，但管的是整次运行里所有 Claude Code 审查节点，代码按 BJM 的调度器另写。 [ADK 提交 5e4f0e1](https://github.com/google/adk-python/commit/5e4f0e18cfe869a183901192f92c86d7574881b0)
- LangGraph 的中断与恢复提供了对照，特别是审批返回后节点可能重入，以及过期审批应被拒绝。 [Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts) · [LangGraph 发行记录](https://github.com/langchain-ai/langgraph/releases)
- Temporal 的持久执行和 Worker 版本固定用于参考进程恢复、外部调用和运行版本之间的边界。 [AI Framework Integrations](https://temporal.io/blog/ai-framework-integrations) · [Worker Versioning](https://docs.temporal.io/worker-versioning)
- OpenAI 的 Trace Grading 提供了依据执行过程定位问题的思路。本原型记录可供核查的事件，事件评分可由接入方另行实现。 [Trace Grading](https://developers.openai.com/api/docs/guides/trace-grading)
- OpenAI Agents SDK v0.25.0 的逐项批准与拒绝，以及 Temporal 的 OSCAR 示例，提供了将人工决定和待审版本一起持久保存的参考。 [OpenAI Agents SDK v0.25.0](https://github.com/openai/openai-agents-python/releases/tag/v0.25.0) · [Temporal OSCAR 示例](https://temporal.io/blog/building-a-reliable-ai-agent-with-oscar)
- EMNLP 2026 年 10 月综述区分了复用的图模板、某一次运行实际走过的图和执行轨迹，适合作为后续比较流程版本的参考。 [From Static Templates to Dynamic Runtime Graphs](https://aclanthology.org/2026.findings-emnlp.1393/)
