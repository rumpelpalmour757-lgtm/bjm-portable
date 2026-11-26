# 版本记录

日期按台北时间（UTC+8）记。

## v1.12.1

2026-11-27。在本仓库 v1.10.1 上合入作者交来的 v1.12 包里 v1.11、v1.12 两版新加的东西：`events --after` 和 `--limit` 分页读取执行记录、只由 `init` 建库、打开库以前检查线程上限，以及 Agent Skills 0.6.18；再按复核改了几处。在本仓库里，上一版是 v1.10.1。v1.11 是作者在自己的 v1.10 上做的，v1.12 又在 v1.11 上做，两版都没进本仓库，所以三方合并以作者交来的 v1.10 包为底，一边是 v1.12 包，一边是本仓库 v1.10.1。这一版改过它们的代码、测试和说明，照本仓库的习惯（作者交来的版本在仓库里改过的，版本号加 .1）不叫 v1.12，记作 v1.12.1；本仓库从 v1.10.1 直接到 v1.12.1，v1.11 没有单独进本仓库。协议的规则、`SKILL.md`、`scripts/`、`tests/`、检查点格式和图执行器的数据库结构与 v1.10.1 相同；协议只改了附录 C“改编依据”里的一句说明。

- 合并：v1.12 包相对作者的 v1.10 包改了 `CHANGELOG.md`、`README.md`、`THIRD-PARTY-NOTICES.md`、`graph-runtime/README.md`、`graph-runtime/engine.py`、`graph-runtime/workflow.py`、`graph-runtime/tests/test_claude_cli.py`、`graph-runtime/tests/test_cli.py`、`references/bjm-v3.2.md` 和 `references/methods.md`，并把 `vendor/` 换成 Agent Skills 0.6.18。`engine.py`、`workflow.py`、`test_cli.py` 三方合并没有文本冲突：本仓库 v1.10.1 改的是 `run()` 里 `worker_limits` 的检查和 `run_tasks` 里 `--claude-workers` 的检查，v1.12 改的是引擎的构造函数、`events()` 和命令行的 `main()`，两边挨不着。`test_claude_cli.py` 两边改的是同一项测试（`test_cli_caps_review_nodes_and_keeps_the_existing_approval_flow`），本仓库 v1.10.1 还把它挪到了文件末尾；两份断言等价，保留 v1.10.1 的写法，这个文件和 v1.10.1 相同。`test_scheduling.py` 只有 v1.10.1 改过，照仓库。说明文件以仓库为底，接上 v1.12 的改动，再按下面几条改。v1.12 包和作者的 v1.10 包一样，封面用文字链接代替下载按钮（v1.12 指向本仓库 v1.10.1），把“获取和许可”里的下载说明换成“本包是 v1.12……”，这是站在包的角度写的，没有取，仍用仓库原来的按钮和说明，只改版本。v1.12 包自带的 v1.12、v1.11 两节版本记录原文照录在下面。
- 分页读取执行记录（来自 v1.11）：`events` 新加可选的 `--after ID` 和 `--limit N`。`--after` 只返回这个运行里 ID 比它大的事件，按 ID 从小到大排；`--limit` 一次最多返回 N 条，只能和 `--after` 一起用，单独给报 `limit requires an after cursor`。`--after` 须是 0 到 2^63−1 的整数，`--limit` 须是 1 到 2^63−1 的整数，不合格报错，退出码 2；上限是必要的，超过 2^63−1 时 sqlite3 抛 `OverflowError`，不在命令行捕获的异常里，会打出 Python 的内部错误。不带这两个选项时，查询语句和以前逐字相同，输出不变。代码上是 `engine.py` 的 `events()` 多了只能按名字传的 `after` 和 `limit`，`True`、`False` 不算整数。同一个库里的几个运行共用一串事件 ID，一个运行的 ID 会跳号。
- 只由 `init` 建库（来自 v1.12）：`Engine` 的构造函数多了只能按名字传的 `initialize`，默认是 `True`，`Engine(路径)` 和以前一样，遇到没初始化的库会建表；命令行只有 `init` 传 `True`。`init` 以外的命令（`status`、`events`、`run`、`retry`、`edit`、`approve`、`reject`、`resolve`）遇到没初始化的文件（`user_version` 为 0：空文件，或者别的程序建的 SQLite 库），在拿锁以前报 `database is not initialized; run init first`，退出码 2，文件不变，也不留锁文件。本仓库 v1.10.1 和作者的 v1.10 遇到空文件，会先写进表结构（文件变成 24,576 字节）、留下 `.lock` 文件，再以 `unknown run`、`unknown node` 这类错误退出 2。路径不存在时，从 v1.4 起本来就报 `database does not exist`，这一点没有变。所以以前能成功的用法都不受影响，变的只是空文件不再被改写；`demo.py` 先 `init`，说明里用 `mktemp -d` 建的是目录，不是空文件，两者照旧能跑。
- 打开库以前检查线程上限（来自 v1.12，报错的打法按复核改过）：`run --workers` 或 `--claude-workers` 不是正整数时，在查库存不存在、打开库以前就报错退出，退出码 2。本仓库 v1.10.1 只在 `run_tasks` 里查 `--claude-workers`，那时库已经打开；`--workers 0` 要到引擎里才报 `workers must be a positive integer`。
- Agent Skills 0.6.18（来自 v1.11）：删掉 `vendor/agent-skills-0.6.17/` 和 `vendor/agent-skills-0.6.17.zip`，换成 `vendor/agent-skills-0.6.18/` 和 `vendor/agent-skills-0.6.18.zip`。ZIP 取自作者的 v1.12 包，649,475 字节，SHA-256 为 `d6bade14a2fec866be3c44bcba7ca5cd0817d7856bb10d175e4a9b7acc5a4065`，ZIP 注释记的提交是 `e997ac5b9a74eab332d5e9793bb38a38c8cfdd74`，ZIP 里记的时间是 2026-11-24 07:11:15（UTC），即台北时间 2026-11-24 15:11。GitHub 上 0.6.18 标签的官方源码 ZIP 这次取不到（403），没有直接比对；改用 git 取下 0.6.18 标签（附注标签，指向提交 e997ac5b，标签时间和 ZIP 里的相同），在 `TZ=America/Los_Angeles` 下用 `git archive --format=zip --prefix=agent-skills-0.6.18/` 打出来的 ZIP 和这份逐字节相同；同样的办法打 0.6.17，得到的正是仓库里那份 `f2d2dfca…`，那份 v1.9.1 时和官方 ZIP 逐字节比过。和 0.6.17 比，模块仍是 26 个，没有新加或删掉的；13 份模块的 `SKILL.md` 改过，其中 12 个模块改成链接模块自己带的共享清单，`accessibility-engineering` 另改了找审查脚本的说法，`ci-cd-and-automation` 把示例里的 GitHub Actions 从 v4 升到 v6；文件新增 18 个、改了 39 个、删除 0 个，新增的是 12 个模块下共 16 份 `references/shared/` 副本（每份都和包根目录 `references/` 下的同名文件逐字节相同）和 `scripts/sync-shared-references.js` 及它的测试。`LICENSE` 和 0.6.17 的逐字节相同，仍是 MIT，版权行仍是 Copyright (c) 2025 Addy Osmani。
- 展开目录照 0.6.17 的规矩办：279 个普通文件和 ZIP 逐字节相同，原包的符号链接 `.opencode/skills` 只留在 ZIP 里；ZIP 里标成可执行的 9 个 shell 脚本保留可执行位，和 0.6.17 是同样 9 个（v1.12 包里这 9 个记的也是可执行）。0.6.18 自带的 `vendor/agent-skills-0.6.18/.gitattributes` 多了一行 `skills/*/references/shared/** linguist-generated=true`，在本仓库也生效，GitHub 的差异页面会把那 16 份副本默认折叠。新加的 `scripts/sync-shared-references.js` 不联网，但不带 `--check` 运行时会删掉并重写各模块的 `references/shared/`；`hooks/sdd-cache-post.sh` 仍会用 `curl` 发请求，`skills/accessibility-engineering/scripts/audit-a11y.sh` 仍用 `npx --yes` 从网上取程序执行，这两处 0.6.17 就有。这次只读过，`vendor/` 下的脚本一律没有运行。
- 跟着 0.6.18 改的说明：`README.md` 的版本和两处路径；`references/methods.md` 的版本和 26 个模块链接，链接都能打开；`THIRD-PARTY-NOTICES.md` 的版本、三处路径、SHA-256 和提交。`methods.md` 里 v1.12 把“模块的共享资料、模板和脚本沿用原目录结构”换成“模块的共享清单可从其 `references/shared/` 读取”，读起来像每个模块都有，其实 26 个里只有 12 个有，包根目录的 `references/` 也还在；这一版保留原句，再补一句哪些模块另带副本。`references/bjm-v3.2.md` 附录 C“改编依据”那句说明改成 0.6.18：表里引的 12 个上游路径在 0.6.18 里都还在，0.6.18 又改了其中 5 个（`using-agent-skills`、`planning-and-task-breakdown`、`incremental-implementation`、`code-review-and-quality` 四个模块的 `SKILL.md` 只改了共享清单的链接，`docs/skill-anatomy.md` 改了共享清单放在哪里的说明），协议正文没有据此改写；v1.12 只换了版本号，没有补这一句。旧版本各节和 `docs/releases/` 里写 0.6.17 的地方是历史记录，没有改。
- 按复核改的地方：
  - 线程上限的报错：v1.12 用 `parser.error` 报，先打出总命令的用法，再打 `workflow.py: error: …`，而 `--workers abc` 这类由 `run` 子命令报的错打的是 `run` 的用法。现在这两项检查放进 `main()` 原有的报错路径，位置仍在打开库以前，报 `workflow: --workers must be a positive integer` 或 `workflow: --claude-workers must be a positive integer`，退出码 2，和本仓库 v1.10.1 对 `--claude-workers` 的报错一字不差。没有改成在 `run` 子命令上用类型函数检查，那样报错会变成 argparse 的 `argument --workers: …`，v1.10.1、v1.12 的测试和 v1.10.1 的版本记录写的报错都要跟着改。`run_tasks` 里 v1.10.1 那道 `--claude-workers` 检查从命令行已经走不到，删掉；直接调用 `run_tasks` 的程序传了不对的上限，仍由引擎报 `operation worker limits must be positive integers`。
  - 保留本仓库 v1.10.1 在引擎里要求 `worker_limits` 必须是映射的检查。v1.12 没有这一处：把仓库的 `test_scheduling.py` 放到 v1.12 的代码上跑，`test_invalid_worker_limits…` 失败，字符串报 `dictionary update sequence…`，整数报 `TypeError`，键值对的列表被当成映射收下并真的跑了。
  - 图执行器改称 v0.1.9。v0.1.7 有两个意思：v1.11 包里的 v0.1.7 是作者 v1.10 的 v0.1.6 加上事件分页，本仓库 v1.10.1 的 v0.1.7 是 v0.1.6 加上两处输入检查；v1.12 包里的 v0.1.8 是作者的 v0.1.7 加上只由 `init` 建库和线程上限的预检。这一版是两边合起来，又改了报错的打法，照 v1.8.1、v1.9.1 和 v1.10.1 的做法不沿用 v0.1.8，记作 v0.1.9。下面 v1.11 一节原文里的“图执行器 v0.1.7”、v1.12 一节的“v0.1.8”指作者包里的那两版。
  - 测试：v1.11 的两项（游标分页并在新事件以后续读、游标取值越界被拒）和 v1.12 的一项（只有 `init` 建库）移过来。只有 `init` 建库那项，原来只试 `status`、`events`、`run`，现在加上 `retry`、`edit`、`approve`、`reject`、`resolve`，并核对报错以 `workflow: ` 开头；把线程上限的检查改回 `parser.error`，这项就失败。v1.12 在 `test_claude_cli.py` 里原地改的“按两个审查实际开跑的先后比较”，和本仓库 v1.10.1 的改法等价：给初稿 a 加 0.5 秒延迟、让初稿 b 先完成时，两种写法都通过，v1.10 原来的断言失败（`8 not less than 4`）；合并时取 v1.10.1 的一份，不算这一版新加的。在这一版的代码上逐一试了 10 种错误改法：游标改成 `>=`、命令行总是建库、去掉 `--workers` 预检、分页不按运行过滤、`limit` 不要求 `after`、去掉上限、去掉 `main` 里的 `--claude-workers` 预检、忽略 `limit`、线程上限改回 `parser.error` 报错、去掉 `worker_limits` 必须是映射的检查，每一种都有测试失败。
  - 说明文字：`graph-runtime/README.md` 的版本和验证范围一句按这次实测改。v1.12 新加的初始化一段只列了 `status`、`events`、`run`，其实 `init` 以外的命令都这样，改写时写明锁文件的名字、本仓库 v1.10.1 遇到空文件的做法，以及在 Python 里 `Engine(路径)` 照旧会建表。v1.12 新加的“分页读取执行记录”一节插在演示步骤和“验证审批绑定”中间，后者开头的“上一步恢复后”就指到了分页一节上，现在挪到“运行回归测试”前面；那一节写“`--limit` 可选且须为正整数”，没写它只能和 `--after` 一起用，照着跑 `events --limit 100` 会报错，现在写明。v1.12 在设计参考里加的两条没有取：Temporal Python SDK 1.37.0 那一条的机制和 BJM 不同（见下面的加注）；“公开版 v1.10.1”是本仓库自己的上一版，改动记在这里。v1.12 留着作者 v1.10 的 ADK 一条和 `--claude-workers` 段落的旧写法，都用仓库 v1.10.1 的。`README.md` 的版本、下载按钮指向的版本、测试数、入口表和包内组件里图执行器的版本、两处 0.6.18 路径和署名改成这一版的，“可选的图执行器”一节加了一句分页的用法；v1.12 的测试说明是站在包的角度写的，链到仓库里没有的锚点 `#v112`，还去掉了“Python 3.10、Windows 和 macOS 没有实测”和“测试时命令搜索路径里只有模拟程序”两句，没有取，只改仓库那一段的版本和数目；令牌一句里的“演示这次在 Python 3.13 上连续跑了 30 次”，这一版重新跑了 30 次，仍写“这次”。`THIRD-PARTY-NOTICES.md` 保留 v1.10.1 加的 Google ADK 一条（v1.12 包里没有），新加一条写明 v1.11、v1.12 两节链接的项目只作参考。新加 `docs/releases/v1.12.1.md`。
  - 本仓库 v1.10.1 一节里“退出码仍是 2，库里什么也不写”和 `graph-runtime/README.md` 里“N 须是正整数，0 或负数报错退出，库里什么也不写”两句，只对已经 `init` 过的库成立：对空文件，v1.10.1 会先写进 24,576 字节、留下锁文件，再报错。这一版起这两句对空文件也成立。v1.10.1 一节是历史记录，没有改。
  - 复核时看到、没有改的：库的调用者用 `initialize=False` 打开一个不存在的路径，也报“not initialized; run init first”，不报“不存在”，不建任何文件，行为没有问题，命令行在这之前已经先查了路径；`--after 1_0`、`+3`、`-0` 这类写法 argparse 都当整数收下，无害。
