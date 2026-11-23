# Relatório: Sistema Cliente-Servidor com Servidor de Nomes (TCP/UDP)

**Disciplina:** CIN154 Redes de Computadores (UFPE, CIn)
**Professor:** Kelvin Lopes Dias
**Grupo:** Pedro Siqueira de Barros
**Repositório:** https://github.com/Peubarros1/Projeto-redes

> Versão em Markdown do relatório. A versão final, com todas as imagens, é entregue em PDF/Word. Os prints estão na pasta [prints/](prints/).

---

## 1. Descrição do Projeto

O sistema tem três tipos de componente que conversam por sockets usando um protocolo de texto simples (mensagens em string terminadas em `\n`):

1. **Servidor de nomes** (`name_server.py`): serviço de diretório que mantém em memória a tabela `nome do serviço → (ip, porta)`. Escuta em `127.0.0.1:5000` (TCP) e atende cada conexão em uma thread.
2. **Serviços de aplicação**: uma calculadora (ADD, SUB, MUL, DIV) disponibilizada duas vezes:
   - `tcp_server.py`, com o nome `calc-tcp` em `127.0.0.1:6000`, uma thread por conexão;
   - `udp_server.py`, com o nome `calc-udp` em `127.0.0.1:6001`, uma thread por datagrama.
   Ambos se registram no servidor de nomes assim que iniciam (registro feito via TCP).
3. **Clientes**: `tcp_client.py` e `udp_client.py` não conhecem o endereço dos serviços. Eles primeiro consultam o servidor de nomes e só depois falam diretamente com o serviço, medindo o tempo da requisição. `missing_client.py` pede um serviço que não existe para demonstrar o tratamento de erro.

### Protocolo

| Componente | Requisição | Resposta |
|---|---|---|
| Servidor de nomes | `REGISTER <nome> <ip> <porta>` | `OK` / `ERROR <motivo>` |
| Servidor de nomes | `RESOLVE <nome>` | `FOUND <ip> <porta>` / `NOT_FOUND <nome>` |
| Calculadora | `<OP> <a> <b>` | `RESULT <valor>` / `ERROR <motivo>` |

## 2. Instruções de funcionamento para teste

Ordem obrigatória (os servidores devem ficar rodando):

1. `python name_server.py` (ou `make name-server`)
2. `python tcp_server.py` e `python udp_server.py` (ou `make tcp-server` / `make udp-server`)
3. Clientes: `python tcp_client.py MUL 6 7`, `python udp_client.py DIV 10 4`, `python missing_client.py`
4. Benchmark: `python benchmark.py -n 300`

No Windows sem `make`: `.\run.ps1 servers`, depois `.\run.ps1 clients` e `.\run.ps1 benchmark`.

Se um serviço subir antes do servidor de nomes, ele tenta se registrar de novo a cada 1 s (até 10 tentativas) em vez de falhar na hora.

## 3. Prints do funcionamento

### 3.1 Aplicação

Prints em [prints/terminal/](prints/terminal/). Horários dos logs: servidor de nomes às 23:16:43, `calc-tcp` registrado às 23:16:55, `calc-udp` às 23:17:06 e clientes a partir de 23:17:17.

| Print | O que mostra |
|---|---|
| [01_servidor_de_nomes](prints/terminal/01_servidor_de_nomes.png) | Registros de `calc-tcp` e `calc-udp`, resoluções dos clientes e `servico-fantasma` como NAO ENCONTRADO; uma thread por conexão (Thread-1 a Thread-5) |
| [02_servidor_tcp](prints/terminal/02_servidor_tcp.png) | Registro de `calc-tcp` e a requisição `MUL 6 7` → `RESULT 42` vinda da porta 56556 |
| [03_servidor_udp](prints/terminal/03_servidor_udp.png) | Requisição `DIV 10 4` → `RESULT 2.5` vinda da porta 61347 |
| [04_cliente_tcp](prints/terminal/04_cliente_tcp.png) | Resolução em 4,3 ms, `RESULT 42`, requisição de 21,4 ms (21,0 ms abrindo a primeira conexão) |
| [05_cliente_udp](prints/terminal/05_cliente_udp.png) | Resolução em 21,6 ms, `RESULT 2.5`, requisição de 1,2 ms |
| [06_servico_inexistente](prints/terminal/06_servico_inexistente.png) | Mensagem de serviço não registrado e encerramento normal (erro tratado) |

### 3.2 Wireshark

Captura na interface de loopback (Npcap *Adapter for loopback traffic capture*) com o filtro `tcp.port == 5000 || tcp.port == 6000 || udp.port == 6001`. Prints em [prints/wireshark/](prints/wireshark/).

