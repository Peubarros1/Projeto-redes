"""
Configuração e funções utilitárias compartilhadas por todos os componentes.

Protocolo de texto simples (todas as mensagens terminam com '\n'):

  Servidor de nomes (TCP, porta NAME_SERVER_PORT):
    REGISTER <nome> <ip> <porta>   ->  OK | ERROR <motivo>
    RESOLVE <nome>                 ->  FOUND <ip> <porta> | NOT_FOUND <nome> | ERROR <motivo>
    LIST                           ->  SERVICES <nome>=<ip>:<porta> ... (auxiliar, para depuração)

  Serviço de aplicação (calculadora, TCP e UDP):
    <OP> <a> <b>   (OP em ADD, SUB, MUL, DIV)  ->  RESULT <valor> | ERROR <motivo>
"""

import socket

# --- Endereços e portas fixos (definidos no código, fora da faixa reservada 0-1023) ---
NAME_SERVER_HOST = "127.0.0.1"
NAME_SERVER_PORT = 5000

TCP_SERVICE_NAME = "calc-tcp"
TCP_SERVICE_HOST = "127.0.0.1"
TCP_SERVICE_PORT = 6000

UDP_SERVICE_NAME = "calc-udp"
UDP_SERVICE_HOST = "127.0.0.1"
UDP_SERVICE_PORT = 6001

ENCODING = "utf-8"
BUFFER_SIZE = 1024
UDP_TIMEOUT = 2.0      # segundos esperando a resposta UDP antes de retransmitir
UDP_RETRIES = 3        # tentativas de envio no cliente UDP


def send_line(sock: socket.socket, text: str) -> None:
    """Envia uma linha de texto terminada em '\\n' por um socket TCP."""
    sock.sendall((text + "\n").encode(ENCODING))


class LineReader:
    """
    Lê linhas de um socket TCP.

    O TCP é um fluxo de bytes: uma chamada recv() pode trazer meia mensagem
    ou várias mensagens juntas. Por isso guardamos um buffer e só devolvemos
    quando encontramos o '\\n' que delimita a mensagem.
    """

    def __init__(self, sock: socket.socket):
        self.sock = sock
        self.buffer = b""

    def readline(self):
        """Retorna a próxima linha (sem '\\n') ou None se a conexão foi fechada."""
        while b"\n" not in self.buffer:
            chunk = self.sock.recv(BUFFER_SIZE)
            if not chunk:
                return None
            self.buffer += chunk
        line, self.buffer = self.buffer.split(b"\n", 1)
        return line.decode(ENCODING).strip()


def name_server_request(command: str) -> str:
    """Abre uma conexão TCP com o servidor de nomes, envia um comando e devolve a resposta."""
    with socket.create_connection((NAME_SERVER_HOST, NAME_SERVER_PORT), timeout=5) as sock:
        send_line(sock, command)
        reply = LineReader(sock).readline()
        if reply is None:
            raise ConnectionError("servidor de nomes fechou a conexão sem responder")
        return reply


def resolve(service_name: str):
    """
    Consulta o servidor de nomes.
    Retorna (ip, porta) se o serviço existir, ou None se não estiver registrado.
    Levanta ConnectionError/OSError se o servidor de nomes estiver inacessível.
    """
    reply = name_server_request(f"RESOLVE {service_name}")
    parts = reply.split()
    if parts and parts[0] == "FOUND" and len(parts) == 3:
        return parts[1], int(parts[2])
    if parts and parts[0] == "NOT_FOUND":
        return None
    raise ValueError(f"resposta inesperada do servidor de nomes: {reply!r}")


def calculate(request: str) -> str:
    """Lógica da aplicação (calculadora), usada pelos servidores TCP e UDP."""
    parts = request.split()
    if len(parts) != 3:
        return "ERROR formato esperado: <OP> <a> <b>"
    op, a_txt, b_txt = parts[0].upper(), parts[1], parts[2]
    try:
        a, b = float(a_txt), float(b_txt)
    except ValueError:
        return "ERROR operandos devem ser numericos"

    if op == "ADD":
        result = a + b
    elif op == "SUB":
        result = a - b
    elif op == "MUL":
        result = a * b
    elif op == "DIV":
        if b == 0:
            return "ERROR divisao por zero"
        result = a / b
    else:
        return "ERROR operacao invalida (use ADD, SUB, MUL ou DIV)"

    # Mostra inteiro quando o resultado não tem parte fracionária (ex.: 5 em vez de 5.0)
    if result == int(result):
        result = int(result)
    return f"RESULT {result}"
