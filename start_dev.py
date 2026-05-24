#!/usr/bin/env python3
"""
CryptoGhost v5 - Script inteligente de inicialização para desenvolvimento.

Uso:
    python start_dev.py              # Infra Docker + backend/frontend/celery locais (hot reload)
    python start_dev.py --all-docker # Stack completa via docker-compose.dev.yml
    python start_dev.py --check-only # Apenas validações
"""

from __future__ import annotations

import argparse
import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

try:
    import httpx
except ImportError:
    httpx = None  # type: ignore

ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))
os.environ.setdefault("PYTHONPATH", str(ROOT))

COMPOSE_FILE = "docker-compose.dev.yml"
PROCESSES: list[subprocess.Popen] = []


def log(tag: str, msg: str, ok: bool | None = None) -> None:
    prefix = {"ok": "[OK]", "fail": "[FAIL]", "info": "[INFO]", "wait": "[WAIT]"}.get(
        "ok" if ok is True else "fail" if ok is False else "info"
    )
    print(f"{prefix} [{tag}] {msg}", flush=True)


def run_cmd(cmd: list[str], *, check: bool = True, capture: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        cwd=ROOT,
        check=check,
        capture_output=capture,
        text=True,
    )


def check_python() -> bool:
    version = sys.version_info
    ok = version >= (3, 12)
    log("STARTUP", f"Python {version.major}.{version.minor}.{version.micro}", ok)
    return ok


def check_node() -> bool:
    node = shutil.which("node")
    if not node:
        log("STARTUP", "Node.js não encontrado", False)
        return False
    result = run_cmd(["node", "--version"], capture=True)
    log("STARTUP", f"Node {result.stdout.strip()}", True)
    return True


def check_docker() -> bool:
    if not shutil.which("docker"):
        log("STARTUP", "Docker não encontrado", False)
        return False
    try:
        run_cmd(["docker", "info"], capture=True)
        log("STARTUP", "Docker OK", True)
    except subprocess.CalledProcessError:
        log("STARTUP", "Docker não está rodando", False)
        return False

    try:
        run_cmd(["docker", "compose", "version"], capture=True)
        log("STARTUP", "Docker Compose OK", True)
    except subprocess.CalledProcessError:
        log("STARTUP", "Docker Compose não disponível", False)
        return False
    return True


def validate_env() -> bool:
    env_path = ROOT / ".env"
    if not env_path.exists():
        log("STARTUP", ".env não encontrado — copie .env.example", False)
        return False

    required = [
        "CRYPTOGHOST_SECRET_KEY",
        "CRYPTOGHOST_JWT_SECRET",
        "CRYPTOGHOST_DATABASE_URL",
        "CRYPTOGHOST_DATABASE_URL_SYNC",
        "CRYPTOGHOST_REDIS_URL",
    ]
    content = env_path.read_text(encoding="utf-8")
    missing = [k for k in required if k not in content]
    if missing:
        log("STARTUP", f"Variáveis ausentes: {', '.join(missing)}", False)
        return False

    ollama_url = None
    for line in content.splitlines():
        if line.startswith("CRYPTOGHOST_OLLAMA_URL="):
            ollama_url = line.split("=", 1)[1].strip()
        if line.startswith("CRYPTOGHOST_OLLAMA_BASE_URL=") and not ollama_url:
            ollama_url = line.split("=", 1)[1].strip()

    log("STARTUP", f".env validado | Ollama: {ollama_url or 'localhost:11434'}", True)

    from backend.shared.config import get_settings

    get_settings.cache_clear()
    settings = get_settings()
    if settings.paper_trading:
        log("STARTUP", "Paper trading ATIVO (seguro)", True)
    if settings.live_trading_enabled:
        log("STARTUP", "Live trading habilitado — verifique config!", False)
    else:
        log("STARTUP", "Live trading DESABILITADO (seguro)", True)
    return True


def wait_port(host: str, port: int, timeout: float = 60) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=2):
                return True
        except OSError:
            time.sleep(1)
    return False


