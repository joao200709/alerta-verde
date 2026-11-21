# Validação do Alerta Verde

Ensaios executados em 20/11/2026, no Windows, com Python 3.14.3, Flask 3.1.3, Psycopg 3.3.9 e PostgreSQL 18.0 em uma instância local descartável. O site conectou como `alerta_app`. Os dados utilizados foram fictícios.

## Resultados

| Verificação | Resultado observado |
| --- | --- |
| Instalação da demonstração | Um cluster vazio foi inicializado, os cinco scripts foram aplicados, três áreas e um guarda foram criados e o banco foi encerrado pelo comando de preparação. |
| Domínio e POO | Os testes instanciaram os dois subtipos de denúncia, verificaram os valores de identificação e exercitaram as 25 combinações de situação de origem e destino. |
| Visitante e persistência | Registro identificado e anônimo, validação de PNG, busca, PDF, histórico, acesso privado à foto e falha de SMTP passaram. Um envio repetido recuperou o mesmo comprovante. Dois POST simultâneos do mesmo formulário produziram o mesmo protocolo e código, com um único evento inicial. |
| Acesso do guarda | Os testes usaram duas contas. O guarda de outra área não conseguiu consultar denúncia, foto ou edição pelo endereço direto. A aplicação recusou requisição administrativa sem o token do formulário. |
| Estados e sessão | Cinco senhas incorretas bloquearam o login. Foram verificados o bloqueio público por IP e protocolo, o vencimento temporal, o logout e a expiração por inatividade. Uma atualização antiga recebeu HTTP 409. Encerrar o caso retirou a opção de responder. |
| Áreas e histórico | Duplicata com espaços e caixa diferentes foi recusada, inclusive em “Praça”/“PRAÇA”. Desativar impediu novo registro e preservou consulta ao histórico. Reativar recolocou a área na busca. |
| Permissões e relatórios | O catálogo do PostgreSQL confirmou o índice em situação, a ausência de DELETE para a aplicação e de UPDATE do histórico. A conta de leitura não tinha SELECT em denúncia. A view retornou o registro esperado sob a role de leitura. |
| Correio e comprovante | Uma denúncia identificada enviou anexo para um capturador SMTP local. O PDF recebido e o baixado no Chrome tinham o mesmo SHA-256. O teste de falha do SMTP confirmou a manutenção do registro e do download. |
| Recuperação | Executados pg_dump, cópia das fotos e pg_restore em outro banco. A aplicação recuperada aceitou o protocolo e o código anteriores, exibiu o histórico e devolveu os mesmos bytes do PNG. |
| Navegadores | Chrome 157.0.8103.79 a 1.920 e 360 px e Firefox 153.0 a 360 px concluíram escolha, registro, download e acompanhamento. As verificações de largura passaram em busca, formulário e resultado. |

## Desempenho — NF003

O ensaio acrescentou 1.000 denúncias e usou 20 clientes Flask concorrentes, com conexão real ao PostgreSQL. Cada cliente fez cinco acompanhamentos com código válido e cinco registros anônimos sem foto. O tempo inclui a requisição, acesso ao banco e renderização HTML no servidor de teste. O teste exclui a rede externa, o navegador e o SMTP.

| Operação | Amostra | p95 medido | Meta |
| --- | ---: | ---: | ---: |
| Consulta com protocolo e código | 100 | 0,595 s | Até 3 s |
| Registro de denúncia | 100 | 0,609 s | Até 5 s |

Os valores descrevem esta execução local. A homologação de Chrome para Android em aparelho real, a entrega por um provedor SMTP externo e a operação continuada dos backups dependem do ambiente da equipe. O ensaio de recuperação verifica a restauração funcional. O cumprimento contínuo das metas de RPO/RTO depende do agendamento e das medições no ambiente implantado.

## Reproduzir

Com as dependências instaladas, os testes de domínio executam sem banco:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_dominio -v
```

Para os testes integrados, use uma base descartável com os cinco scripts aplicados e as credenciais da conta `alerta_app`. Os testes acrescentam contas, áreas e denúncias. Configure a senha pela variável `PGPASSWORD` como no guia de operação.

```powershell
$env:ALERTA_TEST_DSN = 'host=127.0.0.1 port=5432 dbname=alerta_teste user=alerta_app'
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m tests.carga
```

Os seis testes de domínio e integração passaram. O ensaio de carga grava mais 1.100 denúncias por execução e requer capacidade para pelo menos 20 conexões simultâneas da aplicação.


## Ferramentas de apoio

O OpenAI Codex (família GPT-6) apoiou a implementação e os testes. Foram usados os recursos de leitura de documentos e de PDF para conferir os anexos e revisar o material de avaliação. Os prompts de Banco de Dados constam no PDF e no TXT de entrega.
