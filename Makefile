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
