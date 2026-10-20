from ..extensions import db


class FonteOficial(db.Model):
    __tablename__ = "fonte_oficial"

    id = db.Column(db.Integer, primary_key=True)
    conteudo_id = db.Column(
        db.Integer, db.ForeignKey("conteudo.id", ondelete="CASCADE"), nullable=False
    )
    orgao = db.Column(db.String(120), nullable=False)
    titulo = db.Column(db.String(150), nullable=False)
    url = db.Column(db.String(500), nullable=False)

    conteudo = db.relationship("Conteudo", back_populates="fontes")

    def __repr__(self):
        return f"<FonteOficial {self.url}>"
