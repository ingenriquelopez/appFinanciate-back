from flask import Blueprint, request, jsonify
from api.models import db, PlanAhorro, Categoria,Egreso,Ingreso,Usuario
from api.token_required import token_required
from datetime import date
from sqlalchemy.exc import SQLAlchemyError

#-----------------------------------------------------
plandeahorro_bp = Blueprint('plandeahorro', __name__)
#-----------------------------------------------------


#---------------------------------------------------------
@plandeahorro_bp.route('/agregarplan', methods=['POST'])
@token_required
def agregar_plan_ahorro(payload):
    # El 'id' del usuario ya está disponible a través de 'payload'
    usuario_id = payload.get('id')  # Acceder al 'id' del usuario
    
    if not usuario_id:
        return jsonify({"error": "Usuario no autenticado"}), 401

    # Obtener los datos del nuevo plan desde el body de la solicitud
    data = request.get_json()

    # Verificar que los campos requeridos estén presentes (campos que yo decido son indispensables)
    required_fields = ['nombre_plan', 'monto_objetivo', 'fecha_inicio', 'monto_inicial', 'fecha_objetivo']
    missing_fields = [field for field in required_fields if field not in data]
    
    if missing_fields:
        return jsonify({"error": f"Faltan los siguientes campos: {', '.join(missing_fields)}"}), 400

    # Validar formato de datos
    try:
        fecha_inicio = date.fromisoformat(data['fecha_inicio'])
        fecha_objetivo = date.fromisoformat(data['fecha_objetivo'])
    except ValueError:
        return jsonify({"error": "Las fechas deben estar en formato AAAA-MM-DD"}), 400

    if fecha_inicio > fecha_objetivo:
        return jsonify({"error": "La fecha de inicio no puede ser mayor que la fecha objetivo"}), 400

    try:
        monto_inicial = float(data['monto_inicial'])
        monto_objetivo = float(data['monto_objetivo'])
    except ValueError:
        return jsonify({"error": "El monto inicial y el monto objetivo deben ser números válidos"}), 400

    if monto_inicial < 0 or monto_objetivo <= 0:
        return jsonify({"error": "El monto inicial no puede ser negativo y el monto objetivo debe ser mayor que cero"}), 400

    # Buscar la categoría "Plan de Ahorro"  
    categoria_plan_ahorro = Categoria.query.filter_by(nombre="Plan de ahorro").first()
    # Crear el nuevo plan de ahorroñl
    nuevo_plan = PlanAhorro(
        nombre_plan=data['nombre_plan'],
        fecha_inicio=fecha_inicio,
        monto_inicial=monto_inicial,
        monto_objetivo=monto_objetivo,
        fecha_objetivo=fecha_objetivo,
        usuario_id=usuario_id
    )

    # Guardar en la base de datos
    db.session.add(nuevo_plan)
    db.session.commit()

    # Ahora creamos el nuevo Egreso (registro de la primera transacción de ahorro)

    
    nuevo_egreso = Egreso(
        usuario_id=usuario_id,
        monto=monto_inicial,  # El monto inicial es el primer egreso
        descripcion="Depósito inicial al plan de ahorro",
        fecha=fecha_inicio,  # Usamos la fecha de inicio del plan
        categoria_id=categoria_plan_ahorro.id,  
        plan_ahorro_id=nuevo_plan.id  # Asociamos el egreso con el plan de ahorro recién creado
    )
    # Guardamos el egreso
    db.session.add(nuevo_egreso)
    # Actualizamos el monto acumulado en el plan de ahorro
    nuevo_plan.monto_acumulado += monto_inicial

    db.session.commit()


    # Obtener el usuario para actualizar su capital_actual
    usuario = Usuario.query.get(usuario_id)
    if not usuario:
        return jsonify({"error": "Usuario no encontrado"}), 404
    
    # Actualizar el capital_actual restando el monto del depósito
    usuario.capital_actual -= monto_inicial
    db.session.commit()
    
      # Devolver toda la información del nuevo plan para actualizar la UI
    return jsonify({
        "msg": "Plan de ahorro agregado exitosamente",
        "nuevo_plan": {
            "id": nuevo_plan.id,
            "nombre_plan": nuevo_plan.nombre_plan,
            "fecha_inicio": nuevo_plan.fecha_inicio.isoformat(),
            "monto_inicial": nuevo_plan.monto_inicial,
            "monto_objetivo": nuevo_plan.monto_objetivo,
            "fecha_objetivo": nuevo_plan.fecha_objetivo.isoformat(),
            "usuario_id": nuevo_plan.usuario_id
        }
    }), 201

