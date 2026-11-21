# PRD do Alerta Verde

## Problema e resultado esperado

Quem encontra lixo, vandalismo ou danos em uma praça precisa identificar onde registrar a ocorrência e como saber se houve atendimento. O Alerta Verde liga o visitante ao guarda responsável pela área. O resultado esperado é um protocolo verificável, com histórico desde o recebimento até a conclusão.

## Públicos e acesso

O visitante pesquisa áreas ativas pelo navegador. Pode se identificar para receber o PDF por e-mail ou permanecer anônimo e guardar o comprovante por conta própria. Somente quem apresenta protocolo e código acompanha a ocorrência. O guarda tem uma conta criada pela equipe e trabalha nas áreas vinculadas à sua conta. A equipe usa uma conta PostgreSQL própria para instalação e outra para a aplicação.

## Escopo e critérios de aceite

| ID | Funcionalidade | Evidência observável |
| --- | --- | --- |
| RF001 | Consultar áreas verdes | Buscar por nome, bairro ou endereço, filtrar tipo e navegar por páginas de até dez áreas ativas em ordem alfabética. |
| RF002 | Registrar denúncia | Escolher o tipo antes do formulário. O registro gera um protocolo e um PDF e aceita uma foto PNG opcional. Repetir o envio mantém o protocolo. Somente a identificada gera e-mail. |
| RF003 | Acompanhar denúncia | O par protocolo/código permite consultar situação, foto e histórico sem expor identidade ou código no resultado. |
| RF004 | Autenticar guarda | Uma conta ativa entra no painel. Cinco erros em 15 minutos bloqueiam novos acessos por 15 minutos. A sessão termina ao sair ou após 30 minutos de inatividade. |
| RF005 | Gerenciar áreas | Cadastrar, editar, ativar e confirmar desativação. Uma área inativa deixa a busca pública e conserva seus atendimentos. |
| RF006 | Consultar denúncias no painel | O guarda filtra suas denúncias por situação, busca protocolo, área ou categoria e abre detalhes sem mudar o estado. |
| RF007 | Atualizar atendimento | Responder ou mudar a situação segundo as transições permitidas. Edições simultâneas exigem recarregar a versão antiga. |
| RF008 | Manter histórico | O recebimento é automático. Cada atualização acrescenta um evento com data, situação, texto e autor na mesma transação. |

## Regras do produto

A denúncia identificada corresponde ao valor `PUBLICA` no SQL. Seu nome e e-mail são visíveis ao guarda responsável. A modalidade `ANONIMA` persiste ambos os campos como NULL. Ambas permitem acompanhar o atendimento. Apenas áreas ativas recebem novos registros. As situações finais são Resolvida e Rejeitada. O projeto do semestre prevê o envio do comprovante identificado por e-mail e a consulta de mudanças pelo próprio visitante.

## Metas de qualidade

A interface deve funcionar entre 360 e 1.920 px, com teclado, foco visível e mensagens de validação. O objetivo de carga é p95 de até 3 s nas consultas e 5 s nos registros, com 20 usuários simultâneos e uma base de 1.000 denúncias. A equipe deve manter cópia diária separada do banco e das fotos, com teste de recuperação mensal, RPO de 24 horas e RTO de 4 horas. O relatório de validação distingue medições e obrigações operacionais.

## Referências do projeto

Documento de Requisitos Alerta Verde, CESMAC, 2026, elaborado por Diogo Paes Maia e João Paulo de Castro Portela. Plano de Avaliação Integrada AV03, Programação Orientada a Objetos, 2026.2. Scripts e prompts dos requisitos 1 a 5 fornecidos pela dupla. Este PRD traduz o documento de Engenharia de Software para o formato Markdown pedido em POO.

