# token_required.py

import jwt
from functools import wraps
from flask import request, jsonify, current_app

def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        # Verificar si el token está en los encabezados de la solicitud
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]  # 'Bearer token'
        if not token:
            return jsonify({'msg': 'Token no proporcionado'}), 401
        
        try:
            # Decodificar el token usando el SECRET_KEY
            SECRET_KEY = current_app.config['SECRET_KEY']
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return jsonify({'msg': 'El token ha expirado'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'msg': 'Token inválido'}), 401
        
        # Si el token es válido, pasamos al siguiente handler
        return f(payload, *args, **kwargs)

    return decorated_function
