CREATE OR REPLACE VIEW view_acompanhamento_denuncia AS
SELECT d.protocolo,
       d.categoria,
       d.situacao,
       d.tipo,
       d.criado_em,
       d.atualizado_em,
       a.nome      AS area_nome,
       a.bairro    AS area_bairro,
       a.municipio AS area_municipio,
       a.uf        AS area_uf,
       g.nome      AS guarda_responsavel
FROM denuncia d
JOIN area_verde a ON a.id = d.area_id
JOIN guarda g     ON g.id = a.guarda_id;


GRANT SELECT ON view_acompanhamento_denuncia TO alerta_leitura;
