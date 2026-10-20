from datetime import datetime

from ..extensions import db


class Avaliacao(db.Model):
    """Resposta do visitante à pergunta "Este conteúdo foi útil?" (RF07).

    Não guarda nenhum dado pessoal do visitante (RNF10).
    """
    __tablename__ = "avaliacao"

    id = db.Column(db.Integer, primary_key=True)
    conteudo_id = db.Column(
        db.Integer, db.ForeignKey("conteudo.id", ondelete="CASCADE"), nullable=False
    )
    util = db.Column(db.Boolean, nullable=False)
    comentario = db.Column(db.String(500))
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.now)

    conteudo = db.relationship("Conteudo", back_populates="avaliacoes")