| Figura | Filtro | O que mostra |
|---|---|---|
| [1](prints/wireshark/01_registro_e_resolucao_porta5000.png) | `tcp.port == 5000` | Pacotes 197–207: registro de `calc-tcp` (SYN, SYN-ACK, ACK, `REGISTER` com 33 bytes, `OK` com 3 bytes, FIN/ACK), 11 pacotes. 238–248: o mesmo para `calc-udp`, também via TCP. 267–276: `RESOLVE calc-tcp` (17 bytes) → `FOUND 127.0.0.1 6000` (21 bytes) |
| [2](prints/wireshark/02_visao_geral_filtro_completo.png) | completo | 282–288: fim da requisição TCP. 294–304: cliente UDP resolve `calc-udp`. 305–306: os 2 datagramas UDP. 315–325: `RESOLVE servico-fantasma` → `NOT_FOUND servico-fantasma` |
| [3](prints/wireshark/03_requisicao_tcp_porta6000.png) | `tcp.port == 6000` | 11 pacotes: handshake (278–280), `MUL 6 7` com 8 bytes (281), ACK, `RESULT 42` com 10 bytes (283), ACK, encerramento (285–288). Só 2 dos 11 carregam dados |
| [4](prints/wireshark/04_requisicao_udp_porta6001.png) | `udp.port == 6001` | Só 2 pacotes: `DIV 10 4` (9 bytes) e `RESULT 2.5` (11 bytes). O pacote tem 41 bytes para 9 de dados (cabeçalho UDP de 8 bytes), contra 52 para 8 de dados no TCP (cabeçalho de 20 bytes) |
| [5](prints/wireshark/05_seguir_fluxo_tcp.png) | Seguir → Fluxo TCP | O texto trocado: `MUL 6 7` (cliente) e `RESULT 42` (servidor) |

| Requisição | Pacotes | Pacotes com dados | Cabeçalho de transporte |
|---|---|---|---|
| TCP | 11 | 2 | 20 bytes |
| UDP | 2 | 2 | 8 bytes |

No TCP a troca de dados vem depois do estabelecimento da conexão, cada segmento é confirmado (ACK) e a conexão termina com FIN. No UDP cada mensagem vai sozinha em um datagrama, sem confirmação nem garantia de entrega; por isso o cliente UDP implementa timeout e retransmissão.

## 4. Linha de raciocínio resolutiva

1. **Definir o protocolo primeiro.** Comandos curtos em texto, uma linha por mensagem, para ficarem legíveis tanto no terminal quanto no Wireshark (aba "Follow TCP/UDP Stream").
2. **Servidor de nomes central.** Com ele, os clientes não precisam ter endereços fixos no código: basta saber o nome lógico do serviço. Se o serviço mudar de porta ou máquina, só o registro muda. Isso desacopla clientes e servidores, como faz o DNS.
3. **Concorrência.** Cada conexão (ou datagrama, no UDP) é tratada em uma thread própria, para que um cliente lento não bloqueie os demais. A tabela do servidor de nomes é protegida por um `threading.Lock`, porque várias threads podem ler e escrever nela ao mesmo tempo.
4. **Framing no TCP.** O TCP entrega um fluxo de bytes, não mensagens. Um `recv()` pode trazer meia linha ou duas linhas juntas. Por isso foi criada a classe `LineReader`, que acumula bytes até achar o `\n`. No UDP isso não é necessário, porque cada datagrama já é uma mensagem completa.
5. **Confiabilidade no UDP.** Como o UDP pode perder pacotes, o cliente UDP usa timeout de 2 s e até 3 tentativas antes de reportar erro.
6. **Ordem de inicialização.** O serviço abre o socket **antes** de se registrar, para nunca anunciar um endereço que ainda não atende. Se o servidor de nomes não estiver no ar, o serviço tenta registrar de novo periodicamente.
7. **Medição.** Foi usado `time.perf_counter()` (relógio de alta resolução). No TCP, o tempo da requisição inclui connect, envio e recebimento, e o tempo de conexão (handshake) também é mostrado separado. No UDP, vai do `sendto` ao `recvfrom`.

## 5. Implementação do código

| Módulo | Função / classe | Responsabilidade |
|---|---|---|
| `common.py` | constantes | IPs, portas, nomes dos serviços, timeouts |
| | `send_line(sock, text)` | envia uma linha terminada em `\n` |
| | `LineReader.readline()` | lê uma linha completa de um socket TCP (trata a fragmentação) |
| | `name_server_request(cmd)` | abre conexão TCP com o servidor de nomes, envia o comando e devolve a resposta |
| | `resolve(nome)` | retorna `(ip, porta)` ou `None` se `NOT_FOUND` |
| | `calculate(req)` | lógica da calculadora, compartilhada pelos servidores TCP e UDP; valida formato, números e divisão por zero |
| `name_server.py` | `handle_register` | valida ip (`ipaddress`) e porta (1 a 65535); insere ou atualiza a tabela; responde `OK`/`ERROR` |
| | `handle_resolve` | responde `FOUND ip porta` ou `NOT_FOUND nome` |
| | `handle_client` | thread por conexão; lê comandos em loop e despacha |
| | `main` | `bind`/`listen` em 127.0.0.1:5000 e `accept` em loop criando threads |
| `registration.py` | `register_service` | envia `REGISTER` com novas tentativas se o servidor de nomes estiver fora do ar |
| `tcp_server.py` | `main`, `handle_client` | escuta na 6000, registra `calc-tcp`, uma thread por conexão |
| `udp_server.py` | `main`, `handle_datagram` | escuta na 6001, registra `calc-udp`, uma thread por datagrama recebido, responde com `sendto` |
| `tcp_client.py` | `tcp_request` | connect, envio, leitura, fechamento; devolve resposta e tempos |
| `udp_client.py` | `udp_request` | `sendto`/`recvfrom` com timeout e retransmissão |
| `missing_client.py` | `main` | resolve um nome não registrado e trata `NOT_FOUND`, falha de conexão e resposta inválida |
| `benchmark.py` | `main` | N requisições intercaladas TCP/UDP após aquecimento; estatísticas e CSV em `results/` |

