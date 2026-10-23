from datetime import datetime

from ..extensions import db


class Lembrete(db.Model):
    """Lembrete de prazo que o cidadão coloca na agenda do celular ou do computador."""
    __tablename__ = "lembrete"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(
        db.Integer, db.ForeignKey("usuario.id", ondelete="CASCADE"), nullable=False
    )
    conteudo_id = db.Column(db.Integer, db.ForeignKey("conteudo.id", ondelete="SET NULL"))
    titulo = db.Column(db.String(150), nullable=False)
    data = db.Column(db.Date, nullable=False)
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.now)

    usuario = db.relationship("Usuario", back_populates="lembretes")
    conteudo = db.relationship("Conteudo", back_populates="lembretes")
