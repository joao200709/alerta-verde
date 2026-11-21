"""Medição NF003. Requer ALERTA_TEST_DSN exclusivo para testes. Insere dados sintéticos."""
import json
import math
import os
import secrets
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from time import perf_counter

from tests.test_integracao import dados
from alerta import create_app
from alerta.banco import Banco
from alerta.seguranca import proteger

def main():
    dsn = os.environ["ALERTA_TEST_DSN"]
    tag = secrets.token_hex(4).upper()
    banco = Banco(dsn)
    codigo = secrets.token_hex(12).upper()
    verificador = proteger(codigo)
    with banco.transacao() as c:
        c.execute("INSERT INTO guarda(nome,email,senha_hash) VALUES ('Guarda de carga',%s,%s) RETURNING id",
                  (tag+"@carga.invalid", verificador))
        guarda = c.fetchone()["id"]
        c.execute("""INSERT INTO area_verde(nome,tipo,endereco,bairro,municipio,uf,guarda_id)
                     VALUES (%s,'PRACA','Rua da Carga','Centro','Maceió','AL',%s) RETURNING id""",
                  ("Praça de carga "+tag,guarda))
        area = c.fetchone()["id"]
        c.execute("""INSERT INTO denuncia(area_id,protocolo,codigo_acesso_hash,token_envio,categoria,
                     descricao,ponto_referencia,tipo) SELECT %s,%s || n,%s,%s || n,'LIXO',
                     'Registro sintético para ensaio de desempenho.','Portão','ANONIMA'
                     FROM generate_series(1,1000) s(n)""", (area,tag,verificador,tag))
    app = create_app(dict(DSN=dsn,TESTING=True))
    juntos = Barrier(20)
    url = f"/areas/{area}/denunciar/ANONIMA"

    def usuario(i):
        cl = app.test_client()
        csrf = dados(cl.get("/acompanhar"))["csrf"]
        consultas, registros = [], []
        juntos.wait(timeout=60)
        for j in range(5):
            inicio = perf_counter()
            r = cl.post("/acompanhar",data=dict(csrf=csrf,protocolo=tag.upper()+str(i+1),codigo=codigo))
            consultas.append(perf_counter()-inicio)
            if r.status_code!=200 or "Histórico de atendimento" not in r.text:
                raise RuntimeError(f"Consulta falhou ({r.status_code}).")
            form = dados(cl.get(url))
            inicio = perf_counter()
            r = cl.post(url,data={**form,"categoria":"LIXO","descricao":"Descrição de teste para medição.",
                                  "ponto_referencia":"Entrada"})
            registros.append(perf_counter()-inicio)
            if r.status_code!=200 or "Denúncia recebida" not in r.text:
                raise RuntimeError(f"Registro falhou ({r.status_code}).")
        return consultas, registros

    with ThreadPoolExecutor(max_workers=20) as pool:
        resultados = list(pool.map(usuario,range(20)))
    for coluna, nome in enumerate(("consulta","registro")):
        tempos = sorted(t for grupo in resultados for t in grupo[coluna])
        print(json.dumps(dict(operacao=nome,n=len(tempos),p95_segundos=round(tempos[math.ceil(.95*len(tempos))-1],3))))

if __name__ == "__main__":
    main()

