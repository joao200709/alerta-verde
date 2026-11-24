from datetime import timezone, timedelta
from email.message import EmailMessage
from io import BytesIO
from pathlib import Path
import secrets
import smtplib
import ssl

from PIL import Image, UnidentifiedImageError
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A5
from reportlab.pdfgen.canvas import Canvas

from .dominio import Regra

LIMITE = 5 * 1024 * 1024


def data_local(data):
    return data.astimezone(timezone(timedelta(hours=-3))).strftime("%d/%m/%Y às %H:%M")


class Fotos:
    def __init__(self, pasta):
        self.pasta = Path(pasta)
        self.pasta.mkdir(parents=True, exist_ok=True)

    def preparar(self, upload):
        if not upload or not upload.filename:
            return None
        bruto = upload.stream.read(LIMITE + 1)
        if len(bruto) > LIMITE:
            raise Regra("O PNG deve ter até 5 MB.", "foto")
        try:
            with Image.open(BytesIO(bruto), formats=["PNG"]) as original:
                if original.width * original.height > 24_000_000:
                    raise Regra("Use uma imagem de até 24 megapixels.", "foto")
                original.verify()
            with Image.open(BytesIO(bruto), formats=["PNG"]) as original:
                limpa = original.convert("RGBA")
                limpa.info.clear()
                saida = BytesIO()
                limpa.save(saida, format="PNG")
                return saida.getvalue()
        except (UnidentifiedImageError, OSError, SyntaxError, ValueError, Image.DecompressionBombError) as erro:
            if isinstance(erro, Regra):
                raise
            raise Regra("Escolha um arquivo PNG válido.", "foto") from None

    def salvar(self, imagem):
        nome = secrets.token_hex(24) + ".png"
        try:
            (self.pasta / nome).write_bytes(imagem)
        except OSError:
            self.remover(nome)
            raise
        return nome

    def remover(self, nome):
        (self.pasta / nome).unlink(missing_ok=True)


def comprovante(protocolo, codigo, criado_em):
    saida = BytesIO()
    pdf = Canvas(saida, pagesize=A5, invariant=1)
    pdf.setTitle("Comprovante de denúncia | Alerta Verde")
    pdf.setFillColor(HexColor("#174c39"))
    pdf.rect(0, 485, A5[0], 120, fill=1, stroke=0)
    pdf.setFillColorRGB(1, 1, 1)
    pdf.setFont("Helvetica-Bold", 20)
    pdf.drawString(32, 540, "Alerta Verde")
    pdf.setFont("Helvetica", 12)
    pdf.drawString(32, 511, "Comprovante de registro de denúncia")
    for y, titulo, valor in ((439, "Recebida em", data_local(criado_em)),
                             (360, "Protocolo", protocolo), (281, "Código de acesso", codigo)):
        pdf.setFillColor(HexColor("#41554c"))
        pdf.setFont("Helvetica", 11)
        pdf.drawString(32, y, titulo)
        pdf.setFillColor(HexColor("#143e2d"))
        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawString(32, y - 28, valor)
    pdf.setFont("Helvetica", 11)
    pdf.drawString(32, 168, "Guarde este comprovante. Use o protocolo e o código")
    pdf.drawString(32, 150, "em Acompanhar denúncia para consultar o atendimento.")
    pdf.showPage()
    pdf.save()
    return saida.getvalue()


def enviar_comprovante(config, email, pdf):
    if not config.get("SMTP_HOST") or not config.get("SMTP_FROM"):
        return False
    mensagem = EmailMessage()
    mensagem["From"] = config["SMTP_FROM"]
    mensagem["To"] = email
    mensagem["Subject"] = "Alerta Verde | Comprovante da sua denúncia"
    mensagem.set_content(
        "Olá,\n\nSua denúncia foi registrada no Alerta Verde.\n\n"
        "O comprovante em PDF está em anexo. Para acompanhar o atendimento, "
        "acesse Acompanhar denúncia e informe o protocolo e o código de acesso do comprovante."
    )
    mensagem.add_attachment(pdf, maintype="application", subtype="pdf", filename="comprovante.pdf")
    try:
        with smtplib.SMTP(config["SMTP_HOST"], int(config["SMTP_PORT"]), timeout=8) as cliente:
            if config["SMTP_TLS"]:
                cliente.starttls(context=ssl.create_default_context())
            if config.get("SMTP_USER"):
                cliente.login(config["SMTP_USER"], config["SMTP_PASSWORD"])
            cliente.send_message(mensagem)
        return True
    except (OSError, smtplib.SMTPException):
        return False

