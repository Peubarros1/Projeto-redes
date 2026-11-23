"""
Cliente UDP.

Resolve o serviço no servidor de nomes (via TCP) e depois envia a requisição
em um datagrama UDP diretamente ao serviço. Como o UDP não garante entrega,
o cliente usa timeout e retransmite algumas vezes antes de desistir.

Uso:
  python udp_client.py                 # envia 'ADD 10 5'
  python udp_client.py SUB 9 4
  python udp_client.py MUL 3 3 -n 20   # repete 20 vezes e mostra estatísticas
"""

import argparse
import socket
import statistics
import sys
import time

from common import (BUFFER_SIZE, ENCODING, UDP_RETRIES, UDP_SERVICE_NAME,
                    UDP_TIMEOUT, resolve)


def udp_request(ip: str, port: int, request: str):
    """
    Envia um datagrama e espera a resposta.
    Retorna (resposta, tempo_total_ms, tentativas).
    Levanta TimeoutError se nenhuma resposta chegar após UDP_RETRIES tentativas.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(UDP_TIMEOUT)
        payload = (request + "\n").encode(ENCODING)
        t0 = time.perf_counter()
        for attempt in range(1, UDP_RETRIES + 1):
            sock.sendto(payload, (ip, port))
            try:
                data, _ = sock.recvfrom(BUFFER_SIZE)
            except socket.timeout:
                continue
            except ConnectionResetError:
                # Windows: ICMP "port unreachable" (servidor UDP fora do ar)
                raise ConnectionError("porta UDP inalcancavel (servico fora do ar?)")
            t_end = time.perf_counter()
            return data.decode(ENCODING).strip(), (t_end - t0) * 1000, attempt
    raise TimeoutError(f"sem resposta apos {UDP_RETRIES} tentativas")


def main() -> int:
    parser = argparse.ArgumentParser(description="Cliente UDP da calculadora")
    parser.add_argument("op", nargs="?", default="ADD")
    parser.add_argument("a", nargs="?", default="10")
    parser.add_argument("b", nargs="?", default="5")
    parser.add_argument("-n", type=int, default=1, help="numero de repeticoes")
    parser.add_argument("--service", default=UDP_SERVICE_NAME, help="nome do servico a resolver")
    args = parser.parse_args()
    request = f"{args.op} {args.a} {args.b}"

    # 1) Resolução de nome
    try:
        t0 = time.perf_counter()
        address = resolve(args.service)
        t_resolve = (time.perf_counter() - t0) * 1000
    except OSError as exc:
        print(f"[CLIENTE UDP] Erro: servidor de nomes inacessivel ({exc})")
        return 1
    if address is None:
        print(f"[CLIENTE UDP] Servico '{args.service}' nao esta registrado no servidor de nomes.")
        return 1
    ip, port = address
    print(f"[CLIENTE UDP] '{args.service}' resolvido para {ip}:{port} em {t_resolve:.3f} ms")

    # 2) Requisição(ões) direto ao serviço
    totals = []
    for i in range(args.n):
        try:
            reply, t_total, attempts = udp_request(ip, port, request)
        except (OSError, TimeoutError) as exc:
            print(f"[CLIENTE UDP] Erro ao falar com o servico: {exc}")
            return 1
        totals.append(t_total)
        prefix = f"#{i + 1} " if args.n > 1 else ""
        extra = f" ({attempts} tentativas)" if attempts > 1 else ""
        print(f"[CLIENTE UDP] {prefix}'{request}' -> '{reply}' | total da requisicao {t_total:.3f} ms{extra}")

    if args.n > 1:
        print(f"[CLIENTE UDP] {args.n} requisicoes: media {statistics.mean(totals):.3f} ms | "
              f"min {min(totals):.3f} | max {max(totals):.3f} | "
              f"desvio {statistics.stdev(totals):.3f} ms")
    print(f"[CLIENTE UDP] tempo total (resolucao + 1a requisicao): {t_resolve + totals[0]:.3f} ms")
    return 0


if __name__ == "__main__":
    sys.exit(main())
