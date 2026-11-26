# 第三方组件与许可范围

本仓库按 MIT 许可发布，全文见 [LICENSE](LICENSE)，版权人 Celeste。这份文件说明哪些东西是别人的，继续按它们自己的许可。

## 许可范围

- 根目录的 `LICENSE` 适用于本仓库里版权人自己的内容：`SKILL.md`、`README.md`、`CHANGELOG.md`、`references/`、`scripts/`、`tests/`、`examples/`、`graph-runtime/` 和 `docs/images/`（README 用的图标和题图）。
- 下面列出的第三方组件不算进版权人的版权声明，各按自己的许可，版权归各自的权利人。

## 包里带的第三方组件

| 组件 | 版权行 | 包里的哪些文件 | 许可文件 |
|:-----|:-------|:---------------|:---------|
| [Agent Skills](https://github.com/addyosmani/agent-skills) 0.6.17 | Copyright (c) 2025 Addy Osmani | `vendor/agent-skills-0.6.17/`（展开目录）和 `vendor/agent-skills-0.6.17.zip`（标签源码 ZIP，原样保留） | `vendor/agent-skills-0.6.17/LICENSE`，ZIP 里也有同一份 |

- 标签源码 ZIP 的 SHA-256：`f2d2dfca1ed15b78364623c6d303c626a0518184136520644ec7b15d4ba3aeb0`；ZIP 注释里记的提交是 `8c99fa36d90068c82d547f7c12a9d67a3e95f4ee`。
- 展开目录和 ZIP 的差别：原包里的符号链接 `.opencode/skills -> ../skills/` 只在 ZIP 里，展开目录没有 `.opencode/`。其余文件逐字节相同；`hooks/` 下 7 个、`skills/idea-refine/scripts/` 下 1 个和 `skills/accessibility-engineering/scripts/` 下 1 个 shell 脚本照 ZIP 保留可执行位。
- `references/bjm-v3.2.md` 参考 Agent Skills 改写，出处见那一页“改编依据”一节。那一节写的是当时依据的 `agent-skills-main.zip` 快照（0.6.15 前后的 main 分支）；本仓库带的是 0.6.17 标签版。
- 再分发 `vendor/` 下的文件时，请把 Agent Skills 的版权行和许可声明一起带上。

Agent Skills 的许可声明原文如下，配上表里的版权行：

```text
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 只作参考、没有带进来的

- `graph-runtime/README.md`“设计参考”一节列的 Google ADK、LangGraph、Temporal、OpenAI 和论文只是链接，仓库里没有它们的代码。
- `references/bjm-v3.2.md` 开头的“方法来源”是一条公开讨论的链接。
- `references/blind-review.md` 末尾链接了达尔文（[alchaincyf/darwin-skill](https://github.com/alchaincyf/darwin-skill)）v3.0.0、v3.0.1 和 v3.0.2 的发布页。`scripts/blind_review.py` 参考了它成对盲评的做法和它发现的路径泄露问题；`scripts/check_review_votes.py`（v1.7 起）参考了 v3.0.2 一次列出缺票、只向没交有效票的评委补收的做法。两个脚本都是另外写的（收票脚本照 v1.7 的版本记录是 BJM 自己实现的，这次没有联网和达尔文的代码逐行对照），仓库里没有达尔文的代码或文本。
- `CHANGELOG.md` 的 v1.6 和 v1.7 两节链接了 [Temporal Google GenAI 1.0.0](https://github.com/temporalio/ai-integrations/releases/tag/python/google_genai/v1.0.0) 和 [OpenAI Agents SDK v0.25.0](https://github.com/openai/openai-agents-python/releases/tag/v0.25.0) 的发布页。图执行器参考了前者把必须改输入的错误和可以重试的故障分开、后者减少重复计算输入指纹的思路。照这两节的记录，代码是按 BJM 自己的调度器另外写的；相关改动只有几行（`engine.py` 的 `InputRejected` 和派发前才算指纹），这次没有联网和上游逐行对照，仓库里没有它们的代码。
- `CHANGELOG.md` 的 v1.9 一节和 `graph-runtime/README.md` 链接了 [OpenAI Agents SDK v0.25.0](https://github.com/openai/openai-agents-python/releases/tag/v0.25.0) 的发布页和 [Temporal 的 OSCAR 案例](https://temporal.io/blog/building-a-reliable-ai-agent-with-oscar)。图执行器的 `reject` 参考了把人工决定和待审版本一起保存的思路：批准和退回共用 `engine.py` 里的 `_decide_approval`，几十行，按 BJM 自己的审批节点写，仓库里没有这两个项目的代码；这次没有联网和上游逐行对照，两个链接和它们的日期也没有核对。退回按送审内容对照（`_approval_content`、`_rejected_revision`，以及 `run` 和 `_decide_approval` 里用到它们的几行）是本仓库 v1.9.1 复核时另加的，不是从这两个项目参考来的。
- `CHANGELOG.md` 的 v1.10 和 v1.10.1 两节、`graph-runtime/README.md` 链接了 [Google ADK v2.15.0](https://github.com/google/adk-python/releases/tag/v2.15.0) 的发布页和[提交 5e4f0e1](https://github.com/google/adk-python/commit/5e4f0e18cfe869a183901192f92c86d7574881b0)。图执行器的 `--claude-workers` 参考了它给并行工作节点另设上限的思路；`engine.py` 里按操作计数的几行（`run()` 的 `worker_limits` 和 `in_flight`）是按 BJM 自己的调度器写的，仓库里没有 ADK 的代码。这次用 git 核了标签和提交，读了那个提交的说明和文档改动，没有和 ADK 的代码逐行对照，发布页没有打开。v1.10 一节还链接了 LangGraph 1.2.24、Temporal 的合作生态文章、OpenAI Agents SDK v0.25.0、Agent Skills 0.6.17 和达尔文 v3.0.2，照那一节的说法只是同期看过或核对过，这一版没有据此改动。
- `graph-runtime/README.md` 和 `CHANGELOG.md` 链接了 Claude Code 的文档（子代理、命令行参数、非交互运行）。Claude Code 是使用者在本机另外安装的程序，包里不带；`graph-runtime/claude_review.py` 只在使用者运行 `run --claude` 时把它当作外部命令启动，没有拷贝它的代码或文档。
