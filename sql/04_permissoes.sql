-- =====================================================================
-- Alerta Verde - contas e permissões (PostgreSQL 10+)
-- Rodar com um usuário administrador (ex.: postgres)
-- Defina as senhas após a criação usando o comando interativo do psql.
-- As credenciais reais ficam fora do repositório.
-- =====================================================================

-- Dono da estrutura
CREATE ROLE alerta_admin   LOGIN;
-- Conta usada pelo site
CREATE ROLE alerta_app     LOGIN;
-- Conta só para relatórios
CREATE ROLE alerta_leitura LOGIN;

-- Retira os privilégios padrão do PUBLIC (ninguém tem acesso por padrão)
REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON ALL TABLES    IN SCHEMA public FROM PUBLIC;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM PUBLIC;

-- alerta_admin: vira dono das tabelas (as sequências dos ids acompanham)
ALTER TABLE guarda             OWNER TO alerta_admin;
ALTER TABLE area_verde         OWNER TO alerta_admin;
ALTER TABLE denuncia           OWNER TO alerta_admin;
ALTER TABLE historico_denuncia OWNER TO alerta_admin;

GRANT ALL ON SCHEMA public TO alerta_admin;

-- alerta_app: lê, insere e atualiza (sem DELETE e sem alterar estrutura)
GRANT USAGE ON SCHEMA public TO alerta_app;
GRANT SELECT, INSERT, UPDATE ON guarda     TO alerta_app;
GRANT SELECT, INSERT, UPDATE ON area_verde TO alerta_app;
GRANT SELECT, INSERT, UPDATE ON denuncia   TO alerta_app;

-- Histórico só cresce: sem UPDATE e sem DELETE
GRANT SELECT, INSERT ON historico_denuncia TO alerta_app;

-- Sequências dos ids
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO alerta_app;

-- alerta_leitura: só lê area_verde por enquanto
GRANT USAGE ON SCHEMA public TO alerta_leitura;
GRANT SELECT ON area_verde TO alerta_leitura;
