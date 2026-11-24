import ipaddress
import socket
import threading
from datetime import datetime

from common import IP_SERVIDOR_NOMES, PORTA_SERVIDOR_NOMES, LineReader, send_line

tabela_servicos = {}
trava_tabela = threading.Lock()


def log(mensagem: str) -> None:
    print(f"[{datetime.now():%H:%M:%S}] [NOMES] {mensagem}", flush=True)


def handle_register(argumentos):
    if len(argumentos) != 3:
        return "ERROR uso: REGISTER <nome> <ip> <porta>"
    nome, ip, texto_porta = argumentos
    try:
        ipaddress.ip_address(ip)
    except ValueError:
        return f"ERROR ip invalido: {ip}"
    if not texto_porta.isdigit() or not (1 <= int(texto_porta) <= 65535):
        return f"ERROR porta invalida: {texto_porta}"

    with trava_tabela:
        acao = "atualizado" if nome in tabela_servicos else "registrado"
        tabela_servicos[nome] = (ip, int(texto_porta))
    log(f"servico '{nome}' {acao} -> {ip}:{texto_porta}")
    return "OK"


def handle_resolve(argumentos):
    if len(argumentos) != 1:
        return "ERROR uso: RESOLVE <nome>"
    nome = argumentos[0]
    with trava_tabela:
        registro = tabela_servicos.get(nome)
    if registro is None:
        log(f"resolucao de '{nome}': NAO ENCONTRADO")
        return f"NOT_FOUND {nome}"
    log(f"resolucao de '{nome}' -> {registro[0]}:{registro[1]}")
    return f"FOUND {registro[0]} {registro[1]}"


def handle_list(argumentos):
    with trava_tabela:
        itens = " ".join(f"{n}={ip}:{p}" for n, (ip, p) in tabela_servicos.items())
    return f"SERVICES {itens}".strip()


COMANDOS = {
    "REGISTER": handle_register,
    "RESOLVE": handle_resolve,
    "LIST": handle_list,
}


def handle_client(conexao: socket.socket, endereco) -> None:
    log(f"conexao de {endereco[0]}:{endereco[1]} ({threading.current_thread().name})")
    leitor = LineReader(conexao)
    try:
        with conexao:
            while True:
                linha = leitor.readline()
                if linha is None:
                    break
                if not linha:
                    continue
                partes = linha.split()
                tratador = COMANDOS.get(partes[0].upper())
                resposta = tratador(partes[1:]) if tratador else f"ERROR comando desconhecido: {partes[0]}"
                send_line(conexao, resposta)
    except (ConnectionError, OSError) as erro:
        log(f"erro na conexao com {endereco}: {erro}")


def main() -> None:
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind((IP_SERVIDOR_NOMES, PORTA_SERVIDOR_NOMES))
    servidor.listen()
    servidor.settimeout(1.0)
    log(f"escutando em {IP_SERVIDOR_NOMES}:{PORTA_SERVIDOR_NOMES} (TCP)")
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
