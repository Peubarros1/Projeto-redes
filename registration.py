import time

from common import name_server_request


def register_service(nome: str, ip: str, porta: int, log, tentativas: int = 10, espera: float = 1.0) -> bool:
    for tentativa in range(1, tentativas + 1):
        try:
            resposta = name_server_request(f"REGISTER {nome} {ip} {porta}")
        except OSError as erro:
            log(f"servidor de nomes indisponivel ({erro}); tentativa {tentativa}/{tentativas}")
            time.sleep(espera)
            continue
        if resposta == "OK":
            log(f"registrado no servidor de nomes como '{nome}' -> {ip}:{porta}")
            return True
        log(f"servidor de nomes recusou o registro: {resposta}")
        return False
    log("nao foi possivel contatar o servidor de nomes")
    return False
