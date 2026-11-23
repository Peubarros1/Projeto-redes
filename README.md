# Projeto Cliente-Servidor (TCP/UDP) com Servidor de Nomes

CIN154 Redes de Computadores (UFPE, CIn). Implementado em Python 3 só com a biblioteca padrão (`socket`, `threading`).

## Arquitetura

```
                    +---------------------------+
   REGISTER (TCP)   |   Servidor de Nomes       |   RESOLVE (TCP)
  +---------------->|   127.0.0.1:5000          |<-----------------+
  |                 |   tabela nome -> (ip,porta)|                 |
  |                 +---------------------------+                  |
  |                                                                |
+-+-----------------+     requisição/resposta TCP      +-----------+--+
| Serviço TCP       |<---------------------------------| Cliente TCP  |
| calc-tcp :6000    |                                  +--------------+
+-------------------+
+-------------------+     datagrama UDP / resposta     +--------------+
| Serviço UDP       |<---------------------------------| Cliente UDP  |
| calc-udp :6001    |                                  +--------------+
+-------------------+
```

| Componente | Arquivo | Endereço |
|---|---|---|
| Servidor de nomes (TCP) | `name_server.py` | 127.0.0.1:5000 |
| Serviço calculadora TCP | `tcp_server.py` | 127.0.0.1:6000, nome `calc-tcp` |
| Serviço calculadora UDP | `udp_server.py` | 127.0.0.1:6001, nome `calc-udp` |
| Cliente TCP | `tcp_client.py` | resolve `calc-tcp` |
| Cliente UDP | `udp_client.py` | resolve `calc-udp` |
| Cliente do serviço inexistente | `missing_client.py` | resolve `servico-fantasma` |
| Benchmark TCP x UDP | `benchmark.py` | — |
| Configuração e protocolo | `common.py`, `registration.py` | — |

## Protocolo (texto, uma mensagem por linha terminada em `\n`)

Servidor de nomes:

| Requisição | Resposta |
|---|---|
| `REGISTER <nome> <ip> <porta>` | `OK` ou `ERROR <motivo>` (ip/porta inválidos, argumentos faltando) |
| `RESOLVE <nome>` | `FOUND <ip> <porta>` ou `NOT_FOUND <nome>` |
| `LIST` | `SERVICES nome=ip:porta ...` (auxiliar) |

Serviço de aplicação (calculadora): `ADD|SUB|MUL|DIV <a> <b>` → `RESULT <valor>` ou `ERROR <motivo>`.

## Como executar

Requisito: Python 3.8+. **A ordem importa**: o servidor de nomes primeiro, depois os serviços (que se registram nele ao iniciar) e por último os clientes. Deixe os servidores rodando.

### Com Makefile (um terminal por servidor)

```bash
make name-server     # terminal 1
make tcp-server      # terminal 2
make udp-server      # terminal 3
make clients         # terminal 4: cliente TCP, cliente UDP, serviço inexistente
make benchmark       # comparação de tempos TCP x UDP
```

Em Linux/macOS/Git Bash também dá para usar `make up` (sobe os três em segundo plano) e `make down`.
No Windows com MinGW, use `mingw32-make` no lugar de `make`.

### Com PowerShell (Windows, sem make)

```powershell
.\run.ps1 servers     # abre 3 janelas: nomes -> TCP -> UDP
.\run.ps1 clients
.\run.ps1 benchmark
```

### Manualmente

```bash
python name_server.py
python tcp_server.py
python udp_server.py
python tcp_client.py MUL 6 7          # ou: python tcp_client.py ADD 1 2 -n 20
python udp_client.py DIV 10 4
python missing_client.py servico-fantasma
python benchmark.py -n 300
```

## Captura no Wireshark

Na mesma máquina, capture na interface de loopback (no Windows: *Adapter for loopback traffic capture*, instalada com o Npcap) e use o filtro:

```
tcp.port == 5000 || tcp.port == 6000 || udp.port == 6001
```

Filtros individuais: `tcp.port == 5000` (registro/resolução), `tcp.port == 6000` (serviço TCP), `udp.port == 6001` (serviço UDP).

## Resultados

| | TCP | UDP |
|---|---|---|
| Pacotes por requisição (Wireshark) | 11 | 2 |
| Tempo médio por requisição (`benchmark.py -n 300`) | 7,8 ms | 1,5 ms |

Prints da execução em [prints/terminal/](prints/terminal/) e da captura em [prints/wireshark/](prints/wireshark/). Análise completa em [RELATORIO.md](RELATORIO.md).

## Autor

Pedro Siqueira de Barros
