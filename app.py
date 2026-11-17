import os
from flask import Flask, request,jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity,
    get_jwt
)

from database import conectar_bd
from functools import wraps 
load_dotenv()

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
if not app.config["JWT_SECRET_KEY"]:
    raise RuntimeError("NO SE ENCONTRO LA LLAVE JWT")
jwt = JWTManager(app)
CORS(app)

def rol_requerido(rol):
    def decorador(funcion):
        @wraps(funcion)
        @jwt_required()
        def wrapper(*args,**kwargs):
            claims = get_jwt()

            if claims.get("rol") != rol:
                return jsonify({"mensaje": "No tiene permiso para acceder"}), 403
            return funcion(*args,**kwargs)
        return wrapper
    return decorador



@app.route("/probar")
def probar_data():
    conec = conectar_bd()

    if conec.is_connected():
        conec.close()

    return {
        "mensaje": "Conexion ok"
    }

@app.route("/api/registro-usuario", methods=["POST"])
def registro_usuario():

    datos = request.get_json()

    # Verificar campos vacíos
    if not datos or not datos.get("nombre") or not datos.get("correo") or not datos.get("password"):
        return {
            "mensaje": "Todos los campos son obligatorios"
        }, 400

    nombre = datos["nombre"].strip()
    correo = datos["correo"].strip().lower()
    password = datos["password"]
    rol = datos.get("rol", "aprendiz")

    # Verificar campos vacíos
    if not nombre or not correo or not password.strip():
        return {
            "mensaje": "No se permiten campos vacíos"
        }, 400

    # Validar longitud de contraseña
    if len(password) < 8 or len(password) > 15:
        return {
            "mensaje": "La contraseña debe tener entre 8 y 15 caracteres"
        }, 400

    # Validar rol
    if rol not in ["aprendiz", "reclutador"]:
        return {
            "mensaje": "El rol no es válido"
        }, 400

    conec = conectar_bd()
    cursor = conec.cursor()

    # Verificar si el correo ya existe
    cursor.execute(
        "SELECT id FROM usuarios WHERE correo = %s",
        (correo,)
    )

    existe = cursor.fetchone()

    if existe:
        cursor.close()
        conec.close()

        return {
            "mensaje": "El correo ya está registrado"
        }, 400

    # Encriptar contraseña
    password_encriptada = generate_password_hash(password)

    # Registrar usuario
    sql = """
        INSERT INTO usuarios (nombre, correo, password, rol)
        VALUES (%s, %s, %s, %s)
    """

    cursor.execute(sql, (
        nombre,
        correo,
        password_encriptada,
        rol
    ))

    conec.commit()

    id_usuario = cursor.lastrowid

    cursor.close()
    conec.close()

    return {
        "mensaje": "Usuario registrado correctamente",
        "id": id_usuario
    }, 201

    pass
#contraseña entre 8 y 15 carac sin campos vacios y correo electronico no puede estar 
#registrado y si no se cumple que no dejen registrar y contraseña debe estar encriptadas 


@app.route("/api/login", methods=["POST"])
def login():
    datos = request.get_json()

    if not datos:
        return jsonify({"mensaje": "Datos incompletos"}), 400

    correo = datos.get("correo", "").strip().lower()
    password = datos.get("password", "")

    if not correo or not password:
        return jsonify({"mensaje": "Ingrese correo y contraseña"}), 400

    conexion = conectar_bd()
    cursor = conexion.cursor(dictionary=True)

    try:
        # Buscar usuario por correo
        sql = """
            SELECT id, nombre, correo, password, rol, estado
            FROM usuarios
            WHERE correo = %s
        """

        cursor.execute(sql, (correo,))
        usuario = cursor.fetchone()

        # Verificar si existe
        if not usuario:
            return jsonify({"mensaje": "Correo o contraseña incorrectos"}), 401

        # Verificar estado de la cuenta
        if not usuario["estado"]:
            return jsonify({"mensaje": "La cuenta está desactivada"}), 403

        # Verificar contraseña cifrada
        if not check_password_hash(usuario["password"], password):
            return jsonify({"mensaje": "Correo o contraseña incorrectos"}), 401

        # Generar el token
        token = create_access_token(
            identity=str(usuario["id"]),
            additional_claims={"rol": usuario["rol"]}
        )
        #respuesta
        return jsonify({"mensaje": "inicio de sesion correcto",
                        "token":token,
                        "usuario":{"id":usuario["id"],
                        "nombre":usuario["nombre"],
                        "correo":usuario["correo"],
                        "rol":usuario["rol"]} }),200

        

    finally:
        cursor.close()
        conexion.close()


