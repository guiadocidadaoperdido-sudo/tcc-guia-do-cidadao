"""Formulários do site e da área administrativa. O Flask-WTF inclui o token CSRF (RNF06)."""
from flask_wtf import FlaskForm
from wtforms import BooleanField, EmailField, PasswordField, SelectField, StringField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, Regexp

SLUG_VALIDO = Regexp(
    r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    message="Use só letras minúsculas sem acento, números e hífens. Ex.: bolsa-familia",
)



def tirar_espacos(texto):
    """O teclado do celular costuma colocar um espaço depois do e-mail."""
    return texto.strip() if isinstance(texto, str) else texto


class LoginForm(FlaskForm):
    email = EmailField(
        "E-mail", filters=[tirar_espacos],
        validators=[DataRequired("Informe o e-mail."), Email("E-mail inválido.")],
    )
    senha = PasswordField("Senha", validators=[DataRequired("Informe a senha.")])


# ---------- Conta do cidadão ----------

SENHA_MINIMA = 8


class CadastroForm(FlaskForm):
    email = EmailField(
        "E-mail", filters=[tirar_espacos],
        validators=[DataRequired("Informe o e-mail."), Email("E-mail inválido."), Length(max=150)],
    )
    senha = PasswordField(
        "Senha",
        validators=[
            DataRequired("Crie uma senha."),
            Length(min=SENHA_MINIMA, max=128, message=f"A senha precisa ter pelo menos {SENHA_MINIMA} caracteres."),
        ],
        description=f"Pelo menos {SENHA_MINIMA} caracteres.",
    )
    confirmar_senha = PasswordField(
        "Repita a senha",
        validators=[DataRequired("Repita a senha."), EqualTo("senha", "As senhas não são iguais.")],
    )
    consentimento = BooleanField(
        "Li e concordo que o guia guarde meu e-mail, os temas que eu salvar e meus "
        "lembretes, só para eu usar a minha área.",
        validators=[DataRequired("Para criar a conta, marque que você concorda.")],
    )


class ExcluirContaForm(FlaskForm):
    senha = PasswordField(
        "Digite sua senha para confirmar",
        validators=[DataRequired("Digite sua senha para confirmar.")],
    )


# ---------- Área administrativa ----------

class BloqueioForm(FlaskForm):
    motivo = StringField(
        "Motivo do bloqueio",
        filters=[tirar_espacos],
        validators=[
            DataRequired("Informe o motivo do bloqueio."),
            Length(min=10, max=255, message="Descreva o motivo com 10 a 255 caracteres."),
        ],
        description="Fica registrado aqui. A pessoa só vê que a conta está bloqueada, sem o motivo.",
    )


class CategoriaForm(FlaskForm):
    nome = StringField("Nome", validators=[DataRequired("Informe o nome."), Length(max=80)])
    slug = StringField(
        "Endereço (slug)",
        validators=[Optional(), Length(max=80), SLUG_VALIDO],
        description="Deixe em branco para gerar a partir do nome.",
    )
    descricao = TextAreaField("Descrição", validators=[Optional(), Length(max=500)])


class ConteudoForm(FlaskForm):
    titulo = StringField("Título", validators=[DataRequired("Informe o título."), Length(max=150)])
    slug = StringField(
        "Endereço (slug)",
        validators=[Optional(), Length(max=150), SLUG_VALIDO],
        description="Deixe em branco para gerar a partir do título.",
    )
    categoria_id = SelectField("Categoria", coerce=int, validators=[DataRequired("Escolha a categoria.")])
    resumo = TextAreaField(
        "Resumo",
        validators=[DataRequired("Escreva um resumo."), Length(max=300)],
        description="Até 300 caracteres. Aparece na lista e na busca.",
    )
    o_que_e = TextAreaField(
        "O que é", validators=[DataRequired("Explique o que é.")],
        description="Separe os parágrafos com uma linha em branco.",
    )
    quem_tem_direito = TextAreaField(
        "Quem tem direito", validators=[Optional()], description="Um item por linha."
    )
    documentos = TextAreaField(
        "Documentos necessários", validators=[Optional()], description="Um documento por linha."
    )
    como_solicitar = TextAreaField(
        "Como solicitar (passo a passo)", validators=[Optional()], description="Um passo por linha."
    )
    alerta_golpes = TextAreaField("Alerta sobre golpes", validators=[Optional()])
    publicado = BooleanField("Publicar no site")
