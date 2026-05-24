#!/usr/bin/env python3
"""CryptoGhost - Script de backup do PostgreSQL."""

import argparse
import subprocess
from datetime import datetime
from pathlib import Path

BACKUP_DIR = Path("backups")


def main() -> None:
    parser = argparse.ArgumentParser(description="Backup CryptoGhost PostgreSQL")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", default="5432")
    parser.add_argument("--user", default="cryptoghost")
    parser.add_argument("--db", default="cryptoghost")
    args = parser.parse_args()

    BACKUP_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = BACKUP_DIR / f"cryptoghost_backup_{timestamp}.sql"

    cmd = [
        "pg_dump",
        f"--host={args.host}",
        f"--port={args.port}",
        f"--username={args.user}",
        "--format=plain",
        args.db,
    ]

    with open(output, "w") as f:
        subprocess.run(cmd, stdout=f, check=True)

    print(f"Backup salvo em: {output}")


if __name__ == "__main__":
    main()