#Actualizar hoja de vida por medio del id
@app.route("/api/actualizarhv/<int:id>", methods=["PUT"])
@jwt_required()
def actualizarhv(id):

    # Recibir los datos enviados
    datos = request.json
    conec = conectar_bd()
    cursor = conec.cursor(buffered=True)

    # Verificar que la HV existe
    buscar = """SELECT id FROM hojas_vida WHERE id=%s"""
    cursor.execute(buscar, (id,))
    result = cursor.fetchone()

    if result is None:
        cursor.close()
        conec.close()
        return {
            "Mensaje": "No se encontro la hoja de vida"
        }, 404

    # Verificar que el correo no esté registrado en otra HV
    sqlcorreo = """
        SELECT id
        FROM hojas_vida
        WHERE correo = %s
        AND id != %s
    """

    cursor.execute(sqlcorreo, (datos["correo"], id))
    result = cursor.fetchone()

    if result is not None:
        cursor.close()
        conec.close()
        return {
            "Mensaje": "El correo ya esta registrado con otra hoja de vida"
        }, 400

    # Actualizar
    sqlactualizar = """
        UPDATE hojas_vida
        SET nombre=%s, edad=%s, ciudad=%s, correo=%s,
            fotografia=%s, programa=%s, ficha=%s, jornada=%s
        WHERE id=%s
    """

    valor = (
        datos["nombre"],
        datos["edad"],
        datos["ciudad"],
        datos["correo"],
        datos.get("fotografia"),
        datos["programa"],
        datos["ficha"],
        datos["jornada"],
        id
    )

    cursor.execute(sqlactualizar, valor)
    conec.commit()

    cursor.close()
    conec.close()

    return {
        "Mensaje": "Hoja de vida actualizada",
        "id": id
    }, 200







# Eliminar hoja de vida por id
@app.route("/api/eliminarhv/<int:id>", methods=["DELETE"])
@jwt_required()
def eliminar_hv(id):
    conec = conectar_bd()
    cursor = conec.cursor()

    cursor.execute("SELECT id FROM hojas_vida WHERE id=%s", (id,))
    existe = cursor.fetchone()

    if existe is None:
        cursor.close()
        conec.close()
        return {"mensaje": "No se encontró la hoja de vida"}, 404

    cursor.execute("DELETE FROM hojas_vida WHERE id=%s", (id,))
    conec.commit()

    cursor.close()
    conec.close()

    return {"mensaje": "Hoja de vida eliminada"}, 200

    



#Consultar hoja de vida por id
@app.route("/api/consultahv/<int:id>", methods=["GET"])
@jwt_required()
def obtener_hvida(id):
    conec = conectar_bd()
    cursor = conec.cursor(dictionary=True)

    sql = "SELECT * FROM hojas_vida WHERE id = %s"
    cursor.execute(sql, (id,))

    datos = cursor.fetchone()

    cursor.close()
    conec.close()

    if datos is None:
        return {"mensaje": "No se encontró la hoja de vida"}, 404

    return datos, 200






