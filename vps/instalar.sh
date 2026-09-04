#!/usr/bin/env bash
# =============================================================================================
# instalar.sh — prepara uma VPS Ubuntu 24.04 do ZERO para rodar a cadeia macro-direction
#               sempre ligada (vps/loop.py) e servir o painel pelo nginx.
#
# COMO USAR (como root, logo depois de criar a VPS):
#     bash instalar.sh                          -> painel pelo IP, sem HTTPS
#     bash instalar.sh radar.seudominio.com     -> painel pelo dominio, com HTTPS (certbot)
#     bash instalar.sh radar.seudominio.com voce@email.com   -> idem, com e-mail no certificado
#
# E IDEMPOTENTE: pode rodar de novo quantas vezes quiser. Cada passo confere se ja foi feito.
#
# O QUE ELE FAZ, NA ORDEM
#   1. apt: python3, git, nginx, certbot
#   2. cria o usuario 'hci' (sem senha, sem sudo) — o servico NUNCA roda como root
#   3. gera a chave SSH de deploy (ed25519) do usuario hci e IMPRIME a chave publica
#   4. clona o repositorio em /home/hci/hci-fund-radar (remoto por SSH, para poder dar push)
#   5. cria vps/.env (vazio) para a chave do BLS
#   6. instala e liga o servico systemd hci-macro
#   7. configura o nginx servindo o clone como site estatico (IP ou dominio)
#   8. certbot, se veio dominio
#   9. firewall (ufw): SSH, HTTP, HTTPS
#
# O que ele NAO faz: colar a chave no GitHub (isso e voce, na tela) e preencher o BLS_API_KEY.
# =============================================================================================
set -euo pipefail

# --------------------------------------------------------------------------- parametros
USUARIO="hci"
CASA="/home/${USUARIO}"
CLONE="${CASA}/hci-fund-radar"
REPO_HTTPS="https://github.com/yeIIoe/hci-fund-radar.git"
REPO_SSH="git@github.com:yeIIoe/hci-fund-radar.git"
DOMINIO="${1:-}"          # opcional: radar.seudominio.com
EMAIL="${2:-}"            # opcional: e-mail para o certbot
SERVICO="hci-macro"

# --------------------------------------------------------------------------- funcoes
titulo() { echo; echo "=================================================================="; echo "  $*"; echo "=================================================================="; }
como_hci() { sudo -u "${USUARIO}" -H bash -c "$*"; }

if [ "$(id -u)" -ne 0 ]; then
  echo "Rode como root:  sudo bash instalar.sh"; exit 1
fi

# --------------------------------------------------------------------------- 1. pacotes
titulo "1/9  pacotes do sistema (python3, git, nginx, certbot)"
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y python3 git nginx certbot python3-certbot-nginx ca-certificates curl ufw
python3 --version
git --version

# --------------------------------------------------------------------------- 2. usuario
titulo "2/9  usuario '${USUARIO}' (o servico nunca roda como root)"
if id "${USUARIO}" >/dev/null 2>&1; then
  echo "usuario ${USUARIO} ja existe"
else
  adduser --disabled-password --gecos "HCI Fund Radar" "${USUARIO}"
  echo "usuario ${USUARIO} criado"
fi
# O nginx (usuario www-data) precisa ENTRAR na pasta home para ler o site.
# No Ubuntu 24.04 a home nasce 750; 755 deixa ler, nao deixa escrever.
chmod 755 "${CASA}"

# --------------------------------------------------------------------------- 3. chave SSH
titulo "3/9  chave SSH de deploy (ed25519) do usuario ${USUARIO}"
como_hci "mkdir -p ${CASA}/.ssh && chmod 700 ${CASA}/.ssh"
if [ -f "${CASA}/.ssh/id_ed25519" ]; then
  echo "chave ja existe: ${CASA}/.ssh/id_ed25519"
else
  como_hci "ssh-keygen -t ed25519 -N '' -C 'hci-vps-deploy' -f ${CASA}/.ssh/id_ed25519"
  echo "chave gerada"
fi
# GitHub na lista de hosts conhecidos, para o git nao perguntar 'yes/no' no primeiro push
if ! grep -q "github.com" "${CASA}/.ssh/known_hosts" 2>/dev/null; then
  como_hci "ssh-keyscan -t ed25519 github.com >> ${CASA}/.ssh/known_hosts 2>/dev/null"
fi
como_hci "chmod 600 ${CASA}/.ssh/id_ed25519 ${CASA}/.ssh/known_hosts"

# --------------------------------------------------------------------------- 4. clone
titulo "4/9  clone do repositorio em ${CLONE}"
if [ -d "${CLONE}/.git" ]; then
  echo "clone ja existe — atualizando (git pull)"
  como_hci "cd ${CLONE} && git pull --rebase --autostash origin main || true"
else
  # clona por HTTPS (repo publico, funciona antes da deploy key), depois troca para SSH
  como_hci "git clone ${REPO_HTTPS} ${CLONE}"
