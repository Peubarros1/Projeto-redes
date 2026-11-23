"""Registro de um serviço de aplicação no servidor de nomes (usado pelos servidores TCP e UDP)."""

import time

from common import name_server_request


def register_service(name: str, ip: str, port: int, log, attempts: int = 10, delay: float = 1.0) -> bool:
    """
    Envia REGISTER ao servidor de nomes (via TCP).
    Se o servidor de nomes ainda não estiver no ar, tenta novamente algumas vezes,
    pois a ordem de execução exige que ele suba primeiro.
    """
    for attempt in range(1, attempts + 1):
        try:
            reply = name_server_request(f"REGISTER {name} {ip} {port}")
        except OSError as exc:
            log(f"servidor de nomes indisponivel ({exc}); tentativa {attempt}/{attempts}")
            time.sleep(delay)
            continue
        if reply == "OK":
            log(f"registrado no servidor de nomes como '{name}' -> {ip}:{port}")
            return True
        log(f"servidor de nomes recusou o registro: {reply}")
        return False
    log("nao foi possivel contatar o servidor de nomes")
    return False
