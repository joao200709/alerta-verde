# Fluxos de visitante — RF001 a RF003 e RF008

## Pesquisa e escolha

Ao abrir a página inicial, o visitante vê apenas áreas ativas ordenadas por nome e ID. O sistema combina a busca por nome, bairro ou endereço com o filtro Praça ou Parque. Cada página possui no máximo dez resultados. Uma busca vazia de resultados apresenta “Nenhuma área encontrada”. O cartão leva à escolha de identificação e mantém a área selecionada durante o registro.

## Registro e privacidade

| Campo | Regra |
| --- | --- |
| Categoria | Lixo, vegetação, vandalismo, infraestrutura ou outros |
| Descrição | De 20 a 2.000 caracteres após remover espaços nas extremidades |
| Ponto de referência | De 3 a 200 caracteres |
| Identificação | Nome de 3 a 120 caracteres e e-mail válido de até 254 na identificada. O visitante confirma o endereço de entrega do PDF. Na anônima, o servidor descarta valores enviados nesses campos. |
| Foto opcional | Uma PNG de até 5 MiB. O servidor confere o conteúdo e recodifica a imagem. O processamento aceita até 24 megapixels. |

O sistema confirma que a área continua ativa antes de gravar. A transação persiste a denúncia e o recebimento automático gerado pela trigger. O mesmo token retorna o protocolo anterior. A confirmação mostra data, hora, protocolo, código e download em PDF. Somente o registro identificado envia o comprovante ao SMTP configurado. Se esse envio falhar, o visitante pode baixar o PDF na tela. Campos textuais permanecem preenchidos após erro de validação. O navegador exige selecionar o arquivo novamente.

## Acompanhamento

O visitante fornece protocolo e código em um formulário POST. O resultado exibe área, descrição, referência, categoria, foto autorizada e histórico cronológico. Cada evento indica a situação, a hora e “Sistema” ou “Guarda responsável”. Uma credencial incorreta produz a mesma mensagem para protocolos existentes e inexistentes. Cinco erros para o mesmo IP e protocolo em 15 minutos bloqueiam a consulta por 15 minutos. O resultado omite nome, e-mail e código. A autorização da foto tem duração máxima de 30 minutos.

## Cenário de aceite

Registre uma denúncia anônima, repita o mesmo envio, baixe o PDF e consulte o protocolo. Deve existir uma única denúncia e um único evento de recebimento. Acompanhe novamente depois de uma resposta do guarda para verificar a atualização.

