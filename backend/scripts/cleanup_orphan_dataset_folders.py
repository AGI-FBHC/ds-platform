"""清理 backend/storage/datasets/ 中存在但数据库无对应记录的文件夹。

用法:
    # 仅扫描，列出孤儿目录（不删除）
    python -m scripts.cleanup_orphan_dataset_folders

    # 实际删除（带交互确认）
    python -m scripts.cleanup_orphan_dataset_folders --apply

    # 跳过确认直接删除
    python -m scripts.cleanup_orphan_dataset_folders --apply --yes
"""
import argparse
import os
import shutil
import sys

# 让脚本以 `python -m scripts.xxx` 或 `python scripts/xxx.py` 跑都能 import app.*
BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from app.config import settings  # noqa: E402
from app.models import SessionLocal  # noqa: E402
from app.models.dataset import Dataset  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402

DATASET_DIR_PREFIX = "dataset_"


def collect_db_storage_paths() -> set[str]:
    """读取 datasets 表中所有 storage_path。"""
    engine = create_engine(settings.database_url)
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT storage_path FROM datasets WHERE storage_path IS NOT NULL AND storage_path <> ''")
        ).fetchall()
    return {row[0] for row in rows}


def list_dataset_folders(storage_root: str) -> set[str]:
    """列出 datasets/ 下所有 dataset_* 命名的子目录名。"""
    if not os.path.isdir(storage_root):
        return set()
    return {
        name
        for name in os.listdir(storage_root)
        if name.startswith(DATASET_DIR_PREFIX)
        and os.path.isdir(os.path.join(storage_root, name))
    }


def folder_size(path: str) -> int:
    total = 0
    for root, _dirs, files in os.walk(path):
        for f in files:
            try:
                total += os.path.getsize(os.path.join(root, f))
            except OSError:
                pass
    return total


def fmt_bytes(n: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    v = float(n)
    i = 0
    while v >= 1024 and i < len(units) - 1:
        v /= 1024
        i += 1
    return f"{v:.1f} {units[i]}" if i else f"{int(v)} {units[i]}"


def main() -> int:
    parser = argparse.ArgumentParser(description="清理 datasets/ 中没有 DB 记录的孤儿目录")
    parser.add_argument("--apply", action="store_true", help="实际删除（默认仅扫描）")
    parser.add_argument("--yes", action="store_true", help="跳过交互确认直接删除")
    args = parser.parse_args()

    storage_root = os.path.join(BACKEND_ROOT, "storage", "datasets")
    print(f"扫描目录: {storage_root}")

    db_paths = collect_db_storage_paths()
    print(f"数据库中 storage_path 记录数: {len(db_paths)}")

    fs_folders = list_dataset_folders(storage_root)
    print(f"文件系统中 dataset_* 目录数: {len(fs_folders)}")

    orphans = sorted(fs_folders - db_paths)
    if not orphans:
        print("✓ 没有孤儿目录，跳过清理")
        return 0

    print(f"\n发现 {len(orphans)} 个孤儿目录（数据库无记录）:")
    total_bytes = 0
    for name in orphans:
        path = os.path.join(storage_root, name)
        size = folder_size(path)
        total_bytes += size
        print(f"  - {name}  ({fmt_bytes(size)})")

    print(f"\n预计释放空间: {fmt_bytes(total_bytes)}")

    if not args.apply:
        print("\n[DRY-RUN] 未执行删除。如需实际删除，请加 --apply 参数")
        return 0

    if not args.yes:
        try:
            ans = input(f"\n确认删除以上 {len(orphans)} 个目录？[y/N] ").strip().lower()
        except EOFError:
            ans = ""
        if ans != "y":
            print("已取消")
            return 0

    deleted = 0
    failed = 0
    for name in orphans:
        path = os.path.join(storage_root, name)
        try:
            shutil.rmtree(path)
            deleted += 1
            print(f"  ✓ 已删除 {name}")
        except Exception as exc:
            failed += 1
            print(f"  ✗ 删除失败 {name}: {exc}", file=sys.stderr)

    # 删除后 Sanity check
    SessionLocal().close()
    print(f"\n完成：删除 {deleted} 个，失败 {failed} 个")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())