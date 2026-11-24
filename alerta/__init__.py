import hmac
import os
import secrets
from functools import wraps
from io import BytesIO
from pathlib import Path

import click
import psycopg
from flask import (Flask, abort, flash, g, redirect, render_template, request, send_file,
                   send_from_directory, session, url_for)
from itsdangerous import BadSignature, URLSafeTimedSerializer
from werkzeug.exceptions import RequestEntityTooLarge

from .banco import Banco, Catalogo, Guardas
from .comprovantes import Fotos, comprovante, data_local, enviar_comprovante
from .denuncias import CentralDenuncias
from .dominio import (AreaVerde, Atendimento, CATEGORIAS, Denuncia, Regra, TIPOS_AREA,
                      TRANSICOES, email_valido, texto)
from .seguranca import AcessosTemporarios, proteger

ROTULOS = {"PRACA": "Praça", "PARQUE": "Parque", "EM_ANALISE": "Em análise",
           "EM_ATENDIMENTO": "Em atendimento", "VEGETACAO": "Vegetação",
           "PUBLICA": "Identificada", "ANONIMA": "Anônima"}
FALHA_CONSULTA = "Não foi possível localizar a denúncia com os dados informados."


def create_app(config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("ALERTA_CHAVE") or secrets.token_hex(32),
        DSN=os.environ.get("ALERTA_DSN", "dbname=alerta_verde user=alerta_app"),
        FOTOS=Path(app.instance_path) / "fotos", CAPAS_AREAS={},
        MAX_CONTENT_LENGTH=6 * 1024 * 1024, SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax", SESSION_COOKIE_SECURE=os.environ.get("ALERTA_HTTPS") == "1",
        SMTP_HOST=os.environ.get("SMTP_HOST"), SMTP_FROM=os.environ.get("SMTP_FROM"),
        SMTP_PORT=os.environ.get("SMTP_PORT", "587"), SMTP_USER=os.environ.get("SMTP_USER"),
        SMTP_PASSWORD=os.environ.get("SMTP_PASSWORD", ""), SMTP_TLS=os.environ.get("SMTP_TLS", "1") == "1")
    if config:
        app.config.update(config)
    banco = Banco(app.config["DSN"])
    fotos = Fotos(app.config["FOTOS"])
    neutro = proteger(secrets.token_hex(20))
    central = CentralDenuncias(banco, fotos, app.secret_key, neutro)
    catalogo = Catalogo(banco)
    guardas = Guardas(banco, neutro)
    acessos = AcessosTemporarios()
    assinador = URLSafeTimedSerializer(app.secret_key, salt="formulario-denuncia")
    app.jinja_env.filters["rotulo"] = lambda v: ROTULOS.get(v, str(v).capitalize())
    app.jinja_env.filters["data"] = data_local
    app.jinja_env.globals.update(categorias=CATEGORIAS, tipos_area=TIPOS_AREA, situacoes=TRANSICOES)

    @app.before_request
    def preparar():
        if "csrf" not in session:
            session["csrf"] = secrets.token_hex(24)
        if request.method == "POST" and not hmac.compare_digest(
                request.form.get("csrf", "").encode(), session["csrf"].encode()):
            abort(400, "Formulário expirado. Reabra a página e tente novamente.")

    @app.after_request
    def privacidade(resp):
        resp.headers["Cache-Control"] = "no-store"
        resp.headers["Referrer-Policy"] = "no-referrer"
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["X-Frame-Options"] = "DENY"
        return resp

    @app.errorhandler(RequestEntityTooLarge)
    def grande(_):
        return render_template("erro.html", mensagem="Envio muito grande. Use um PNG de até 5 MB."), 413

    @app.errorhandler(psycopg.OperationalError)
    def sem_banco(_):
        return render_template("erro.html", mensagem="Banco indisponível. Confira a conexão e tente novamente."), 503

    @app.errorhandler(404)
    @app.errorhandler(400)
    def invalido(erro):
        msg = "Registro ou página indisponível." if erro.code == 404 else erro.description
        return render_template("erro.html", mensagem=msg), erro.code

    def restrito(func):
        @wraps(func)
        def rota(*args, **kwargs):
            id_guarda = acessos.guarda(session.get("guarda"))
            g.guarda = guardas.ativo(id_guarda) if id_guarda else None
            if not g.guarda:
                acessos.sair(session.pop("guarda", None))
                return redirect(url_for("login"))
            return func(*args, **kwargs)
        return rota

    def pagina():
        return min(100_000_000, max(1, request.args.get("p", 1, type=int)))

    def areas(privado):
        busca = request.args.get("q", "").strip()[:200]
        tipo = request.args.get("tipo", "")
        p = pagina()
        linhas = catalogo.listar(busca, tipo, p, g.guarda["id"] if privado else None)
        return render_template("areas.html", linhas=linhas[:10], mais=len(linhas)>10,
                               p=p, busca=busca, tipo=tipo, privado=privado)

    @app.get("/")
    def inicio():
        return areas(False)

    @app.get("/areas/<int:area>/denunciar")
    def escolher(area):
        a = catalogo.obter(area) or abort(404)
        return render_template("escolha.html", area=a)

    @app.route("/areas/<int:area>/denunciar/<tipo>", methods=["GET", "POST"])
    def registrar(area, tipo):
        if tipo not in ("ANONIMA", "PUBLICA"):
            abort(404)
        a = catalogo.obter(area) or abort(404)
        vinculo = [area, tipo, session["csrf"]]
        erro = None
        if request.method == "POST":
            envio = request.form.get("envio", "")
            try:
                dados = assinador.loads(envio, max_age=7200)
                if dados[:3] != vinculo:
                    raise BadSignature("vínculo")
            except BadSignature:
                abort(400, "Formulário expirado. Abra um novo registro.")
            try:
                denuncia = Denuncia.do_formulario(tipo, request.form)
                if tipo == "PUBLICA" and request.form.get("confirma_email", "").strip() != denuncia.email:
                    raise Regra("Repita o endereço que receberá o comprovante.", "confirma_email")
                imagem = fotos.preparar(request.files.get("foto"))
                recibo, codigo, novo = central.registrar(area, denuncia, envio, imagem)
            except Regra as falha:
                erro = falha
            else:
                enviado = None
                if novo and tipo == "PUBLICA":
                    enviado = enviar_comprovante(app.config, denuncia.email,
                                                 comprovante(recibo["protocolo"], codigo, recibo["criado_em"]))
                return render_template("recibo.html", recibo=recibo, codigo=codigo, enviado=enviado,
                                       novo=novo, tipo=tipo)
        else:
            envio = assinador.dumps([*vinculo, secrets.token_hex(24)])
        return render_template("registro.html", area=a, tipo=tipo, envio=envio, erro=erro), 422 if erro else 200

    def credenciais():
        protocolo = request.form.get("protocolo", "").strip().upper()[:32]
        codigo = request.form.get("codigo", "").strip().upper()[:128]
        chave = (request.remote_addr, protocolo)
        if acessos.tentativa(chave):
            numero = central.verificar(protocolo, codigo)
            if numero:
                acessos.acertou(chave)
                return numero, codigo
        return None, None

    @app.post("/comprovante")
    def baixar():
        numero, codigo = credenciais()
        if not numero:
            abort(400, FALHA_CONSULTA)
        d = central.detalhes(numero)
        return send_file(BytesIO(comprovante(d["protocolo"], codigo, d["criado_em"])),
                         mimetype="application/pdf", as_attachment=True, download_name=d["protocolo"]+".pdf")

    @app.route("/acompanhar", methods=["GET", "POST"])
    def acompanhar():
        erro = None
        if request.method == "POST":
            session.pop("foto_autorizada", None)
            numero, _ = credenciais()
            if numero:
                session["foto_autorizada"] = assinador.dumps(["foto", numero])
                return render_template("detalhe.html", d=central.detalhes(numero), privado=False)
            erro = Regra(FALHA_CONSULTA)
        return render_template("acesso.html", administrativo=False, erro=erro), 422 if erro else 200

    @app.get("/ocorrencias/<int:numero>/foto")
    def foto_publica(numero):
        try:
            autorizacao = assinador.loads(session.get("foto_autorizada", ""), max_age=1800)
        except BadSignature:
            abort(404)
        if autorizacao != ["foto", numero]:
            abort(404)
        return foto(central.detalhes(numero))

    def foto(d):
        if not d or not d["foto_arquivo"]:
            abort(404)
        return send_from_directory(fotos.pasta, d["foto_arquivo"], mimetype="image/png")

    @app.route("/entrar", methods=["GET", "POST"])
    def login():
        erro = None
        if request.method == "POST":
            id_guarda = guardas.autenticar(request.form.get("email", "")[:254].strip(),
                                           request.form.get("senha", "")[:512])
            if id_guarda:
                acessos.sair(session.get("guarda"))
                session.clear()
                session["guarda"] = acessos.entrar(id_guarda)
                return redirect(url_for("painel"))
            erro = Regra("Não foi possível entrar com os dados informados.")
        return render_template("acesso.html", administrativo=True, erro=erro), 422 if erro else 200

    @app.post("/sair")
    def sair():
        acessos.sair(session.get("guarda"))
        session.clear()
        return redirect(url_for("inicio"))

    @app.get("/painel")
    @restrito
    def painel():
        return render_template("painel.html", resumo=guardas.resumo(g.guarda["id"]))

    @app.get("/painel/areas")
    @restrito
    def minhas_areas():
        return areas(True)

    @app.route("/painel/areas/nova", methods=["GET", "POST"])
    @app.route("/painel/areas/<int:area>/editar", methods=["GET", "POST"])
    @restrito
    def editar(area=None):
        guarda = g.guarda["id"]
        a = (catalogo.obter(area, guarda) or abort(404)) if area else {}
        erro = None
        if request.method == "POST":
            try:
                catalogo.salvar(AreaVerde.do_formulario(request.form), guarda, area)
            except Regra as falha:
                erro = falha
            else:
                flash("Área cadastrada." if area is None else "Alterações salvas.")
                return redirect(url_for("minhas_areas"))
        linhas = catalogo.listar("", "", 1, guarda)[:10]
        return render_template("editar.html", area=a, linhas=linhas, erro=erro), 422 if erro else 200

    @app.route("/painel/areas/<int:area>/disponibilidade", methods=["GET", "POST"])
    @restrito
    def disponibilidade(area):
        a = catalogo.obter(area, g.guarda["id"]) or abort(404)
        if request.method == "POST":
            destino = request.form.get("ativa")
            if destino not in ("0", "1"):
                abort(400)
            if not catalogo.ativar(area, g.guarda["id"], destino == "1"):
                abort(404)
            flash("Disponibilidade atualizada.")
            return redirect(url_for("minhas_areas"))
        return render_template("disponibilidade.html", area=a)

    @app.get("/painel/denuncias")
    @restrito
    def fila():
        busca = request.args.get("q", "")[:200].strip()
        situacao = request.args.get("situacao", "")
        p = pagina()
        linhas = central.listar(g.guarda["id"], busca, situacao, p)
        return render_template("fila.html", linhas=linhas[:10], mais=len(linhas)>10,
                               p=p, busca=busca, situacao=situacao)

    @app.route("/painel/denuncias/<int:numero>", methods=["GET", "POST"])
    @restrito
    def detalhe(numero):
        guarda = g.guarda["id"]
        d = central.detalhes(numero, guarda) or abort(404)
        erro = None
        if request.method == "POST":
            try:
                central.atualizar(numero, guarda, request.form)
            except Regra as falha:
                erro = falha
            else:
                flash("Resposta registrada no histórico.")
                return redirect(url_for("detalhe", numero=numero))
        return render_template("detalhe.html", d=d, privado=True, destinos=Atendimento(d["situacao"]).destinos,
                               erro=erro), (409 if erro and erro.campo == "versao" else 422 if erro else 200)

    @app.get("/painel/denuncias/<int:numero>/foto")
    @restrito
    def foto_interna(numero):
        return foto(central.detalhes(numero, g.guarda["id"]))

    @app.cli.command("criar-guarda")
    @click.option("--nome", prompt="Nome")
    @click.option("--email", prompt="E-mail")
    @click.password_option(prompt="Senha")
    def criar_guarda(nome, email, password):
        """Cria uma conta de guarda pelo terminal da equipe."""
        try:
            nome = texto({"nome": nome}, "nome", 3, 120)
            email = email_valido({"email": email}, "email")
            if not 8 <= len(password) <= 512:
                raise Regra("Use uma senha com 8 a 512 caracteres.")
            with banco.transacao() as c:
                c.execute("INSERT INTO guarda (nome,email,senha_hash) VALUES (%s,%s,%s)",
                          (nome, email, proteger(password)))
        except Regra as erro:
            raise click.ClickException(str(erro)) from None
        except psycopg.errors.UniqueViolation:
            raise click.ClickException("Este e-mail já está cadastrado.") from None
        click.echo("Guarda cadastrado.")
    return app

