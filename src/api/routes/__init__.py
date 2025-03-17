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

# Función que inicializa la aplicación con todos los blueprints registrados
def init_app(app):
    # Registrar los blueprints secundarios con el prefijo /api
    app.register_blueprint(usuarios_bp, url_prefix='/usuarios')
    app.register_blueprint(ingresos_bp, url_prefix='/ingresos')
    app.register_blueprint(categorias_bp, url_prefix='/categorias')
    app.register_blueprint(egresos_bp, url_prefix='/egresos')
    app.register_blueprint(plandeahorro_bp, url_prefix='/plandeahorro')
    app.register_blueprint(fondos_emergencia_bp, url_prefix='/fondos_emergencia')
    app.register_blueprint(suscripciones_bp, url_prefix='/suscripciones')
    app.register_blueprint(alertas_bp, url_prefix='/alertas')

    # Ahora registramos el blueprint principal api_bp en la app
    app.register_blueprint(api_bp, url_prefix='/api')
