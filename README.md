# 问天讲师团 · 学业支持资料库（hoa.moe 镜像）

哈尔滨工业大学未来技术学院「问天讲师团」的课程复习资料仓库，同时是 [hoa.moe](https://hoa.moe) 站点「站外资料」板块的数据源。

> 原始仓库：<https://gitee.com/jacobbbbb/lecturer-group>
> 本仓库由 HITSZ 开源技术协会维护，内容以原始仓库为准，会定期自动同步。

站内入口：<https://hoa.moe/resources/wentian>

## 内容一览

| 科目 | 资料 | 形式 | 适用阶段 |
| --- | --- | --- | --- |
| 离散数学 | 期末复习讲义（final version） | PDF | 期末 |
| 理论力学B | 期中题型总结、期末题型总结 | PDF | 期中、期末 |
| 机械工程制图 | 复习讲座 PPT、复习讲义（简化画法 · 尺寸标注 · 零件图与装配体）、三讲录播 | PPTX / DOCX / MP4 | 期末 |
| C 语言 | 2025 秋程设基础期中回忆版真题（多选题、编程题、改错题） | DOCX | 期中 |

## 目录结构

```
hoa-wentian-lecturer-group/
├── README.md               # 本文件
├── LICENSE                 # 木兰宽松许可证，第 2 版
├── resources.json          # 站点读取的元信息 + 未入库文件的原地址清单
├── docs/                   # 讲师团原始说明
├── c语言/                   # 程设基础真题与讲义
├── 机械工程制图/             # 复习讲座 PPT、讲义
│   └── 讲座cut/             # 讲座录播视频（P1 标准件和常用件 / P2 零件图 / P3 装配体）
├── 理论力学B/                # 期中、期末题型总结
├── 离散数学/                 # 期末复习讲义
└── scripts/
    ├── sync-gitee.py       # 从 Gitee 原始仓库同步
    └── update-worktree.py  # 重新生成 worktree 分支的文件清单
```

## 为什么要有这个镜像

Gitee 公开可读，但**大文件的 raw 直链会返回 403**，只靠原始仓库，站内无法给出稳定的下载入口。
本仓库把资料镜像成普通 Git 仓库，站点为每个文件生成一条经 `gh.hoa.moe` 网关加速的直链，点开即下。

## 自动化链路

```
Gitee 原始仓库
        │  .github/workflows/sync-gitee.yml（每日定时）
        │  scripts/sync-gitee.py
        ▼
本仓库 main 分支 ──push──▶ GitHub Actions
                                │  scripts/update-worktree.py
                                ▼
                          worktree 分支（worktree.json）
                                │
                                ▼
                    hoa.moe 构建时 scripts/fetch-resources.mjs
                                │
                                ▼
                       hoa.moe/resources/wentian
```

- `sync-gitee.yml` 每日拉取 Gitee 最新内容，有变化才提交；
- 提交后 `update-worktree.yml` 自动重新生成 `worktree` 分支；
- 站点构建时读取该分支的清单，渲染资料树。

单文件超过 100 MiB（GitHub 硬限制）不入库，在 `resources.json` 中登记原始仓库地址，站内点击跳转。

### 本地同步

```bash
python3 scripts/sync-gitee.py --dry-run   # 只看会变什么
python3 scripts/sync-gitee.py --commit    # 同步并提交推送
```

## 使用与转载

课件（PPTX / DOCX）可以直接下载后修改成自己的笔记版本，但请保留原作者与出处。资料由问天讲师团成员原创整理，版权所有 © 2026 问天讲师团，以[木兰宽松许可证，第 2 版](LICENSE)（Mulan PSL v2）授权：

- 可以自由复制、使用、修改和分发，包括用于商业用途；
- 分发时需保留本许可证、版权声明与修改说明；
- 本资料按「现状」提供，不保证覆盖全部考点，也不对使用结果承担责任；
- 转载或二次整理时请注明来源：**问天讲师团（哈尔滨工业大学未来技术学院）**。

讲师团原始说明见 [`docs/问天讲师团说明.md`](docs/问天讲师团说明.md)，其中包含目录规范、提交信息约定与协作流程。

## 反馈与联系

- 发现错误、缺页或打不开的文件，欢迎在 [Gitee 原始仓库](https://gitee.com/jacobbbbb/lecturer-group) 提 Issue；
- 想补充自己科目的资料，欢迎按原始仓库的协作规范提交 PR，镜像会自动同步；
- 负责人：廖敬远（问天讲师团 25 级负责人）。

## 致谢

资料中的题目与知识点均来自课程教学，版权归原作者与学校所有，本仓库仅作学习交流使用；如涉及侵权，请联系删除。
