import argparse
import socket
import statistics
import sys
import time

from common import NOME_SERVICO_TCP, LineReader, resolve, send_line


def tcp_request(ip: str, porta: int, requisicao: str):
    inicio = time.perf_counter()
    with socket.create_connection((ip, porta), timeout=5) as soquete:
        instante_conexao = time.perf_counter()
        send_line(soquete, requisicao)
        resposta = LineReader(soquete).readline()
        fim = time.perf_counter()
    if resposta is None:
        raise ConnectionError("servidor fechou a conexao sem responder")
    return resposta, (instante_conexao - inicio) * 1000, (fim - inicio) * 1000


def main() -> int:
    analisador = argparse.ArgumentParser(description="Cliente TCP da calculadora")
    analisador.add_argument("op", nargs="?", default="ADD")
    analisador.add_argument("a", nargs="?", default="10")
    analisador.add_argument("b", nargs="?", default="5")
    analisador.add_argument("-n", type=int, default=1, help="numero de repeticoes")
    analisador.add_argument("--service", default=NOME_SERVICO_TCP, help="nome do servico a resolver")
    argumentos = analisador.parse_args()
    requisicao = f"{argumentos.op} {argumentos.a} {argumentos.b}"

    try:
        inicio = time.perf_counter()
        endereco = resolve(argumentos.service)
        tempo_resolucao = (time.perf_counter() - inicio) * 1000
    except OSError as erro:
        print(f"[CLIENTE TCP] Erro: servidor de nomes inacessivel ({erro})")
        return 1
    if endereco is None:
        print(f"[CLIENTE TCP] Servico '{argumentos.service}' nao esta registrado no servidor de nomes.")
        return 1
    ip, porta = endereco
    print(f"[CLIENTE TCP] '{argumentos.service}' resolvido para {ip}:{porta} em {tempo_resolucao:.3f} ms")

    totais = []
    for i in range(argumentos.n):
        try:
            resposta, tempo_conexao, tempo_total = tcp_request(ip, porta, requisicao)
        except OSError as erro:
            print(f"[CLIENTE TCP] Erro ao falar com o servico: {erro}")
            return 1
        totais.append(tempo_total)
        prefixo = f"#{i + 1} " if argumentos.n > 1 else ""
        print(f"[CLIENTE TCP] {prefixo}'{requisicao}' -> '{resposta}' | conexao {tempo_conexao:.3f} ms | "
              f"total da requisicao {tempo_total:.3f} ms")

    if argumentos.n > 1:
        print(f"[CLIENTE TCP] {argumentos.n} requisicoes: media {statistics.mean(totais):.3f} ms | "
              f"min {min(totais):.3f} | max {max(totais):.3f} | "
              f"desvio {statistics.stdev(totais):.3f} ms")
    print(f"[CLIENTE TCP] tempo total (resolucao + 1a requisicao): {tempo_resolucao + totais[0]:.3f} ms")
    return 0


if __name__ == "__main__":
    sys.exit(main())
