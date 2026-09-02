# Ponte MT5 → MACRO DIRECTION — instalação

O leitor precisa do **valor divulgado no instante em que sai**. O feed do Forex Factory dá
previsão e anterior, nunca o resultado — conferido três vezes em 01 e 02/set/2026.

O MetaTrader tem o calendário completo embutido, com resultado, previsão e anterior, para as
8 moedas. Mas **o pacote Python do MT5 não expõe função nenhuma de calendário** — verificado
na máquina: `MetaTrader5 5.0.5735`, zero funções com "calendar". Por isso a leitura acontece
do lado MQL5, num Service, e chega ao Python por arquivo.

---

## O que você faz — cinco passos, uma vez só

### 1. Copiar o arquivo

Copie `HCI_CalendarBridge.mq5` (desta pasta) para:

```
C:\Users\eduar\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Services\
```

Já existe um arquivo com esse nome ali, de ontem. **Substitua** — a versão nova conserta um
bug real (ver o rodapé).

### 2. Compilar

No MetaTrader: **Ferramentas → Editor MetaQuotes** (ou F4).
No Navegador do editor, abra `Services\HCI_CalendarBridge.mq5` e aperte **F7**.

Deve aparecer `0 errors, 0 warnings`.

### 3. Ligar o calendário no terminal

Se o calendário nunca foi usado, o banco local pode estar vazio.
No MetaTrader: **Exibir → Calendário** (ou Ctrl+D). Confirme que aparecem eventos.
Sem isso o Service roda mas não encontra nada.

### 4. Iniciar o Service

No MetaTrader, painel **Navegador** (Ctrl+N) → seção **Serviços** →
clique com o botão direito em `HCI_CalendarBridge` → **Adicionar serviço** →
confirme os parâmetros → **OK**.

Depois, botão direito de novo → **Iniciar**.

Na aba **Especialistas** deve aparecer:
`HCI bridge v2: sincronizado, change_id=..., poll=200ms`

### 5. Conferir do lado Python

```bash
python mt5_ponte.py
```

Deve dizer **ponte VIVA** com o batimento de poucos segundos atrás.

---

## O que acontece depois

O Service fica rodando enquanto o MetaTrader estiver aberto. A cada 200 ms ele pergunta ao
banco local do calendário o que mudou. Quando um número é divulgado, ele aparece na próxima
volta e é escrito em:

```
MQL5\Files\hci_calendar.ndjson      uma linha por valor novo ou revisado
MQL5\Files\hci_bridge_status.json   batimento, para o Python saber que está vivo
```

Não há rede, não há limite de requisição — é um banco local.

---

## ⚠️ A latência ainda não é conhecida, e é isso que vamos medir

Relatos no fórum da MQL5 vão de **15 segundos a mais de 2 minutos**, e um moderador da própria
MetaQuotes escreveu que *"atraso dentro de 1 minuto é normal"*. A alegação de "dezenas de
milissegundos" é material de venda, contradita pelos próprios usuários.

Por isso cada linha traz `latencia_ms` — o intervalo entre o **horário do evento** e o
**instante em que o valor apareceu na ponte**. Depois de alguns dias, `mt5_ponte.py` mostra a
distribuição e a pergunta fica respondida com número.

**Isso decide o projeto:** se a mediana for de segundos, a ponte serve para disparar na
notícia. Se for de minutos, ela serve para arquivar, e a leitura ao vivo precisa de outra
fonte.

**O primeiro teste bom é o NFP de sexta, 09:30 ET** — evento de alto impacto, hora conhecida.

---

## 🔴 O bug que a versão nova conserta

A versão anterior fazia:

```mql5
double Val(long v){ return (v==LONG_MIN) ? 0.0 : (double)v/1000000.0; }
```

Campo **vazio** virava `0.0`. Então *"sem previsão"* e *"previsão de 0,0%"* ficavam idênticos
no arquivo. E havia sinalizador só para o resultado e para o revisado — não para previsão nem
para anterior.

Não é hipotético: **o CPI mensal da Suíça tem previsão de 0,0%** no calendário desta semana.
O leitor classificaria um valor legítimo como ausente, ou o inverso.

É o mesmo gênero do arquivo do dólar que continha a série da libra: **valor plausível,
silenciosamente errado.** A versão nova emite `null` de verdade e tem sinalizador para os
quatro campos.

---

## ⚠️ Relógio

Os horários da ponte vêm em **hora do servidor do broker**, não em UTC. A FTMO opera em
GMT+2/+3 conforme o horário de verão europeu. O campo `gmt_offset_h` do arquivo de status
traz o deslocamento medido pelo próprio terminal, e `mt5_ponte.py` usa ele para converter.

Sem isso o evento entra com até 3 horas de erro — o tipo de bug que já custou caro duas vezes
neste projeto.
