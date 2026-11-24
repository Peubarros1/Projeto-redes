import socket
import sys
import threading
from datetime import datetime

from common import (TAMANHO_BUFFER, CODIFICACAO, IP_SERVICO_UDP, NOME_SERVICO_UDP,
                    PORTA_SERVICO_UDP, calculate)
from registration import register_service


def log(mensagem: str) -> None:
    print(f"[{datetime.now():%H:%M:%S}] [UDP] {mensagem}", flush=True)


def handle_datagram(soquete: socket.socket, dados: bytes, endereco) -> None:
    requisicao = dados.decode(CODIFICACAO, errors="replace").strip()
    resposta = calculate(requisicao)
    soquete.sendto((resposta + "\n").encode(CODIFICACAO), endereco)
    log(f"{endereco[0]}:{endereco[1]} '{requisicao}' -> '{resposta}'")


def main() -> None:
    soquete = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    soquete.bind((IP_SERVICO_UDP, PORTA_SERVICO_UDP))
    soquete.settimeout(1.0)
    log(f"escutando em {IP_SERVICO_UDP}:{PORTA_SERVICO_UDP}")

    if not register_service(NOME_SERVICO_UDP, IP_SERVICO_UDP, PORTA_SERVICO_UDP, log):
        soquete.close()
        sys.exit(1)

    try:
        while True:
            try:
                dados, endereco = soquete.recvfrom(TAMANHO_BUFFER)
            except socket.timeout:
                continue
            except ConnectionResetError:
                continue
            threading.Thread(target=handle_datagram, args=(soquete, dados, endereco), daemon=True).start()
    except KeyboardInterrupt:
        log("encerrando")
    finally:
        soquete.close()


if __name__ == "__main__":
    main()
