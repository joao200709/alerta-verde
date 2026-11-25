# Instalação, e-mail e recuperação

## Rodar a demonstração no Windows

Usamos Python 3.14 e PostgreSQL 18 com suporte a ICU. Depois de instalar os dois, abra o PowerShell na pasta que contém `demonstracao.py` e execute os comandos abaixo.

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe demonstracao.py
```

Abra [o Alerta Verde no navegador](http://127.0.0.1:5000/). Na primeira execução, o script aplica os cinco arquivos SQL em um banco de demonstração e cadastra seis áreas e uma conta de guarda. O terminal mostra o e-mail e a senha dessa conta. Deixe a janela aberta enquanto usa o site. Pressione `Ctrl+C` para encerrar.

Se o script não encontrar o PostgreSQL, ajuste o caminho abaixo para a pasta `bin` da sua instalação e rode a demonstração de novo.

```powershell
$env:PG_BIN = 'C:\Program Files\PostgreSQL\18\bin'
```

## Usar um PostgreSQL já instalado

Use um banco dedicado no PostgreSQL e uma conta com permissão de administrador. Se as tabelas já existirem, compare as definições antes de executar os scripts. As três contas do projeto (chamadas de *roles* no PostgreSQL) são registradas na instância inteira. O arquivo de permissões altera o acesso ao schema `public` do banco em que é executado.

Em um terminal com `psql` no PATH, crie um banco vazio e entre nele. Execute a partir da raiz do projeto.

```powershell
createdb -h localhost -U postgres -E UTF8 alerta_verde
psql -X -h localhost -U postgres -d alerta_verde
```

No prompt do psql, execute na ordem:

```sql
\set ON_ERROR_STOP on
BEGIN;
\i sql/01_tabelas.sql
\i sql/02_trigger.sql
\i sql/03_indice.sql
\i sql/04_permissoes.sql
\i sql/05_view.sql
COMMIT;
\password alerta_admin
\password alerta_app
\password alerta_leitura
\q
```

Os arquivos do trabalho original trazem uma senha de exemplo para as contas. Nesta entrega as contas são criadas com LOGIN e a senha é definida no prompt privado do psql. O índice de unicidade usa a collation ICU `und-x-icu` para que as letras acentuadas também sejam convertidas em um banco inicializado com locale C. Em uma instalação anterior com esses índices já existentes, mantenha o esquema original se a conversão regional já atender ao teste de duplicidade do projeto.

Crie o ambiente Python e instale as dependências com os dois primeiros comandos da [demonstração](#rodar-a-demonstração-no-windows). Use PowerShell 7 para os comandos abaixo. Gere a chave do site uma vez e guarde-a no gerenciador de segredos do ambiente.

```powershell
$env:PGHOST = '127.0.0.1'
$env:PGPORT = '5432'
$env:PGPASSWORD = Read-Host 'Senha de alerta_app' -MaskInput
$env:ALERTA_DSN = 'dbname=alerta_verde user=alerta_app'
$env:ALERTA_CHAVE = .\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_hex(32))"
.\.venv\Scripts\python.exe -m flask --app alerta criar-guarda
.\.venv\Scripts\python.exe -m flask --app alerta run
```

A equipe fornece nome, e-mail e senha do guarda no terminal. O site usa a conta técnica `alerta_app`. O código de acompanhamento e a senha do guarda são protegidos com Argon2id. O guarda pode cadastrar suas primeiras áreas pelo painel. Para relatórios, conecte com `alerta_leitura` e execute `SELECT * FROM view_acompanhamento_denuncia;`.

## Enviar comprovantes por e-mail

Antes de iniciar o site, configure `SMTP_HOST`, `SMTP_PORT` (padrão 587), `SMTP_FROM`, `SMTP_USER` e `SMTP_PASSWORD`. O padrão `SMTP_TLS=1` negocia STARTTLS. O servidor deve autorizar o remetente informado. Para um capturador de e-mail isolado na máquina de demonstração que aceite SMTP simples, use `SMTP_TLS=0` e deixe o usuário e a senha vazios. A mensagem contém o PDF para o endereço confirmado pela pessoa. Em caso de falha, o site informa como baixá-lo no navegador.

## HTTPS e dados locais

Na demonstração, o site só abre no computador onde está rodando. Para hospedar, use um servidor WSGI de um único processo com threads, HTTPS, `ALERTA_HTTPS=1` e uma `ALERTA_CHAVE` persistente. A sessão do guarda termina após 30 minutos sem atividade no painel. Se houver um proxy, aceite a informação de IP apenas de um proxy confiável. O site usa o IP que recebe para contar as tentativas de consulta.

Fotos ficam em `instance/fotos` na instalação normal e em `instance/demo/fotos` na demonstração. Restrinja acesso a essa pasta e aos arquivos de configuração local. A aplicação entrega cada foto depois de autorizar a consulta.

## Backup e restauração

O plano do semestre prevê backup diário em dispositivo ou armazenamento separado, retenção suficiente para recuperação e teste mensal cronometrado. A equipe responsável configura o agendamento no ambiente de hospedagem. Para obter um conjunto consistente, coloque o site em manutenção durante a cópia do banco e das fotos. Use um operador com leitura das quatro tabelas e acesso à pasta privada de fotos.

Exemplo em PowerShell para a instalação normal. Ajuste `D:\Backups\AlertaVerde` para o volume separado. O banco continua ativo durante o dump. O teste de restauração deve usar um banco vazio.

```powershell
$destino = Join-Path 'D:\Backups\AlertaVerde' (Get-Date -Format yyyyMMdd-HHmmss)
New-Item -ItemType Directory -Path $destino
pg_dump -h localhost -U postgres -d alerta_verde -Fc -f "$destino\alerta.dump"
if ($LASTEXITCODE) { throw 'Backup do banco falhou' }
Copy-Item -LiteralPath '.\instance\fotos' -Destination "$destino\fotos" -Recurse
```

Preserve também as configurações e as credenciais no cofre da equipe. Para recuperar em outro servidor, provisione primeiro as três roles citadas no SQL e a role proprietária do dump, ou use uma conta administradora e ajuste a propriedade restaurada. A cópia lógica de um banco não inclui senhas das roles globais.

```powershell
createdb -h localhost -U postgres -E UTF8 alerta_recuperado
pg_restore -h localhost -U postgres -d alerta_recuperado --exit-on-error "$destino\alerta.dump"
```

Restaure a pasta `fotos` em uma nova instalação, aponte `ALERTA_DSN` para o banco recuperado e abra um protocolo conhecido. Verifique conteúdo da foto, situação, contagem de eventos e permissões da conta de aplicação. Registre o instante do backup, duração da restauração e resultado antes de colocar o banco recuperado em uso. As metas são perder no máximo 24 horas de dados e restabelecer o serviço em até quatro horas.

