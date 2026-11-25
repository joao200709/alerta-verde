# PRD do Alerta Verde

## Problema e resultado esperado

Quem encontra lixo, vandalismo ou danos em uma praça pode fazer uma denúncia pelo Alerta Verde. O guarda responsável recebe o registro pelo painel. Com o protocolo e o código de acesso, o visitante acompanha o caso desde o recebimento até a conclusão.

## Públicos e acesso

O visitante pesquisa áreas ativas pelo navegador. Pode se identificar para receber o PDF por e-mail ou fazer a denúncia anônima e baixar o comprovante na hora. Para consultar uma denúncia, precisa do protocolo e do código de acesso. A equipe cria as contas dos guardas, e cada guarda atende as áreas sob sua responsabilidade. A instalação e o site usam contas diferentes no PostgreSQL.

## Escopo e critérios de aceite

| ID | Funcionalidade | O que deve acontecer |
| --- | --- | --- |
| RF001 | Consultar áreas verdes | Buscar por nome, bairro ou endereço, filtrar tipo e navegar por páginas de até dez áreas ativas em ordem alfabética. |
| RF002 | Registrar denúncia | O visitante escolhe o tipo antes de preencher o formulário e pode anexar uma foto PNG. Depois do envio, recebe protocolo, código de acesso e PDF. Se repetir o envio, recebe o mesmo protocolo. O site envia o PDF por e-mail somente para denúncias identificadas, quando o envio estiver configurado. |
| RF003 | Acompanhar denúncia | O par protocolo/código permite consultar situação, foto e histórico sem expor identidade ou código no resultado. |
| RF004 | Autenticar guarda | Uma conta ativa entra no painel. Cinco erros em 15 minutos bloqueiam novos acessos por 15 minutos. A sessão termina ao sair ou após 30 minutos de inatividade. |
| RF005 | Gerenciar áreas | Cadastrar, editar, ativar e confirmar desativação. Uma área inativa deixa a busca pública e conserva seus atendimentos. |
| RF006 | Consultar denúncias no painel | O guarda filtra suas denúncias por situação, busca protocolo, área ou categoria e abre detalhes sem mudar o estado. |
| RF007 | Atualizar atendimento | O guarda pode responder e, se quiser, escolher uma mudança de situação permitida. Se alguém atualizar a denúncia enquanto ele estiver editando, precisa recarregar a página antes de salvar. |
| RF008 | Manter histórico | O recebimento é automático. Cada atualização acrescenta um evento com data, situação, texto e autor na mesma transação. |

## Regras do produto

A denúncia identificada aparece como `PUBLICA` no SQL. Só o guarda responsável pode ver o nome e o e-mail do visitante. Na denúncia `ANONIMA`, o banco guarda esses campos como `NULL`. Nos dois tipos, o visitante pode acompanhar o atendimento. Apenas áreas ativas recebem novas denúncias. Quando a situação chega a **Resolvida** ou **Rejeitada**, o atendimento é encerrado.

## Metas de qualidade

A interface deve funcionar entre 360 e 1.920 px. Quem usa o teclado precisa ver qual elemento está em foco, e os formulários devem indicar os erros de preenchimento.

Com 20 usuários ao mesmo tempo e uma base de 1.000 denúncias, pelo menos 95% das consultas devem terminar em até 3 segundos e 95% dos registros em até 5 segundos. Esse é o critério de desempenho chamado p95.

A equipe deve guardar uma cópia diária do banco e das fotos em um local separado e testar a recuperação todo mês. Em caso de perda, as metas são recuperar os dados com no máximo 24 horas de defasagem (RPO) e voltar a funcionar em até 4 horas (RTO). [Resultados dos testes](docs/validacao.md)

## Referências do projeto

Documento de Requisitos Alerta Verde, CESMAC, 2026, elaborado por Diogo Paes Maia e João Paulo de Castro Portela. Plano de Avaliação Integrada AV03, Programação Orientada a Objetos, 2026.2. Scripts e prompts dos requisitos 1 a 5 fornecidos pela dupla. Este PRD traduz o documento de Engenharia de Software para o formato Markdown pedido em POO.