#------------------------------------------------------
@plandeahorro_bp.route('/editarplan', methods=['PUT'])
@token_required
def editar_plan_ahorro(payload):
   # El 'id' del usuario ya está disponible a través de 'payload'
    usuario_id = payload.get('id')

    if not usuario_id:
        return jsonify({"error": "Usuario no autenticado"}), 401

    # Obtener el id del plan desde el cuerpo de la solicitud
    data = request.get_json()
    plan_id = data.get('id')  # Aquí es donde obtienes el id del plan

    if not plan_id:
        return jsonify({"error": "ID del plan es necesario"}), 400

    # Buscar el plan de ahorro por ID
    plan = PlanAhorro.query.get_or_404(plan_id)

    # Verificar que el plan pertenece al usuario autenticado
    if plan.usuario_id != usuario_id:
        return jsonify({"error": "No tienes permiso para modificar este plan"}), 403

    # Obtener los datos para actualizar
    data = request.get_json()

    if 'nombre_plan' in data:
        plan.nombre_plan = data['nombre_plan']
    if 'fecha_inicio' in data:
        plan.fecha_inicio = data['fecha_inicio']
    if 'monto_objetivo' in data:
        plan.monto_objetivo = data['monto_objetivo']
    if 'fecha_objetivo' in data:
        plan.fecha_objetivo = data['fecha_objetivo']

    # Guardar los cambios en la base de datos
    db.session.commit()

    return jsonify({"msg": "Plan de ahorro actualizado exitosamente"}), 200
#---------------------------------------------------------

@plandeahorro_bp.route('/eliminar_plan_ahorro', methods=['DELETE'])
@token_required
def eliminar_plan_ahorro(payload):
    data = request.get_json()
    usuario_id = payload.get('id')

    # Validar que se reciba el ID del plan de ahorro
    if 'plan_ahorro_id' not in data:
        return jsonify({'error': 'Falta el campo "plan_ahorro_id".'}), 400

    plan_ahorro_id = data['plan_ahorro_id']

    try:
        # Buscar el plan de ahorro por ID
        plan_ahorro = PlanAhorro.query.get(plan_ahorro_id)
        
        if not plan_ahorro:
            return jsonify({'error': 'Plan de ahorro no encontrado.'}), 404

        # Si el plan de ahorro tiene egresos asociados, procesamos la reversión
        egresos = plan_ahorro.egresos  # Asegúrate de usar el nombre correcto del backref
        # Tomar la categoría del primer egreso (todas las categorías son las mismas)
        #categoria_id = egresos[0].categoria_id

        # Generar un ingreso por la cancelación del plan de ahorro
        ingresos_por_cancelacion = 0
        for egreso in egresos:
            ingresos_por_cancelacion += egreso.monto  # Acumulamos el monto de los egresos

            # Crear el ingreso que "restituye" el monto del egreso
            # ingreso_cancelacion = Ingreso(
            #     monto=egreso.monto,
            #     descripcion=f'Reversión por cancelación de plan de ahorro: {plan_ahorro.nombre_plan}',
            #     usuario_id=plan_ahorro.usuario_id,  # Asociamos al mismo usuario
            #     fecha = date.today(),
            #     categoria_id= egreso.categoria_id
            # )

            # db.session.add(ingreso_cancelacion)

            # Eliminar el egreso asociado
            db.session.delete(egreso)
        
         # Obtener el usuario para actualizar su capital_actual
        usuario = Usuario.query.get(usuario_id)
        if not usuario:
            return jsonify({"error": "Usuario no encontrado"}), 404

        # Actualizar el capital_actual restando el monto del depósito
        usuario.capital_actual += plan_ahorro.monto_acumulado

        # Actualizar el capital acumulado del plan de ahorro a cero
        plan_ahorro.monto_acumulado = 0.0

        # Eliminar el plan de ahorro
        db.session.delete(plan_ahorro)
    
        # Hacer commit de todas las operaciones en la base de datos
        db.session.commit()
        print("170")
        return jsonify({
            'message': 'Plan de ahorro eliminado correctamente y egresos revertidos.',
            'ingreso_generado': ingresos_por_cancelacion
        }), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': 'Error al eliminar el plan de ahorro.', 'details': str(e)}), 500
#---------------------------------------------------------

