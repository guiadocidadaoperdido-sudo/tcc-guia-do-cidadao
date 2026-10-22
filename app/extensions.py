"""Extensões do Flask criadas uma vez e ligadas à aplicação em create_app."""
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
# Limite de requisições por endereço IP, usado no login e na avaliação.
# O IP fica só na memória do servidor, por poucos minutos, e não vai para o banco.
limiter = Limiter(key_func=get_remote_address, default_limits=[])
