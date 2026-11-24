import socket

IP_SERVIDOR_NOMES = "127.0.0.1"
PORTA_SERVIDOR_NOMES = 5000

NOME_SERVICO_TCP = "calc-tcp"
IP_SERVICO_TCP = "127.0.0.1"
PORTA_SERVICO_TCP = 6000

NOME_SERVICO_UDP = "calc-udp"
IP_SERVICO_UDP = "127.0.0.1"
PORTA_SERVICO_UDP = 6001

CODIFICACAO = "utf-8"
TAMANHO_BUFFER = 1024
TEMPO_LIMITE_UDP = 2.0
MAX_TENTATIVAS_UDP = 3


def send_line(soquete: socket.socket, texto: str) -> None:
    soquete.sendall((texto + "\n").encode(CODIFICACAO))


class LineReader:
    def __init__(self, soquete: socket.socket):
        self.soquete = soquete
        self.buffer = b""

    def readline(self):
        while b"\n" not in self.buffer:
            pedaco = self.soquete.recv(TAMANHO_BUFFER)
            if not pedaco:
                return None
            self.buffer += pedaco
        linha, self.buffer = self.buffer.split(b"\n", 1)
        return linha.decode(CODIFICACAO).strip()


def name_server_request(comando: str) -> str:
    with socket.create_connection((IP_SERVIDOR_NOMES, PORTA_SERVIDOR_NOMES), timeout=5) as soquete:
        send_line(soquete, comando)
        resposta = LineReader(soquete).readline()
        if resposta is None:
            raise ConnectionError("servidor de nomes fechou a conexão sem responder")
        return resposta


def resolve(nome_servico: str):
    resposta = name_server_request(f"RESOLVE {nome_servico}")
    partes = resposta.split()
    if partes and partes[0] == "FOUND" and len(partes) == 3:
        return partes[1], int(partes[2])
    if partes and partes[0] == "NOT_FOUND":
        return None
    raise ValueError(f"resposta inesperada do servidor de nomes: {resposta!r}")


def calculate(requisicao: str) -> str:
    partes = requisicao.split()
    if len(partes) != 3:
        return "ERROR formato esperado: <OP> <a> <b>"
    operacao, texto_a, texto_b = partes[0].upper(), partes[1], partes[2]
    try:
        a, b = float(texto_a), float(texto_b)
    except ValueError:
        return "ERROR operandos devem ser numericos"

    if operacao == "ADD":
        resultado = a + b
    elif operacao == "SUB":
        resultado = a - b
    elif operacao == "MUL":
        resultado = a * b
    elif operacao == "DIV":
        if b == 0:
            return "ERROR divisao por zero"
        resultado = a / b
    else:
        return "ERROR operacao invalida (use ADD, SUB, MUL ou DIV)"

    if resultado == int(resultado):
        resultado = int(resultado)
    return f"RESULT {resultado}"
