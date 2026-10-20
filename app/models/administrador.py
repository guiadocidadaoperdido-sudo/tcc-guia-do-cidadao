from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from ..extensions import db, login_manager


class Administrador(UserMixin, db.Model):
    __tablename__ = "administrador"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), nullable=False, unique=True)
    senha_hash = db.Column(db.String(255), nullable=False)
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.now)

    conteudos = db.relationship("Conteudo", back_populates="administrador")

    def definir_senha(self, senha):
        # RNF04: a senha nunca é guardada em texto puro, só o hash.
        self.senha_hash = generate_password_hash(senha)

    def conferir_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)

    def __repr__(self):
        return f"<Administrador {self.email}>"


@login_manager.user_loader
def carregar_administrador(id_admin):
    return db.session.get(Administrador, int(id_admin))
