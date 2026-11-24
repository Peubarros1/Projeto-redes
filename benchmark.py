import argparse
import csv
import os
import statistics
import time

from common import NOME_SERVICO_TCP, NOME_SERVICO_UDP, resolve
from tcp_client import tcp_request
from udp_client import udp_request

REQUISICAO = "MUL 12345 6789"


def summarize(rotulo, amostras):
    ordenadas = sorted(amostras)
    p95 = ordenadas[int(0.95 * (len(ordenadas) - 1))]
    print(f"{rotulo:<22} media {statistics.mean(amostras):8.3f} | mediana {statistics.median(amostras):8.3f} | "
          f"min {min(amostras):8.3f} | max {max(amostras):8.3f} | "
          f"desvio {statistics.stdev(amostras):7.3f} | p95 {p95:8.3f}  (ms)")


def timed_resolve(nome, n):
    amostras = []
    for _ in range(n):
        inicio = time.perf_counter()
        endereco = resolve(nome)
        amostras.append((time.perf_counter() - inicio) * 1000)
    if endereco is None:
        raise SystemExit(f"servico '{nome}' nao registrado - suba os servidores antes")
    return endereco, amostras


def main() -> None:
    analisador = argparse.ArgumentParser()
    analisador.add_argument("-n", type=int, default=200, help="requisicoes por protocolo")
    analisador.add_argument("--warmup", type=int, default=10, help="requisicoes de aquecimento descartadas")
    argumentos = analisador.parse_args()

    (ip_tcp, porta_tcp), resolucao_tcp = timed_resolve(NOME_SERVICO_TCP, argumentos.n)
    (ip_udp, porta_udp), resolucao_udp = timed_resolve(NOME_SERVICO_UDP, argumentos.n)

    for _ in range(argumentos.warmup):
        tcp_request(ip_tcp, porta_tcp, REQUISICAO)
        udp_request(ip_udp, porta_udp, REQUISICAO)

    conexoes_tcp, totais_tcp, totais_udp = [], [], []
    for _ in range(argumentos.n):
        _, tempo_conexao, tempo = tcp_request(ip_tcp, porta_tcp, REQUISICAO)
        conexoes_tcp.append(tempo_conexao)
        totais_tcp.append(tempo)
        _, tempo, _ = udp_request(ip_udp, porta_udp, REQUISICAO)
        totais_udp.append(tempo)

    print(f"\nRequisicao: '{REQUISICAO}'  |  {argumentos.n} amostras por medida  |  {argumentos.warmup} de aquecimento\n")
    summarize("Resolucao de nome", resolucao_tcp + resolucao_udp)
    summarize("TCP (so handshake)", conexoes_tcp)
    summarize("TCP (requisicao)", totais_tcp)
    summarize("UDP (requisicao)", totais_udp)
    razao = statistics.mean(totais_tcp) / statistics.mean(totais_udp)
    print(f"\nTCP foi em media {razao:.2f}x o tempo do UDP por requisicao.")

    os.makedirs("results", exist_ok=True)
    caminho = os.path.join("results", "benchmark.csv")
    with open(caminho, "w", newline="") as arquivo:
        escritor = csv.writer(arquivo)
        escritor.writerow(["amostra", "resolucao_ms", "tcp_conexao_ms", "tcp_total_ms", "udp_total_ms"])
        for i in range(argumentos.n):
            escritor.writerow([i + 1, f"{resolucao_tcp[i]:.4f}", f"{conexoes_tcp[i]:.4f}",
                               f"{totais_tcp[i]:.4f}", f"{totais_udp[i]:.4f}"])
    print(f"Amostras salvas em {caminho}")


if __name__ == "__main__":
    main()
