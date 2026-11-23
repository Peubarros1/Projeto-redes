"""
Cliente TCP.

Não conhece o endereço do serviço: primeiro consulta o servidor de nomes,
depois conecta direto no serviço e mede o tempo da requisição.

Uso:
  python tcp_client.py                 # envia 'ADD 10 5'
  python tcp_client.py MUL 6 7
  python tcp_client.py DIV 10 4 -n 20  # repete 20 vezes e mostra estatísticas
"""

import argparse
import socket
import statistics
import sys
import time

from common import TCP_SERVICE_NAME, LineReader, resolve, send_line


def tcp_request(ip: str, port: int, request: str):
    """
    Faz uma requisição completa: conecta, envia, recebe e fecha.
    Retorna (resposta, tempo_conexao_ms, tempo_total_ms).
    O tempo total vai do início (connect + envio) até o recebimento da resposta.
    """
    t0 = time.perf_counter()
    with socket.create_connection((ip, port), timeout=5) as sock:
        t_conn = time.perf_counter()
        send_line(sock, request)
        reply = LineReader(sock).readline()
        t_end = time.perf_counter()
    if reply is None:
        raise ConnectionError("servidor fechou a conexao sem responder")
    return reply, (t_conn - t0) * 1000, (t_end - t0) * 1000


def main() -> int:
    parser = argparse.ArgumentParser(description="Cliente TCP da calculadora")
    parser.add_argument("op", nargs="?", default="ADD")
    parser.add_argument("a", nargs="?", default="10")
    parser.add_argument("b", nargs="?", default="5")
    parser.add_argument("-n", type=int, default=1, help="numero de repeticoes")
    parser.add_argument("--service", default=TCP_SERVICE_NAME, help="nome do servico a resolver")
    args = parser.parse_args()
    request = f"{args.op} {args.a} {args.b}"

    # 1) Resolução de nome
    try:
        t0 = time.perf_counter()
        address = resolve(args.service)
        t_resolve = (time.perf_counter() - t0) * 1000
    except OSError as exc:
        print(f"[CLIENTE TCP] Erro: servidor de nomes inacessivel ({exc})")
        return 1
    if address is None:
        print(f"[CLIENTE TCP] Servico '{args.service}' nao esta registrado no servidor de nomes.")
        return 1
    ip, port = address
    print(f"[CLIENTE TCP] '{args.service}' resolvido para {ip}:{port} em {t_resolve:.3f} ms")

    # 2) Requisição(ões) direto ao serviço
    totals = []
    for i in range(args.n):
        try:
            reply, t_conn, t_total = tcp_request(ip, port, request)
        except OSError as exc:
            print(f"[CLIENTE TCP] Erro ao falar com o servico: {exc}")
            return 1
        totals.append(t_total)
        prefix = f"#{i + 1} " if args.n > 1 else ""
        print(f"[CLIENTE TCP] {prefix}'{request}' -> '{reply}' | conexao {t_conn:.3f} ms | "
              f"total da requisicao {t_total:.3f} ms")

    if args.n > 1:
        print(f"[CLIENTE TCP] {args.n} requisicoes: media {statistics.mean(totals):.3f} ms | "
              f"min {min(totals):.3f} | max {max(totals):.3f} | "
              f"desvio {statistics.stdev(totals):.3f} ms")
    print(f"[CLIENTE TCP] tempo total (resolucao + 1a requisicao): {t_resolve + totals[0]:.3f} ms")
    return 0


if __name__ == "__main__":
    sys.exit(main())
