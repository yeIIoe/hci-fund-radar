# VPS do HCI Fund Radar — guia de instalação do zero

**Para quê:** tirar a cadeia macro-direction do cron do GitHub (que roda "a cada 15 min" mas na
prática entrega a cada 15–35 min, e às vezes pula) e colocá-la num computador alugado que fica
ligado 24 h. Lá o `vps/loop.py` roda a cadeia a cada 15 min de verdade e, em volta de cada
evento HIGH/MEDIUM, consulta a FXStreet **a cada 5 segundos** até o número sair — e só então
recalcula o sentimento e commita (antes do número não há nada novo a publicar). O resultado
é commitado no GitHub como hoje (o Pages continua funcionando) e, além disso, o painel fica
servido direto pelo IP da VPS, sem esperar o Pages.

| | |
|---|---|
| **Custo** | Hetzner CX22/CX23 (2 vCPU, 4 GB, Ubuntu 24.04): **~€4–5/mês (~R$25–35)**. Contabo e DigitalOcean: US$5–7/mês. Qualquer um serve; a cadeia usa pouquíssima máquina. |
| **Tempo** | 30 a 45 minutos, a maior parte esperando a VPS ser criada e o `apt` instalar. |
| **Pré-requisitos** | Cartão de crédito; conta no GitHub com acesso ao repositório `yeIIoe/hci-fund-radar`; Windows 10/11 com PowerShell. |

Ao longo do guia, só três coisas são suas e não posso escrever por você: **o IP da VPS**, **o
domínio (opcional)** e **as chaves** (SSH e BLS). Tudo o mais é copiar e colar.

---

## Passo 0 — Publicar a pasta `vps/` no GitHub (no seu Windows)

O instalador da VPS baixa o `instalar.sh` **do GitHub**. Então a pasta `vps/` precisa estar lá
antes. Abra o PowerShell na pasta do projeto e cole:

```powershell
cd "C:\Users\eduar\Downloads\CÓDIGOS\hci_fund_radar"
git add vps
git commit -m "vps: loop sempre ligado, service, instalador e guia"
git push origin main
```

Confira no navegador: https://github.com/yeIIoe/hci-fund-radar/tree/main/vps deve mostrar
`loop.py`, `hci-macro.service`, `instalar.sh` e este `INSTALAR.md`.
(O `vps/.gitignore` já impede que `.env` e `logs/` subam algum dia.)

---

## Passo 1 — Criar a sua chave SSH no Windows (uma vez na vida)

É com ela que você entra na VPS, sem senha. No PowerShell:

```powershell
ssh-keygen -t ed25519 -C "eduardo-windows"
```

Aperte **Enter** três vezes (aceita o caminho padrão e deixa sem senha). Depois copie a chave
pública para a área de transferência:

```powershell
Get-Content "$env:USERPROFILE\.ssh\id_ed25519.pub" | Set-Clipboard
```

Pronto: a chave está no Ctrl+V. Ela começa com `ssh-ed25519 AAAA...`.

> Se `ssh-keygen` não for reconhecido: Configurações do Windows > Aplicativos > Recursos
> opcionais > adicione **"Cliente OpenSSH"**. Vem no Windows 10/11, só pode estar desligado.

---

## Passo 2 — Criar a VPS na Hetzner

1. Crie a conta em https://www.hetzner.com/cloud (pede cartão ou PayPal e uma verificação de
   identidade que pode levar algumas horas na primeira vez).
2. Em **Cloud Console** > **New Project** (nome: `hci`) > **Add Server**.
3. Escolha:
   - **Location:** Ashburn (EUA) ou Falkenstein/Nuremberg (Alemanha). Ashburn fica mais perto
     da FXStreet/BLS/Fed; Alemanha é mais barata. Qualquer um.
   - **Image:** **Ubuntu 24.04**.
   - **Type:** Shared vCPU > **x86** > o mais barato (CX22 ou CX23).
   - **SSH keys:** clique **Add SSH key**, cole (Ctrl+V) a chave do Passo 1, dê o nome `windows`.
   - **Name:** `hci-radar`.
   - Deixe o resto no padrão. **Create & Buy now**.
4. Em um minuto aparece o servidor com um **IPv4** (algo como `65.108.xx.xx`). **Anote esse IP.**

**Contabo / DigitalOcean:** a lógica é a mesma — Ubuntu 24.04, plano mais barato, colar a sua
chave SSH pública na criação, anotar o IP.

---

## Passo 3 — Entrar na VPS pelo PowerShell

No PowerShell (troque `SEU.IP` pelo IP anotado):

```powershell
ssh root@SEU.IP
```

Na primeira vez ele pergunta `Are you sure you want to continue connecting (yes/no)?` —
digite `yes` e Enter. Se aparecer `root@hci-radar:~#`, você está dentro.