Erros tratados: entrada inválida no registro (ip, porta, número de argumentos), comando desconhecido, serviço inexistente, servidor de nomes fora do ar, operação inválida ou divisão por zero na calculadora, timeout no UDP e porta UDP inalcançável (ICMP, no Windows aparece como `ConnectionResetError`).

## 6. Resultado: comparação TCP x UDP

Medição com `python benchmark.py -n 300` (300 amostras por medida, 10 de aquecimento descartadas, requisição `MUL 12345 6789`, tudo em loopback 127.0.0.1, Windows 11, Python 3.14). 

| Medida | Média (ms) | Mediana (ms) | Mín (ms) | Máx (ms) | p95 (ms) |
|---|---|---|---|---|---|
| Resolução de nome (TCP) | 5,940 | 2,099 | 0,565 | 26,965 | 22,080 |
| TCP: só o handshake | 6,897 | 1,175 | 0,316 | 26,451 | 24,061 |
| TCP: requisição completa | 7,832 | 2,164 | 0,671 | 26,686 | 24,764 |
| UDP: requisição completa | 1,521 | 1,232 | 0,502 | 39,097 | 2,255 |

**Análise:**

- Por requisição, o UDP foi cerca de **5x mais rápido em média** (e cerca de 1,8x pela mediana). A diferença vem quase toda do estabelecimento da conexão TCP: só o handshake já custa mais do que a requisição UDP inteira. Retirando o handshake, a troca de dados em si (≈1 ms) é parecida nos dois protocolos.
- O TCP mostrou variação bem maior (p95 ≈ 25 ms contra ≈ 2 ms no UDP). Criar e fechar uma conexão envolve mais chamadas ao sistema operacional e mais pacotes (≈10 contra 2), o que dá mais chances de atraso por escalonamento.
- A resolução de nome também usa TCP, por isso tem custo parecido com o de uma requisição TCP. Ela é feita **uma vez** e o endereço é reaproveitado nas requisições seguintes.
- Em loopback não há perda de pacotes, então o UDP nunca precisou retransmitir. Numa rede real com perda, o UDP dependeria do timeout de 2 s do cliente, enquanto o TCP retransmite sozinho, de forma transparente e mais rápida.
- O máximo isolado do UDP (39 ms) é um ponto fora da curva causado pelo SO; mediana e p95 mostram o comportamento típico.

O arquivo `results/benchmark.csv` traz todas as amostras para montar gráficos (por exemplo, histograma ou boxplot TCP x UDP).

## 7. Conclusão Final

O projeto cumpre os requisitos: há um servidor de nomes que registra e resolve serviços dinamicamente, dois serviços de aplicação (TCP e UDP) em portas fixas que se anunciam ao iniciar, clientes que descobrem os serviços em tempo de execução e tratamento correto de serviço inexistente. A comparação confirma a teoria: o UDP tem menor latência e overhead para mensagens curtas do tipo pergunta e resposta, porque não estabelece conexão. O TCP oferece entrega confiável e ordenada ao custo do handshake e dos ACKs. Para uma calculadora, em que cada requisição é pequena e independente, o UDP com uma retransmissão simples já basta. Para dados maiores ou que não podem se perder, o TCP é o mais adequado.

## 8. Declaração / explicação de autoria **[PREENCHER: com as palavras do grupo]**

> Esta seção precisa ser escrita pelo próprio grupo; ela é usada para verificar se vocês entenderam o trabalho. Pontos que o enunciado pede para cobrir:
>
> - Como o código e o relatório foram desenvolvidos e se/como IA foi usada como apoio (declarar com honestidade).
> - Por que usar um servidor de nomes central (veja a seção 4, item 2).
> - Por que separar TCP e UDP (comparar conexão x sem conexão, confiabilidade x latência).
> - Dificuldades encontradas (ex.: framing de mensagens no TCP, ICMP "port unreachable" no Windows virando `ConnectionResetError` no UDP, captura de loopback no Wireshark, ordem de inicialização).
> - O raciocínio por trás das soluções.
>
> Antes de entregar, todos do grupo devem conseguir explicar qualquer trecho do código.
