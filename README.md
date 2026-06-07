# Controle de Figurinhas Copa do Mundo 2026

Base Flask para autenticacao com email e senha, cadastro, recuperacao de senha por email e bloqueio por excesso de tentativas.

## Stack

- Flask
- PostgreSQL via Flask-SQLAlchemy e psycopg
- Flask-Login
- Flask-WTF com CSRF
- Flask-Mail para SMTP Gmail
- Flask-Limiter para rate limit

## Configuracao local

1. Crie um ambiente virtual e instale as dependencias:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Copie `.env.example` para `.env` e ajuste `SECRET_KEY`, `DATABASE_URL`, `POSTGRES_SCHEMA` e credenciais de email.

3. Crie o banco PostgreSQL definido em `DATABASE_URL`.

O projeto usa por padrao:

```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@127.0.0.1:5432/fwc_26
POSTGRES_SCHEMA=app
```

A estrutura da URL e:

```text
postgresql+psycopg://USUARIO:SENHA@IP:PORTA/NOME_DO_BANCO
```

Se sua senha tiver caracteres especiais, codifique antes de colocar na URL. Exemplo:

```text
Minha@Senha#123 -> Minha%40Senha%23123
```

Para confirmar qual configuracao o Flask carregou:

```powershell
flask --app run.py show-db-config
```

Se o banco e o schema ja existirem, o usuario informado em `DATABASE_URL` precisa ter permissao para criar tabelas no schema `app`.
Execute algo assim no PostgreSQL com um usuario administrador, ajustando `app_figurinhas` para o usuario real da sua URL:

```sql
GRANT CONNECT ON DATABASE fwc_26 TO app_figurinhas;
GRANT USAGE, CREATE ON SCHEMA app TO app_figurinhas;
```

Se o schema ainda nao existir, crie-o assim:

```sql
CREATE SCHEMA app AUTHORIZATION app_figurinhas;
```

4. Inicialize o schema e as tabelas:

```powershell
flask --app run.py init-db
```

5. Rode a aplicacao:

```powershell
flask --app run.py run
```

## Gmail

Use uma senha de app do Google em `MAIL_PASSWORD`. A senha normal da conta Gmail geralmente nao funciona para SMTP.

## Seguranca implementada

- Senhas armazenadas com hash do Werkzeug.
- Senha minima de 8 caracteres com letras, numeros e caractere especial.
- CSRF em formularios.
- Rate limit por IP nas rotas de login, cadastro e recuperacao.
- Storage de rate limit configuravel por `RATELIMIT_STORAGE_URI`; em producao, use Redis ou outro backend persistente suportado pelo Flask-Limiter.
- Rate limit global configuravel por `RATELIMIT_DEFAULT`.
- Bloqueio de conta por 24h apos 5 falhas de login.
- Token de recuperacao aleatorio, armazenado apenas como SHA-256 e valido por 1h.
- Mensagem generica na recuperacao para nao revelar emails cadastrados.
- Cookies de sessao `HttpOnly` e `SameSite=Lax`.
- Headers de seguranca: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`, CSP e HSTS quando `SESSION_COOKIE_SECURE=true`.
- `TRUSTED_HOSTS` para mitigar Host header injection.
- `ProxyFix` configuravel para preservar IP/protocolo reais atras de proxy reverso.
- `MAX_CONTENT_LENGTH` para rejeitar corpos de requisicao grandes demais.

## Checklist para VPS

- Gere uma `SECRET_KEY` longa e aleatoria; nunca use a chave de exemplo.
- Use HTTPS e configure `SESSION_COOKIE_SECURE=true`.
- Configure `APP_BASE_URL` com o dominio HTTPS real, pois links de reset de senha usam esse valor.
- Configure `TRUSTED_HOSTS` com o dominio e aliases reais.
- Rode a app com Gunicorn atras de Nginx, Caddy ou Traefik; nao exponha Gunicorn direto na internet.
- Use `RATELIMIT_STORAGE_URI=redis://127.0.0.1:6379/0` ou outro backend compartilhado. `memory://` so serve para desenvolvimento ou instancia unica sem multiplos workers.
- Restrinja portas no firewall: publique apenas 80/443; PostgreSQL e Redis devem ficar locais ou em rede privada.
- Desative debug: `FLASK_DEBUG=0`.
- Rode o processo com usuario sem privilegio de root.

## Mitigacao de DDoS

O Flask-Limiter ajuda contra abuso de formulario e automacao simples, mas DDoS volumetrico precisa ser filtrado antes da aplicacao. Use um provedor com protecao de rede, CDN/WAF quando possivel e limite requisicoes no proxy reverso.

Exemplo minimo para Nginx:

```nginx
limit_req_zone $binary_remote_addr zone=app_per_ip:10m rate=10r/s;
limit_conn_zone $binary_remote_addr zone=conn_per_ip:10m;

server {
    listen 443 ssl http2;
    server_name seudominio.com.br www.seudominio.com.br;

    client_max_body_size 1m;
    limit_conn conn_per_ip 20;

    location /static/ {
        alias /caminho/para/figurinhas-copa-2026/app/static/;
        expires 7d;
        add_header Cache-Control "public";
    }

    location / {
        limit_req zone=app_per_ip burst=30 nodelay;
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Se usar Cloudflare ou outro CDN, ajuste Nginx para confiar apenas nos IPs do CDN antes de usar o IP real do cliente. Nao aceite `X-Forwarded-For` diretamente de clientes externos.

## Deploy no Portainer

O arquivo `docker-compose.portainer.yml` sobe a aplicacao com:

- Nginx reverso em `80` e `443`.
- Certificado HTTPS automatico via Let's Encrypt.
- Redis para rate limit compartilhado.
- App Flask sem porta publica, acessivel internamente por `figurinhas_2026_app:8000`.
- Rede Docker externa `figurinhas_2026_net`.

Antes de subir a stack:

1. Aponte o DNS `A` de `faltamquais.cloud` para o IP da VPS.
2. Se for usar `www`, aponte `www.faltamquais.cloud` tambem para a VPS.
3. Garanta que as portas `80` e `443` estejam liberadas no firewall.
4. Confirme que nenhum outro container esta usando `80` ou `443` nessa VPS.
5. Ajuste no compose: `SECRET_KEY`, `DATABASE_URL`, `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_DEFAULT_SENDER`, `DEFAULT_EMAIL` e `LETSENCRYPT_EMAIL`.

No Portainer:

1. Abra `Stacks > Add stack`.
2. Use Git Repository apontando para este projeto, ou envie os arquivos da pasta do projeto.
3. Use `docker-compose.portainer.yml`.
4. Faça o deploy.
5. Depois que o container `figurinhas_2026_app` estiver de pe, execute:

```bash
flask --app run.py init-db
```

O usuario acessa sem porta:

```text
https://faltamquais.cloud
```
