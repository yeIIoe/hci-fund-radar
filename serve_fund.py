#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Servidor local do HCI FUND Radar."""
from __future__ import annotations

import argparse
import json
import threading
import webbrowser
import socket
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

import update_fund


ROOT = Path(__file__).resolve().parent
HOST = "127.0.0.1"
PORT = 8765
UPDATE_LOCK = threading.Lock()


class FundHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self) -> None:
        # painel local: nada de cache. Evita servir app.js/index.html velhos
        # depois de uma alteracao (o navegador guardava a versao antiga).
        self.send_header("Cache-Control", "no-store, max-age=0")
        super().end_headers()

    def do_GET(self) -> None:  # noqa: N802 - assinatura da stdlib
        if urlparse(self.path).path == "/api/health":
            self.send_json({"ok": True, "service": "HCI FUND Radar"})
            return
        if urlparse(self.path).path == "/api/pre-fund-health":
            self.send_json({"ok": True, "feature": "PRE_FUND_D1", "version": 1})
            return
        super().do_GET()

    def do_POST(self) -> None:  # noqa: N802 - assinatura da stdlib
        route = urlparse(self.path).path
        if route not in ("/api/update", "/api/backtest"):
            self.send_error(404)
            return
        if not UPDATE_LOCK.acquire(blocking=False):
            self.send_json({"ok": False, "error": "Atualizacao ja esta em andamento."}, status=409)
            return
        try:
            if route == "/api/update":
                snapshot = update_fund.main(["--force"])
                self.send_json({"ok": True, "meta": snapshot["meta"]})
            else:
                length = int(self.headers.get("Content-Length", "0"))
                if length > 65_536:
                    raise ValueError("requisicao muito grande")
                raw = self.rfile.read(length) if length else b"{}"
                payload = json.loads(raw.decode("utf-8"))
                result = update_fund.run_backtest_request(payload)
                self.send_json({"ok": True, **result})
        except Exception as error:
            self.send_json({"ok": False, "error": str(error)}, status=500)
        finally:
            UPDATE_LOCK.release()

    def send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, template: str, *args) -> None:
        print(f"[RADAR] {self.address_string()} - {template % args}")


def ensure_snapshot() -> None:
    if update_fund.SNAPSHOT_PATH.exists() and update_fund.BACKTEST_PATH.exists():
        return
    print("Primeira abertura: gerando snapshot...")
    update_fund.main([])


def instancia_unica() -> None:
    """Garante um unico painel rodando.

    Nao da para usar a porta como trava: o HTTPServer liga com SO_REUSEADDR, e no
    Windows isso permite dois processos na mesma porta. E desligar o reuse quebraria
    o reinicio automatico, porque um socket em TIME_WAIT bloquearia o rebind por
    ~2 minutos. Um mutex nomeado resolve os dois problemas de uma vez.
    """
    if sys.platform != "win32":
        return
    import ctypes
    ERRO_JA_EXISTE = 183
    k32 = ctypes.windll.kernel32
    k32.CreateMutexW(None, False, r"Global\HCI_FUND_RADAR")
    if k32.GetLastError() == ERRO_JA_EXISTE:
        print("O painel ja esta rodando. Abra http://localhost:8765")
        raise SystemExit(0)
    globals()["_trava"] = True        # mantem o handle vivo pelo processo inteiro


def main() -> None:
    instancia_unica()
    parser = argparse.ArgumentParser(description="Servidor local do HCI FUND Radar")
    parser.add_argument("--no-browser", action="store_true", help="nao abre o navegador automaticamente")
    args = parser.parse_args()
    ensure_snapshot()
    url = f"http://{HOST}:{PORT}"
    # DOIS listeners de loopback, um por familia de endereco.
    # Tentativa anterior ligava so em "::1" com IPV6_V6ONLY=0 — isso NAO cobre
    # 127.0.0.1, porque o mapeamento IPv4 exige bind no coringa "::", e "::"
    # exporia o painel para a rede local. Dois sockets resolvem sem expor nada:
    # localhost resolve para ::1 ou 127.0.0.1 e os dois respondem.
    class ServidorV4(ThreadingHTTPServer):
        pass

    class ServidorV6(ThreadingHTTPServer):
        address_family = socket.AF_INET6

    servidores = []
    try:
        servidores.append(ServidorV4((HOST, PORT), FundHandler))            # 127.0.0.1
    except OSError as erro:
        print(f"aviso: IPv4 indisponivel ({erro})")
    try:
        servidores.append(ServidorV6(("::1", PORT), FundHandler))           # [::1]
    except OSError:
        pass          # maquina sem IPv6: o listener IPv4 basta
    if not servidores:
        raise SystemExit(f"porta {PORT} ocupada — feche o painel anterior e tente de novo")
    for extra in servidores[1:]:
        threading.Thread(target=extra.serve_forever, daemon=True).start()
    server = servidores[0]

    print("=" * 66)
    print("HCI FUND RADAR ATIVO")
    print(url)
    print("Mantenha esta janela aberta. Ctrl+C encerra o painel.")
    print("=" * 66)
    if not args.no_browser:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nRadar encerrado.")
    finally:
        for srv in servidores:
            srv.server_close()


if __name__ == "__main__":
    main()
