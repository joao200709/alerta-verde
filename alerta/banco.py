from contextlib import contextmanager
from dataclasses import astuple
from datetime import datetime, timezone

import psycopg
from psycopg.rows import dict_row

from .dominio import Regra
from .seguranca import JANELA, confere


class Banco:
    def __init__(self, dsn):
        self._dsn = dsn

    @contextmanager
    def transacao(self):
        with psycopg.connect(self._dsn, row_factory=dict_row, connect_timeout=5) as conexao:
            with conexao.cursor() as cursor:
                yield cursor


class Catalogo:
    def __init__(self, banco):
        self.banco = banco

    def listar(self, busca, tipo, pagina, guarda=None):
        termo = f"%{busca}%"
        with self.banco.transacao() as c:
            c.execute("""SELECT *, count(*) OVER () AS total FROM area_verde
                         WHERE ((%s::int IS NULL AND ativa) OR guarda_id=%s)
                           AND (%s='' OR tipo=%s)
                           AND (nome COLLATE "und-x-icu" ILIKE %s OR bairro COLLATE "und-x-icu" ILIKE %s OR endereco COLLATE "und-x-icu" ILIKE %s)
                         ORDER BY nome COLLATE "und-x-icu", id LIMIT 11 OFFSET %s""",
                      (guarda, guarda, tipo, tipo, termo, termo, termo, (pagina-1)*10))
            return c.fetchall()

    def obter(self, id_area, guarda=None):
        with self.banco.transacao() as c:
            c.execute("""SELECT a.*, g.nome AS editor FROM area_verde a
                         LEFT JOIN guarda g ON g.id=a.atualizado_por
                         WHERE a.id=%s AND ((%s::int IS NULL AND a.ativa) OR a.guarda_id=%s)""",
                      (id_area, guarda, guarda))
            return c.fetchone()

    def salvar(self, area, guarda, id_area=None):
        try:
            with self.banco.transacao() as c:
                if id_area is None:
                    c.execute("""INSERT INTO area_verde (nome,tipo,endereco,bairro,municipio,uf,guarda_id)
                                 VALUES (%s,%s,%s,%s,%s,%s,%s)""", (*astuple(area), guarda))
                else:
                    c.execute("""UPDATE area_verde SET nome=%s,tipo=%s,endereco=%s,bairro=%s,
                                 municipio=%s,uf=%s,atualizado_por=%s,atualizado_em=clock_timestamp()
                                 WHERE id=%s AND guarda_id=%s""", (*astuple(area), guarda, id_area, guarda))
                    if not c.rowcount:
                        raise Regra("Área indisponível.")
        except psycopg.errors.UniqueViolation:
            raise Regra("Já existe uma área com este nome e endereço no município.", "nome") from None

    def ativar(self, id_area, guarda, ativa):
        with self.banco.transacao() as c:
            c.execute("""UPDATE area_verde SET ativa=%s, atualizado_por=%s, atualizado_em=clock_timestamp()
                         WHERE id=%s AND guarda_id=%s""", (ativa, guarda, id_area, guarda))
            return bool(c.rowcount)


class Guardas:
    def __init__(self, banco, verificador_neutro):
        self.banco = banco
        self.neutro = verificador_neutro

    def resumo(self, guarda):
        with self.banco.transacao() as c:
            c.execute("""SELECT count(d.id) AS recebidas,
                                count(d.id) FILTER (WHERE d.situacao='EM_ATENDIMENTO') AS atendimento,
                                count(DISTINCT a.id) FILTER (WHERE a.ativa) AS ativas
                         FROM area_verde a LEFT JOIN denuncia d ON d.area_id=a.id
                         WHERE a.guarda_id=%s""", (guarda,))
            return c.fetchone()

    def autenticar(self, email, senha):
        with self.banco.transacao() as c:
            c.execute('SELECT * FROM guarda WHERE lower(email COLLATE "und-x-icu")=lower(%s COLLATE "und-x-icu") FOR UPDATE', (email,))
            g = c.fetchone()
            agora = datetime.now(timezone.utc)
            if not g or not g["ativo"] or (g["bloqueado_ate"] and g["bloqueado_ate"] > agora):
                confere(senha, self.neutro)
                return None
            valido = confere(senha, g["senha_hash"])
            inicio = g["primeira_falha_em"]
            if valido:
                n, inicio, bloqueio = 0, None, None
            else:
                if inicio is None or inicio + JANELA <= agora:
                    inicio, n = agora, 1
                else:
                    n = g["tentativas_falhas"] + 1
                bloqueio = agora + JANELA if n >= 5 else None
            c.execute("UPDATE guarda SET tentativas_falhas=%s, primeira_falha_em=%s, bloqueado_ate=%s WHERE id=%s",
                      (n, inicio, bloqueio, g["id"]))
            return g["id"] if valido else None

    def ativo(self, id_guarda):
        with self.banco.transacao() as c:
            c.execute("SELECT id, nome FROM guarda WHERE id=%s AND ativo", (id_guarda,))
            return c.fetchone()

