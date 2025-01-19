# api/routes/ingresos.py
from flask import Blueprint, request, jsonify
from api.models import db, Ingreso,Usuario
from api.token_required import token_required
from datetime import date


#--------------------------------------------
ingresos_bp = Blueprint('ingresos', __name__)
#--------------------------------------------

# Ruta para obtener ingresos
@ingresos_bp.route('/ingresos', methods=['GET'])
@token_required
def obtener_ingresos(payload):
    try:
        # Obtener el id del usuario desde el token
        usuario_id = payload['id']
        
        # Filtrar los ingresos por el id del usuario autenticado
        ingresos = Ingreso.query.filter_by(usuario_id=usuario_id).all()
        
        # Formatear los ingresos como una lista de diccionarios
        ingresos_serializados = [
            {
                "id": ingreso.id,
                "monto": ingreso.monto,
                "descripcion": ingreso.descripcion,
                "fecha": ingreso.fecha.isoformat(),
                "categoria_id": ingreso.categoria_id,
                "usuario_id": ingreso.usuario_id
            }
            for ingreso in ingresos
        ]

        return jsonify(ingresos_serializados), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


#----------------------------------------------------------------------------------------
# Ruta para crear un INGRESO
@ingresos_bp.route('/ingreso', methods=['POST'])
@token_required
def crear_ingreso(payload):
    data = request.get_json()
    # Validar que todos los campos requeridos estén presentes
    if not data or not all(k in data for k in ('monto', 'descripcion', 'fecha', 'usuario_id', 'categoria_id')):
        return jsonify({'msg': 'Datos incompletos'}), 400

    try:
        # Convertir fecha desde el formato ISO 8601
        fecha = date.fromisoformat(data['fecha'])
    except ValueError:
        return jsonify({'msg': 'Formato de fecha inválido. Debe ser YYYY-MM-DD.'}), 400

    nuevo_ingreso = Ingreso(
        monto=data['monto'],
        descripcion=data['descripcion'],
        fecha=fecha,
        usuario_id=data['usuario_id'],
        categoria_id=data['categoria_id']
    )
    db.session.add(nuevo_ingreso)

    # Obtener el usuario para actualizar su capital_actual
    usuario = Usuario.query.get(data['usuario_id'])
    if not usuario:
        return jsonify({"error": "Usuario no encontrado"}), 404
    
    # Actualizar el capital_actual sumando el monto del depósito
    usuario.capital_actual += float(data['monto'])


    db.session.commit()
    return jsonify({'msg': 'Ingreso creado exitosamente'}), 201


