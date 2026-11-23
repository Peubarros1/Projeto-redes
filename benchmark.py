"""
Benchmark TCP x UDP para o relatório.

Resolve os dois serviços no servidor de nomes, executa N requisições em cada um
e mostra estatísticas (média, mediana, mín, máx, desvio, p95). Salva as amostras em
results/benchmark.csv para gerar gráficos/tabelas no relatório.

Uso:
  python benchmark.py          # 200 requisições por protocolo
  python benchmark.py -n 1000
"""

import argparse
import csv
import os
import statistics
import time

from common import TCP_SERVICE_NAME, UDP_SERVICE_NAME, resolve
from tcp_client import tcp_request
from udp_client import udp_request

REQUEST = "MUL 12345 6789"


def summarize(label, samples):
    ordered = sorted(samples)
    p95 = ordered[int(0.95 * (len(ordered) - 1))]
    print(f"{label:<22} media {statistics.mean(samples):8.3f} | mediana {statistics.median(samples):8.3f} | "
          f"min {min(samples):8.3f} | max {max(samples):8.3f} | "
          f"desvio {statistics.stdev(samples):7.3f} | p95 {p95:8.3f}  (ms)")


def timed_resolve(name, n):
    samples = []
    for _ in range(n):
        t0 = time.perf_counter()
        addr = resolve(name)
        samples.append((time.perf_counter() - t0) * 1000)
    if addr is None:
        raise SystemExit(f"servico '{name}' nao registrado - suba os servidores antes")
    return addr, samples


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", type=int, default=200, help="requisicoes por protocolo")
    parser.add_argument("--warmup", type=int, default=10, help="requisicoes de aquecimento descartadas")
    args = parser.parse_args()

    (tcp_ip, tcp_port), res_tcp = timed_resolve(TCP_SERVICE_NAME, args.n)
    (udp_ip, udp_port), res_udp = timed_resolve(UDP_SERVICE_NAME, args.n)

    for _ in range(args.warmup):
        tcp_request(tcp_ip, tcp_port, REQUEST)
        udp_request(udp_ip, udp_port, REQUEST)

    tcp_conn, tcp_total, udp_total = [], [], []
    # Intercala TCP e UDP para que variações de carga da máquina afetem os dois igualmente
    for _ in range(args.n):
        _, c, t = tcp_request(tcp_ip, tcp_port, REQUEST)
        tcp_conn.append(c)
        tcp_total.append(t)
        _, t, _ = udp_request(udp_ip, udp_port, REQUEST)
        udp_total.append(t)

    print(f"\nRequisicao: '{REQUEST}'  |  {args.n} amostras por medida  |  {args.warmup} de aquecimento\n")
    summarize("Resolucao de nome", res_tcp + res_udp)
    summarize("TCP (so handshake)", tcp_conn)
    summarize("TCP (requisicao)", tcp_total)
    summarize("UDP (requisicao)", udp_total)
    ratio = statistics.mean(tcp_total) / statistics.mean(udp_total)
    print(f"\nTCP foi em media {ratio:.2f}x o tempo do UDP por requisicao.")

    os.makedirs("results", exist_ok=True)
    path = os.path.join("results", "benchmark.csv")
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["amostra", "resolucao_ms", "tcp_conexao_ms", "tcp_total_ms", "udp_total_ms"])
        for i in range(args.n):
            w.writerow([i + 1, f"{res_tcp[i]:.4f}", f"{tcp_conn[i]:.4f}",
                        f"{tcp_total[i]:.4f}", f"{udp_total[i]:.4f}"])
    print(f"Amostras salvas em {path}")


if __name__ == "__main__":
    main()