- 测试：`tests/` 下 53 项（BJM 36 项、匿名对照材料 12 项、收票 5 项），`graph-runtime/tests/` 下 41 项（v1.9.1 的 33 项、v1.10 的 2 项、v1.10.1 的 3 项、v1.11 的 2 项、v1.12 的 1 项）。在 Linux 上用 Python 3.11、3.12、3.13 跑：`tests/` 各跑一遍，`graph-runtime/tests/` 各连跑五遍，都通过，没有跳过的项；演示在三个版本上各跑一遍，再在 3.13 上连续跑 30 次，都通过。跑的时候命令搜索路径上找不到真的 `claude`。其余实测见 `docs/releases/v1.12.1.md`。
- 回退和兼容：图执行器的数据库结构没有变，`user_version` 仍是 1。v1.10.1 不认 `events --after` 和 `--limit`，报用法错误，退出码 2，其余命令照旧能用；v1.10.1 遇到空文件仍会建表。用同一个库在 v1.10.1 和 v1.12.1 之间交替运行，两个方向各试一遍（两章演示图）：一版跑出失败，另一版 `retry` 后只补跑失败的一支，另一支沿用原结果；再跑一遍状态不变；一版发的令牌由另一版退回，被退回的令牌不能再批准；改稿后发新令牌，旧令牌被拒，新令牌由另一版批准；v1.12.1 分页读到的拼起来等于完整记录；两版不带参数的 `events` 输出逐字节相同；两个方向建出的库结构文字相同。在 Python 3.11、3.12、3.13 上都是 29 项核对全过；同样的核对在作者的 v1.10 和 v1.12.1、本仓库 v1.9.1 和 v1.12.1 之间也全过。v1.4 和 v1.8.1 建库并跑出失败的库，v1.12.1 能重试、续跑、分页，旧版能批准 v1.12.1 发的令牌。
- 没有验证的：v1.11 包没有交来，它的 SHA-256、它记的对照数字和 v1.11 与 v1.12 之间的双向续跑都没有核对；真实的 Claude Code 调用，只用了模拟程序；按 Ctrl-C 中断时分页会怎样，没有试；Windows、macOS，Python 3.9 和 3.10；Agent Skills 0.6.18 的官方源码 ZIP 和发布页、v1.11 和 v1.12 引的别的项目的发布页，这次都打不开，只用 git 核了标签、提交和日期，见下面的加注；13 份 `SKILL.md` 的改动只看了大意，没有逐条审读。