@app.route("/api/registrohv", methods=["POST"])
@jwt_required()
def registrar_hojavida():
    

    conec = conectar_bd()
    cursor = conec.cursor()
    datos = request.get_json()

    # Consultar si el correo ya existe en la base de datos
    cursor.execute(
        "SELECT * FROM hojas_vida WHERE correo = %s",
        (datos['correo'],)
    )

    resultado = cursor.fetchone()

    if resultado:
        cursor.close()
        conec.close()

        return {
            "mensaje": "El correo ya está registrado"
        }, 400

    sql = """
        INSERT INTO hojas_vida
        (nombre, edad, ciudad, correo, fotografia, programa, ficha, jornada)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """

    cursor.execute(sql, (
        datos['nombre'],
        datos['edad'],
        datos['ciudad'],
        datos['correo'],
        datos['fotografia'],
        datos['programa'],
        datos['ficha'],
        datos['jornada']
    ))

    conec.commit()

    # Obtener el ID generado automáticamente
    id_regenerado = cursor.lastrowid

    cursor.close()
    conec.close()

    return {
        "mensaje": "Registro de hoja de vida",
        "id": id_regenerado
    }, 201



# CONSULTAR MI HOJA DE VIDA CON EL TOKEN JWT
@app.route("/api/mi-hoja-vida", methods=["GET"]) 
@jwt_required()
def mi_hoja_vida():
    # Obtener el id del usuario desde el token
    usuario_id = int(get_jwt_identity())
    rol = get_jwt().get("rol")

    if rol != "aprendiz":
        return jsonify({"mensaje": "Consulta exclusiva para aprendices"}), 403

    conec = conectar_bd()
    cursor = conec.cursor(dictionary=True)

    try:
        # 1. Obtener datos personales
        cursor.execute("SELECT * FROM hojas_vida WHERE usuario_id = %s", (usuario_id,))
        hv = cursor.fetchone()

        if not hv:
            return jsonify({"mensaje": "No tienes una hoja de vida registrada"}), 404

        hoja_vida_id = hv["id"]

        # 2. Obtener estudios
        cursor.execute("SELECT * FROM estudios WHERE hoja_vida_id = %s", (hoja_vida_id,))
        estudios = cursor.fetchall()

        # 3. Obtener cursos
        cursor.execute("SELECT * FROM cursos WHERE hoja_vida_id = %s", (hoja_vida_id,))
        cursos = cursor.fetchall()

        # 4. Obtener experiencias
        cursor.execute("SELECT * FROM experiencias WHERE hoja_vida_id = %s", (hoja_vida_id,))
        experiencias = cursor.fetchall()

        # 5. Obtener habilidades vinculadas a las experiencias de esta HV
        cursor.execute("""
            SELECT h.id, h.nombre, h.experiencia_id
            FROM habilidades h
            INNER JOIN experiencias e ON h.experiencia_id = e.id
            WHERE e.hoja_vida_id = %s
        """, (hoja_vida_id,))
        habilidades = cursor.fetchall()

        # Asociar habilidades con cada experiencia
        for experiencia in experiencias:
            experiencia["habilidades"] = [
                h for h in habilidades if h["experiencia_id"] == experiencia["id"]
            ]

        return jsonify({
            "datos_personales": hv,
            "estudios": estudios,
            "cursos": cursos,
            "experiencias": experiencias
        }), 200
    finally:
        cursor.close()
        conec.close()










@app.route("/")
def inicio():
    return "Api hoja de vida funcionando"


# BUSCAR UNA HOJA DE VIDA POR ID
@app.route("/api/hojas-vida/<int:id>") 
def obtener_hojasvidaid(id):

    conec = conectar_bd()
    cursor = conec.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM hojas_vida WHERE id = %s",
        (id,)
    )

    hoja_vida = cursor.fetchone()

    cursor.close()
    conec.close()

    if hoja_vida:
        return hoja_vida

    return {
        "mensaje": "Hoja de vida no encontrada"
    }, 404


# LISTAR TODAS LAS HOJAS DE VIDA
@app.route("/api/hojas-vida")    #reclutador
@rol_requerido("reclutador")
def obtener_hojasvida():

    conec = conectar_bd()
    cursor = conec.cursor(dictionary=True)

    # Consultar todos los registros de la base de datos
    cursor.execute("SELECT * FROM hojas_vida")

    # Obtener todos los registros
    hojas_vida = cursor.fetchall()

    cursor.close()
    conec.close()

    return hojas_vida




