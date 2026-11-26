# Fluxos do guarda — RF004 a RF008

## Autenticação e áreas

A equipe cria a conta do guarda pelo terminal. Se ele errar cinco vezes em 15 minutos, a conta fica bloqueada por 15 minutos. Um login bem-sucedido zera o contador de erros. A sessão termina quando o guarda sai ou passa 30 minutos sem usar o painel.

A área recém-cadastrada começa ativa e fica ligada à conta do guarda que a cadastrou. O nome deve ter de 3 a 120 caracteres, o endereço de 5 a 200, o bairro e o município de 2 a 100, e a UF duas letras. O tipo deve ser praça ou parque. O banco recusa outra área com o mesmo nome, endereço, município e UF, mesmo com diferenças de maiúsculas ou espaços. A edição registra quem fez a mudança e quando. O guarda confirma a desativação em uma tela própria, e as denúncias anteriores continuam disponíveis.

## Fila e atualização

A fila inclui ocorrências das áreas sob responsabilidade do guarda, inclusive áreas inativas. A busca aceita protocolo, nome da área ou categoria e pode ser combinada com situação. Os resultados são apresentados do mais recente ao mais antigo, dez por página. Abrir o caso exibe dados autorizados, foto e histórico e preserva a situação atual.

| Situação atual | Mudanças permitidas |
| --- | --- |
| Recebida | Em análise |
| Em análise | Em atendimento, resolvida ou rejeitada |
| Em atendimento | Resolvida ou rejeitada |
| Resolvida ou rejeitada | Nenhuma mudança permitida |

O guarda pode escrever uma resposta de 10 a 500 caracteres e manter a situação atual, desde que a denúncia esteja aberta. Ao salvar, o servidor confere se a área está ligada à conta do guarda. Se outra atualização tiver sido salva desde que ele abriu a tela, o site pede que recarregue a página. A mudança de situação e o registro da resposta no histórico são gravados juntos. No histórico, a conta do site só pode consultar e acrescentar registros.

## Cenário de aceite

1. Com dois guardas responsáveis por áreas diferentes, confirme que cada um só consegue abrir as denúncias, as fotos e as telas de edição das próprias áreas, inclusive por link direto.
2. Abra a mesma denúncia em duas abas com a conta do guarda responsável. Salve uma resposta na primeira e tente salvar na segunda. O site deve pedir que você recarregue a página.
3. Mude a situação para **Resolvida** ou **Rejeitada** a partir de uma situação que permita a mudança. O histórico deve continuar visível e a opção de responder deve sumir.

