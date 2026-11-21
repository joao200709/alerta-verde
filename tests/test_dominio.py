import unittest
from unittest.mock import patch

from alerta.dominio import Atendimento, Denuncia, DenunciaAnonima, DenunciaPublica, Regra
from alerta.seguranca import AcessosTemporarios


class Dominio(unittest.TestCase):
    def test_identidade_polimorfica(self):
        form = dict(categoria="LIXO",descricao="Há lixo acumulado no portão.",ponto_referencia="Entrada",
                    nome="Ana Silva",email="ana@exemplo.invalid")
        anonima = Denuncia.do_formulario("ANONIMA",form)
        publica = Denuncia.do_formulario("PUBLICA",form)
        self.assertIsInstance(anonima,DenunciaAnonima)
        self.assertIsInstance(publica,DenunciaPublica)
        self.assertEqual(anonima.identificacao(),("ANONIMA",None,None))
        self.assertEqual(publica.identificacao(),("PUBLICA","Ana Silva",form["email"]))
        with self.assertRaises(TypeError):
            Denuncia("LIXO","Descrição do problema","Entrada")

    def test_matriz_de_transicoes(self):
        esperadas = {"RECEBIDA":{"RECEBIDA","EM_ANALISE"},
                     "EM_ANALISE":{"EM_ANALISE","EM_ATENDIMENTO","RESOLVIDA","REJEITADA"},
                     "EM_ATENDIMENTO":{"EM_ATENDIMENTO","RESOLVIDA","REJEITADA"},
                     "RESOLVIDA":set(),"REJEITADA":set()}
        for origem, destinos in esperadas.items():
            for destino in esperadas:
                with self.subTest(origem=origem,destino=destino):
                    dados = dict(situacao=destino,resposta="A equipe visitou a área.")
                    atendimento = Atendimento(origem)
                    if destino in destinos:
                        self.assertEqual(atendimento.responder(dados),(destino,dados["resposta"]))
                    else:
                        with self.assertRaises(Regra):
                            atendimento.responder(dados)

    def test_inatividade_e_bloqueio_temporario(self):
        estado = AcessosTemporarios()
        with patch("alerta.seguranca.monotonic",return_value=1000):
            chave = estado.entrar(45)
            for _ in range(5):
                self.assertTrue(estado.tentativa(("ip","AV-1")))
            self.assertFalse(estado.tentativa(("ip","AV-1")))
        with patch("alerta.seguranca.monotonic",return_value=1899):
            self.assertFalse(estado.tentativa(("ip","AV-1")))
        with patch("alerta.seguranca.monotonic",return_value=1900):
            self.assertTrue(estado.tentativa(("ip","AV-1")))
        with patch("alerta.seguranca.monotonic",return_value=2800):
            self.assertIsNone(estado.guarda(chave))