#ESTUDIOS HOJA DE VIDA

#Consultar todos los estudios asociados a una hoja de vida.
@app.route("/api/hojasvida/<int:hoja_vida_id>/estudios", methods=["GET"])
def consultar_estudios(hoja_vida_id):

    conec = conectar_bd()
    cursor = conec.cursor(dictionary=True)

    sql = """
        SELECT id, hoja_vida_id, nivel, institucion, titulo, anio_graduacion
        FROM estudios
        WHERE hoja_vida_id = %s
    """

    cursor.execute(sql, (hoja_vida_id,))

    estudios = cursor.fetchall()

    cursor.close()
    conec.close()

    return estudios, 200


#Registrar un nuevo esstudio 
@app.route("/api/hojasvida/<int:hoja_vida_id>/estudios", methods=["POST"])
def registrar_estudio(hoja_vida_id):

    datos = request.get_json()

    conec = conectar_bd()
    cursor = conec.cursor()

    sql = """
        INSERT INTO estudios
        (hoja_vida_id, nivel, institucion, titulo, anio_graduacion)
        VALUES (%s, %s, %s, %s, %s)
    """

    valores = (
        hoja_vida_id,
        datos["nivel"],
        datos["institucion"],
        datos["titulo"],
        datos["anio_graduacion"]
    )

    cursor.execute(sql, valores)
    conec.commit()

    id_estudio = cursor.lastrowid

    cursor.close()
    conec.close()

    return {
        "mensaje": "Estudio registrado correctamente",
        "id": id_estudio,
        "hoja_vida_id": hoja_vida_id
    }, 201


#Consultar un estudio especifico 
@app.route("/api/estudios/<int:id>", methods=["GET"])
def consultar_estudio(id):

    conec = conectar_bd()
    cursor = conec.cursor(dictionary=True)

    sql = """
        SELECT id, hoja_vida_id, nivel, institucion, titulo, anio_graduacion
        FROM estudios
        WHERE id = %s
    """

    cursor.execute(sql, (id,))

    estudio = cursor.fetchone()

    cursor.close()
    conec.close()

    if estudio is None:
        return {
            "mensaje": "Estudio no encontrado"
        }, 404

    return estudio, 200


#Actualizar un estudio

@app.route("/api/actualizarestudios/<int:id>", methods=["PUT"])
def actualizar_estudio(id):

    datos = request.json
    conec = conectar_bd()
    cursor = conec.cursor(buffered=True)

    # Verificar si el estudio existe
    buscar = """SELECT id FROM estudios WHERE id=%s"""
    cursor.execute(buscar, (id,))
    result = cursor.fetchone()

    if result is None:
        cursor.close()
        conec.close()
        return {
            "Mensaje": "No se encontro el estudio"
        }, 404

    # Actualizar
    sqlactualizar = """
        UPDATE estudios
        SET nivel=%s,
            institucion=%s,
            titulo=%s,
            anio_graduacion=%s
        WHERE id=%s
    """

    valor = (
        datos["nivel"],
        datos["institucion"],
        datos["titulo"],
        datos["anio_graduacion"],
        id
    )

    cursor.execute(sqlactualizar, valor)
    conec.commit()

    cursor.close()
    conec.close()

    return {
        "Mensaje": "Estudio actualizado",
        "id": id
    }, 200
    
    
    # Eliminar estudio por id
@app.route("/api/eliminarestudio/<int:id>", methods=["DELETE"])
def eliminar_estudio(id):
    conec = conectar_bd()
    cursor = conec.cursor()

    cursor.execute("SELECT id FROM estudios WHERE id=%s", (id,))
    existe = cursor.fetchone()

    if existe is None:
        cursor.close()
        conec.close()
        return {"mensaje": "No se encontró el estudio"}, 404

    cursor.execute("DELETE FROM estudios WHERE id=%s", (id,))
    conec.commit()

    cursor.close()
    conec.close()

    return {"mensaje": "Estudio eliminado"}, 200


