"""
Cliente do cenário "serviço inexistente".

Pede ao servidor de nomes a resolução de um nome que nunca foi registrado e
trata a resposta NOT_FOUND com uma mensagem amigável, sem travar e sem exceção não tratada.

Uso:
  python missing_client.py                 # tenta resolver 'servico-fantasma'
  python missing_client.py meu-servico
"""

import sys

from common import resolve


def main() -> int:
    name = sys.argv[1] if len(sys.argv) > 1 else "servico-fantasma"
    print(f"[CLIENTE] Solicitando ao servidor de nomes a resolucao de '{name}'...")
    try:
        address = resolve(name)
    except OSError as exc:
        print(f"[CLIENTE] Nao foi possivel falar com o servidor de nomes: {exc}")
        return 1
    except ValueError as exc:
        print(f"[CLIENTE] Resposta invalida do servidor de nomes: {exc}")
        return 1

    if address is None:
        print(f"[CLIENTE] O servico '{name}' NAO esta registrado. "
              "Verifique o nome ou se o servidor do servico foi iniciado.")
        print("[CLIENTE] Encerrando normalmente (erro tratado).")
        return 0

    print(f"[CLIENTE] Inesperado: '{name}' esta registrado em {address[0]}:{address[1]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
