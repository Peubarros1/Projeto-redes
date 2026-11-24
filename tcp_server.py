import socket
import sys
import threading
from datetime import datetime

from common import (IP_SERVICO_TCP, NOME_SERVICO_TCP, PORTA_SERVICO_TCP,
                    LineReader, calculate, send_line)
from registration import register_service


def log(mensagem: str) -> None:
    print(f"[{datetime.now():%H:%M:%S}] [TCP] {mensagem}", flush=True)


def handle_client(conexao: socket.socket, endereco) -> None:
    leitor = LineReader(conexao)
    try:
        with conexao:
            while True:
                requisicao = leitor.readline()
                if requisicao is None:
                    break
                if not requisicao:
                    continue
                resposta = calculate(requisicao)
                send_line(conexao, resposta)
                log(f"{endereco[0]}:{endereco[1]} '{requisicao}' -> '{resposta}'")
    except (ConnectionError, OSError) as erro:
        log(f"erro na conexao com {endereco}: {erro}")


def main() -> None:
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind((IP_SERVICO_TCP, PORTA_SERVICO_TCP))
    servidor.listen()
    servidor.settimeout(1.0)
    log(f"escutando em {IP_SERVICO_TCP}:{PORTA_SERVICO_TCP}")

    if not register_service(NOME_SERVICO_TCP, IP_SERVICO_TCP, PORTA_SERVICO_TCP, log):
        servidor.close()
        sys.exit(1)

    try:
        while True:
            try:
                conexao, endereco = servidor.accept()
            except socket.timeout:
                continue
            threading.Thread(target=handle_client, args=(conexao, endereco), daemon=True).start()
    except KeyboardInterrupt:
        log("encerrando")
    finally:
        servidor.close()


if __name__ == "__main__":
    main()
