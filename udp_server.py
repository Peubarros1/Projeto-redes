"""
Serviço de aplicação via UDP (calculadora).

Mesma lógica do serviço TCP, mas sem conexão: cada datagrama recebido é uma
requisição completa e a resposta vai em um datagrama para o endereço de origem.
Cada datagrama é processado em uma thread, para não bloquear o recebimento de outros.
O registro no servidor de nomes é feito via TCP (decisão do grupo).
"""

import socket
import sys
import threading
from datetime import datetime

from common import (BUFFER_SIZE, ENCODING, UDP_SERVICE_HOST, UDP_SERVICE_NAME,
                    UDP_SERVICE_PORT, calculate)
from registration import register_service


def log(msg: str) -> None:
    print(f"[{datetime.now():%H:%M:%S}] [UDP] {msg}", flush=True)


def handle_datagram(sock: socket.socket, data: bytes, addr) -> None:
    request = data.decode(ENCODING, errors="replace").strip()
    reply = calculate(request)
    sock.sendto((reply + "\n").encode(ENCODING), addr)
    log(f"{addr[0]}:{addr[1]} '{request}' -> '{reply}'")


def main() -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_SERVICE_HOST, UDP_SERVICE_PORT))
    sock.settimeout(1.0)
    log(f"escutando em {UDP_SERVICE_HOST}:{UDP_SERVICE_PORT}")

    if not register_service(UDP_SERVICE_NAME, UDP_SERVICE_HOST, UDP_SERVICE_PORT, log):
        sock.close()
        sys.exit(1)

    try:
        while True:
            try:
                data, addr = sock.recvfrom(BUFFER_SIZE)
            except socket.timeout:
                continue
            except ConnectionResetError:
                # No Windows, um ICMP "port unreachable" de um envio anterior aparece aqui; ignoramos.
                continue
            threading.Thread(target=handle_datagram, args=(sock, data, addr), daemon=True).start()
    except KeyboardInterrupt:
        log("encerrando")
    finally:
        sock.close()


if __name__ == "__main__":
    main()
