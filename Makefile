# Ordem obrigatória: 1) servidor de nomes  2) servidores TCP e UDP  3) clientes
# Rode cada servidor em um terminal próprio e deixe-os no ar:
#   terminal 1: make name-server
#   terminal 2: make tcp-server
#   terminal 3: make udp-server
#   terminal 4: make clients   (ou make tcp-client / udp-client / missing-client / benchmark)
# No Linux/macOS (ou Git Bash), "make up" sobe os três servidores em segundo plano.

PYTHON ?= python

.PHONY: name-server tcp-server udp-server up down clients tcp-client udp-client missing-client benchmark

name-server:
	$(PYTHON) -u name_server.py

tcp-server:
	$(PYTHON) -u tcp_server.py

udp-server:
	$(PYTHON) -u udp_server.py

up:
	$(PYTHON) -u name_server.py & echo $$! > .pids
	sleep 1
	$(PYTHON) -u tcp_server.py & echo $$! >> .pids
	$(PYTHON) -u udp_server.py & echo $$! >> .pids
	sleep 1

down:
	-kill $$(cat .pids) && rm -f .pids

tcp-client:
	$(PYTHON) tcp_client.py MUL 6 7

udp-client:
	$(PYTHON) udp_client.py DIV 10 4

missing-client:
	$(PYTHON) missing_client.py servico-fantasma

benchmark:
	$(PYTHON) benchmark.py -n 300

clients: tcp-client udp-client missing-client
