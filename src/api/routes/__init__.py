# api/routes/__init__.py

from flask import Blueprint

# Crear el blueprint principal para 'api'
api_bp = Blueprint('api', __name__)

# Luego importamos los otros blueprints
from .usuarios import usuarios_bp
from .ingresos import ingresos_bp
from .categorias import categorias_bp
from .egresos import egresos_bp
from .plandeahorro import plandeahorro_bp
from .fondos_emergencia import fondos_emergencia_bp
from .suscripciones import suscripciones_bp
from .alertas import alertas_bp

# Registrar los blueprints secundarios con el prefijo /api
api_bp.register_blueprint(usuarios_bp, url_prefix='/usuarios')
api_bp.register_blueprint(ingresos_bp, url_prefix='/ingresos')
api_bp.register_blueprint(categorias_bp, url_prefix='/categorias')
api_bp.register_blueprint(egresos_bp, url_prefix='/egresos')
api_bp.register_blueprint(plandeahorro_bp, url_prefix='/plandeahorro')
api_bp.register_blueprint(fondos_emergencia_bp, url_prefix='/fondos_emergencia')
api_bp.register_blueprint(suscripciones_bp, url_prefix='/suscripciones')
api_bp.register_blueprint(alertas_bp, url_prefix='/alertas')

# Función que inicializa la aplicación con todos los blueprints registrados
def init_app(app):
    app.register_blueprint(api_bp, url_prefix='/api')