下面 v1.12、v1.11 两节是作者交来的 v1.12 包自带的版本记录，原文照录。v1.11 是作者在自己的 v1.10 上做的，v1.12 又在 v1.11 上做，两版都没有单独发布到本仓库；本仓库从 v1.10.1 直接到 v1.12.1。

## v1.12

2026-11-27。基于已交付的 v1.11 通用包（SHA-256 `bd92c40f04844f5fb1faafa56f9b92f5e95e367877d27ec14ef85f9f1ba50876`）。含 BJM v3.2、Agent Skills 0.6.18 和图执行器 v0.1.8。

- 参考 [公开版 v1.10.1](https://github.com/rumpelpalmour757-lgtm/bjm-portable/releases/tag/v1.10.1)（2026-11-26）的并发参数校验和测试修正。v1.12 在接触运行库前拒绝非正整数的线程上限。初始化图运行使用 `init`，其他命令要求库已初始化。Python 引擎原有构造方式仍可用，数据库版本为 1。
- 以空 SQLite 文件对照。v1.11 在报错前会写入 24,576 字节并生成锁文件。v1.12 下无效线程参数、无效事件游标、`status` 和 `events` 都退出且保留空文件，无锁文件。显式 `init` 能初始化同一个路径。并发回归按实际派发顺序核对限制。
- 核对 [Agent Skills 0.6.18 正式版](https://github.com/addyosmani/agent-skills/releases/tag/0.6.18)（2026-11-24）与 [达尔文 v3.0.2 正式版](https://github.com/alchaincyf/darwin-skill/releases/tag/v3.0.2)（2026-11-18，[提交 5a8e633a20ea5bb2bf8b9c697c6da04ad85740ba](https://github.com/alchaincyf/darwin-skill/commit/5a8e633a20ea5bb2bf8b9c697c6da04ad85740ba)）。本版资源及评估方法承接 v1.11。查阅 [LangGraph CLI 0.4.44](https://github.com/langchain-ai/langgraph/releases/tag/cli%3D%3D0.4.44)（2026-11-26）的部署命令更新和 [Agent-Kernel](https://arxiv.org/abs/2611.31727)（2026-11-24）的子图恢复方法。
- 从最终 ZIP 解压后，在 Linux 的 Python 3.12 和 3.13 上各通过 53 项 BJM 测试、38 项图执行器测试及模拟联审。v1.11 和 v1.12 可用同一 SQLite 文件双向续跑，核对了失败重试、结果复用、审批和事件分页。真实 Claude Code 调用尚未实测。

## v1.11

2026-11-26。基于已交付的 v1.10 通用包（SHA-256 `c1363aa64db806c6c96f4b6fe5a8d14b1324f09df21d04083abcad01df65c647`）。含 BJM v3.2、Agent Skills 0.6.18 和图执行器 v0.1.7。

- 采用 [Agent Skills 0.6.18 正式版](https://github.com/addyosmani/agent-skills/releases/tag/0.6.18)（2026-11-24，[提交 e997ac5b9a74eab332d5e9793bb38a38c8cfdd74](https://github.com/addyosmani/agent-skills/commit/e997ac5b9a74eab332d5e9793bb38a38c8cfdd74)）。仍含 26 个模块，13 份模块说明有更新，新增 16 份模块内共享清单。单独取出代码审查模块后，两份清单由 0/2 可读变为 2/2 可读。保留 MIT 许可和原始源码 ZIP，SHA-256 为 `d6bade14a2fec866be3c44bcba7ca5cd0817d7856bb10d175e4a9b7acc5a4065`。验收未执行上游脚本。
- 新增 `events --after ID [--limit N]`，从最后读到的事件 ID 续读。参考 [Temporal Python SDK 1.37.0](https://github.com/temporalio/sdk-python/releases/tag/1.37.0)（2026-11-25）在分页执行回执中保留运行标识的做法。用同一 SQLite 文件对照追加 3 条后的轮询，完整导出 132 条、30,292 字节，按游标导出 3 条、688 字节。分页顺序与完整记录一致。默认 `events` 输出和数据库结构沿用基线。
- 核对 [达尔文 v3.0.2 正式版](https://github.com/alchaincyf/darwin-skill/releases/tag/v3.0.2)（2026-11-18，[提交 5a8e633a20ea5bb2bf8b9c697c6da04ad85740ba](https://github.com/alchaincyf/darwin-skill/commit/5a8e633a20ea5bb2bf8b9c697c6da04ad85740ba)，[MIT 许可](https://github.com/alchaincyf/darwin-skill/blob/v3.0.2/LICENSE)），本轮沿用 v1.7 记录的评估方法。同期查阅 [Google ADK v2.15.1](https://github.com/google/adk-python/releases/tag/v2.15.1)（2026-11-25）、[OpenAI Agents SDK v0.26.0](https://github.com/openai/openai-agents-python/releases/tag/v0.26.0)（2026-11-24）和 [LangGraph 1.2.24](https://github.com/langchain-ai/langgraph/releases/tag/1.2.24)（2026-11-20）。
- 从最终 ZIP 解压后，在 Linux 的 Python 3.12 和 3.13 上各通过 53 项 BJM 测试、37 项图执行器测试和模拟联审。v1.10 与 v1.11 用同一 SQLite 文件双向续跑，核对了失败后重试、审批继续、分页和原接口兼容。真实 Claude Code 调用尚未实测。

以上 v1.12、v1.11 两节对照本仓库的版本线，补充几点（v1.12.1 加注）：

- “基于已交付的 v1.11 通用包（SHA-256 `bd92c40f…`）”“基于已交付的 v1.10 通用包”说的是作者那条线上的包。v1.11 包没有交来，也没进本仓库，这个 SHA-256 没有核对；v1.11 一节写的 v1.10 包摘要 `c1363aa6…`，和作者先前交来的 `bjm-portable-v1.10.zip` 算出的相同。日期 2026-11-26、2026-11-27 是两节自己记的。
- v1.11 一节的“图执行器 v0.1.7”是作者 v1.10 包里的 v0.1.6 加上事件分页，和本仓库 v1.10.1 的图执行器 v0.1.7（v0.1.6 加上两处输入检查）同名，不是同一样东西；v1.12 一节的“v0.1.8”是作者那条线上的再下一版。两边合在一起、又改过报错的打法，本仓库叫 v0.1.9，见上面 v1.12.1 一节。
- v1.12 第一条“参考公开版 v1.10.1（2026-11-26）的并发参数校验和测试修正”：链接是本仓库 v1.10.1 的发布页，复核时核到标签 v1.10.1 指向提交 2c192ed，发布于 2026-11-26 09:44:12（UTC），即台北时间 17:44，不是草稿，也不是预发布。v1.12 实际取的只有两样：命令行对 `--claude-workers` 的检查（提前到打开库以前，另加查 `--workers`），和 `test_claude_cli.py` 里按两个审查实际开跑的先后比较那处测试修正（写法不同，断言等价）。v1.10.1 在引擎里要求 `worker_limits` 是映射的检查、调度测试新加的三项和放宽到 30 秒的时限、说明的改写，v1.12 包里都没有；这一版里的这些来自本仓库。
- v1.12 第一条后半“在接触运行库前拒绝非正整数的线程上限……数据库版本为 1”和代码对得上。和 v1.10.1 比有两处不同：现在也查 `--workers`；v1.12 的报错是 argparse 的“usage: …”加“workflow.py: error: …”，这一版改回 `workflow: …`，见上面。v1.12 第二条“v1.12 下无效线程参数、无效事件游标、`status` 和 `events` 都退出且保留空文件，无锁文件。显式 `init` 能初始化同一个路径”，复核时在 v1.12 代码的副本上跑过，属实；空文件上的无效游标是被 `database is not initialized` 拦下的，没有走到游标检查；`init` 以外的命令都是这样，不只这几个。
- v1.12 第二条“v1.11 在报错前会写入 24,576 字节并生成锁文件”：v1.11 没有交来，跑不了。作者的 v1.10 和本仓库 v1.10.1 复核时都是这样：对空文件跑 `status`、`events`、`run`、`retry`、`approve`、`reject`、`edit`、`resolve` 和取值不对的 `run --workers 0`、`run --claude-workers 0`，都先把文件写成 24,576 字节、留下 `.lock`，再以退出码 2 退出。所以本仓库 v1.10.1 一节的“库里什么也不写”只对已经 `init` 过的库成立，见上面 v1.12.1 一节。第二条末尾的“并发回归按实际派发顺序核对限制”，就是本仓库 v1.10.1 已经做过的那处测试修正，合并时取 v1.10.1 的一份。
- v1.12 第四条和 v1.11 第四条：“53 项 BJM 测试”指 `tests/` 下全部 53 项，其中 BJM 36 项、匿名对照材料 12 项、收票 5 项。“38 项图执行器测试”是作者线上 v1.10 的 35 项加 v1.11、v1.12 的 3 项，和本仓库 v1.10.1 的 38 项（35 项加 v1.10.1 的 3 项）数目相同，不是同一批；“37 项”是 35 项加 v1.11 的 2 项。合并以后是 41 项。“从最终 ZIP 解压后”通过的测试和两处“双向续跑”是两节自己记的，v1.11 没有交来，v1.11 与 v1.10、v1.12 之间的续跑核不了；这次没有从作者的 ZIP 重新打包再跑。本仓库这次的测试和交替运行见上面 v1.12.1 一节和 `docs/releases/v1.12.1.md`，其中拿作者的 v1.10 和 v1.12 代替 v1.10 和 v1.11 做过一组交替运行，29 项核对全过。
- v1.11 第一条和 v1.12 第三条的 Agent Skills 0.6.18：复核时用 git 核到 0.6.18 是附注标签，指向提交 e997ac5b…，和这里写的相同，标签时间 2026-11-24 07:11:15（UTC），即台北时间 15:11，日期对得上；ZIP 的 SHA-256 也对得上。“13 份模块说明有更新，新增 16 份模块内共享清单”数目属实，16 份里有两份（`orchestration-patterns.md`、`testing-patterns.md`）是模式说明，不是清单。“单独取出代码审查模块后，两份清单由 0/2 可读变为 2/2 可读”属实：0.6.17 的 `code-review-and-quality/SKILL.md` 指向模块外的 `../../references/`，0.6.18 改成指向模块里的 `references/shared/`，两份都在；整包使用时两版都读得到。“验收未执行上游脚本”是 v1.11 自己说的，无从核对；这次也没有运行。
- 达尔文 v3.0.2：复核时用 git 核到附注标签指向提交 5a8e633a…，标签时间 2026-11-18 06:10:59（UTC），即台北时间 14:10，日期对得上，那一版的树里有 MIT 的 `LICENSE`。Agent Skills 0.6.18 和达尔文 v3.0.2 的发布页这次都打不开，“正式版”没有核到。“本版资源及评估方法承接 v1.11”“本轮沿用 v1.7 记录的评估方法”是两节自己的说法，无从核对。
- v1.11 第二条“参考 Temporal Python SDK 1.37.0（2026-11-25）在分页执行回执中保留运行标识的做法”：复核时用 git 核到标签 1.37.0 指向提交 83f91fd（“Prepare release 1.37.0 (#2161)”），提交时间 2026-11-24 14:58（UTC−8），即台北时间 2026-11-25 06:58，上游 `CHANGELOG.md` 记的是 2026-11-24。读了上游版本记录从 1.36.1 到 1.37.0 的改动，和“分页”“回执”对得上的只有一条：工作流任务的完成和失败消息里设 `resource_id` 为 `workflow:<工作流 ID>`，分页提交时每一页都设，让代理不用解码任务令牌就能认出是哪个工作流。和这里的说法有三处出入：1.37.0 起才设这个字段，不是“保留”；标识是工作流 ID（活动任务一般也用工作流 ID，单独运行的活动才用活动 ID；工作者心跳用工作者的分组键），不是 Temporal 的运行 ID；分页的是工作者交给服务端的完成消息，不是读执行记录。BJM 的 `events --after` 按事件 ID 续读本地 SQLite 里的事件，每条事件本来就带运行 ID、节点 ID 和事件 ID，机制不同，本仓库不写成“参考”，只算同期看过，说明里也没有收这一条。发布页这次打不开。
- v1.11 第二条“完整导出 132 条、30,292 字节，按游标导出 3 条、688 字节”是 v1.11 自己量的，没写用的是哪张图、什么场景，没有复现。“分页顺序与完整记录一致。默认 `events` 输出和数据库结构沿用基线”属实：不带参数时查询语句没有变，表结构没有动；复核时一边跑 40 个节点、3 个线程的图，一边按每页 3 条轮询，拼起来和完整记录相同，没有重复，也没有缺漏。
- v1.11 第三条和 v1.12 第三条的其余几项：Google ADK v2.15.1 的标签指向提交 4798b7f，提交时间 2026-11-24 12:24（UTC−8），即台北时间 2026-11-25 04:24；OpenAI Agents SDK v0.26.0 的标签指向 0ad2d63，提交时间 2026-11-24 03:06（UTC），即台北时间 11:06；LangGraph 1.2.24 的标签指向 58a6e1c，提交时间 2026-11-20 01:00（UTC），即台北时间 09:00；LangGraph CLI 0.4.44 的标签 `cli==0.4.44` 指向 3e3dbd4，提交时间 2026-11-25 15:48（UTC−5），即台北时间 2026-11-26 04:48，和 0.4.43 之间改的是部署相关的几处，“部署命令更新”的说法对得上。这几样都是用 git 核的标签和日期，和这里写的对得上，发布页都没打开。arXiv 2611.31727 确有其文，题目是“fork() for Agents: Agent Kernel for Non-blocking LLM Orchestration”，系统叫 Agent-Kernel，是预印本，只有 v1，提交于 2026-11-24 00:33（UTC），即台北时间同日 08:33；它的子图恢复（Sub-Graph Recovery）在失败时只重置失败节点的后代、保留已经完成的兄弟节点，“子图恢复方法”的说法对得上。BJM 的 `retry` 本来就只补跑失败的分支、沿用已完成的分支，这几样这一版都没有据此改动。

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
