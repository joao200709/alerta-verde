"""Sobe um PostgreSQL exclusivo da apresentação e abre o site no endereço informado."""
import argparse
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import tempfile

import psycopg
from psycopg import sql
from psycopg.conninfo import make_conninfo

from alerta import create_app
from alerta.seguranca import proteger

RAIZ = Path(__file__).resolve().parent


def binarios():
    caminho = os.getenv("PG_BIN") or shutil.which("pg_ctl")
    if caminho:
        local = Path(caminho)
        return local if local.is_dir() else local.parent
    instalacoes = Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "PostgreSQL"
    candidatos = sorted(instalacoes.glob("*/bin/pg_ctl.exe"),
                        key=lambda p: int(p.parents[1].name) if p.parents[1].name.isdigit() else 0)
    if candidatos:
        return candidatos[-1].parent
    raise SystemExit("Instale o PostgreSQL com suporte a ICU ou defina PG_BIN para a pasta bin.")


def chaves(pasta):
    arquivo = pasta / "config-local.json"
    if not arquivo.exists():
        valores = {k: secrets.token_urlsafe(24) for k in ("admin", "app", "guarda", "site")}
        with arquivo.open("x", encoding="utf-8") as f:
            arquivo.chmod(0o600)
            json.dump(valores, f)
    return json.loads(arquivo.read_text(encoding="utf-8"))


AREAS_DEMO = (
    ("acacias", "Parque Municipal das Acácias", "PARQUE", "Rua das Acácias, 40", "Jaraguá"),
    ("sol", "Praça do Sol Nascente", "PRACA", "Rua do Sol, 15", "Ponta Verde"),
    ("ipe", "Parque do Ipê Amarelo", "PARQUE", "Rua dos Ipês, 21", "Farol"),
    ("palmeiras", "Praça das Palmeiras", "PRACA", "Rua das Palmeiras, 120", "Jatiúca"),
    ("lagoa", "Parque da Lagoa Azul", "PARQUE", "Rua da Lagoa, 38", "Cruz das Almas"),
    ("esperanca", "Praça da Esperança", "PRACA", "Rua da Esperança, 12", "Pajuçara"),
)


def preparar(conexao, config, pasta):
    manifesto = pasta / "capas.json"
    with psycopg.connect(conexao) as c:
        instalada = bool(c.execute("SELECT to_regclass('public.guarda')").fetchone()[0])
        if instalada and manifesto.exists():
            return json.loads(manifesto.read_text(encoding="utf-8"))
        if not instalada:
            for arquivo in sorted((RAIZ / "sql").glob("*.sql")):
                c.execute(arquivo.read_text(encoding="utf-8"))
            c.execute(sql.SQL("ALTER ROLE alerta_app PASSWORD {}").format(sql.Literal(config["app"])))
            c.execute("INSERT INTO guarda(nome,email,senha_hash) VALUES (%s,%s,%s)",
                      ("Guarda de demonstração", "guarda@exemplo.invalid", proteger(config["guarda"])))
        guarda = c.execute("SELECT id FROM guarda WHERE email='guarda@exemplo.invalid'").fetchone()
        if not guarda:
            return {}
        capas = {}
        for imagem, nome, tipo, rua, bairro in AREAS_DEMO:
            linha = c.execute("""SELECT id FROM area_verde WHERE guarda_id=%s AND endereco=%s
                                 AND municipio='Maceió' AND uf='AL' AND tipo=%s
                                 AND nome IN (%s,%s) ORDER BY id LIMIT 1""",
                              (guarda[0], rua, tipo, nome,
                               "Parque das Acácias" if imagem == "acacias" else nome)).fetchone()
            if not linha and (not instalada or imagem in ("ipe", "lagoa", "esperanca")):
                linha = c.execute("""INSERT INTO area_verde(nome,tipo,endereco,bairro,municipio,uf,guarda_id)
                                     VALUES (%s,%s,%s,%s,'Maceió','AL',%s)
                                     ON CONFLICT DO NOTHING RETURNING id""", (nome,tipo,rua,bairro,guarda[0])).fetchone()
            if linha:
                capas[str(linha[0])] = imagem
    with tempfile.NamedTemporaryFile(mode="w", dir=pasta, delete=False, encoding="utf-8") as f:
        json.dump(capas, f)
    Path(f.name).replace(manifesto)
    return capas


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preparar", action="store_true", help="prepara os dados e encerra")
    args = parser.parse_args()
    pasta = RAIZ / "instance" / "demo"
    pasta.mkdir(parents=True, exist_ok=True, mode=0o700)
    config = chaves(pasta)
    pg = binarios()
    cluster = pasta / "postgres"
    porta = int(os.getenv("ALERTA_PORTA_BD", "55438"))
    sufixo = ".exe" if os.name == "nt" else ""
    if not (cluster / "PG_VERSION").exists():
        with tempfile.NamedTemporaryFile(mode="w", dir=pasta, delete=False) as senha:
            senha.write(config["admin"] + "\n")
        try:
            subprocess.run([pg / ("initdb"+sufixo), "-D", cluster, "-U", "demo_admin", "-E", "UTF8",
                            "--locale=C", "-A", "scram-sha-256", "--pwfile", senha.name], check=True)
        finally:
            Path(senha.name).unlink(missing_ok=True)
    ctl = [pg / ("pg_ctl"+sufixo), "-D", cluster]
    iniciou = subprocess.run([*ctl,"status"], stdout=subprocess.DEVNULL).returncode != 0
    if iniciou:
        subprocess.run([*ctl, "-l", pasta / "postgres.log", "-o", f"-h 127.0.0.1 -p {porta}", "-w", "start"], check=True)
    try:
        local = dict(host="127.0.0.1", port=porta, dbname="postgres", connect_timeout=5)
        capas = preparar(make_conninfo(**local, user="demo_admin", password=config["admin"]), config, pasta)
        if not args.preparar:
            app = create_app(dict(DSN=make_conninfo(**local,user="alerta_app",password=config["app"]),
                                  SECRET_KEY=config["site"], FOTOS=pasta/"fotos", CAPAS_AREAS=capas))
            porta_web = int(os.getenv("ALERTA_PORTA_WEB", "5000"))
            print(f"\nAbra http://127.0.0.1:{porta_web}\nGuarda: guarda@exemplo.invalid")
            print("Senha local do guarda:", config["guarda"], flush=True)
            app.run(host="127.0.0.1", port=porta_web, debug=False, use_reloader=False)
    finally:
        if iniciou:
            subprocess.run([*ctl,"-m","fast","-w","stop"], check=True)


if __name__ == "__main__":
    main()