@plandeahorro_bp.route('/traerplan', methods=['GET'])
@token_required
def obtener_planes_ahorro(payload):
    # El 'id' del usuario ya está disponible a través de 'payload'
    usuario_id = payload.get('id')  # Acceder al 'id' del usuario

    # Verificar que el usuario_id esté presente en el payload
    if not usuario_id:
        return jsonify({"error": "Usuario no autenticado"}), 401
    
    planes = PlanAhorro.query.filter_by(usuario_id=usuario_id).all()
    # Serializar los planes de ahorro filtrados por usuario según token
    planes_serializados = [p.to_dict() for p in planes]

    usuario = Usuario.query.get(usuario_id)
    if not usuario:
        return jsonify({"error": "Usuario no encontrado"}), 404

    # Añadir el capital actual del usuario a la respuesta
    return jsonify({
        "capital_actual": usuario.capital_actual,
        "planes": planes_serializados
    }), 200

#---------------------------------------------------------
@plandeahorro_bp.route('/depositar', methods=['POST'])
@token_required
def registrar_deposito_plan(payload):
    #Registra un monto hacia un plan de ahorro y crea un egreso asociado.
    data = request.json  # Datos enviados en el cuerpo de la solicitud aqui los recibo

     # El 'id' del usuario ya está disponible a través de 'payload'
    usuario_id = payload.get('id')  # Acceder al 'id' del usuario

    # Obtener los datos del cuerpo de la solicitud
    plan_id = data.get('plan_id')  # ID del plan de ahorro al que se deposita
    nombre_plan = data.get('nombre_plan')  # ID del plan de ahorro al que se deposita
    monto_ahorro = float(data.get('monto_ahorro'))  # Monto a depositar
    descripcion_deposito = data.get('descripcion', "Deposito al plan de ahorro")  # Descripción opcional
    fecha = data.get('fecha')

    # Validar datos requeridos
    if not usuario_id or not plan_id or not monto_ahorro or not fecha:
        return jsonify({"error": "Faltan datos requeridos (usuario_id, plan_id, nombre_plan,monto_monto_ahorro,fecha)"}), 400

    # Buscar la categoría "Plan de Ahorro"  
    categoria_plan_ahorro = Categoria.query.filter_by(nombre="Plan de ahorro").first()
     
    try:

        # Buscar el plan de ahorro
        plan = PlanAhorro.query.get(plan_id)
        
        if not plan:
            return jsonify({"error": "Plan de ahorro no encontrado"}), 404
        
        if plan.usuario_id != usuario_id:
            return jsonify({"error": "El plan de ahorro no pertenece al usuario"}), 403

        # Verificar que el monto sea válido
        if monto_ahorro <= 0:
            return jsonify({"error": "El monto debe ser mayor a cero"}), 400

        if not categoria_plan_ahorro:
            return jsonify({"error": "La categoría 'Plan de Ahorro' no está definida"}), 500

        try:
            # Convertir fecha desde el formato ISO 8601
            fecha = date.fromisoformat(data['fecha'])
        except ValueError:
            return jsonify({'msg': 'Formato de fecha inválido. Debe ser YYYY-MM-DD.'}), 400

        # Registrar el egreso
        nuevo_egreso = Egreso(
            usuario_id=usuario_id,
            monto=monto_ahorro,
            descripcion=descripcion_deposito,
            fecha=fecha,
            categoria_id=categoria_plan_ahorro.id,
            plan_ahorro_id = plan.id,
        )

        db.session.add(nuevo_egreso)

        # Actualizar el monto acumulado en el plan de ahorro
        plan.monto_acumulado += monto_ahorro

        # Obtener el usuario para actualizar su capital_actual
        usuario = Usuario.query.get(usuario_id)
        if not usuario:
            return jsonify({"error": "Usuario no encontrado"}), 404

        # Actualizar el capital_actual restando el monto del depósito
        usuario.capital_actual -= monto_ahorro

        # Guardar cambios
        db.session.commit()

        return jsonify({
            "message": "Depósito registrado exitosamente",
            "plan": plan.to_dict(),
            "egreso": {
                "id": nuevo_egreso.id,
                "monto": nuevo_egreso.monto,
                "descripcion": nuevo_egreso.descripcion,
                "fecha": nuevo_egreso.fecha.isoformat(),
                "categoria_id": nuevo_egreso.categoria_id
            }
        }), 201

    except Exception as e:
        db.session.rollback()  # Revertir cambios en caso de error
        return jsonify({"error": f"Ocurrió un error al registrar el depósito: {str(e)}"}), 500