#Endpoints experiencia laboral

#Consultar todas las experiencias laborales asociadas a una hoja de vida.

@app.route("/api/hojasvida/<int:hoja_vida_id>/experiencias", methods=["GET"])
def consultar_experiencias(hoja_vida_id):

    conec = conectar_bd()
    cursor = conec.cursor(dictionary=True)

    sql = """
        SELECT id, hoja_vida_id, empresa, cargo, tiempo, funciones
        FROM experiencias
        WHERE hoja_vida_id = %s
    """

    cursor.execute(sql, (hoja_vida_id,))

    experiencias = cursor.fetchall()

    cursor.close()
    conec.close()

    return experiencias, 200



# Registrar una nueva experiencia laboral
@app.route("/api/hojasvida/<int:hoja_vida_id>/experiencias", methods=["POST"])
def registrar_experiencia(hoja_vida_id):

    datos = request.get_json()

    conec = conectar_bd()
    cursor = conec.cursor()

    sql = """
        INSERT INTO experiencias
        (hoja_vida_id, empresa, cargo, tiempo, funciones)
        VALUES (%s, %s, %s, %s, %s)
    """

    valores = (
        hoja_vida_id,
        datos["empresa"],
        datos["cargo"],
        datos["tiempo"],
        datos["funciones"]
    )

    cursor.execute(sql, valores)
    conec.commit()

    id_experiencia = cursor.lastrowid

    cursor.close()
    conec.close()

    return {
        "mensaje": "Experiencia registrada correctamente",
        "id": id_experiencia,
        "hoja_vida_id": hoja_vida_id
    }, 201
    
    
    
    
    # Actualizar una experiencia laboral
@app.route("/api/actualizarexperiencia/<int:id>", methods=["PUT"])
def actualizar_experiencia(id):

    datos = request.json
    conec = conectar_bd()
    cursor = conec.cursor(buffered=True)

    # Verificar si la experiencia existe
    buscar = """SELECT id FROM experiencias WHERE id=%s"""
    cursor.execute(buscar, (id,))
    result = cursor.fetchone()

    if result is None:
        cursor.close()
        conec.close()
        return {
            "Mensaje": "No se encontro la experiencia"
        }, 404

    # Actualizar
    sqlactualizar = """
        UPDATE experiencias
        SET empresa=%s,
            cargo=%s,
            tiempo=%s,
            funciones=%s
        WHERE id=%s
    """

    valor = (
        datos["empresa"],
        datos["cargo"],
        datos["tiempo"],
        datos["funciones"],
        id
    )

    cursor.execute(sqlactualizar, valor)
    conec.commit()

    cursor.close()
    conec.close()

    return {
        "Mensaje": "Experiencia actualizada",
        "id": id
    }, 200



# Eliminar experiencia por id
@app.route("/api/eliminarexperiencia/<int:id>", methods=["DELETE"])
def eliminar_experiencia(id):

    conec = conectar_bd()
    cursor = conec.cursor()

    cursor.execute(
        "SELECT id FROM experiencias WHERE id=%s",
        (id,)
    )

    existe = cursor.fetchone()

    if existe is None:
        cursor.close()
        conec.close()

        return {
            "mensaje": "No se encontró la experiencia"
        }, 404

    cursor.execute(
        "DELETE FROM experiencias WHERE id=%s",
        (id,)
    )

    conec.commit()

    cursor.close()
    conec.close()

    return {
        "mensaje": "Experiencia eliminada"
    }, 200
    
    
    
    
    #Endpoints habilidades
    

# Consultar todas las habilidades asociadas a una experiencia
@app.route("/api/experiencias/<int:experiencia_id>/habilidades", methods=["GET"])
def consultar_habilidades(experiencia_id):

    conec = conectar_bd()
    cursor = conec.cursor(dictionary=True)

    sql = """
        SELECT id, experiencia_id, nombre
        FROM habilidades
        WHERE experiencia_id = %s
    """

    cursor.execute(sql, (experiencia_id,))

    habilidades = cursor.fetchall()

    cursor.close()
    conec.close()

    return habilidades, 200