fi
como_hci "cd ${CLONE} && git remote set-url origin ${REPO_SSH}"
como_hci "cd ${CLONE} && git config user.name hci-bot && git config user.email bot@hokiresearch.com"
como_hci "cd ${CLONE} && git config pull.rebase true"
# Se o ssh-keyscan acima falhou em silencio (rede), o git nao pode ficar parado numa pergunta
# 'yes/no' que ninguem vai responder: aceita a chave do GitHub na primeira vez.
como_hci "cd ${CLONE} && git config core.sshCommand 'ssh -o StrictHostKeyChecking=accept-new'"
como_hci "mkdir -p ${CLONE}/vps/logs"
chmod 755 "${CLONE}"
if [ ! -f "${CLONE}/vps/hci-macro.service" ] || [ ! -f "${CLONE}/vps/loop.py" ]; then
  echo
  echo "ERRO: ${CLONE}/vps/ nao tem loop.py e hci-macro.service."
  echo "      A pasta vps/ ainda nao foi publicada no GitHub (Passo 0 do INSTALAR.md)."
  echo "      Faca o commit + push no Windows e rode este instalador de novo."
  exit 1
fi

# --------------------------------------------------------------------------- 5. .env
titulo "5/9  vps/.env (chave do BLS)"
if [ -f "${CLONE}/vps/.env" ]; then
  echo ".env ja existe — nao mexi"
else
  como_hci "printf '# chave da API do BLS (gratis, 500 chamadas/dia): https://data.bls.gov/registrationEngine/\nBLS_API_KEY=\n' > ${CLONE}/vps/.env"
  echo ".env criado VAZIO em ${CLONE}/vps/.env — preencha BLS_API_KEY= depois"
fi
como_hci "chmod 600 ${CLONE}/vps/.env"

# --------------------------------------------------------------------------- 6. systemd
titulo "6/9  servico systemd ${SERVICO}"
cp "${CLONE}/vps/hci-macro.service" "/etc/systemd/system/${SERVICO}.service"
systemctl daemon-reload
systemctl enable "${SERVICO}"
systemctl restart "${SERVICO}"
sleep 2
systemctl --no-pager --lines=5 status "${SERVICO}" || true

# --------------------------------------------------------------------------- 7. nginx
titulo "7/9  nginx servindo o painel (${DOMINIO:-pelo IP})"
NOME_SERVIDOR="${DOMINIO:-_}"
cat > /etc/nginx/sites-available/hci-radar <<NGINX
# Painel HCI Fund Radar — a pasta do clone, servida como site estatico.
server {
    listen 80;
    listen [::]:80;
    server_name ${NOME_SERVIDOR};

    root ${CLONE};
    index index.html;

    # os JSONs mudam a cada minuto: o navegador nao pode guardar copia velha
    location /data/ {
        add_header Cache-Control "no-cache, must-revalidate";
        try_files \$uri =404;
    }

    location / {
        try_files \$uri \$uri/ =404;
    }

    # nunca expor o .git, o .env, os logs e os scripts da VPS
    location ~ /\\.git { deny all; }
    location /vps/     { deny all; }
    location ~ \\.(py|bat|vbs|md|bak|log)\$ { deny all; }
}
NGINX
ln -sf /etc/nginx/sites-available/hci-radar /etc/nginx/sites-enabled/hci-radar
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl enable nginx
systemctl reload nginx

# --------------------------------------------------------------------------- 8. certbot
titulo "8/9  HTTPS (certbot)"
if [ -n "${DOMINIO}" ]; then
  if [ -n "${EMAIL}" ]; then
    certbot --nginx -d "${DOMINIO}" --non-interactive --agree-tos -m "${EMAIL}" --redirect || \
      echo "certbot falhou — o DNS do dominio ja aponta para este IP? Rode de novo depois."
  else
    certbot --nginx -d "${DOMINIO}" --non-interactive --agree-tos --register-unsafely-without-email --redirect || \
      echo "certbot falhou — o DNS do dominio ja aponta para este IP? Rode de novo depois."
  fi
else
  echo "sem dominio: painel so por http://IP (sem HTTPS). Para HTTPS rode: bash instalar.sh SEU.DOMINIO"
fi

# --------------------------------------------------------------------------- 9. firewall
titulo "9/9  firewall (ufw): 22, 80, 443"
ufw allow 22/tcp  >/dev/null
ufw allow 80/tcp  >/dev/null
ufw allow 443/tcp >/dev/null
ufw --force enable >/dev/null
ufw status | head -n 8

# --------------------------------------------------------------------------- resumo
IP_PUBLICO="$(curl -s --max-time 5 https://api.ipify.org || hostname -I | awk '{print $1}')"
CHAVE_PUB="$(cat ${CASA}/.ssh/id_ed25519.pub)"

titulo "PRONTO. Faltam DUAS coisas que so voce pode fazer:"
cat <<FIM

(1) COLAR A CHAVE DE DEPLOY NO GITHUB — sem isto o push nao funciona.
    Abra:  https://github.com/yeIIoe/hci-fund-radar/settings/keys
    Clique "Add deploy key"
      Title:            hci-vps
      Key:              (cole a linha abaixo, INTEIRA)
      Allow write access:  MARQUE a caixinha  <-- obrigatorio
    Clique "Add key".

${CHAVE_PUB}

(2) CHAVE DO BLS (opcional, mas recomendado: 500 chamadas/dia em vez de 25)
    nano ${CLONE}/vps/.env         (preencha BLS_API_KEY=suachave, Ctrl+O, Enter, Ctrl+X)
    systemctl restart ${SERVICO}

DEPOIS, CONFIRA:
    systemctl status ${SERVICO}
    journalctl -u ${SERVICO} -f
    tail -f ${CLONE}/vps/logs/loop.log
    painel:  http://${IP_PUBLICO}/${DOMINIO:+   ou   https://${DOMINIO}/}

FIM
