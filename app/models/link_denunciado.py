from datetime import datetime

from ..extensions import db

PENDENTE = "pendente"
CONFIRMADO = "confirmado"
DESCARTADO = "descartado"


class LinkDenunciado(db.Model):
    """Link suspeito enviado por um cidadão com conta.

    O administrador revisa: os confirmados entram na lista de golpes e são
    usados pelo verificador de golpe.
    """
    __tablename__ = "link_denunciado"
    __table_args__ = (
        db.CheckConstraint(
            "status IN ('pendente', 'confirmado', 'descartado')",
            name="ck_link_denunciado_status",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id", ondelete="SET NULL"))
    administrador_id = db.Column(
        db.Integer, db.ForeignKey("administrador.id", ondelete="SET NULL")
    )
    url = db.Column(db.String(500), nullable=False)
    dominio = db.Column(db.String(255), nullable=False, index=True)
    descricao = db.Column(db.String(500))
    status = db.Column(db.String(20), nullable=False, default=PENDENTE, index=True)
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.now)
    revisado_em = db.Column(db.DateTime)

    usuario = db.relationship("Usuario", back_populates="denuncias")
    administrador = db.relationship("Administrador")

    def revisar(self, status, administrador):
        """O admin confirma ou descarta (ou volta para pendente) e fica registrado quem foi."""
        self.status = status
        self.administrador = administrador if status != PENDENTE else None
        self.revisado_em = datetime.now() if status != PENDENTE else None
