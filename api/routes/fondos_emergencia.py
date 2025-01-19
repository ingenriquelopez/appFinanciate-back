#PARA RADO
from flask import Blueprint, request, jsonify
from api.models import db, FondoEmergencia
from api.token_required import token_required

#--------------------------------------------------------------
fondos_emergencia_bp = Blueprint('fondos_emergencia', __name__)
#--------------------------------------------------------------

# CRUD para FondoEmergencia
@fondos_emergencia_bp.route('/fondos_emergencia/activo', methods=['GET'])
@token_required
def obtener_fondo_emergencia_activo(payload):
    usuario_id = payload.get('id')

    fondo = FondoEmergencia.query.filter_by(usuario_id=usuario_id).first()

    if not fondo:
        return jsonify({'msg': 'No se encontró un fondo de emergencia para este usuario.'}), 200

    return jsonify({
        'id': fondo.id,
        'monto': fondo.monto,
        'monto_actual': fondo.monto_actual,
        'razon': fondo.razon,
        'usuario_id': fondo.usuario_id
    }), 200


@fondos_emergencia_bp.route('/fondos_emergencia', methods=['POST'])
@token_required
def crear_fondo_emergencia(payload):
    datos = request.get_json()
    monto = datos.get('monto')
    razon = datos.get('razon')

    if not monto or not razon:
        return jsonify({'msg': 'Faltan datos requeridos (monto, razon).'}), 400

    usuario_id = payload.get('id')

    nuevo_fondo = FondoEmergencia(
        monto=monto,
        monto_actual=0.0,
        razon=razon,
        usuario_id=usuario_id
    )
    db.session.add(nuevo_fondo)
    db.session.commit()
    emergency = FondoEmergencia.query.filter_by(usuario_id=usuario_id).first()

    return jsonify({'msg': 'Fondo de emergencia creado exitosamente.', 'id':emergency.id}), 201

@fondos_emergencia_bp.route('/fondos_emergencia', methods=['DELETE'])
@token_required
def eliminar_fondo_emergencia(payload):
    usuario_id = payload.get('id')
    datos = request.get_json()
    id_emergencia = datos["id"]
    fondo = FondoEmergencia.query.filter_by(id=id_emergencia, usuario_id=usuario_id).first()
    if not fondo:
        return jsonify({'msg': 'No se encontró un fondo de emergencia para este usuario.'}), 404

    db.session.delete(fondo)
    db.session.commit()

    return jsonify({'msg': 'Fondo de emergencia eliminado exitosamente.'}), 200




