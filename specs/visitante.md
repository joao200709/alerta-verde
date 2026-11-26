# Fluxos de visitante — RF001 a RF003 e RF008

## Pesquisa e escolha

Na página inicial, o visitante vê as áreas ativas em ordem alfabética. A busca por nome, bairro ou endereço pode ser combinada com o filtro de praça ou parque. Cada página mostra até dez resultados. Se nenhum resultado aparecer, o site exibe “Nenhuma área encontrada”. Ao clicar em **Fazer denúncia**, o visitante escolhe o tipo de denúncia com a área já selecionada.

## Registro e privacidade

| Campo | Regra |
| --- | --- |
| Categoria | Lixo, vegetação, vandalismo, infraestrutura ou outros |
| Descrição | De 20 a 2.000 caracteres após remover espaços nas extremidades |
| Ponto de referência | De 3 a 200 caracteres |
| Identificação | Nome de 3 a 120 caracteres e e-mail válido de até 254 na identificada. O visitante confirma o endereço de entrega do PDF. Na anônima, o servidor descarta valores enviados nesses campos. |
| Foto opcional | Um arquivo PNG de até 5 MiB e 24 megapixels. O servidor confere o formato e gera uma nova cópia da imagem sem os metadados. |

Antes de gravar, o site confere se a área continua ativa. O banco salva a denúncia e cria o primeiro evento do histórico por meio da trigger. Se o visitante repetir o mesmo envio, recebe o protocolo anterior.

A confirmação mostra data, hora, protocolo e código de acesso, com um botão para baixar o PDF. Na denúncia identificada, o site também tenta enviar o comprovante por e-mail quando o serviço está configurado. O botão de download continua disponível se o e-mail falhar. Se o site devolver o formulário com um erro de preenchimento, os campos de texto continuam preenchidos. A foto precisa ser selecionada de novo.

## Acompanhamento

O visitante informa o protocolo e o código de acesso. O formulário usa POST para manter o código fora do endereço da página. Com os dados corretos, o site mostra a área, a descrição, a referência, a categoria, a foto quando houver e os eventos em ordem. Cada evento mostra a situação, a hora e o autor como “Sistema” ou “Guarda responsável”.

A tela protege o nome, o e-mail e o código de acesso. A mensagem é a mesma sempre que a combinação informada estiver incorreta. Cinco erros para o mesmo IP e protocolo em 15 minutos bloqueiam a consulta por 15 minutos. A permissão para ver a foto vale por até 30 minutos.

## Cenário de aceite

1. Registre uma denúncia anônima. Na confirmação, confira a data, a hora, o protocolo e o código. Baixe o PDF e confira se ele contém os mesmos dados.
2. Em **Acompanhar denúncia**, use o protocolo e o código. A consulta deve mostrar a situação **Recebida** e um evento inicial no histórico.
3. Depois que o guarda responder, consulte de novo. A resposta deve aparecer com o autor **Guarda responsável**.

O [teste de integração](../tests/test_integracao.py#L68) também repete o envio do mesmo formulário e verifica se o site devolve o comprovante anterior e mantém um único evento de recebimento.

