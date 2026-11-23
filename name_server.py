"""
Servidor de nomes (serviço de diretório).

Mantém em memória a tabela  nome do serviço -> (ip, porta).
Escuta em endereço/porta fixos via TCP e trata cada conexão em uma thread separada,
para que um cliente lento não bloqueie novos registros/resoluções.
"""

import ipaddress
import socket
import threading
from datetime import datetime

from common import NAME_SERVER_HOST, NAME_SERVER_PORT, LineReader, send_line

registry = {}                     # nome -> (ip, porta)
registry_lock = threading.Lock()  # protege a tabela contra acesso concorrente das threads


def log(msg: str) -> None:
    print(f"[{datetime.now():%H:%M:%S}] [NOMES] {msg}", flush=True)


def handle_register(args):
    if len(args) != 3:
        return "ERROR uso: REGISTER <nome> <ip> <porta>"
    name, ip, port_txt = args
    try:
        ipaddress.ip_address(ip)
    except ValueError:
        return f"ERROR ip invalido: {ip}"
    if not port_txt.isdigit() or not (1 <= int(port_txt) <= 65535):
        return f"ERROR porta invalida: {port_txt}"

    with registry_lock:
        action = "atualizado" if name in registry else "registrado"
        registry[name] = (ip, int(port_txt))
    log(f"servico '{name}' {action} -> {ip}:{port_txt}")
    return "OK"


def handle_resolve(args):
    if len(args) != 1:
        return "ERROR uso: RESOLVE <nome>"
    name = args[0]
    with registry_lock:
        entry = registry.get(name)
    if entry is None:
        log(f"resolucao de '{name}': NAO ENCONTRADO")
        return f"NOT_FOUND {name}"
    log(f"resolucao de '{name}' -> {entry[0]}:{entry[1]}")
    return f"FOUND {entry[0]} {entry[1]}"


def handle_list(args):
    with registry_lock:
        items = " ".join(f"{n}={ip}:{p}" for n, (ip, p) in registry.items())
    return f"SERVICES {items}".strip()


COMMANDS = {
    "REGISTER": handle_register,
    "RESOLVE": handle_resolve,
    "LIST": handle_list,
}


def handle_client(conn: socket.socket, addr) -> None:
    """Executada em uma thread por conexão. Aceita vários comandos na mesma conexão."""
    log(f"conexao de {addr[0]}:{addr[1]} ({threading.current_thread().name})")
    reader = LineReader(conn)
    try:
        with conn:
            while True:
                line = reader.readline()
                if line is None:          # cliente fechou a conexão
                    break
                if not line:
                    continue
                parts = line.split()
                handler = COMMANDS.get(parts[0].upper())
                reply = handler(parts[1:]) if handler else f"ERROR comando desconhecido: {parts[0]}"
                send_line(conn, reply)
    except (ConnectionError, OSError) as exc:
        log(f"erro na conexao com {addr}: {exc}")


def main() -> None:
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((NAME_SERVER_HOST, NAME_SERVER_PORT))
    server.listen()
    server.settimeout(1.0)  # permite que Ctrl+C seja percebido no Windows
    log(f"escutando em {NAME_SERVER_HOST}:{NAME_SERVER_PORT} (TCP)")
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
