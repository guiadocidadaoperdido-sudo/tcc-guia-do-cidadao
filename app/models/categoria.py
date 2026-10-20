from ..extensions import db


class Categoria(db.Model):
    __tablename__ = "categoria"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(80), nullable=False, unique=True)
    descricao = db.Column(db.Text)

    conteudos = db.relationship(
        "Conteudo", back_populates="categoria", order_by="Conteudo.titulo"
    )

    @property
    def conteudos_publicados(self):
        return [c for c in self.conteudos if c.publicado]

    def __repr__(self):
        return f"<Categoria {self.slug}>"