> Se pedir senha, a chave não foi anexada na criação. Na Hetzner: Server > **Rescue** >
> **Reset root password**, entre com a senha e depois cole a sua chave em
> `~/.ssh/authorized_keys`. Ou simplesmente apague o servidor e crie de novo marcando a chave.

---

## Passo 4 — Rodar o instalador (UM comando)

Dentro da VPS (o prompt `root@hci-radar:~#`), cole **uma** destas linhas:

**Sem domínio (painel pelo IP):**
```bash
curl -fsSL https://raw.githubusercontent.com/yeIIoe/hci-fund-radar/main/vps/instalar.sh -o instalar.sh && bash instalar.sh
```

**Com domínio + HTTPS** (antes, no seu registrador de domínio, crie um registro **A** apontando
`radar.hokiresearch.com` — ou o nome que quiser — para o IP da VPS, e espere uns minutos):
```bash
curl -fsSL https://raw.githubusercontent.com/yeIIoe/hci-fund-radar/main/vps/instalar.sh -o instalar.sh && bash instalar.sh radar.hokiresearch.com eduardogodooihoki@gmail.com
```

Leva de 2 a 5 minutos. Ele instala Python, git e nginx; cria o usuário `hci`; clona o
repositório em `/home/hci/hci-fund-radar`; instala o serviço; configura o nginx e o firewall.
Pode rodar de novo à vontade — ele confere o que já foi feito.

**No fim ele imprime uma chave que começa com `ssh-ed25519 AAAA... hci-vps-deploy`.** É a
chave de deploy — vá para o Passo 5 com ela na tela.

---

## Passo 5 — Colar a chave de deploy no GitHub

Sem isto a VPS lê o GitHub mas **não consegue fazer push**.

1. Copie a linha inteira `ssh-ed25519 AAAA... hci-vps-deploy`. O jeito seguro, ainda dentro da
   VPS, é imprimi-la sozinha e selecionar com o mouse do início ao fim:
   ```bash
   cat /home/hci/.ssh/id_ed25519.pub
   ```
   No Terminal do Windows, selecionar e apertar **Ctrl+C** copia (ou **Ctrl+Shift+C**); no
   PowerShell antigo (janela azul), selecionar e apertar **Enter** copia.
2. Abra https://github.com/yeIIoe/hci-fund-radar/settings/keys
3. **Add deploy key**:
   - **Title:** `hci-vps`
   - **Key:** cole a linha
   - **Allow write access:** **MARQUE** (obrigatório — sem isto o push é recusado)
4. **Add key**.

Se precisar ver a chave de novo mais tarde, na VPS:
```bash
cat /home/hci/.ssh/id_ed25519.pub
```

---

## Passo 6 — Colar a chave do BLS

A chave do BLS é grátis e sobe a cota de 25 para 500 chamadas/dia. Registre em
https://data.bls.gov/registrationEngine/ (chega por e-mail). Na VPS:

```bash
nano /home/hci/hci-fund-radar/vps/.env
```

Deixe assim (substitua pela sua chave, sem aspas, sem espaço):

```
BLS_API_KEY=a1b2c3d4e5f6...
```

Salvar: **Ctrl+O**, **Enter**; sair: **Ctrl+X**. Depois:

```bash
systemctl restart hci-macro
```

Sem a chave o serviço funciona do mesmo jeito — só que o `eua_leitor.py` fica na cota pequena.

---

## Passo 7 — Verificar

```bash
systemctl status hci-macro
```
Tem de mostrar **`active (running)`** em verde. Se mostrar `failed`, veja o log (abaixo).

```bash
journalctl -u hci-macro -f
```
Log ao vivo. Nos primeiros minutos você deve ver `RODADA COMPLETA comecando`, uma linha `ok`
por script e, se algo mudou, `publicado no GitHub (rodada completa)`. **Ctrl+C** sai.

```bash
tail -n 50 /home/hci/hci-fund-radar/vps/logs/loop.log
```
O mesmo log, gravado em arquivo. Cada script tem o seu:
`/home/hci/hci-fund-radar/vps/logs/fxstreet_calendario.log` etc.

```bash
cat /home/hci/hci-fund-radar/vps/logs/estado.json
```
Batimento resumido: última rodada, próxima rodada, último push, fast lane.

**O painel:** no navegador, `http://SEU.IP/` (ou `https://radar.hokiresearch.com/` com
domínio). É o mesmo painel do Pages, lido direto da VPS.

**O GitHub:** em https://github.com/yeIIoe/hci-fund-radar/commits/main devem aparecer commits
`macro direction ... (vps, rodada completa)` e, em dia de notícia, `(vps, fast lane)`.

**Se o push falhar** o log diz `push falhou` e `a deploy key ja esta no GitHub com WRITE?`.
Volte ao Passo 5. A VPS guarda o commit local e tenta de novo na próxima rodada — nada se perde.

---

## Passo 8 — Desligar o cron do GitHub Actions (recomendado)

