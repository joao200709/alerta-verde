from hashlib import sha256
from hmac import digest
import secrets

from .dominio import Atendimento, Regra
from .seguranca import confere, proteger


class CentralDenuncias:
    def __init__(self, banco, fotos, chave, neutro):
        self.banco = banco
        self.fotos = fotos
        self.chave = chave.encode()
        self.neutro = neutro

    def registrar(self, area, denuncia, envio, imagem):
        # O banco recebe somente uma impressão do nonce privado do formulário.
        token = sha256(envio.encode()).hexdigest()
        codigo = digest(self.chave, b"acesso:" + envio.encode(), "sha256").hex()[:24].upper()
        protocolo = "AV-" + secrets.token_hex(8).upper()
        tipo, nome, email = denuncia.identificacao()
        arquivo = None
        try:
            with self.banco.transacao() as c:
                c.execute("SELECT nome FROM area_verde WHERE id=%s AND ativa FOR SHARE", (area,))
                if not c.fetchone():
                    raise Regra("Esta área está inativa e não recebe novas denúncias.")
                c.execute("""INSERT INTO denuncia
                    (area_id,categoria,descricao,ponto_referencia,tipo,nome_denunciante,
                     email_denunciante,protocolo,token_envio,codigo_acesso_hash)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (token_envio) DO NOTHING RETURNING id,protocolo,criado_em""",
                          (area, denuncia.categoria, denuncia.descricao, denuncia.ponto_referencia,
                           tipo, nome, email, protocolo, token, proteger(codigo)))
                recibo = c.fetchone()
                novo = recibo is not None
                if novo and imagem:
                    arquivo = self.fotos.salvar(imagem)
                    c.execute("UPDATE denuncia SET foto_arquivo=%s WHERE id=%s", (arquivo, recibo["id"]))
                if not novo:
                    c.execute("SELECT id,protocolo,criado_em FROM denuncia WHERE token_envio=%s", (token,))
                    recibo = c.fetchone()
        except Exception:
            if arquivo:
                self.fotos.remover(arquivo)
            raise
        return recibo, codigo, novo

    def verificar(self, protocolo, codigo):
        with self.banco.transacao() as c:
            c.execute("SELECT id,codigo_acesso_hash FROM denuncia WHERE protocolo=%s", (protocolo,))
            d = c.fetchone()
            valido = confere(codigo, d["codigo_acesso_hash"] if d else self.neutro)
            return d["id"] if valido and d else None

    def listar(self, guarda, busca, situacao, pagina):
        termo = f"%{busca}%"
        with self.banco.transacao() as c:
            c.execute("""SELECT d.id,d.protocolo,a.nome AS area,d.categoria,d.situacao,d.criado_em
                         FROM denuncia d JOIN area_verde a ON a.id=d.area_id WHERE a.guarda_id=%s
                         AND (%s='' OR d.situacao=%s)
                         AND (d.protocolo ILIKE %s OR a.nome COLLATE "und-x-icu" ILIKE %s
                              OR d.categoria ILIKE translate(%s, 'çãÇÃ', 'caCA'))
                         ORDER BY d.criado_em DESC,d.id DESC LIMIT 11 OFFSET %s""",
                      (guarda, situacao, situacao, termo, termo, termo, (pagina-1)*10))
            return c.fetchall()

    def detalhes(self, id_denuncia, guarda=None):
        # A rota pública só chama este método após validar o par protocolo/código.
        with self.banco.transacao() as c:
            c.execute("""SELECT d.id,d.protocolo,d.tipo,d.categoria,d.descricao,d.ponto_referencia,
                         d.criado_em,d.situacao,d.atualizado_em,d.foto_arquivo,a.nome AS area,
                         CASE WHEN a.guarda_id=%s THEN d.nome_denunciante END AS nome,
                         CASE WHEN a.guarda_id=%s THEN d.email_denunciante END AS email
                         FROM denuncia d JOIN area_verde a ON a.id=d.area_id
                         WHERE d.id=%s AND (%s::int IS NULL OR a.guarda_id=%s) FOR SHARE OF d""",
                      (guarda, guarda, id_denuncia, guarda, guarda))
            d = c.fetchone()
            if d:
                c.execute("""SELECT h.criado_em,h.situacao_anterior,h.situacao_atual,h.texto,
                             CASE WHEN h.autor_guarda_id IS NULL THEN 'Sistema'
                                  WHEN %s::int IS NULL THEN 'Guarda responsável' ELSE g.nome END AS autor
                             FROM historico_denuncia h LEFT JOIN guarda g ON g.id=h.autor_guarda_id
                             WHERE h.denuncia_id=%s ORDER BY h.id""", (guarda, id_denuncia))
                d["historico"] = c.fetchall()
            return d

    def atualizar(self, id_denuncia, guarda, dados):
        with self.banco.transacao() as c:
            c.execute("""SELECT d.situacao,d.atualizado_em FROM denuncia d JOIN area_verde a ON a.id=d.area_id
                         WHERE d.id=%s AND a.guarda_id=%s FOR UPDATE OF d""", (id_denuncia, guarda))
            atual = c.fetchone()
            if not atual:
                raise Regra("Denúncia indisponível.")
            if atual["atualizado_em"].isoformat() != dados.get("versao"):
                raise Regra("Outro atendimento foi salvo. Recarregue a página e confira o histórico.", "versao")
            destino, resposta = Atendimento(atual["situacao"]).responder(dados)
            c.execute("""UPDATE denuncia SET situacao=%s,
                         atualizado_em=greatest(clock_timestamp(), atualizado_em+interval '1 microsecond')
                         WHERE id=%s""", (destino, id_denuncia))
            c.execute("""INSERT INTO historico_denuncia
                         (denuncia_id,tipo_evento,situacao_anterior,situacao_atual,texto,autor_guarda_id)
                         VALUES (%s,'ATUALIZACAO',%s,%s,%s,%s)""",
                      (id_denuncia, atual["situacao"], destino, resposta, guarda))

