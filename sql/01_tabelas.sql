-- =====================================================================
-- Alerta Verde - criação das tabelas (PostgreSQL 10+)
-- Ordem: guarda -> area_verde -> denuncia -> historico_denuncia
-- =====================================================================


-- ---------------------------------------------------------------------
-- 1) GUARDA: usuário com login e senha que cuida das áreas
-- ---------------------------------------------------------------------
CREATE TABLE guarda (
    id                integer GENERATED ALWAYS AS IDENTITY,
    nome              varchar(120) NOT NULL,
    email             varchar(254) NOT NULL,
    senha_hash        text         NOT NULL,   -- nunca a senha original
    ativo             boolean      NOT NULL DEFAULT true,
    -- Dados do bloqueio de login (a lógica fica no programa)
    tentativas_falhas integer      NOT NULL DEFAULT 0,
    primeira_falha_em timestamptz,
    bloqueado_ate     timestamptz,
    criado_em         timestamptz  NOT NULL DEFAULT now(),

    CONSTRAINT pk_guarda PRIMARY KEY (id),
    CONSTRAINT ck_guarda_nome
        CHECK (char_length(btrim(nome)) BETWEEN 3 AND 120),
    -- Formato simples de e-mail: algo@algo.algo, sem espaços
    CONSTRAINT ck_guarda_email_formato
        CHECK (email ~* '^[^@[:space:]]+@[^@[:space:]]+\.[^@[:space:]]+$'),
    CONSTRAINT ck_guarda_senha_hash
        CHECK (char_length(senha_hash) > 0),
    CONSTRAINT ck_guarda_tentativas_falhas
        CHECK (tentativas_falhas >= 0)
);

-- A collation ICU garante minúsculas Unicode mesmo em um banco com locale C.
-- E-mail único sem diferenciar maiúsculas de minúsculas
-- ("ANA@x.com" e "ana@x.com" são o mesmo e-mail)
CREATE UNIQUE INDEX uq_guarda_email_lower ON guarda (lower(email COLLATE "und-x-icu"));


-- ---------------------------------------------------------------------
-- 2) AREA_VERDE: praças e parques cadastrados pelos guardas
-- ---------------------------------------------------------------------
CREATE TABLE area_verde (
    id              integer GENERATED ALWAYS AS IDENTITY,
    nome            varchar(120) NOT NULL,
    tipo            varchar(10)  NOT NULL,
    endereco        varchar(200) NOT NULL,
    bairro          varchar(100) NOT NULL,
    municipio       varchar(100) NOT NULL,
    uf              char(2)      NOT NULL,
    ativa           boolean      NOT NULL DEFAULT true,  -- desativar não apaga nada
    guarda_id       integer      NOT NULL,               -- guarda responsável
    criado_em       timestamptz  NOT NULL DEFAULT now(),
    atualizado_por  integer,                             -- vazio até alguém alterar
    atualizado_em   timestamptz,                         -- vazio até alguém alterar

    CONSTRAINT pk_area_verde PRIMARY KEY (id),
    CONSTRAINT fk_area_verde_guarda
        FOREIGN KEY (guarda_id) REFERENCES guarda (id) ON DELETE RESTRICT,
    CONSTRAINT fk_area_verde_atualizado_por
        FOREIGN KEY (atualizado_por) REFERENCES guarda (id) ON DELETE RESTRICT,
    CONSTRAINT ck_area_verde_nome
        CHECK (char_length(btrim(nome)) BETWEEN 3 AND 120),
    CONSTRAINT ck_area_verde_tipo
        CHECK (tipo IN ('PRACA', 'PARQUE')),
    CONSTRAINT ck_area_verde_endereco
        CHECK (char_length(btrim(endereco)) BETWEEN 5 AND 200),
    CONSTRAINT ck_area_verde_bairro
        CHECK (char_length(btrim(bairro)) BETWEEN 2 AND 100),
    CONSTRAINT ck_area_verde_municipio
        CHECK (char_length(btrim(municipio)) BETWEEN 2 AND 100),
    CONSTRAINT ck_area_verde_uf
        CHECK (uf ~ '^[A-Za-z]{2}$'),
    -- Os dois campos de "última alteração" ficam vazios ou preenchidos juntos
    CONSTRAINT ck_area_verde_atualizacao
        CHECK ((atualizado_por IS NULL) = (atualizado_em IS NULL))
);

-- Não pode haver duas áreas iguais (nome + endereço + município + UF),
-- ignorando maiúsculas/minúsculas e espaços repetidos/nas pontas.
-- Ex.: "Praça da Paz" e "  praça  da paz " são a mesma área.
CREATE UNIQUE INDEX uq_area_verde_identidade ON area_verde (
    lower(regexp_replace(btrim(nome),      '\s+', ' ', 'g') COLLATE "und-x-icu"),
    lower(regexp_replace(btrim(endereco),  '\s+', ' ', 'g') COLLATE "und-x-icu"),
    lower(regexp_replace(btrim(municipio), '\s+', ' ', 'g') COLLATE "und-x-icu"),
    upper(uf)
);


