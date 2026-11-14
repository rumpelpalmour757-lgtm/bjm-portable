# 版本记录

日期按台北时间（UTC+8）记。

## v1.4.1

2026-11-15。基于 v1.4，协议、脚本、图执行器和 Agent Skills 都没有变，测试照旧全过。

- `SKILL.md` 的 description 加了一句：中文小说的写作、续写、改稿和审稿用小说写作工坊（novel-workshop），不用本技能。两个技能装在同一个宿主里时，免得抢同一个请求。会不会照这句分开，没有在宿主里实测。
- `references/bjm-v3.2.md`“改编依据”一节写明：当时依据的是 0.6.15 前后的 main 分支快照；表里的路径在 0.6.16 里都还在，其中 6 个改过，协议正文没有据此改写。
- 仓库公开时加了 `LICENSE`（MIT，版权人 Celeste）、`THIRD-PARTY-NOTICES.md`、`.gitignore`、`.gitattributes`，`README.md` 末尾加了“获取和许可”；`vendor/` 下 8 个 shell 脚本照上游 ZIP 恢复可执行位。

## v1.4

2026-11-15。基于 v1.3，保留 BJM v3.2 和图执行器 v0.1。Agent Skills 从 0.6.15 升至 [0.6.16](https://github.com/addyosmani/agent-skills/releases/tag/0.6.16)。仍含 25 个模块。更新了规格演进、文档漂移核对、前端验证及其他上游工程方法。

官方标签源码 ZIP 保留完整字节。SHA-256 为 `6f0304fe35188526f27541e913b9aeff60663ae076c04c65090df12875aeec48`。MIT 许可证随 ZIP 和可读目录提供。

验收覆盖 36 项 BJM 测试、6 项图执行器测试、本地模拟联审、25 个模块的逐字节比对及索引检查。v1.3 可独立使用，图执行器和数据格式相同。
