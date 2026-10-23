from ..extensions import db


class TermoGlossario(db.Model):
    """Termo do glossário "O que é isso?". Aparece sublinhado nos textos do guia."""
    __tablename__ = "termo_glossario"

    id = db.Column(db.Integer, primary_key=True)
    termo = db.Column(db.String(80), nullable=False, unique=True)
    explicacao = db.Column(db.String(400), nullable=False)

    def __repr__(self):
        return f"<TermoGlossario {self.termo}>"
