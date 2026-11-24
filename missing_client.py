import sys

from common import resolve


def main() -> int:
    nome = sys.argv[1] if len(sys.argv) > 1 else "servico-fantasma"
    print(f"[CLIENTE] Solicitando ao servidor de nomes a resolucao de '{nome}'...")
    try:
        endereco = resolve(nome)
    except OSError as erro:
        print(f"[CLIENTE] Nao foi possivel falar com o servidor de nomes: {erro}")
        return 1
    except ValueError as erro:
        print(f"[CLIENTE] Resposta invalida do servidor de nomes: {erro}")
        return 1

    if endereco is None:
        print(f"[CLIENTE] O servico '{nome}' NAO esta registrado. "
              "Verifique o nome ou se o servidor do servico foi iniciado.")
        print("[CLIENTE] Encerrando normalmente (erro tratado).")
        return 0

    print(f"[CLIENTE] Inesperado: '{nome}' esta registrado em {endereco[0]}:{endereco[1]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