def docker_up(services: list[str]) -> bool:
    log("STARTUP", f"Subindo containers: {', '.join(services)}")
    try:
        run_cmd(["docker", "compose", "-f", COMPOSE_FILE, "up", "-d", *services])
        return True
    except subprocess.CalledProcessError as exc:
        log("STARTUP", f"Falha ao subir Docker: {exc}", False)
        return False


def run_migrations() -> bool:
    log("DATABASE", "Executando Alembic migrations...")
    alembic_ini = ROOT / "backend" / "alembic.ini"
    cmd = [sys.executable, "-m", "alembic", "-c", str(alembic_ini), "upgrade", "head"]
    try:
        subprocess.run(
            cmd,
            cwd=ROOT,
            check=True,
            env={**os.environ, "PYTHONPATH": str(ROOT)},
        )
        log("DATABASE", "Migrations OK", True)
        return True
    except subprocess.CalledProcessError as exc:
        log("DATABASE", f"Migrations falharam: {exc}", False)
        return False


def start_process(name: str, cmd: list[str], cwd: Path | None = None) -> subprocess.Popen | None:
    log("STARTUP", f"Iniciando {name}...")
    flags = subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
    try:
        proc = subprocess.Popen(
            cmd,
            cwd=cwd or ROOT,
            env={**os.environ, "PYTHONPATH": str(ROOT)},
            creationflags=flags,
        )
        PROCESSES.append(proc)
        return proc
    except Exception as exc:
        log("STARTUP", f"Falha ao iniciar {name}: {exc}", False)
        return None


def check_http(url: str, timeout: float = 10) -> tuple[bool, dict | None]:
    if httpx is None:
        return False, None
    try:
        with httpx.Client(timeout=timeout) as client:
            r = client.get(url)
            return r.status_code < 500, r.json() if r.headers.get("content-type", "").startswith("application/json") else None
    except Exception:
        return False, None


def validate_services() -> dict[str, bool]:
    results: dict[str, bool] = {}

    pg_ok = wait_port("localhost", 5432, timeout=30)
    results["PostgreSQL"] = pg_ok
    log("DATABASE", "PostgreSQL OK" if pg_ok else "PostgreSQL indisponível", pg_ok)

    redis_ok = wait_port("localhost", 6379, timeout=15)
    results["Redis"] = redis_ok
    log("REDIS", "Redis OK" if redis_ok else "Redis indisponível", redis_ok)

    from backend.shared.config import get_settings

    settings = get_settings()
    ollama_url = settings.effective_ollama_base_url
    if httpx:
        try:
            with httpx.Client(timeout=15) as client:
                r = client.get(f"{ollama_url}/api/tags")
                ollama_ok = r.status_code == 200
                models = [m.get("name") for m in r.json().get("models", [])] if ollama_ok else []
        except Exception:
            ollama_ok = False
            models = []
    else:
        ollama_ok = False
        models = []
    results["Ollama"] = ollama_ok
    log("OLLAMA", f"Ollama OK ({ollama_url}) modelos={len(models)}" if ollama_ok else f"Ollama indisponível ({ollama_url})", ollama_ok)

    backend_ok, _ = check_http("http://localhost:8000/health", timeout=5)
    if not backend_ok:
        time.sleep(5)
        backend_ok, _ = check_http("http://localhost:8000/health", timeout=10)
    results["Backend"] = backend_ok
    log("API", "Backend OK — http://localhost:8000/docs" if backend_ok else "Backend indisponível", backend_ok)

    frontend_ok = wait_port("localhost", 5173, timeout=20) if not results.get("Backend") else wait_port("localhost", 5173, timeout=30)
    results["Frontend"] = frontend_ok
    log("FRONTEND", "Frontend OK — http://localhost:5173" if frontend_ok else "Frontend indisponível", frontend_ok)

    full_ok, full_data = check_http("http://localhost:8000/health/full", timeout=15)
    celery_ok = full_data and full_data.get("checks", {}).get("celery", {}).get("status") in ("healthy", "degraded") if full_data else False
    results["Celery"] = celery_ok
    log("CELERY", "Celery OK" if celery_ok else "Celery degradado/indisponível", celery_ok if celery_ok else None)

    return results


