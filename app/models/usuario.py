from datetime import datetime

from werkzeug.security import check_password_hash, generate_password_hash

from ..extensions import db


class Usuario(db.Model):
    """Cidadão com conta. O login é opcional: o site funciona sem ele.

    LGPD: guarda só o mínimo (e-mail e senha em hash) e a data em que a
    pessoa aceitou o termo de uso dos dados. Ao excluir a conta, os temas
    salvos e os lembretes são apagados juntos.
    """
    __tablename__ = "usuario"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), nullable=False, unique=True)
    senha_hash = db.Column(db.String(255), nullable=False)
    consentimento_em = db.Column(db.DateTime, nullable=False)
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.now)

    # A exclusão em cascata é feita pelo próprio ORM (sem passive_deletes),
    # porque o SQLite dos testes não aplica o ON DELETE CASCADE sozinho.
    acompanhamentos = db.relationship(
        "Acompanhamento", back_populates="usuario",
        cascade="all, delete-orphan", order_by="Acompanhamento.criado_em.desc()",
    )
    lembretes = db.relationship(
        "Lembrete", back_populates="usuario",
        cascade="all, delete-orphan", order_by="Lembrete.data",
    )
    # As denúncias continuam depois que a conta é excluída, mas sem dono.
    denuncias = db.relationship("LinkDenunciado", back_populates="usuario")

    def definir_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def conferir_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)

    def __repr__(self):
        return f"<Usuario {self.id}>"
