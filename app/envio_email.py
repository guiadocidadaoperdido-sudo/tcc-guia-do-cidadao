"""Envio de e-mail do site (por enquanto, só o de recuperação de senha).

Escolhe sozinho o jeito de mandar, conforme o que estiver no .env:

1. BREVO_API_KEY preenchida: manda pela API do Brevo (HTTPS). É o jeito usado
   no Render, porque o plano grátis do Render bloqueia o SMTP (portas 25, 465
   e 587) desde setembro de 2025.
2. MAIL_SENHA preenchida: manda pelo SMTP do Gmail (bom para rodar no PC).
3. Nenhum dos dois: não manda nada e só escreve o e-mail no log. Assim dá para
   testar no computador sem configurar e-mail nenhum.

Não usa biblioteca nova: o smtplib e o urllib já vêm com o Python.
"""
import json
import smtplib
import ssl
import urllib.error
import urllib.request
from email.message import EmailMessage

from flask import current_app

URL_BREVO = "https://api.brevo.com/v3/smtp/email"


def enviar_email(para, assunto, texto):
    """Manda um e-mail de texto simples. Devolve True se deu certo.

    Nunca levanta erro: se o envio falhar, registra no log e devolve False,
    para a página não quebrar por causa do e-mail.
    """
    config = current_app.config
    try:
        if config.get("BREVO_API_KEY"):
            _enviar_pelo_brevo(para, assunto, texto)
        elif config.get("MAIL_SENHA"):
            _enviar_pelo_smtp(para, assunto, texto)
        else:
            # Sem e-mail configurado (computador de desenvolvimento).
            current_app.logger.warning(
                "E-mail não configurado. Mensagem que seria enviada:\n%s\n\n%s", assunto, texto
            )
        return True
    except (OSError, smtplib.SMTPException, urllib.error.URLError) as erro:
        # O log não guarda o e-mail da pessoa (RNF10), só o tipo do erro.
        current_app.logger.error("Falha ao enviar e-mail: %s", type(erro).__name__)
        return False


def _remetente():
    config = current_app.config
    return config["MAIL_REMETENTE_NOME"], config["MAIL_REMETENTE"]


def _enviar_pelo_brevo(para, assunto, texto):
    nome, email = _remetente()
    corpo = json.dumps({
        "sender": {"name": nome, "email": email},
        "to": [{"email": para}],
        "subject": assunto,
        "textContent": texto,
    }).encode("utf-8")
    pedido = urllib.request.Request(URL_BREVO, data=corpo, method="POST", headers={
        "api-key": current_app.config["BREVO_API_KEY"],
        "Content-Type": "application/json",
        "Accept": "application/json",
    })
    # O urllib levanta HTTPError (que é um URLError) se o Brevo responder com erro.
    with urllib.request.urlopen(pedido, timeout=10):
        pass


def _enviar_pelo_smtp(para, assunto, texto):
    config = current_app.config
    nome, email = _remetente()
    mensagem = EmailMessage()
    mensagem["From"] = f"{nome} <{email}>"
    mensagem["To"] = para
    mensagem["Subject"] = assunto
    mensagem.set_content(texto)

    with smtplib.SMTP(config["MAIL_SERVIDOR"], config["MAIL_PORTA"], timeout=10) as smtp:
        smtp.starttls(context=ssl.create_default_context())
        smtp.login(config["MAIL_USUARIO"] or email, config["MAIL_SENHA"])
        smtp.send_message(mensagem)
