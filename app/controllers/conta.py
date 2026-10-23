"""Blueprint da conta do cidadão (login opcional).

O site continua funcionando sem conta. Quem cria uma conta pode salvar temas,
acompanhar o passo a passo e criar lembretes.

O login do cidadão é separado do login do administrador: o cidadão fica em
session["cidadao_id"] e o administrador continua no Flask-Login. A sessão
acaba quando o navegador é fechado.
"""
from datetime import datetime
from functools import wraps

from flask import (
    Blueprint, current_app, flash, redirect, render_template, request, session, url_for,
)
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from ..extensions import db, limiter
from ..forms import CadastroForm, ExcluirContaForm, LoginForm
from ..models import Usuario

bp = Blueprint("conta", __name__)


# ---------- Quem está logado ----------

def cidadao_atual():
    """Devolve o cidadão logado ou None.

    O db.session.get reaproveita o objeto já carregado na mesma requisição,
    então chamar esta função várias vezes não repete a consulta no banco.
    """
    cidadao_id = session.get("cidadao_id")
    if not cidadao_id:
        return None
    usuario = db.session.get(Usuario, cidadao_id)
    if usuario is None or not usuario.esta_ativo:
        # A conta foi bloqueada ou excluída: quem estava logado sai na hora.
        session.pop("cidadao_id", None)
        return None
    return usuario


def exigir_conta(view):
    """Decorador para as páginas que só funcionam com a pessoa logada."""
    @wraps(view)
    def envolvida(*args, **kwargs):
        if cidadao_atual() is None:
            flash("Entre na sua conta para ver esta página.", "aviso")
            return redirect(url_for("conta.entrar"))
        return view(*args, **kwargs)
    return envolvida


@bp.app_context_processor
def disponibilizar_cidadao():
    # Deixa {{ cidadao }} disponível em todos os templates (ex.: ícone do topo).
    return {"cidadao": cidadao_atual()}


@bp.after_request
def sem_cache(resposta):
    # Páginas da conta não ficam guardadas no navegador (computador compartilhado).
    resposta.headers["Cache-Control"] = "no-store"
    return resposta


def _logar(usuario):
    session["cidadao_id"] = usuario.id
    session.permanent = False  # sai ao fechar o navegador


# ---------- Cadastro, entrar e sair ----------

@bp.route("/cadastrar", methods=["GET", "POST"])
@limiter.limit(lambda: current_app.config["LIMITE_LOGIN"], methods=["POST"])
def cadastrar():
    if cidadao_atual():
        return redirect(url_for("conta.minha_area"))
    form = CadastroForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        if Usuario.query.filter(func.lower(Usuario.email) == email).first():
            form.email.errors.append("Já existe uma conta com esse e-mail. Tente entrar.")
        else:
            usuario = Usuario(email=email, consentimento_em=datetime.now())
            usuario.definir_senha(form.senha.data)
            db.session.add(usuario)
            try:
                db.session.commit()
            except IntegrityError:
                # Dois cadastros com o mesmo e-mail ao mesmo tempo: o UNIQUE do banco segura.
                db.session.rollback()
                form.email.errors.append("Já existe uma conta com esse e-mail. Tente entrar.")
                return render_template("publico/conta/cadastrar.html", form=form)
            # O log não guarda o e-mail (RNF10).
            current_app.logger.info("Conta de cidadão criada (id %s).", usuario.id)
            _logar(usuario)
            flash("Conta criada! Agora você pode salvar temas e criar lembretes.", "sucesso")
            return redirect(url_for("conta.minha_area"))
    return render_template("publico/conta/cadastrar.html", form=form)


@bp.route("/entrar", methods=["GET", "POST"])
# Mesmo limite de tentativas do login do administrador (força bruta).
@limiter.limit(lambda: current_app.config["LIMITE_LOGIN"], methods=["POST"])
def entrar():
    if cidadao_atual():
        return redirect(url_for("conta.minha_area"))
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        usuario = Usuario.query.filter(func.lower(Usuario.email) == email).first()
        if usuario and usuario.conferir_senha(form.senha.data):
            if not usuario.esta_ativo:
                # O motivo do bloqueio é interno e não aparece para a pessoa.
                flash("Sua conta está bloqueada. Se achar que é um engano, fale com a "
                      "equipe do guia.", "erro")
                return render_template("publico/conta/entrar.html", form=form)
            _logar(usuario)
            flash("Que bom ver você de novo!", "sucesso")
            return redirect(url_for("conta.minha_area"))
        # Mesma mensagem para e-mail e senha errados, para não revelar qual falhou.
        flash("E-mail ou senha incorretos.", "erro")
    return render_template("publico/conta/entrar.html", form=form)


@bp.route("/sair", methods=["POST"])
def sair():
    # Tira só o cidadão da sessão; se houver admin logado no mesmo navegador, ele continua.
    session.pop("cidadao_id", None)
    flash("Você saiu da sua conta.", "sucesso")
    return redirect(url_for("publico.inicio"))


# ---------- Minha área ----------

@bp.route("/")
@exigir_conta
def minha_area():
    return render_template(
        "publico/conta/minha_area.html", usuario=cidadao_atual(), form_excluir=ExcluirContaForm()
    )


@bp.route("/excluir", methods=["POST"])
@exigir_conta
@limiter.limit(lambda: current_app.config["LIMITE_LOGIN"])
def excluir():
    """Exclusão a pedido do titular (LGPD). Pede a senha de novo para confirmar.

    Apaga o e-mail, a senha, os temas salvos e os lembretes. A linha fica,
    sem dados pessoais, para aparecer em "Contas excluídas" no admin.
    """
    usuario = cidadao_atual()
    form = ExcluirContaForm()
    if not (form.validate_on_submit() and usuario.conferir_senha(form.senha.data)):
        flash("Senha incorreta. A conta não foi excluída.", "erro")
        return redirect(url_for("conta.minha_area") + "#excluir")

    usuario_id = usuario.id
    usuario.excluir_conta()
    db.session.commit()
    session.pop("cidadao_id", None)
    current_app.logger.info("Conta de cidadão excluída (id %s).", usuario_id)
    flash("Sua conta e todos os seus dados foram apagados.", "sucesso")
    return redirect(url_for("publico.inicio"))