Com a VPS ligada, o workflow `macro-direction` do GitHub vira um segundo robô fazendo a mesma
coisa. O `loop.py` já resolve os conflitos sozinho (a versão da VPS vence), mas é ruído. Para
desligar sem mexer em código:

https://github.com/yeIIoe/hci-fund-radar/actions > clique em **macro-direction** (na lista à
esquerda) > botão **"..."** (canto superior direito) > **Disable workflow**.

Para religar um dia (VPS fora do ar), o mesmo caminho: **Enable workflow**.

---

## Dia a dia

**Atualizar o código** (depois de você dar push de uma mudança no Windows):
```bash
sudo -u hci git -C /home/hci/hci-fund-radar pull --rebase --autostash origin main
systemctl restart hci-macro
```

**Parar / ligar / reiniciar:**
```bash
systemctl stop hci-macro
systemctl start hci-macro
systemctl restart hci-macro
```

**Ver se está vivo, de longe:** abra `http://SEU.IP/data/sentimento.json` e olhe o campo
`gerado_em` — tem de ter menos de 20 minutos.

**Rodar a cadeia uma vez na mão, sem commit** (para testar):
```bash
sudo -u hci python3 /home/hci/hci-fund-radar/vps/loop.py --uma-rodada
```

**Ver o que o loop faria, sem rodar nada** (passada seca):
```bash
sudo -u hci python3 /home/hci/hci-fund-radar/vps/loop.py --uma-vez
```

**Atualizar o sistema operacional** (uma vez por mês):
```bash
apt-get update && apt-get upgrade -y && reboot
```
O serviço volta sozinho depois do reboot (`enable` já foi feito pelo instalador).

**Renovação do HTTPS:** automática (o certbot instala um timer). Nada a fazer.

---

## O que NÃO fazer

- **Não rode a cadeia como root.** O serviço roda como o usuário `hci` de propósito. Se você
  rodar um script na mão como root dentro de `/home/hci/hci-fund-radar`, os arquivos ficam do
  root e o serviço para de conseguir escrever. Use sempre `sudo -u hci ...` como nos exemplos.
  Se já aconteceu: `chown -R hci:hci /home/hci/hci-fund-radar` e `systemctl restart hci-macro`.
- **Não commite o `.env`.** Ele tem a sua chave do BLS. O `vps/.gitignore` já bloqueia; não use
  `git add -f`. Se vazar, gere outra chave no BLS.
- **Não faça `git add .` nem `git commit` na VPS.** A VPS só commita os JSONs de `data/`, pelo
  loop. Código se edita no Windows e vem por `git pull`.
- **Não copie a chave privada** (`/home/hci/.ssh/id_ed25519`, sem `.pub`) para lugar nenhum.
  Só a `.pub` vai para o GitHub. A privada nasce e morre na VPS.
- **Não passe `--forcar`** nos scripts para "atualizar mais rápido". O BLS tem cota diária, o
  GDELT limita a taxa; os caches (60 min, 3 h, 20 h) existem por isso e o loop os respeita.
- **Não deixe dois robôs ligados** (Actions + VPS) por muito tempo — Passo 8.
- **Não abra portas além de 22, 80 e 443.** O instalador já deixa o firewall assim.

---

## Se der errado

| Sintoma | O que olhar |
|---|---|
| `ssh: connect ... timed out` | IP errado, ou a VPS ainda está sendo criada. Espere 1 min. |
| `Permission denied (publickey)` | A sua chave SSH não está na VPS (Passo 2/3). |
| `systemctl status` mostra `failed` | `journalctl -u hci-macro -n 50` mostra o erro. Quase sempre é caminho: o clone tem de estar em `/home/hci/hci-fund-radar`. |
| `push falhou` ou `pull falhou (sem conflito)` no log | Deploy key sem **write** ou não colada (Passo 5). Teste: `sudo -u hci ssh -T git@github.com` deve responder `Hi yeIIoe/hci-fund-radar!`. |
| `ERRO: .../vps/ nao tem loop.py` no instalador | A pasta `vps/` ainda não está no GitHub. Volte ao Passo 0. |
| Painel abre mas dados velhos | Ctrl+F5 no navegador; depois `cat .../vps/logs/estado.json` para ver se a rodada está acontecendo. |
| `FALHA fxstreet_calendario.py rc=1` repetido | A FXStreet não respondeu; o arquivo anterior fica. Se persistir por horas, pode ser bloqueio do IP — troque a localização da VPS. |
| `rc=2` no `eua_leitor.py` | Cota do BLS acabou. Coloque a chave (Passo 6). |
| Certbot falhou | O DNS ainda não apontava para o IP. Espere e rode `bash instalar.sh SEU.DOMINIO SEU@EMAIL` de novo. |

Para recomeçar do zero: apague o servidor na Hetzner, crie outro, repita do Passo 3. Nada de
valor mora na VPS — tudo está no GitHub.
