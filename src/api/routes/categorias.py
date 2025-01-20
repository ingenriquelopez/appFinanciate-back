# api/routes/categorias.py
from flask import Blueprint, request, jsonify
from api.models import db, Categoria, Ingreso, Egreso
from api.token_required import token_required
from .default_categories import default_categories
from sqlalchemy import exists

#------------------------------------------------
categorias_bp = Blueprint('categorias', __name__)
#------------------------------------------------


@categorias_bp.route('/traertodas', methods=['GET'])
@token_required
def listar_categorias(payload):
    current_user_id = payload.get('id')  # Acceder al 'id' del usuario
    # Ordeno categorías por 'nombre' de forma ascendente
    default_categories = Categoria.query.filter_by(is_default=True).all()
    user_categories = Categoria.query.filter_by(user_id=current_user_id).all()
    all_categories = default_categories + user_categories
     # Ordenar por el atributo 'nombre' (de forma ascendente)
    sorted_categories = sorted(all_categories, key=lambda c: c.nombre)

    return jsonify([{
        'id': e.id,
        'nombre': e.nombre,
        'icono':e.icono,
        'is_default': e.is_default,
    } for e in sorted_categories]), 200



#----------------------------------------------------
# Ruta para crear una nueva categoría
@categorias_bp.route('/categoria', methods=['POST'])
@token_required
def crear_categoria(payload):
     # El 'id' del usuario ya está disponible a través de 'payload'
    usuario_id = payload.get('id')  # Acceder al 'id' del usuario

    # Verificar que el usuario_id esté presente en el payload
    if not usuario_id:
        return jsonify({"error": "Usuario no autenticado"}), 401
    
    data = request.get_json()  # Obtener los datos enviados en el cuerpo de la solicitud
    # Validar que los datos necesarios estén presentes
    if not data or 'nombre' not in data:
        return jsonify({'msg': 'El nombre de la categoría es obligatorio'}), 400

    # Verificar si ya existe una categoría con el mismo nombre
    
    #if Categoria.query.filter_by(nombre=data['nombre']).first():
    if db.session.query(exists().where(Categoria.nombre == data['nombre'] )).scalar():
        return jsonify({'msg': 'La categoría ya existe'}), 400

    # Crear la nueva categoría
    nueva_categoria = Categoria(
        nombre=data['nombre'],
        icono = data['icono'],
        user_id= usuario_id,
        is_default= False,
    )
    
    # Agregarla a la base de datos
    db.session.add(nueva_categoria)
    db.session.commit()

    # Retornar el ID de la nueva categoría
    return jsonify({'msg': 'Categoría creada exitosamente', 'id': nueva_categoria.id,"nombre":nueva_categoria.nombre,"icono":nueva_categoria.icono}), 201


#---------------------------------------------------
@categorias_bp.route('/categoria', methods=['DELETE'])
@token_required
def eliminar_categoria(payload):
    # Verificar si la categoría existe
    data = request.get_json()
    id= data['id'] 
    categoria = Categoria.query.get(id)
    
    if not categoria:
        return jsonify({"error": "Categoría no encontrada"}), 404

    # Verificar si la categoría está relacionada con algún ingreso o egreso
    ingresos_relacionados = Ingreso.query.filter_by(categoria_id=id).count()
    egresos_relacionados = Egreso.query.filter_by(categoria_id=id).count()

    if ingresos_relacionados > 0 or egresos_relacionados > 0:
            return jsonify({
                "error": "La categoría está relacionada con ingresos o egresos.",
                "details": {
                    "ingresos_relacionados": ingresos_relacionados,
                    "egresos_relacionados": egresos_relacionados
                }
            }), 400

    # Eliminar la categoría si no está relacionada
    db.session.delete(categoria)
    db.session.commit()

    return jsonify({"message": "Categoría eliminada correctamente"}), 200

#----------------------------------------------------
@categorias_bp.route('/eliminartodas', methods=['DELETE'])
@token_required
def eliminar_todas_las_categorias(payload):
    try:
        # Obtener todas las categorías no predeterminadas (is_default=False)
        categorias = Categoria.query.filter_by(is_default=False).all()

        if not categorias:
            return jsonify({"message": "No hay categorías para eliminar."}), 200

        print("aqaui")
        # Filtrar las categorías no comprometidas
        categorias_no_comprometidas = []
        categorias_comprometidas = []

        for categoria in categorias:
            # Verificar si la categoría tiene ingresos o egresos relacionados
            ingresos_relacionados = Ingreso.query.filter_by(categoria_id=categoria.id).count()
            egresos_relacionados = Egreso.query.filter_by(categoria_id=categoria.id).count()

            # Si no tiene ingresos ni egresos, se agrega a las categorías no comprometidas
            if ingresos_relacionados == 0 and egresos_relacionados == 0:
                categorias_no_comprometidas.append(categoria)
            else:
                categorias_comprometidas.append({
                    "id": categoria.id,
                    "nombre": categoria.nombre,
                    "ingresos_relacionados": ingresos_relacionados,
                    "egresos_relacionados": egresos_relacionados
                })

        # Solo eliminar las categorías que no son predeterminadas y que no tienen ingresos ni egresos relacionados
        if categorias_no_comprometidas:
            for categoria in categorias_no_comprometidas:
                db.session.delete(categoria)

            db.session.commit()

            # Verificar si la tabla está vacía
            categorias_count = db.session.execute('SELECT COUNT(*) FROM categorias').scalar()
            if categorias_count == 0:
                db.session.execute('ALTER SEQUENCE categorias_id_seq RESTART WITH 1;')
                db.session.commit()

            print("llegue aqui")
            return jsonify({
                "message": f"{len(categorias_no_comprometidas)} categorías eliminadas correctamente.",
                "comprometidas": categorias_comprometidas
            }), 200
        else:
            return jsonify({"message": "No hay categorías no comprometidas para eliminar."}), 200

    except Exception as e:
        return jsonify({"error": "Error interno del servidor", "details": str(e)}), 500

#---------------------------------------------------
@categorias_bp.route('/default', methods=['POST'])
def insertar_categorias_por_defecto():
    # Verificar si la tabla 'Categoria' está vacía
    if db.session.query(Categoria).count() == 0:
        # Insertar las categorías en la base de datos
        try:
            for categoria in default_categories:
                default_categoria = Categoria(
                    nombre=categoria['nombre'],
                    icono=categoria['icono'],
                    is_default=True,
                    user_id=None
                )
                
                if not db.session.query(exists().where(Categoria.nombre == categoria['nombre'], Categoria.is_default == True)).scalar():
                    db.session.add(default_categoria)
            
            db.session.commit()

            return jsonify({"msg": "Categorías insertadas exitosamente"}), 201

        except Exception as e:
            db.session.rollback()
            # Retornar un mensaje de error si ocurre una excepción
            return jsonify({"error": "Hubo un error al insertar las categorías", "details": str(e)}), 500

    # Si la tabla no está vacía, podrías retornar otro mensaje si es necesario
    return jsonify({"msg": "Las categorías ya están presentes"}), 200
