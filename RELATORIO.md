# Relatório: Sistema Cliente-Servidor com Servidor de Nomes (TCP/UDP)

**Disciplina:** CIN154 Redes de Computadores (UFPE, CIn)
**Professor:** Kelvin Lopes Dias
**Grupo:** _(nomes e logins)_
**Repositório:** https://github.com/Peubarros1/Projeto-redes

> Rascunho para passar ao template oficial (Word/PDF). Os trechos marcados com **[PREENCHER]** dependem da execução de vocês (prints, números do benchmark na sua máquina, seção de autoria).

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

### 3.1 Aplicação **[PREENCHER com prints]**

- Terminal do servidor de nomes mostrando os registros de `calc-tcp` e `calc-udp` e as resoluções.
- Terminais dos servidores TCP e UDP mostrando as requisições atendidas.
- Cliente TCP, por exemplo:
  ```
  [CLIENTE TCP] 'calc-tcp' resolvido para 127.0.0.1:6000 em 8.177 ms
  [CLIENTE TCP] 'MUL 6 7' -> 'RESULT 42' | conexao 0.898 ms | total da requisicao 1.846 ms
  ```
- Cliente UDP, por exemplo:
  ```
  [CLIENTE UDP] 'calc-udp' resolvido para 127.0.0.1:6001 em 5.000 ms
  [CLIENTE UDP] 'DIV 10 4' -> 'RESULT 2.5' | total da requisicao 1.110 ms
  ```
- Serviço inexistente (prova de tratamento de erro):
  ```
  [CLIENTE] Solicitando ao servidor de nomes a resolucao de 'servico-fantasma'...
  [CLIENTE] O servico 'servico-fantasma' NAO esta registrado. Verifique o nome ou se o servidor do servico foi iniciado.
  [CLIENTE] Encerrando normalmente (erro tratado).
  ```
  No log do servidor de nomes aparece `resolucao de 'servico-fantasma': NAO ENCONTRADO`. O cliente termina com código 0, sem exceção e sem travar.

### 3.2 Wireshark **[PREENCHER com prints]**

Captura na interface de loopback (Npcap *Adapter for loopback traffic capture*) com o filtro
`tcp.port == 5000 || tcp.port == 6000 || udp.port == 6001`. Sugestão de prints e do que comentar em cada um:

| Print | Filtro | O que deve aparecer / comentar |
|---|---|---|
| Registro dos serviços | `tcp.port == 5000` | Handshake de 3 vias (SYN, SYN-ACK, ACK) entre uma porta efêmera e a 5000; segmento PSH com `REGISTER calc-tcp 127.0.0.1 6000`; resposta `OK`; encerramento com FIN/ACK. Cerca de 9 a 10 pacotes por registro. |
| Resolução de nome | `tcp.port == 5000` | Mesma estrutura: `RESOLVE calc-tcp` → `FOUND 127.0.0.1 6000`. Para o serviço inexistente: `RESOLVE servico-fantasma` → `NOT_FOUND servico-fantasma`. |
| Requisição TCP | `tcp.port == 6000` | Handshake + `MUL 6 7` + `RESULT 42` + ACKs + FIN. Cerca de 9 a 10 pacotes para trocar uma pergunta e uma resposta. |
| Requisição UDP | `udp.port == 6001` | Só **2 pacotes**: o datagrama `DIV 10 4` e o datagrama `RESULT 2.5`. Sem handshake, sem ACK, sem encerramento. |

Diferenças a destacar: no TCP a troca de dados vem depois do estabelecimento da conexão e cada segmento é confirmado (ACK), com números de sequência; no UDP cada mensagem vai sozinha em um datagrama, com cabeçalho de 8 bytes (contra 20+ do TCP), sem confirmação nem garantia de entrega. É por isso que o cliente UDP implementa timeout e retransmissão.

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

Medição com `python benchmark.py -n 300` (300 amostras por medida, 10 de aquecimento descartadas, requisição `MUL 12345 6789`, tudo em loopback 127.0.0.1, Windows 11, Python 3.14). **[PREENCHER: rodar de novo na máquina de vocês e substituir os números]**

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