-- ---------------------------------------------------------------------
-- 3) DENUNCIA: problema reportado em uma área (pública ou anônima)
-- ---------------------------------------------------------------------
CREATE TABLE denuncia (
    id                  integer GENERATED ALWAYS AS IDENTITY,
    protocolo           varchar(20)  NOT NULL,
    codigo_acesso_hash  text         NOT NULL,   -- nunca o código original
    -- Código único por envio do formulário: evita denúncia duplicada
    -- quando o botão "Enviar" é clicado duas vezes
    token_envio         varchar(64)  NOT NULL,
    area_id             integer      NOT NULL,
    categoria           varchar(20)  NOT NULL,
    descricao           text         NOT NULL,
    ponto_referencia    varchar(200) NOT NULL,
    foto_arquivo        varchar(255),            -- só o nome do arquivo
    tipo                varchar(10)  NOT NULL,
    nome_denunciante    varchar(120),
    email_denunciante   varchar(254),
    situacao            varchar(20)  NOT NULL DEFAULT 'RECEBIDA',
    criado_em           timestamptz  NOT NULL DEFAULT now(),
    atualizado_em       timestamptz  NOT NULL DEFAULT now(),  -- controle de edição simultânea

    CONSTRAINT pk_denuncia PRIMARY KEY (id),
    CONSTRAINT uq_denuncia_protocolo UNIQUE (protocolo),
    CONSTRAINT uq_denuncia_token_envio UNIQUE (token_envio),
    CONSTRAINT fk_denuncia_area
        FOREIGN KEY (area_id) REFERENCES area_verde (id) ON DELETE RESTRICT,
    CONSTRAINT ck_denuncia_codigo_hash
        CHECK (char_length(codigo_acesso_hash) > 0),
    CONSTRAINT ck_denuncia_categoria
        CHECK (categoria IN ('LIXO', 'VEGETACAO', 'VANDALISMO', 'INFRAESTRUTURA', 'OUTROS')),
    CONSTRAINT ck_denuncia_descricao
        CHECK (char_length(btrim(descricao)) BETWEEN 20 AND 2000),
    CONSTRAINT ck_denuncia_ponto_referencia
        CHECK (char_length(btrim(ponto_referencia)) BETWEEN 3 AND 200),
    CONSTRAINT ck_denuncia_tipo
        CHECK (tipo IN ('PUBLICA', 'ANONIMA')),
    CONSTRAINT ck_denuncia_nome_denunciante
        CHECK (nome_denunciante IS NULL
               OR char_length(btrim(nome_denunciante)) BETWEEN 3 AND 120),
    CONSTRAINT ck_denuncia_email_denunciante
        CHECK (email_denunciante IS NULL
               OR email_denunciante ~* '^[^@[:space:]]+@[^@[:space:]]+\.[^@[:space:]]+$'),
    -- Pública: nome e e-mail obrigatórios.
    -- Anônima: nome e e-mail PROIBIDOS (têm que ficar vazios).
    CONSTRAINT ck_denuncia_identificacao
        CHECK (
            (tipo = 'PUBLICA'
                AND nome_denunciante  IS NOT NULL
                AND email_denunciante IS NOT NULL)
            OR
            (tipo = 'ANONIMA'
                AND nome_denunciante  IS NULL
                AND email_denunciante IS NULL)
        ),
    CONSTRAINT ck_denuncia_situacao
        CHECK (situacao IN ('RECEBIDA', 'EM_ANALISE', 'EM_ATENDIMENTO', 'RESOLVIDA', 'REJEITADA'))
);


-- ---------------------------------------------------------------------
-- 4) HISTORICO_DENUNCIA: "diário" da denúncia (só cresce)
-- ---------------------------------------------------------------------
CREATE TABLE historico_denuncia (
    id                 integer GENERATED ALWAYS AS IDENTITY,
    denuncia_id        integer      NOT NULL,
    tipo_evento        varchar(15)  NOT NULL,
    situacao_anterior  varchar(20),
    situacao_atual     varchar(20)  NOT NULL,
    texto              varchar(500) NOT NULL,
    autor_guarda_id    integer,                  -- vazio = foi o próprio sistema
    criado_em          timestamptz  NOT NULL DEFAULT now(),

    CONSTRAINT pk_historico_denuncia PRIMARY KEY (id),
    CONSTRAINT fk_historico_denuncia
        FOREIGN KEY (denuncia_id) REFERENCES denuncia (id) ON DELETE RESTRICT,
    CONSTRAINT fk_historico_autor_guarda
        FOREIGN KEY (autor_guarda_id) REFERENCES guarda (id) ON DELETE RESTRICT,
    CONSTRAINT ck_historico_tipo_evento
        CHECK (tipo_evento IN ('RECEBIMENTO', 'ATUALIZACAO')),
    CONSTRAINT ck_historico_situacao_anterior
        CHECK (situacao_anterior IS NULL
               OR situacao_anterior IN ('RECEBIDA', 'EM_ANALISE', 'EM_ATENDIMENTO', 'RESOLVIDA', 'REJEITADA')),
    CONSTRAINT ck_historico_situacao_atual
        CHECK (situacao_atual IN ('RECEBIDA', 'EM_ANALISE', 'EM_ATENDIMENTO', 'RESOLVIDA', 'REJEITADA')),
    CONSTRAINT ck_historico_texto
        CHECK (char_length(btrim(texto)) >= 1
               AND (tipo_evento <> 'ATUALIZACAO' OR char_length(btrim(texto)) >= 10)),
    -- RECEBIMENTO: sem situação anterior, situação atual RECEBIDA, sem autor (sistema).
    -- ATUALIZACAO: situação anterior e autor obrigatórios
    -- (a situação atual pode ser igual à anterior).
    CONSTRAINT ck_historico_coerencia
        CHECK (
            (tipo_evento = 'RECEBIMENTO'
                AND situacao_anterior IS NULL
                AND situacao_atual = 'RECEBIDA'
                AND autor_guarda_id IS NULL)
            OR
            (tipo_evento = 'ATUALIZACAO'
                AND situacao_anterior IS NOT NULL
                AND autor_guarda_id IS NOT NULL)
        )
);
