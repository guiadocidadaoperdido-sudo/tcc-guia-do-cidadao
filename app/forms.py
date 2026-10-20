"""Formulários da área administrativa. O Flask-WTF inclui o token CSRF (RNF06)."""
from flask_wtf import FlaskForm
from wtforms import BooleanField, EmailField, PasswordField, SelectField, StringField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, Optional, Regexp

SLUG_VALIDO = Regexp(
    r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    message="Use só letras minúsculas sem acento, números e hífens. Ex.: bolsa-familia",
)


class LoginForm(FlaskForm):
    email = EmailField("E-mail", validators=[DataRequired("Informe o e-mail."), Email("E-mail inválido.")])
    senha = PasswordField("Senha", validators=[DataRequired("Informe a senha.")])


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
