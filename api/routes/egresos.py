from flask import Blueprint, request, jsonify
from api.models import db, Egreso,Usuario
from api.token_required import token_required
from datetime import date
#------------------------------------------
egresos_bp = Blueprint('egresos', __name__)
#-----------------------------------------


# CRUD para Egreso
@egresos_bp.route('/egresos', methods=['GET'])
@token_required
def obtener_egresos(payload):
    try:
        # Obtener el id del usuario desde el token
        usuario_id = payload['id']
        
        # Filtrar los egresos por el id del usuario autenticado
        egresos = Egreso.query.filter_by(usuario_id=usuario_id).all()
        
        # Formatear los egresos como una lista de diccionarios
        egresos_serializados = [
            {
                "id": egreso.id,
                "monto": egreso.monto,
                "descripcion": egreso.descripcion,
                "fecha": egreso.fecha.isoformat(),
                "categoria_id": egreso.categoria_id,
                "usuario_id": egreso.usuario_id
            }
            for egreso in egresos
        ]

        return jsonify(egresos_serializados), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500




#----------------------------------------------------------------------------------------
# Ruta para crear un EGRESO
@egresos_bp.route('/agrega_egreso', methods=['POST'])
@token_required
def crear_egreso(payload):
    data = request.get_json()
    # Validar que todos los campos requeridos estén presentes
    if not data or not all(k in data for k in ('monto', 'descripcion', 'fecha', 'usuario_id', 'categoria_id')):
        return jsonify({'msg': 'Datos incompletos'}), 400

    try:
        # Convertir fecha desde el formato ISO 8601
        fecha = date.fromisoformat(data['fecha'])
    except ValueError:
        return jsonify({'msg': 'Formato de fecha inválido. Debe ser YYYY-MM-DD.'}), 400

    nuevo_egreso = Egreso(
        monto=data['monto'],
        descripcion=data['descripcion'],
        fecha=fecha,
        usuario_id=data['usuario_id'],
        categoria_id=data['categoria_id']
    )
    db.session.add(nuevo_egreso)

    # Obtener el usuario para actualizar su capital_actual
    usuario = Usuario.query.get(data['usuario_id'])
    if not usuario:
        return jsonify({"error": "Usuario no encontrado"}), 404

    # Actualizar el capital_actual RESTANDO el monto del depósito
    usuario.capital_actual -=  float(data['monto'])

    db.session.commit()
    return jsonify({'msg': 'Egreso creado exitosamente'}), 201
