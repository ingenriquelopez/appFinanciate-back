import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify, url_for, send_from_directory
from flask_migrate import Migrate
from flask_swagger import swagger
from api.utils import APIException, generate_sitemap
from api.models import db
from api.routes import init_app, api_bp  # Importar api_bp aquí
from api.commands import setup_commands
from flask_cors import CORS

ENV = "development" if os.getenv("FLASK_DEBUG") == "1" else "production"

if ENV == "development":
    load_dotenv()  # Cargar el archivo .env solo en desarrollo
static_file_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../static/')

app = Flask(__name__)
app.url_map.strict_slashes = False
print(os.getenv('FLASK_APP'))

# Database configuration
db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace(
        "postgres://", "postgresql://")

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv("FLASK_APP_KEY")  # Esto también funcionará para JWT

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)

# Add the admin
setup_commands(app)

# Inicializar los blueprints con init_app
init_app(app)

# Registra el blueprint api_bp
app.register_blueprint(api_bp, url_prefix='/api')  # Esto ya no da error porque ahora api_bp está importado correctamente

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# Generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    if ENV == "development":
        return generate_sitemap(app)
    return send_from_directory(static_file_dir, 'index.html')

# Serve static files
@app.route('/<path:path>', methods=['GET'])
def serve_any_other_file(path):
    if not os.path.isfile(os.path.join(static_file_dir, path)):
        path = 'index.html'
    response = send_from_directory(static_file_dir, path)
    response.cache_control.max_age = 0  # avoid cache memory
    return response

# Runs only if `$ python src/main.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3001))
    app.run(host='0.0.0.0', port=PORT, debug=True)
