"""Entidades e regras do Alerta Verde, independentes de Flask e PostgreSQL."""
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass

CATEGORIAS = ("LIXO", "VEGETACAO", "VANDALISMO", "INFRAESTRUTURA", "OUTROS")
TIPOS_AREA = ("PRACA", "PARQUE")
TRANSICOES = {
    "RECEBIDA": ("EM_ANALISE",),
    "EM_ANALISE": ("EM_ATENDIMENTO", "RESOLVIDA", "REJEITADA"),
    "EM_ATENDIMENTO": ("RESOLVIDA", "REJEITADA"),
    "RESOLVIDA": (),
    "REJEITADA": (),
}


class Regra(ValueError):
    def __init__(self, mensagem, campo=None):
        super().__init__(mensagem)
        self.campo = campo


def texto(dados, campo, minimo, maximo):
    valor = dados.get(campo, "").strip()
    if not minimo <= len(valor) <= maximo:
        raise Regra(f"Use de {minimo} a {maximo} caracteres.", campo)
    return valor


def email_valido(dados, campo):
    valor = texto(dados, campo, 3, 254)
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", valor):
        raise Regra("Informe um e-mail válido.", campo)
    return valor


def escolha(dados, campo, opcoes):
    valor = dados.get(campo)
    if valor not in opcoes:
        raise Regra("Selecione uma das opções disponíveis.", campo)
    return valor


@dataclass(frozen=True)
class AreaVerde:
    nome: str
    tipo: str
    endereco: str
    bairro: str
    municipio: str
    uf: str

    @classmethod
    def do_formulario(cls, dados):
        uf = texto(dados, "uf", 2, 2).upper()
        if not re.fullmatch("[A-Z]{2}", uf):
            raise Regra("Use uma sigla com duas letras.", "uf")
        return cls(texto(dados, "nome", 3, 120), escolha(dados, "tipo", TIPOS_AREA),
                   texto(dados, "endereco", 5, 200), texto(dados, "bairro", 2, 100),
                   texto(dados, "municipio", 2, 100), uf)


@dataclass(frozen=True)
class Denuncia(ABC):
    categoria: str
    descricao: str
    ponto_referencia: str

    @staticmethod
    def do_formulario(tipo, dados):
        categoria = escolha(dados, "categoria", CATEGORIAS)
        descricao = texto(dados, "descricao", 20, 2000)
        ponto_referencia = texto(dados, "ponto_referencia", 3, 200)

        if tipo == "ANONIMA":
            return DenunciaAnonima(categoria, descricao, ponto_referencia)

        if tipo == "PUBLICA":
            nome = texto(dados, "nome", 3, 120)
            email = email_valido(dados, "email")
            return DenunciaPublica(categoria, descricao, ponto_referencia, nome, email)

        raise Regra("Escolha o tipo da denúncia.")

    @abstractmethod
    def identificacao(self):
        """Retorna tipo, nome e e-mail que podem ser persistidos."""


@dataclass(frozen=True)
class DenunciaAnonima(Denuncia):
    def identificacao(self):
        return "ANONIMA", None, None


@dataclass(frozen=True)
class DenunciaPublica(Denuncia):
    nome: str
    email: str

    def identificacao(self):
        return "PUBLICA", self.nome, self.email


@dataclass(frozen=True)
class Atendimento:
    situacao: str

    @property
    def destinos(self):
        seguintes = TRANSICOES[self.situacao]
        return (self.situacao, *seguintes) if seguintes else ()

    def responder(self, dados):
        if not self.destinos:
            raise Regra("O atendimento já foi encerrado.")
        return escolha(dados, "situacao", self.destinos), texto(dados, "resposta", 10, 500)

