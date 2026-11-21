# Alerta Verde

Projeto integrado de Programação Orientada a Objetos, Engenharia de Software e Banco de Dados — CESMAC, Sistemas de Informação, 2026.2.

O visitante escolhe uma praça ou parque, registra um problema e recebe um protocolo e um código privado. O guarda responsável atende a denúncia, e o visitante pode consultar a resposta. O site implementa os oito requisitos funcionais do documento de Engenharia de Software em Python, Flask e PostgreSQL.

## Executar a demonstração no Windows

Instale Python 3.11 ou superior e PostgreSQL com ICU e ferramentas de linha de comando. A demonstração foi executada com Python 3.14 e PostgreSQL 18. Extraia o ZIP em uma pasta local. Abra o PowerShell nessa pasta, onde estão `requirements.txt` e `demonstracao.py`, e execute:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe demonstracao.py
```

Abra **http://127.0.0.1:5000**. O terminal mostra o e-mail e a senha local do guarda. O primeiro início prepara um PostgreSQL exclusivo em `instance/demo`, aplica os cinco scripts e cadastra três áreas fictícias de Maceió. Os próximos inícios reutilizam os dados. Use Ctrl+C nessa janela para encerrar o site e a instância que o comando iniciou. Se o executável do PostgreSQL estiver em outro local, defina `$env:PG_BIN` com o caminho da pasta `bin`. Para escolher outras portas, use `ALERTA_PORTA_BD` antes do primeiro início e `ALERTA_PORTA_WEB` (padrões 55438 e 5000).

Para uma instalação com o banco da dupla, configuração de e-mail, provisionamento de guardas e restauração, consulte [Operação](docs/operacao.md). Os dados locais e as senhas ficam na pasta `instance/`, excluída do pacote e do controle de versão. O pacote distribuível contém apenas código, scripts, documentação e material de avaliação.

## Apresentar em cinco minutos

1. Na página inicial, busque **Palmeiras** e escolha **Fazer denúncia → Continuar anonimamente**. Registre lixo com a descrição “Há sacos de lixo acumulados na entrada da praça” e o ponto “Portão norte”.
2. Baixe o PDF, guarde o protocolo e copie o código. Em **Acompanhar denúncia**, consulte os dois dados. O primeiro evento veio da trigger do PostgreSQL.
3. Entre na **Área administrativa** com a conta que aparece no terminal. Abra **Denúncias recebidas**, busque pelo protocolo e abra o caso em duas abas.
4. Na primeira aba, mude para **Em análise** e registre “Equipe acionada para vistoria”. Na segunda, tente salvar a versão antiga. Recarregue para ver o atendimento atual.
5. Volte ao acompanhamento público e mostre a resposta com o autor **Guarda responsável**. No código, abra `alerta/dominio.py` e siga `Denuncia.do_formulario`, `identificacao` e `Atendimento.responder`. Os [pilares de POO](docs/arquitetura.md) explicam por que cada decisão ficou nessa classe.

## Material de entrega

| Disciplina | Onde encontrar |
| --- | --- |
| POO | Código em `alerta/`, [PRD](prd.md), [arquitetura e pilares](docs/arquitetura.md), [especificação do visitante](specs/visitante.md) e [especificação do guarda](specs/guarda.md) |
| Banco de Dados | Cinco arquivos em `sql/` e [PDF para avaliação](entrega/BD_Alerta_Verde.pdf), com introdução, SQL, prompts e identificação da IA |
| Engenharia de Software | IDs RF001–RF008 preservados no PRD e nas especificações. Resultados e limites em [Validação](docs/validacao.md) |

A AV03 pede um repositório público no GitHub ou GitLab. Publique o conteúdo deste pacote após a revisão da dupla. No PDF de Banco de Dados, explicamos como usamos o Astra 6.2 e apresentamos os prompts completos junto ao SQL correspondente.