def print_summary(results: dict[str, bool]) -> None:
    print("\n" + "=" * 60)
    print("  CryptoGhost v5.0 — Status Final")
    print("=" * 60)
    for name, ok in results.items():
        mark = "[OK]" if ok else "[FAIL]"
        print(f"  {mark} {name} {'OK' if ok else 'FALHOU'}")
    print("=" * 60)
    print("\n  URLs:")
    print("    API Docs:    http://localhost:8000/docs")
    print("    Dashboard:   http://localhost:5173")
    print("    Health Full: http://localhost:8000/health/full")
    print("    Prometheus:  http://localhost:9090")
    print("    Grafana:     http://localhost:3000  (admin/cryptoghost)")
    print("=" * 60 + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="CryptoGhost v5 Dev Startup")
    parser.add_argument("--all-docker", action="store_true", help="Subir stack completa via Docker")
    parser.add_argument("--check-only", action="store_true", help="Apenas validar ambiente")
    parser.add_argument("--skip-migrations", action="store_true")
    parser.add_argument("--skip-frontend", action="store_true")
    parser.add_argument("--no-docker", action="store_true", help="Pular Docker (infra já rodando localmente)")
    args = parser.parse_args()

    print("\nCryptoGhost v5.0 — Inicializacao Dev\n")

    checks = [check_python(), check_node()]
    docker_ok = check_docker() if not args.no_docker else True
    if not args.check_only and not args.no_docker:
        checks.append(docker_ok)
    elif args.no_docker:
        log("STARTUP", "Docker ignorado (--no-docker)", True)
    checks.append(validate_env())
    if not all(checks):
        log("STARTUP", "Validação de ambiente falhou", False)
        return 1

    if args.check_only:
        log("STARTUP", "Modo check-only — validações concluídas", True)
        return 0

    if args.all_docker:
        if not docker_up(["postgres", "redis", "backend", "celery-worker", "celery-beat", "frontend", "prometheus", "grafana"]):
            return 1
        if not args.skip_migrations:
            time.sleep(8)
            run_migrations()
        time.sleep(10)
        results = validate_services()
        print_summary(results)
        return 0 if all(results.values()) else 1

    # Modo híbrido: infra Docker + apps locais (hot reload)
    if not args.no_docker:
        if not docker_up(["postgres", "redis", "prometheus", "grafana"]):
            return 1
    else:
        log("STARTUP", "Usando PostgreSQL/Redis locais existentes", True)

    log("STARTUP", "Aguardando PostgreSQL e Redis...")
    if not wait_port("localhost", 5432, timeout=60):
        log("DATABASE", "Timeout PostgreSQL", False)
        return 1
    if not wait_port("localhost", 6379, timeout=30):
        log("REDIS", "Timeout Redis", False)
        return 1

    if not args.skip_migrations:
        if not run_migrations():
            log("DATABASE", "Continuando sem migrations (verifique manualmente)", None)

    start_process(
        "Backend",
        [sys.executable, "-m", "uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
    )
    start_process(
        "Celery",
        [
            sys.executable, "-m", "celery", "-A", "backend.shared.celery_app", "worker",
            "--loglevel=info", "-Q", "celery,intelligence", "-c", "2",
        ],
    )

    if not args.skip_frontend:
        frontend_dir = ROOT / "frontend" / "dashboard"
        if (frontend_dir / "node_modules").exists() is False:
            log("FRONTEND", "Instalando dependências npm...")
            run_cmd(["npm", "install"], cwd=frontend_dir, check=False)
        start_process(
            "Frontend",
            ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"],
            cwd=frontend_dir,
        )

    log("STARTUP", "Aguardando serviços...")
    time.sleep(8)
    results = validate_services()
    print_summary(results)

    all_critical = results.get("PostgreSQL", False) and results.get("Redis", False) and results.get("Backend", False)
    if all_critical:
        log("STARTUP", "CryptoGhost v5 operacional — Ctrl+C para encerrar processos locais", True)
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            log("STARTUP", "Encerrando processos...")
            for proc in PROCESSES:
                proc.terminate()
    return 0 if all_critical else 1


if __name__ == "__main__":
    raise SystemExit(main())
