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
- Bloqueio de conta por 24h apos 5 falhas de login.
- Token de recuperacao aleatorio, armazenado apenas como SHA-256 e valido por 1h.
- Mensagem generica na recuperacao para nao revelar emails cadastrados.
- Cookies de sessao `HttpOnly` e `SameSite=Lax`.
