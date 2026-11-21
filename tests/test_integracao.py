"""Executar somente com um PostgreSQL descartável preparado pelos cinco scripts."""
import os
import re
import secrets
import unittest

from html.parser import HTMLParser
from io import BytesIO
from tempfile import TemporaryDirectory
from unittest.mock import patch


from PIL import Image
from alerta import create_app
from alerta.banco import Banco
from alerta.seguranca import proteger


class Campos(HTMLParser):
    def __init__(self, resposta):
        super().__init__()
        self.valores = {}
        self.feed(resposta.get_data(as_text=True))

    def handle_starttag(self, tag, attrs):
        dados = dict(attrs)
        if tag == "input" and "name" in dados:
            self.valores[dados["name"]] = dados.get("value", "")


def dados(resposta):
    return Campos(resposta).valores


def tela(cliente, url, codigo=200):
    resposta = cliente.get(url)
    assert resposta.status_code == codigo, (url, resposta.status_code)
    return resposta


def enviar(cliente, url, campos, **extras):
    return cliente.post(url, data={**campos, **extras})


@unittest.skipUnless(os.getenv("ALERTA_TEST_DSN"), "Defina ALERTA_TEST_DSN para um banco descartável.")
class Integracao(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pasta = TemporaryDirectory()
        cls.addClassCleanup(cls.pasta.cleanup)
        cls.banco = Banco(os.environ["ALERTA_TEST_DSN"])
        cls.app = create_app(dict(TESTING=True, DSN=os.environ["ALERTA_TEST_DSN"], FOTOS=cls.pasta.name))
        cls.senha = secrets.token_hex(16)
        cls.tag = secrets.token_hex(5)
        cls.emails = [f"{n}.{cls.tag}@teste.invalid" for n in ("ana","bia")]
        with cls.banco.transacao() as c:
            for nome, email in zip(("Ana Guarda", "Bia Guarda"), cls.emails):
                c.execute("INSERT INTO guarda (nome,email,senha_hash) VALUES (%s,%s,%s)",
                          (nome,email,proteger(cls.senha)))

    def entrar(self, n):
        cli = self.app.test_client()
        r = enviar(cli, "/entrar", dados(tela(cli,"/entrar")), email=self.emails[n], senha=self.senha)
        self.assertEqual(r.status_code, 302)
        tela(cli,"/painel")
        return cli

    def test_01_fluxos_integrados(self):
        guarda, outro = self.entrar(0), self.entrar(1)
        visita = self.app.test_client()
        nome = "Praça das Palmeiras " + self.tag
        area = dict(nome=nome,tipo="PRACA",endereco="Rua das Flores, 10",bairro="Centro",municipio="Maceió",uf="AL")
        url = "/painel/areas/nova"
        self.assertEqual(enviar(guarda,url,dados(tela(guarda,url)),**area).status_code,302)
        duplicada = {**area, "nome":nome.upper().replace(" ", "   ")}
        self.assertEqual(enviar(guarda,url,dados(tela(guarda,url)),**duplicada).status_code,422)
        inicio = tela(visita,"/?q="+self.tag).text
        numero = re.search(r"/areas/(\d+)/denunciar", inicio)[1]
        editar = f"/painel/areas/{numero}/editar"
        tela(outro,editar,404)
        self.assertEqual(enviar(guarda,editar,dados(tela(guarda,editar)),**{**area,"bairro":"Jaraguá"}).status_code,302)
        self.assertIn("Jaraguá",tela(visita,"/?q="+self.tag).text)
        tela(visita,f"/areas/{numero}/denunciar")

        base = dict(categoria="LIXO", descricao="Há lixo acumulado na entrada principal.", ponto_referencia="Portão norte")
        for tipo in ("PUBLICA","ANONIMA"):
            url = f"/areas/{numero}/denunciar/{tipo}"
            form = dados(tela(visita,url))
            pessoal = dict(nome="Pessoa Teste", email="pessoa@teste.invalid", confirma_email="pessoa@teste.invalid")
            self.assertEqual(enviar(visita,url,form,**base,**pessoal,foto=(BytesIO(b"arquivo"),"x.png")).status_code,422)
            imagem = BytesIO()
            Image.new("RGB",(8,8),"green").save(imagem,"PNG")
            imagem.seek(0)
            with patch("alerta.enviar_comprovante", return_value=False) as correio:
                r = enviar(visita,url,form,**base,**pessoal,foto=(imagem,"folhas.png"))
                self.assertEqual(r.status_code,200)
                if tipo=="PUBLICA":
                    self.assertIn("envio por e-mail falhou", r.text)
                    self.assertEqual(correio.call_args.args[1], pessoal["email"])
                    self.assertTrue(correio.call_args.args[2].startswith(b"%PDF-"))
                else:
                    correio.assert_not_called()
            recibo = dados(r)
            repetido = enviar(visita,url,form,**base,**pessoal)
            self.assertEqual(dados(repetido)["codigo"],recibo["codigo"])
            self.assertIn("já estava registrado",repetido.text)
            pdf = enviar(visita,"/comprovante",recibo)
            self.assertTrue(pdf.data.startswith(b"%PDF-"))
            with self.banco.transacao() as c:
                c.execute("SELECT * FROM denuncia WHERE protocolo=%s",(recibo["protocolo"],))
                d = c.fetchone()
                self.assertNotEqual(d["codigo_acesso_hash"],recibo["codigo"])
                self.assertEqual(d["email_denunciante"],pessoal["email"] if tipo=="PUBLICA" else None)
                self.assertEqual(d["nome_denunciante"],pessoal["nome"] if tipo=="PUBLICA" else None)
                c.execute("SELECT count(*) AS n FROM historico_denuncia WHERE denuncia_id=%s",(d["id"],))
                self.assertEqual(c.fetchone()["n"],1)
            detalhe = f"/painel/denuncias/{d['id']}"
            tela(outro,detalhe,404)
            tela(outro,detalhe+"/foto",404)
            self.assertNotIn(recibo["protocolo"],tela(outro,"/painel/denuncias").text)
            self.assertIn(recibo["protocolo"],tela(guarda,"/painel/denuncias?q="+recibo["protocolo"]+"&situacao=RECEBIDA").text)
            tela_guarda = tela(guarda,detalhe)
            self.assertEqual("pessoa@teste.invalid" in tela_guarda.text,tipo=="PUBLICA")
            versao = dados(tela_guarda)
            self.assertEqual(enviar(guarda,detalhe,versao,situacao="RESOLVIDA",resposta="Intervenção finalizada.").status_code,422)
            self.assertEqual(enviar(guarda,detalhe,versao,situacao="EM_ANALISE",resposta="Vistoria iniciada hoje.").status_code,302)
            self.assertEqual(enviar(guarda,detalhe,versao,situacao="EM_ANALISE",resposta="Outra resposta antiga.").status_code,409)
            self.assertEqual(enviar(guarda,detalhe,dados(tela(guarda,detalhe)),situacao="EM_ANALISE",
                                    resposta="A equipe recebeu a solicitação.").status_code,302)
            publica = enviar(visita,"/acompanhar",recibo)
            self.assertNotIn(pessoal["email"],publica.text)
            self.assertNotIn(recibo["codigo"],publica.text)
            self.assertIn("Guarda responsável",publica.text)
            self.assertEqual(publica.text.count("Guarda responsável"),2)
            self.assertIn("Denúncia recebida pelo sistema.",publica.text)
            foto = f"/ocorrencias/{d['id']}/foto"
            tela(self.app.test_client(),foto,404)
            with tela(visita,foto) as resposta_foto:
                self.assertEqual(resposta_foto.mimetype,"image/png")
            self.assertEqual(enviar(guarda,detalhe,dados(tela(guarda,detalhe)),situacao="RESOLVIDA",
                                    resposta="A coleta foi concluída.").status_code,302)
            self.assertIn("Atendimento encerrado",tela(guarda,detalhe).text)

        status = f"/painel/areas/{numero}/disponibilidade"
        tela(outro,status,404)
        self.assertEqual(enviar(guarda,status,dados(tela(guarda,status)),ativa="0").status_code,302)
        self.assertNotIn(nome,tela(visita,"/?q="+self.tag).text)
        tela(visita,url,404)
        self.assertIn("A coleta foi concluída.",enviar(visita,"/acompanhar",recibo).text)
        self.assertEqual(enviar(guarda,status,dados(tela(guarda,status)),ativa="1").status_code,302)
        self.assertIn(nome,tela(visita,"/?q="+self.tag).text)
        for _ in range(5):
            self.assertEqual(enviar(visita,"/acompanhar",recibo,codigo="errado").status_code,422)
        self.assertEqual(enviar(visita,"/acompanhar",recibo).status_code,422)
        self.assertEqual(guarda.post(status,data={"ativa":"0"}).status_code,400)
        self.assertEqual(enviar(guarda,"/sair",dados(tela(guarda,"/painel"))).status_code,302)
        tela(guarda,"/painel",302)

    def test_02_bloqueio_guarda(self):
        cli = self.app.test_client()
        form = dados(tela(cli,"/entrar"))
        for _ in range(5):
            self.assertEqual(enviar(cli,"/entrar",form,email=self.emails[1],senha="incorreta").status_code,422)
        self.assertEqual(enviar(cli,"/entrar",form,email=self.emails[1],senha=self.senha).status_code,422)
        with self.banco.transacao() as c:
            c.execute("SELECT tentativas_falhas,bloqueado_ate>now() AS bloqueado FROM guarda WHERE email=%s", (self.emails[1],))
            self.assertEqual(c.fetchone(),{"tentativas_falhas":5,"bloqueado":True})

    def test_03_permissoes_e_view(self):
        with self.banco.transacao() as c:
            c.execute("""SELECT current_user AS usuario,
                has_table_privilege('alerta_app','historico_denuncia','UPDATE') AS altera,
                has_table_privilege('alerta_app','denuncia','DELETE') AS apaga,
                has_table_privilege('alerta_leitura','denuncia','SELECT') AS le_dados,
                has_table_privilege('alerta_leitura','view_acompanhamento_denuncia','SELECT') AS le_view""")
            self.assertEqual(c.fetchone(),dict(usuario="alerta_app",altera=False,apaga=False,le_dados=False,le_view=True))
            c.execute("SELECT count(*) AS n FROM pg_indexes WHERE indexname='indice_denuncia_situacao'")
            self.assertEqual(c.fetchone()["n"],1)


if __name__ == "__main__":
    unittest.main()