# Registrar una nueva habilidad

@app.route("/api/experiencias/<int:experiencia_id>/habilidades", methods=["POST"])
def registrar_habilidad(experiencia_id):

    datos = request.get_json()

    conec = conectar_bd()
    cursor = conec.cursor()

    sql = """
        INSERT INTO habilidades
        (experiencia_id, nombre)
        VALUES (%s, %s)
    """

    valores = (
        experiencia_id,
        datos["nombre"]
    )

    cursor.execute(sql, valores)
    conec.commit()

    id_habilidad = cursor.lastrowid

    cursor.close()
    conec.close()

    return {
        "mensaje": "Habilidad registrada correctamente",
        "id": id_habilidad,
        "experiencia_id": experiencia_id
    }, 201
    
    
    
    # Actualizar una habilidad
@app.route("/api/actualizarhabilidad/<int:id>", methods=["PUT"])
def actualizar_habilidad(id):

    datos = request.json
    conec = conectar_bd()
    cursor = conec.cursor(buffered=True)

    # Verificar si la habilidad existe
    buscar = """SELECT id FROM habilidades WHERE id=%s"""
    cursor.execute(buscar, (id,))
    result = cursor.fetchone()

    if result is None:
        cursor.close()
        conec.close()

        return {
            "Mensaje": "No se encontro la habilidad"
        }, 404

    # Actualizar
    sqlactualizar = """
        UPDATE habilidades
        SET nombre=%s
        WHERE id=%s
    """

    valor = (
        datos["nombre"],
        id
    )

    cursor.execute(sqlactualizar, valor)
    conec.commit()

    cursor.close()
    conec.close()

    return {
        "Mensaje": "Habilidad actualizada",
        "id": id
    }, 200
    
    
    
    # Eliminar habilidad por id
@app.route("/api/eliminarhabilidad/<int:id>", methods=["DELETE"])
def eliminar_habilidad(id):

    conec = conectar_bd()
    cursor = conec.cursor()

    cursor.execute(
        "SELECT id FROM habilidades WHERE id=%s",
        (id,)
    )

    existe = cursor.fetchone()

    if existe is None:
        cursor.close()
        conec.close()

        return {
            "mensaje": "No se encontró la habilidad"
        }, 404

    cursor.execute(
        "DELETE FROM habilidades WHERE id=%s",
        (id,)
    )

    conec.commit()

    cursor.close()
    conec.close()

    return {
        "mensaje": "Habilidad eliminada"
    }, 200




# Endpoints cursos

# Consultar todos los cursos asociados a una hoja de vida
@app.route("/api/hojasvida/<int:hoja_vida_id>/cursos", methods=["GET"])
def consultar_cursos(hoja_vida_id):

    conec = conectar_bd()
    cursor = conec.cursor(dictionary=True)

    sql = """
        SELECT id, hoja_vida_id, nombre
        FROM cursos
        WHERE hoja_vida_id = %s
    """

    cursor.execute(sql, (hoja_vida_id,))

    cursos = cursor.fetchall()

    cursor.close()
    conec.close()

    return cursos, 200



# Registrar un nuevo curso
@app.route("/api/hojasvida/<int:hoja_vida_id>/cursos", methods=["POST"])
def registrar_curso(hoja_vida_id):

    datos = request.get_json()

    conec = conectar_bd()
    cursor = conec.cursor()

    sql = """
        INSERT INTO cursos
        (hoja_vida_id, nombre)
        VALUES (%s, %s)
    """

    valores = (
        hoja_vida_id,
        datos["nombre"]
    )

    cursor.execute(sql, valores)
    conec.commit()

    id_curso = cursor.lastrowid

    cursor.close()
    conec.close()

    return {
        "mensaje": "Curso registrado correctamente",
        "id": id_curso,
        "hoja_vida_id": hoja_vida_id
    }, 201



