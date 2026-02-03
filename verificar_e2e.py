"""Teste E2E (smoke) do Sistema de Biblioteca.

O que este script faz (automático):
- Sobe a API Node (Biblioteca/API/server.js) usando as configs do .env local
- Espera o /health responder
- Executa uma bateria de checks HTTP que exercitam API + Supabase
- Finaliza o processo da API ao término (por padrão)

Limitações:
- Não clica em *todos os botões* da GUI. Isso exigiria automação de UI para Tkinter.
- O foco aqui é validar a integração API ↔ Banco (Supabase) e contratos HTTP consumidos pelo app.

Uso:
    python verificar_e2e.py

Opções:
    python verificar_e2e.py --base-url http://127.0.0.1:3000
    python verificar_e2e.py --keep-running
    python verificar_e2e.py --timeout 25

Exit code:
- 0: passou
- 1: falhou
"""

from __future__ import annotations

import argparse
import os
import sys
import time
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests


REPO_ROOT = Path(__file__).resolve().parent
API_DIR = REPO_ROOT / "Biblioteca" / "API"


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str = ""


def _print_header(text: str) -> None:
    print("\n" + "=" * 80)
    print(text)
    print("=" * 80)


def _http_json(resp: requests.Response) -> Any:
    try:
        return resp.json()
    except Exception:
        return None


def wait_for_health(base_url: str, timeout_s: int) -> bool:
    deadline = time.time() + timeout_s
    url = f"{base_url.rstrip('/')}/health"

    while time.time() < deadline:
        try:
            r = requests.get(url, timeout=2)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(0.5)

    return False


def start_api_process() -> subprocess.Popen:
    if not API_DIR.exists():
        raise RuntimeError(f"Pasta da API não encontrada: {API_DIR}")

    # A API usa dotenv.config() e lê Biblioteca/API/.env automaticamente.
    # Não imprimimos o conteúdo do .env por segurança.
    return subprocess.Popen(
        ["node", "server.js"],
        cwd=str(API_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def run_checks(base_url: str) -> list[CheckResult]:
    checks: list[CheckResult] = []

    # 1) Health
    try:
        r = requests.get(f"{base_url.rstrip('/')}/health", timeout=5)
        checks.append(CheckResult("GET /health", r.status_code == 200, f"HTTP {r.status_code}"))
    except Exception as exc:
        checks.append(CheckResult("GET /health", False, str(exc)))

    # 2) Swagger (não prova banco, mas prova server + middleware)
    try:
        r = requests.get(f"{base_url.rstrip('/')}/api-docs", timeout=8)
        ok = r.status_code == 200
        checks.append(CheckResult("GET /api-docs", ok, f"HTTP {r.status_code}"))
    except Exception as exc:
        checks.append(CheckResult("GET /api-docs", False, str(exc)))

    # 3) Gêneros (prova Supabase, pois consulta tabela)
    try:
        r = requests.get(f"{base_url.rstrip('/')}/genero", timeout=10)
        payload = _http_json(r)
        ok = r.status_code == 200 and isinstance(payload, dict) and isinstance(payload.get("data"), list)
        detail = f"HTTP {r.status_code}"
        if isinstance(payload, dict) and isinstance(payload.get("data"), list):
            detail += f" | itens={len(payload.get('data', []))}"
        checks.append(CheckResult("GET /genero (listar)", ok, detail))
    except Exception as exc:
        checks.append(CheckResult("GET /genero (listar)", False, str(exc)))

    # 4) Cliente por nome (exercita rota + banco; pode retornar vazio, mas deve ser 200)
    try:
        r = requests.get(f"{base_url.rstrip('/')}/cliente", params={"Nome": "Gabriel"}, timeout=10)
        payload = _http_json(r)
        ok = r.status_code == 200 and isinstance(payload, dict) and isinstance(payload.get("data"), list)
        detail = f"HTTP {r.status_code}"
        if isinstance(payload, dict) and isinstance(payload.get("data"), list):
            detail += f" | itens={len(payload.get('data', []))}"
        checks.append(CheckResult("GET /cliente?Nome=...", ok, detail))
    except Exception as exc:
        checks.append(CheckResult("GET /cliente?Nome=...", False, str(exc)))

    # 5) Livros por autor (exercita rota + banco; deve ser 200 com lista)
    try:
        r = requests.get(f"{base_url.rstrip('/')}/livro/autor", params={"NomeAutor": ""}, timeout=10)
        # Aqui a API pode validar e retornar 400 quando autor vazio.
        # A checagem serve para confirmar que a rota responde corretamente.
        ok = r.status_code in (200, 400)
        checks.append(CheckResult("GET /livro/autor (responde)", ok, f"HTTP {r.status_code}"))
    except Exception as exc:
        checks.append(CheckResult("GET /livro/autor (responde)", False, str(exc)))

    return checks


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default=os.getenv("API_BASE_URL", "http://127.0.0.1:3000"))
    parser.add_argument("--timeout", type=int, default=25)
    parser.add_argument("--keep-running", action="store_true")
    args = parser.parse_args()

    _print_header("E2E Smoke Test - Sistema de Biblioteca")
    print(f"Base URL: {args.base_url}")

    api_proc: subprocess.Popen | None = None

    try:
        print("\n[1/3] Subindo API Node...")
        api_proc = start_api_process()

        print("[2/3] Aguardando /health...")
        if not wait_for_health(args.base_url, args.timeout):
            # API não subiu. Vamos coletar logs para ajudar.
            out, err = api_proc.communicate(timeout=2)
            print("\n❌ API não respondeu no /health dentro do timeout.")
            if out.strip():
                print("\n--- stdout ---\n" + out[-4000:])
            if err.strip():
                print("\n--- stderr ---\n" + err[-4000:])
            return 1

        print("[3/3] Rodando checks...")
        results = run_checks(args.base_url)

        _print_header("Resultados")
        any_fail = False
        for r in results:
            status = "OK" if r.ok else "FAIL"
            print(f"[{status:4}] {r.name} :: {r.detail}")
            if not r.ok:
                any_fail = True

        if any_fail:
            print("\n❌ Falhou em pelo menos um check.")
            return 1

        print("\n✅ Todos os checks passaram.")
        return 0

    except KeyboardInterrupt:
        print("\nInterrompido.")
        return 1

    finally:
        if api_proc is not None and not args.keep_running:
            try:
                api_proc.terminate()
                api_proc.wait(timeout=5)
            except Exception:
                try:
                    api_proc.kill()
                except Exception:
                    pass


if __name__ == "__main__":
    raise SystemExit(main())
