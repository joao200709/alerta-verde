-- Função: cria o primeiro registro (RECEBIMENTO) no histórico da denúncia
CREATE OR REPLACE FUNCTION fn_denuncia_registrar_recebimento()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO historico_denuncia (
        denuncia_id,
        tipo_evento,
        situacao_anterior,
        situacao_atual,
        texto,
        autor_guarda_id
    )
    VALUES (
        NEW.id,
        'RECEBIMENTO',
        NULL,                                -- RECEBIMENTO não tem situação anterior
        'RECEBIDA',                          -- RECEBIMENTO sempre começa como RECEBIDA
        'Denúncia recebida pelo sistema.',
        NULL                                 -- vazio = foi o próprio sistema
    );

    RETURN NULL;  -- em trigger AFTER o retorno é ignorado
END;
$$;

-- Trigger: depois de cada INSERT em denuncia, chama a função acima
CREATE TRIGGER trg_denuncia_registrar_recebimento
AFTER INSERT ON denuncia
FOR EACH ROW
EXECUTE PROCEDURE fn_denuncia_registrar_recebimento();
