import argparse
import socket
import statistics
import sys
import time

from common import (TAMANHO_BUFFER, CODIFICACAO, MAX_TENTATIVAS_UDP, NOME_SERVICO_UDP,
                    TEMPO_LIMITE_UDP, resolve)


def udp_request(ip: str, porta: int, requisicao: str):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as soquete:
        soquete.settimeout(TEMPO_LIMITE_UDP)
        carga = (requisicao + "\n").encode(CODIFICACAO)
        inicio = time.perf_counter()
        for tentativa in range(1, MAX_TENTATIVAS_UDP + 1):
            soquete.sendto(carga, (ip, porta))
            try:
                dados, _ = soquete.recvfrom(TAMANHO_BUFFER)
            except socket.timeout:
                continue
            except ConnectionResetError:
                raise ConnectionError("porta UDP inalcancavel (servico fora do ar?)")
            fim = time.perf_counter()
            return dados.decode(CODIFICACAO).strip(), (fim - inicio) * 1000, tentativa
    raise TimeoutError(f"sem resposta apos {MAX_TENTATIVAS_UDP} tentativas")


def main() -> int:
    analisador = argparse.ArgumentParser(description="Cliente UDP da calculadora")
    analisador.add_argument("op", nargs="?", default="ADD")
    analisador.add_argument("a", nargs="?", default="10")
    analisador.add_argument("b", nargs="?", default="5")
    analisador.add_argument("-n", type=int, default=1, help="numero de repeticoes")
    analisador.add_argument("--service", default=NOME_SERVICO_UDP, help="nome do servico a resolver")
    argumentos = analisador.parse_args()
    requisicao = f"{argumentos.op} {argumentos.a} {argumentos.b}"

    try:
        inicio = time.perf_counter()
        endereco = resolve(argumentos.service)
        tempo_resolucao = (time.perf_counter() - inicio) * 1000
    except OSError as erro:
        print(f"[CLIENTE UDP] Erro: servidor de nomes inacessivel ({erro})")
        return 1
    if endereco is None:
        print(f"[CLIENTE UDP] Servico '{argumentos.service}' nao esta registrado no servidor de nomes.")
        return 1
    ip, porta = endereco
    print(f"[CLIENTE UDP] '{argumentos.service}' resolvido para {ip}:{porta} em {tempo_resolucao:.3f} ms")

    totais = []
    for i in range(argumentos.n):
        try:
            resposta, tempo_total, tentativas = udp_request(ip, porta, requisicao)
        except (OSError, TimeoutError) as erro:
            print(f"[CLIENTE UDP] Erro ao falar com o servico: {erro}")
            return 1
        totais.append(tempo_total)
        prefixo = f"#{i + 1} " if argumentos.n > 1 else ""
        extra = f" ({tentativas} tentativas)" if tentativas > 1 else ""
        print(f"[CLIENTE UDP] {prefixo}'{requisicao}' -> '{resposta}' | total da requisicao {tempo_total:.3f} ms{extra}")

    if argumentos.n > 1:
        print(f"[CLIENTE UDP] {argumentos.n} requisicoes: media {statistics.mean(totais):.3f} ms | "
              f"min {min(totais):.3f} | max {max(totais):.3f} | "
              f"desvio {statistics.stdev(totais):.3f} ms")
    print(f"[CLIENTE UDP] tempo total (resolucao + 1a requisicao): {tempo_resolucao + totais[0]:.3f} ms")
    return 0


if __name__ == "__main__":
    sys.exit(main())
