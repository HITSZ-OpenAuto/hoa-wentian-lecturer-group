#!/usr/bin/env python3
"""从 Gitee 原始仓库同步资料到本仓库。

原始仓库：https://gitee.com/jacobbbbb/lecturer-group.git
Gitee 公开可读，GitHub Actions 的 runner 能直接访问，因此本仓库的同步可以完全自动化。

用法：

    python3 scripts/sync-gitee.py                 # 同步并更新清单
    python3 scripts/sync-gitee.py --commit        # 同步后提交并推送
    python3 scripts/sync-gitee.py --dry-run       # 只看会变什么

参数：

    --repo <path>      仓库根目录（默认脚本所在仓库）
    --source <url>     Gitee 仓库地址
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# GitHub 单文件硬限制 100 MiB，超过一律不入库
MIRROR_MAX_SIZE = 100 * 1024 * 1024

# 原始仓库的文件改名后放进 docs/，
# 避免和本仓库自身的 README.md / LICENSE 大小写冲突
RENAME = {
    "README.md": "docs/问天讲师团说明.md",
}

# 仓库自身文件，不属于资料内容
REPO_OWNED = {"README.md", "LICENSE", "resources.json", ".gitignore", ".gitattributes"}

# 仓库自身的目录，不参与同步
REPO_OWNED_DIRS = {"scripts", ".github", ".git", "history"}

DEFAULT_SOURCE = "https://gitee.com/jacobbbbb/lecturer-group.git"


def log(message: str) -> None:
    print(message, flush=True)


def run(args: list[str], cwd: str | None = None) -> str:
    result = subprocess.run(args, check=True, capture_output=True, text=True, cwd=cwd)
    return result.stdout.strip()


def human(size: int) -> str:
    value = float(size)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} GB"


def target_path(path: str) -> str:
    return RENAME.get(path, path)


def is_repo_owned(relative: str) -> bool:
    """判断仓库内相对路径是否属于仓库自身（脚本、配置、.git 等）。"""
    head = relative.split("/")[0]
    return relative in REPO_OWNED or head in REPO_OWNED_DIRS


def collect(source_dir: Path) -> list[dict]:
    """列出源仓库的文件，并用 git blob sha 作为内容指纹。"""
    entries = []
    for path in sorted(source_dir.rglob("*")):
        if not path.is_file():
            continue
        relative = str(path.relative_to(source_dir))
        if relative.startswith(".git/"):
            continue
        # 仓库自身的文件不参与同步；但被改名的文件（如 README.md）要同步
        if relative in REPO_OWNED and relative not in RENAME:
            continue
        entries.append(
            {
                "path": relative,
                "size": path.stat().st_size,
                "mtime": int(path.stat().st_mtime),
                "sha": blob_sha(source_dir, relative),
            }
        )
    return entries


def blob_sha(source_dir: Path, relative: str) -> str:
    """取文件内容的 git blob sha，用于精确判断文件是否变化。"""
    output = run(
        ["git", "-C", str(source_dir), "hash-object", "--", relative]
    )
    return output.strip()


def clone_source(source: str, destination: Path) -> None:
    """克隆原始仓库。

    Gitee 的浅克隆不稳定（大仓库容易传输中断），因此浅克隆失败后
    自动降级为完整克隆，并对两种方式都做重试。
    """
    attempts = [
        ["git", "clone", "--depth", "1", source, str(destination)],
        ["git", "clone", source, str(destination)],
    ]

    last_error = ""
    for command in attempts:
        for attempt in range(1, 3):
            log(f"  克隆尝试 {attempt}：{' '.join(command[1:3])} …")
            result = subprocess.run(command, capture_output=True, text=True)
            if result.returncode == 0:
                return
            last_error = (result.stderr or result.stdout).strip().splitlines()[-1:]
            log(f"    ! 失败：{last_error}")
            shutil.rmtree(destination, ignore_errors=True)
            time.sleep(attempt * 3)

    raise RuntimeError(f"克隆失败：{source}（{last_error}）")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parent.parent))
    parser.add_argument("--source", default=DEFAULT_SOURCE)
    parser.add_argument(
        "--source-dir",
        default=None,
        help="直接使用已有的本地克隆（不联网），用于网络不佳或离线场景",
    )
    parser.add_argument("--commit", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    # 资料内容与组织课程仓一致，直接放在仓库根目录
    content_root = repo

    workdir = Path(tempfile.mkdtemp(prefix="wentian-sync-"))
    try:
        if args.source_dir:
            source_dir = Path(args.source_dir).resolve()
            if not (source_dir / ".git").exists():
                raise RuntimeError(f"不是 git 仓库：{source_dir}")
            log(f"→ 使用本地克隆 {source_dir}")
        else:
            log(f"→ 拉取 {args.source}")
            clone_source(args.source, workdir / "source")
            source_dir = workdir / "source"

        entries = collect(source_dir)

        mirrored = [item for item in entries if item["size"] <= MIRROR_MAX_SIZE]
        external = [item for item in entries if item["size"] > MIRROR_MAX_SIZE]
        log(
            f"  共 {len(entries)} 个文件：入库 {len(mirrored)} 个"
            f"（{human(sum(i['size'] for i in mirrored))}），"
            f"仅登记原地址 {len(external)} 个"
        )

        if not args.dry_run:
            for item in mirrored:
                source = source_dir / item["path"]
                target = content_root / target_path(item["path"])
                target.parent.mkdir(parents=True, exist_ok=True)
                # 内容指纹一致就跳过，避免重复拷贝大文件
                if target.exists() and blob_sha(repo, target_path(item["path"])) == item["sha"]:
                    continue
                log(f"  更新 {item['path']}")
                shutil.copyfile(source, target)

            # 清理源端已删除的文件
            wanted = {target_path(item["path"]) for item in mirrored}
            for path in sorted(content_root.rglob("*"), reverse=True):
                if not path.is_file():
                    continue
                relative = str(path.relative_to(content_root))
                if relative in wanted or is_repo_owned(relative):
                    continue
                log(f"  - 删除失效文件 {relative}")
                path.unlink()

            # 未入库文件的原地址
            external_entries = []
            for item in external:
                external_entries.append(
                    {
                        "path": item["path"],
                        "name": Path(item["path"]).name,
                        "size": item["size"],
                        "time": item["mtime"],
                        "url": f"{args.source.removesuffix('.git')}/raw/master/"
                        + "/".join(urllib_parse(item["path"])),
                        "note": "体积超过 GitHub 单文件限制，保留在原始仓库下载",
                    }
                )

            meta_path = repo / "resources.json"
            meta = json.loads(meta_path.read_text("utf-8")) if meta_path.exists() else {}
            meta["external"] = external_entries
            meta["policy"] = {
                "mirroredMaxSize": MIRROR_MAX_SIZE,
                "mirroredCount": len(mirrored),
                "externalCount": len(external),
                "mirroredSize": sum(i["size"] for i in mirrored),
                "externalSize": sum(i["size"] for i in external),
                "syncedAt": int(time.time()),
            }
            meta_path.write_text(
                json.dumps(meta, ensure_ascii=False, indent=2) + "\n", "utf8"
            )
            log(f"→ 已更新 {meta_path.relative_to(repo)}")

        if args.commit and not args.dry_run:
            run(["git", "add", "-A"], cwd=str(repo))
            changed = (
                subprocess.run(
                    ["git", "diff", "--staged", "--quiet"], cwd=str(repo)
                ).returncode
                != 0
            )
            if not changed:
                log("没有变更，跳过提交")
            else:
                run(
                    ["git", "commit", "-m", "chore: 同步 Gitee 原始仓库"],
                    cwd=str(repo),
                )
                run(["git", "push", "origin", "HEAD:main"], cwd=str(repo))
                log("→ 已推送到 main")
    finally:
        shutil.rmtree(workdir, ignore_errors=True)

    return 0


def urllib_parse(path: str) -> str:
    from urllib.parse import quote

    return quote(path)


if __name__ == "__main__":
    sys.exit(main())
