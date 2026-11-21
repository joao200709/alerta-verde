# Fluxos do guarda — RF004 a RF008

## Autenticação e áreas

A equipe cria o guarda pelo terminal. Cinco falhas no intervalo de 15 minutos bloqueiam a conta por 15 minutos. Uma autenticação bem-sucedida zera os contadores. Ao sair, o servidor revoga a sessão. Após 30 minutos sem acesso a páginas internas, exige novo login.

Ao cadastrar uma área, o servidor atribui o guarda autenticado e começa com situação ativa. Nome deve ter de 3 a 120 caracteres, endereço de 5 a 200, bairro e município de 2 a 100, e UF duas letras. O tipo deve ser praça ou parque. O banco garante unicidade de nome, endereço, município e UF após normalização. A edição registra autor e data. O guarda confirma a desativação em uma tela própria. As denúncias anteriores continuam disponíveis ao visitante e ao guarda.

## Fila e atualização

A fila inclui ocorrências das áreas sob responsabilidade do guarda, inclusive áreas inativas. A busca aceita protocolo, nome da área ou categoria e pode ser combinada com situação. Os resultados são apresentados do mais recente ao mais antigo, dez por página. Abrir o caso exibe dados autorizados, foto e histórico e preserva a situação atual.

| Situação atual | Mudanças permitidas |
| --- | --- |
| Recebida | Em análise |
| Em análise | Em atendimento, resolvida ou rejeitada |
| Em atendimento | Resolvida ou rejeitada |
| Resolvida ou rejeitada | Encerrada |

Uma denúncia aberta também aceita resposta sem mudança de situação. O texto exige de 10 a 500 caracteres. O servidor verifica o vínculo com a área, confere o instante da última atualização e exige recarregar a tela em caso de conflito. Situação, resposta, autor e evento são gravados juntos. A conta de aplicação tem apenas SELECT e INSERT no histórico.

## Cenário de aceite

Com dois guardas e áreas distintas, verifique os links diretos de edição, denúncia e foto. Só o responsável tem acesso. Abra o mesmo atendimento em duas abas e salve na primeira. A segunda deve receber um conflito. Após encerrar o caso, confirme que o histórico pode ser lido e que a opção de responder deixou de aparecer.

