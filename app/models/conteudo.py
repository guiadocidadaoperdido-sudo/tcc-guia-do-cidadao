from datetime import datetime

from sqlalchemy import DDL, event, func, literal_column, or_

from ..extensions import db

# Configuração de idioma da pesquisa de texto do PostgreSQL.
PORTUGUES = literal_column("'portuguese'::regconfig")


class Conteudo(db.Model):
    """Classe central do sistema: um tema explicado em partes (RF04)."""
    __tablename__ = "conteudo"

    id = db.Column(db.Integer, primary_key=True)
    categoria_id = db.Column(db.Integer, db.ForeignKey("categoria.id"), nullable=False)
    administrador_id = db.Column(
        db.Integer, db.ForeignKey("administrador.id", ondelete="SET NULL")
    )
    titulo = db.Column(db.String(150), nullable=False)
    slug = db.Column(db.String(150), nullable=False, unique=True)
    resumo = db.Column(db.String(300), nullable=False)
    o_que_e = db.Column(db.Text, nullable=False)
    quem_tem_direito = db.Column(db.Text)
    documentos = db.Column(db.Text)
    como_solicitar = db.Column(db.Text)
    alerta_golpes = db.Column(db.Text)
    publicado = db.Column(db.Boolean, nullable=False, default=False)
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.now)
    atualizado_em = db.Column(db.DateTime, nullable=False, default=datetime.now)

    categoria = db.relationship("Categoria", back_populates="conteudos")
    administrador = db.relationship("Administrador", back_populates="conteudos")
    fontes = db.relationship(
        "FonteOficial",
        back_populates="conteudo",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="FonteOficial.id",
    )
    avaliacoes = db.relationship(
        "Avaliacao", back_populates="conteudo", cascade="all, delete-orphan", passive_deletes=True
    )
    # Quem salvou este tema. Se o conteúdo for excluído, o acompanhamento some junto.
    acompanhamentos = db.relationship(
        "Acompanhamento", back_populates="conteudo", cascade="all, delete-orphan"
    )
    # Lembretes ligados a este tema. Se o conteúdo for excluído, o lembrete fica sem tema.
    lembretes = db.relationship("Lembrete", back_populates="conteudo")

    @property
    def total_util(self):
        return sum(1 for a in self.avaliacoes if a.util)

    @property
    def total_nao_util(self):
        return sum(1 for a in self.avaliacoes if not a.util)

    @classmethod
    def buscar(cls, termo):
        """Busca por palavra-chave nos conteúdos publicados (RF03).

        No PostgreSQL usa a pesquisa de texto em português, com a mesma
        expressão do índice idx_conteudo_busca, para que "documento" também
        encontre "documentos". Em outros bancos (SQLite, usado nos testes)
        faz uma busca simples por trecho do texto.
        """
        termo = (termo or "").strip()
        if not termo:
            return []
        consulta = cls.query.filter(cls.publicado.is_(True))

        if db.engine.dialect.name == "postgresql":
            documento = func.to_tsvector(
                PORTUGUES, cls.titulo + " " + cls.resumo + " " + cls.o_que_e
            )
            pergunta = func.plainto_tsquery(PORTUGUES, termo)
            return (
                consulta.filter(documento.op("@@")(pergunta))
                .order_by(func.ts_rank(documento, pergunta).desc(), cls.titulo)
                .all()
            )

        padrao = f"%{termo}%"
        return (
            consulta.filter(
                or_(cls.titulo.ilike(padrao), cls.resumo.ilike(padrao), cls.o_que_e.ilike(padrao))
            )
            .order_by(cls.titulo)
            .all()
        )

    def __repr__(self):
        return f"<Conteudo {self.slug}>"


# Índice da busca em português (o mesmo do Apêndice B). Só é criado no
# PostgreSQL, logo depois da tabela conteudo.
event.listen(
    Conteudo.__table__,
    "after_create",
    DDL(
        "CREATE INDEX IF NOT EXISTS idx_conteudo_busca ON conteudo USING GIN ("
        "to_tsvector('portuguese', titulo || ' ' || resumo || ' ' || o_que_e))"
    ).execute_if(dialect="postgresql"),
)
