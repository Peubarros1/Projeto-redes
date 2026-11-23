"""
Serviço de aplicação via TCP (calculadora).

1. Abre o socket na porta fixa TCP_SERVICE_PORT.
2. Registra-se no servidor de nomes com o nome único TCP_SERVICE_NAME.
3. Aceita várias conexões, cada uma tratada em uma thread separada.
"""

import socket
import sys
import threading
from datetime import datetime

from common import (TCP_SERVICE_HOST, TCP_SERVICE_NAME, TCP_SERVICE_PORT,
                    LineReader, calculate, send_line)
from registration import register_service


def log(msg: str) -> None:
    print(f"[{datetime.now():%H:%M:%S}] [TCP] {msg}", flush=True)


def handle_client(conn: socket.socket, addr) -> None:
    reader = LineReader(conn)
    try:
        with conn:
            while True:
                request = reader.readline()
                if request is None:
                    break
                if not request:
                    continue
                reply = calculate(request)
                send_line(conn, reply)
                log(f"{addr[0]}:{addr[1]} '{request}' -> '{reply}'")
    except (ConnectionError, OSError) as exc:
        log(f"erro na conexao com {addr}: {exc}")


def main() -> None:
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((TCP_SERVICE_HOST, TCP_SERVICE_PORT))
    server.listen()
    server.settimeout(1.0)
    log(f"escutando em {TCP_SERVICE_HOST}:{TCP_SERVICE_PORT}")

    # Socket já está escutando antes do registro: quando o cliente resolver o nome, o serviço já atende.
    if not register_service(TCP_SERVICE_NAME, TCP_SERVICE_HOST, TCP_SERVICE_PORT, log):
        server.close()
        sys.exit(1)

    try:
        while True:
            try:
                conn, addr = server.accept()
            except socket.timeout:
                continue
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
    except KeyboardInterrupt:
        log("encerrando")
    finally:
        server.close()


if __name__ == "__main__":
    main()
