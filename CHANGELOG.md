# 版本记录

日期按台北时间（UTC+8）记。

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
