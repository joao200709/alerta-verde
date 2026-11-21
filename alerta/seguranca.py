import os
import secrets
from datetime import timedelta
from threading import RLock
from time import monotonic

from cryptography.exceptions import InvalidKey
from cryptography.hazmat.primitives.kdf.argon2 import Argon2id

JANELA = timedelta(minutes=15)


def proteger(valor):
    kdf = Argon2id(salt=os.urandom(16), length=32, iterations=2, lanes=1, memory_cost=19456)
    return kdf.derive_phc_encoded(valor.encode())


def confere(valor, verificador):
    try:
        Argon2id.verify_phc_encoded(valor.encode(), verificador)
        return True
    except (InvalidKey, ValueError):
        return False


class AcessosTemporarios:
    """Estado privado do processo web. O navegador recebe só o identificador da sessão."""
    def __init__(self):
        self._sessoes = {}
        self._falhas = {}
        self._lock = RLock()
        self._ultima_limpeza = 0

    def _limpar(self, agora):
        if agora - self._ultima_limpeza >= 60:
            self._sessoes = {k: v for k, v in self._sessoes.items() if v[1] > agora}
            self._falhas = {k: v for k, v in self._falhas.items() if v[1] > agora}
            self._ultima_limpeza = agora

    def entrar(self, guarda_id):
        chave = secrets.token_urlsafe(32)
        with self._lock:
            agora = monotonic()
            self._limpar(agora)
            self._sessoes[chave] = (guarda_id, agora + 1800)
        return chave

    def guarda(self, chave):
        with self._lock:
            agora = monotonic()
            self._limpar(agora)
            registro = self._sessoes.get(chave)
            if registro and registro[1] > agora:
                self._sessoes[chave] = (registro[0], agora + 1800)
                return registro[0]
            self._sessoes.pop(chave, None)
            return None

    def sair(self, chave):
        with self._lock:
            self._sessoes.pop(chave, None)

    def tentativa(self, chave):
        """Reserva a tentativa antes da consulta, inclusive sob requisições simultâneas."""
        with self._lock:
            agora = monotonic()
            self._limpar(agora)
            n, fim = self._falhas.get(chave, (0, agora + 900))
            if fim <= agora:
                n, fim = 0, agora + 900
            if n >= 5:
                return False
            self._falhas[chave] = (n + 1, agora + 900 if n == 4 else fim)
            return True

    def acertou(self, chave):
        with self._lock:
            self._falhas.pop(chave, None)

