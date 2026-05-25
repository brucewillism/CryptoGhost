#!/usr/bin/env python3
"""CryptoGhost — Cria banco, extensões e executa migrations Alembic."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from getpass import getpass
from pathlib import Path
from urllib.parse import quote_plus

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

INIT_SQL = ROOT / "database" / "init.sql"
ALEMBIC_INI = ROOT / "backend" / "alembic.ini"


def get_password(args: argparse.Namespace) -> str:
    if args.password:
        return args.password
    if os.environ.get("PGPASSWORD"):
        return os.environ["PGPASSWORD"]
    if os.environ.get("CRYPTOGHOST_DB_PASSWORD"):
        return os.environ["CRYPTOGHOST_DB_PASSWORD"]
    return getpass(f"Senha PostgreSQL do usuário '{args.user}': ")


def run_psql(user: str, password: str, database: str, sql: str) -> None:
    psql = os.environ.get(
        "PSQL_PATH",
        r"C:\Program Files\PostgreSQL\18\bin\psql.exe",
    )
    if not Path(psql).exists():
        psql = "psql"

    env = {**os.environ, "PGPASSWORD": password}
    result = subprocess.run(
        [psql, "-U", user, "-h", "127.0.0.1", "-p", "5432", "-d", database, "-v", "ON_ERROR_STOP=1", "-c", sql],
        env=env,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())


def run_psql_file(user: str, password: str, database: str, filepath: Path) -> None:
    psql = os.environ.get(
        "PSQL_PATH",
        r"C:\Program Files\PostgreSQL\18\bin\psql.exe",
    )
    if not Path(psql).exists():
        psql = "psql"

    env = {**os.environ, "PGPASSWORD": password}
    result = subprocess.run(
        [psql, "-U", user, "-h", "localhost", "-p", "5432", "-d", database, "-v", "ON_ERROR_STOP=1", "-f", str(filepath)],
        env=env,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())


def database_exists(user: str, password: str, db_name: str) -> bool:
    psql = os.environ.get("PSQL_PATH", r"C:\Program Files\PostgreSQL\18\bin\psql.exe")
    if not Path(psql).exists():
        psql = "psql"
    env = {**os.environ, "PGPASSWORD": password}
    result = subprocess.run(
        [psql, "-U", user, "-h", "localhost", "-d", "postgres", "-tAc",
         f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'"],
        env=env,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0 and result.stdout.strip() == "1"


def update_env_file(db_user: str, db_password: str, db_name: str) -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return

    async_url = f"postgresql+asyncpg://{db_user}:{db_password}@localhost:5432/{db_name}"
    sync_url = f"postgresql://{db_user}:{db_password}@localhost:5432/{db_name}"
    lines = env_path.read_text(encoding="utf-8").splitlines()
    updated: list[str] = []
    for line in lines:
        if line.startswith("CRYPTOGHOST_DATABASE_URL="):
            updated.append(f"CRYPTOGHOST_DATABASE_URL={async_url}")
        elif line.startswith("CRYPTOGHOST_DATABASE_URL_SYNC="):
            updated.append(f"CRYPTOGHOST_DATABASE_URL_SYNC={sync_url}")
        else:
            updated.append(line)
    env_path.write_text("\n".join(updated) + "\n", encoding="utf-8")
    print(f"[OK] .env atualizado para usuário {db_user}")


def run_migrations() -> None:
    env = {**os.environ, "PYTHONPATH": str(ROOT)}
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "-c", str(ALEMBIC_INI), "upgrade", "head"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    print("[OK] Alembic migrations aplicadas (head)")


def main() -> int:
    parser = argparse.ArgumentParser(description="Setup PostgreSQL CryptoGhost")
    parser.add_argument("--user", default="bruce", help="Usuário PostgreSQL")
    parser.add_argument("--password", default="", help="Senha PostgreSQL")
    parser.add_argument("--database", default="cryptoghost", help="Nome do banco")
    parser.add_argument("--skip-env-update", action="store_true")
    args = parser.parse_args()

    password = get_password(args)
    print(f"[INFO] Conectando como {args.user}...")

    try:
        run_psql(args.user, password, "postgres", "SELECT 1")
        print("[OK] Conexão PostgreSQL")
    except Exception as exc:
        print(f"[FAIL] Não foi possível conectar: {exc}")
        return 1

    if not database_exists(args.user, password, args.database):
        try:
            run_psql(args.user, password, "postgres", f"CREATE DATABASE {args.database} OWNER {args.user}")
            print(f"[OK] Banco '{args.database}' criado")
        except Exception as exc:
            print(f"[FAIL] Criar banco: {exc}")
            return 1
    else:
        print(f"[OK] Banco '{args.database}' já existe")

    if INIT_SQL.exists():
        try:
            run_psql_file(args.user, password, args.database, INIT_SQL)
            print("[OK] Extensões instaladas (uuid-ossp, pgcrypto, vector)")
        except Exception as exc:
            if "already exists" not in str(exc).lower():
                print(f"[WARN] Extensões: {exc}")

    if not args.skip_env_update:
        update_env_file(args.user, password, args.database)

    encoded = quote_plus(password)
    os.environ["CRYPTOGHOST_DATABASE_URL"] = (
        f"postgresql+asyncpg://{db_user}:{encoded}@127.0.0.1:5432/{db_name}"
    )
    os.environ["CRYPTOGHOST_DATABASE_URL_SYNC"] = (
        f"postgresql://{db_user}:{encoded}@127.0.0.1:5432/{db_name}"
    )

    try:
        run_migrations()
    except Exception as exc:
        print(f"[FAIL] Migrations: {exc}")
        return 1

    print("\n[OK] CryptoGhost database pronto!")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
