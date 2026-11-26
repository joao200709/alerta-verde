# ADR 001 · Acesso ao PostgreSQL com SQL direto

**Status** · Adotado no projeto

## Contexto

O trabalho de Banco de Dados já tinha scripts PostgreSQL para criar as tabelas, a trigger de recebimento, o índice, as contas e a view. A aplicação em Python precisava ler e gravar dados nessa mesma estrutura. Uma operação importante é salvar a mudança de situação e o evento do histórico juntos.

## Decisão

Usamos o Psycopg para conectar o Python ao PostgreSQL e executar consultas SQL com parâmetros. A classe `Banco` cuida da conexão e da transação. As classes `Catalogo`, `Guardas` e `CentralDenuncias` escrevem as consultas de que precisam.

Também seria possível usar um ORM, uma biblioteca que mapeia classes Python para tabelas. Escolhemos escrever o SQL porque podemos aproveitar os scripts da disciplina e ler no próprio código quais tabelas cada operação consulta ou altera. [Scripts do banco](../sql/) · [Classe `Banco`](../alerta/banco.py#L12)

## Consequências

Quando o guarda muda a situação de uma denúncia, dá para ver o `UPDATE` da denúncia e o `INSERT` do histórico dentro da mesma transação. Se uma gravação falhar, o PostgreSQL desfaz as duas. Como escrevemos as consultas à mão, uma mudança no esquema também exige revisar as consultas que usam as tabelas ou colunas alteradas. [Atualização de atendimento](../alerta/denuncias.py#L88)