# Consultar un curso específico
@app.route("/api/cursos/<int:id>", methods=["GET"])
def consultar_curso(id):

    conec = conectar_bd()
    cursor = conec.cursor(dictionary=True)

    sql = """
        SELECT id, hoja_vida_id, nombre
        FROM cursos
        WHERE id = %s
    """

    cursor.execute(sql, (id,))

    curso = cursor.fetchone()

    cursor.close()
    conec.close()

    if curso is None:
        return {
            "mensaje": "Curso no encontrado"
        }, 404

    return curso, 200


# Actualizar un curso
@app.route("/api/actualizarcurso/<int:id>", methods=["PUT"])
def actualizar_curso(id):

    datos = request.json
    conec = conectar_bd()
    cursor = conec.cursor(buffered=True)

    # Verificar si el curso existe
    buscar = """SELECT id FROM cursos WHERE id=%s"""
    cursor.execute(buscar, (id,))
    result = cursor.fetchone()

    if result is None:
        cursor.close()
        conec.close()

        return {
            "Mensaje": "No se encontro el curso"
        }, 404

    # Actualizar
    sqlactualizar = """
        UPDATE cursos
        SET nombre=%s
        WHERE id=%s
    """

    valor = (
        datos["nombre"],
        id
    )

    cursor.execute(sqlactualizar, valor)
    conec.commit()

    cursor.close()
    conec.close()

    return {
        "Mensaje": "Curso actualizado",
        "id": id
    }, 200
    
    
    
    # Eliminar curso por id
@app.route("/api/eliminarcurso/<int:id>", methods=["DELETE"])
def eliminar_curso(id):

    conec = conectar_bd()
    cursor = conec.cursor()

    cursor.execute(
        "SELECT id FROM cursos WHERE id=%s",
        (id,)
    )

    existe = cursor.fetchone()

    if existe is None:
        cursor.close()
        conec.close()

        return {
            "mensaje": "No se encontró el curso"
        }, 404

    cursor.execute(
        "DELETE FROM cursos WHERE id=%s",
        (id,)
    )

    conec.commit()

    cursor.close()
    conec.close()

    return {
        "mensaje": "Curso eliminado"
    }, 200
    
    
    # CONSULTA COMPLETA DE LA HOJA DE VIDA

@app.route("/api/hojasvida/<int:id>/completa", methods=["GET"])
def consultar_hoja_vida_completa(id):

    conec = conectar_bd()
    cursor = conec.cursor(dictionary=True)

    # Buscar la hoja de vida
    cursor.execute(
        "SELECT * FROM hojas_vida WHERE id = %s",
        (id,)
    )

    hoja_vida = cursor.fetchone()

    if hoja_vida is None:
        cursor.close()
        conec.close()

        return {
            "mensaje": "Hoja de vida no encontrada"
        }, 404

    # Consultar estudios
    cursor.execute(
        """
        SELECT id, nivel, institucion, titulo, anio_graduacion
        FROM estudios
        WHERE hoja_vida_id = %s
        """,
        (id,)
    )

    estudios = cursor.fetchall()

    # Consultar cursos
    cursor.execute(
        """
        SELECT id, nombre
        FROM cursos
        WHERE hoja_vida_id = %s
        """,
        (id,)
    )

    cursos = cursor.fetchall()

    # Consultar experiencias
    cursor.execute(
        """
        SELECT id, empresa, cargo, tiempo, funciones
        FROM experiencias
        WHERE hoja_vida_id = %s
        """,
        (id,)
    )

    experiencias = cursor.fetchall()

    # Consultar habilidades de cada experiencia
    for experiencia in experiencias:

        cursor.execute(
            """
            SELECT id, nombre
            FROM habilidades
            WHERE experiencia_id = %s
            """,
            (experiencia["id"],)
        )

        habilidades = cursor.fetchall()

        experiencia["habilidades"] = habilidades

    cursor.close()
    conec.close()

    return {
        "hoja_vida": hoja_vida,
        "estudios": estudios,
        "cursos": cursos,
        "experiencias": experiencias
    }, 200



if __name__ == "__main__":
    app.run(debug=True)
