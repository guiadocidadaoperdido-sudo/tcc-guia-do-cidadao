"""Comandos de terminal do projeto (rodar com: flask --app run <comando>)."""
import getpass

import click

from .extensions import db
from .models import Administrador, Categoria, Conteudo, FonteOficial


def registrar_comandos(app):
    @app.cli.command("criar-banco")
    def criar_banco():
        """Cria ou atualiza as tabelas aplicando as migrações (Flask-Migrate).

        Bancos criados antes das migrações (com db.create_all) já têm as cinco
        tabelas: nesse caso o banco é só marcado como estando na primeira
        migração, e as seguintes são aplicadas normalmente.
        """
        from flask_migrate import stamp, upgrade
        from sqlalchemy import inspect

        tabelas = set(inspect(db.engine).get_table_names())
        if "conteudo" in tabelas and "alembic_version" not in tabelas:
            stamp(revision="0001")
            click.echo("Banco antigo reconhecido e marcado na migração 0001.")
        upgrade()
        click.echo(f"Banco atualizado em: {db.engine.url.render_as_string(hide_password=True)}")

    @app.cli.command("dados-iniciais")
    def dados_iniciais():
        """Cadastra as categorias e os conteúdos iniciais (só os que ainda não existem)."""
        from .dados_iniciais import CATEGORIAS, CONTEUDOS

        categorias = {}
        for dados in CATEGORIAS:
            cat = Categoria.query.filter_by(slug=dados["slug"]).first()
            if cat is None:
                cat = Categoria(**dados)
                db.session.add(cat)
                click.echo(f"Categoria criada: {dados['nome']}")
            categorias[dados["slug"]] = cat
        db.session.flush()

        for dados in CONTEUDOS:
            if Conteudo.query.filter_by(slug=dados["slug"]).first():
                click.echo(f"Já existe, mantido: {dados['titulo']}")
                continue
            dados = dict(dados)
            fontes = dados.pop("fontes")
            categoria = categorias[dados.pop("categoria")]
            conteudo = Conteudo(categoria=categoria, publicado=True, **dados)
            conteudo.fontes = [FonteOficial(**f) for f in fontes]
            db.session.add(conteudo)
            click.echo(f"Conteúdo criado: {conteudo.titulo}")
        db.session.commit()

    @app.cli.command("criar-admin")
    @click.option("--nome", prompt="Nome")
    @click.option("--email", prompt="E-mail")
    def criar_admin(nome, email):
        """Cadastra um administrador. A senha é pedida no terminal e guardada só como hash."""
        email = email.strip().lower()
        if Administrador.query.filter_by(email=email).first():
            raise click.ClickException("Já existe um administrador com esse e-mail.")
        senha = getpass.getpass("Senha (mínimo 8 caracteres): ")
        if len(senha) < 8:
            raise click.ClickException("A senha precisa ter pelo menos 8 caracteres.")
        if senha != getpass.getpass("Repita a senha: "):
            raise click.ClickException("As senhas não são iguais.")
        admin = Administrador(nome=nome.strip(), email=email)
        admin.definir_senha(senha)
        db.session.add(admin)
        db.session.commit()
        click.echo(f"Administrador {email} criado.")
