from flask import Flask, request
from database import conectar_bd

app = Flask(__name__)


@app.route("/probar")
def probar_data():
    conec = conectar_bd()

    if conec.is_connected():
        conec.close()

    return {
        "mensaje": "Conexion ok"
    }


#Actualizar hoja de vida por medio del id
@app.route("/api/actualizarhv/<int:id>", methods=["PUT"])
def actualizarhv(id):

    # Recibir los datos enviados
    datos = request.json()
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


@app.route("/")
def inicio():
    return "Api hoja de vida funcionando"


# buscar una hoja de vida por id
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


# listar todas las hojas de vida
@app.route("/api/hojas-vida")
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




# GESTION DE ESTUDIOS

#  1 . Consultar todos los estudios asociados a una hoja de vida.
@app.route("/api/hojas-vida/<int:id>/estudios", methods=["GET"])
def consultar_estudios(id):

    conec = conectar_bd()
    cursor = conec.cursor(dictionary=True)

    # Verificar que la hoja de vida existe
    cursor.execute(
        "SELECT id FROM hojas_vida WHERE id = %s",
        (id,)
    )

    hoja = cursor.fetchone()

    if hoja is None:
        cursor.close()
        conec.close()

        return {
            "mensaje": "No se encontró la hoja de vida"
        }, 404

    # Consultar los estudios
    cursor.execute(
        """
        SELECT id, hoja_vida_id, nivel, institucion, titulo, anio_graduacion FROM estudios WHERE hoja_vida_id = %s""",
        (id,)
    )

    estudios = cursor.fetchall()
    cursor.close()
    conec.close()

    return estudios, 200

# 2. Registrar un nuevo estudio para una hoja de vida. 
@app.route("/api/hojas-vida/<int:id>/estudios", methods=["POST"])
def registrar_estudio(id):

    datos = request.get_json()

    conec = conectar_bd()
    cursor = conec.cursor()

    # Verificar que la hoja de vida existe
    cursor.execute(
        "SELECT id FROM hojas_vida WHERE id = %s",
        (id,)
    )

    hoja = cursor.fetchone()

    if hoja is None:
        cursor.close()
        conec.close()

        return {
            "mensaje": "No se encontró la hoja de vida"
        }, 404

    # Registrar el estudio
    sql = """
        INSERT INTO estudios(hoja_vida_id, nivel, institucion, titulo, anio_graduacion)VALUES (%s, %s, %s, %s, %s)"""

    valores = (
        id,
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
        "hoja_vida_id": id
    }, 201


# 3. Consultar un estudio específico
@app.route("/api/estudios/<int:id>", methods=["GET"])
def consultar_estudio(id):

    conec = conectar_bd()
    cursor = conec.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT id, hoja_vida_id, nivel, institucion, titulo, anio_graduacion FROM estudios WHERE id = %s""",
        (id,)
    )

    estudio = cursor.fetchone()

    cursor.close()
    conec.close()

    if estudio is None:
        return {
            "mensaje": "No se encontró el estudio"
        }, 404

    return estudio, 200


# 4. Actualizar un estudio
@app.route("/api/estudios/<int:id>", methods=["PUT"])
def actualizar_estudio(id):

    # Recibir los datos enviados desde Postman
    datos = request.get_json()

    conec = conectar_bd()
    cursor = conec.cursor()

    # Verificar que el estudio existe
    cursor.execute(
        "SELECT id FROM estudios WHERE id = %s",
        (id,)
    )

    estudio = cursor.fetchone()

    if estudio is None:
        cursor.close()
        conec.close()

        return {
            "mensaje": "No se encontró el estudio"
        }, 404

    # Actualizar los datos del estudio
    sql = """
        UPDATE estudios
        SET nivel = %s,
            institucion = %s,
            titulo = %s,
            anio_graduacion = %s
        WHERE id = %s
    """

    valores = (
        datos["nivel"],
        datos["institucion"],
        datos["titulo"],
        datos["anio_graduacion"],
        id
    )

    cursor.execute(sql, valores)

    conec.commit()

    cursor.close()
    conec.close()

    return {
        "mensaje": "Estudio actualizado correctamente",
        "id": id
    }, 200


# 5. Eliminar un estudio
@app.route("/api/estudios/<int:id>", methods=["DELETE"])
def eliminar_estudio(id):

    conec = conectar_bd()
    cursor = conec.cursor()

    # Verificar que el estudio existe
    cursor.execute(
        "SELECT id FROM estudios WHERE id = %s",
        (id,)
    )

    estudio = cursor.fetchone()

    if estudio is None:
        cursor.close()
        conec.close()

        return {
            "mensaje": "No se encontró el estudio"
        }, 404

    # Eliminar el estudio
    cursor.execute(
        "DELETE FROM estudios WHERE id = %s",
        (id,)
    )

    conec.commit()

    cursor.close()
    conec.close()

    return {
        "mensaje": "Estudio eliminado correctamente",
        "id": id
    }, 200

#GESTION DE EXPERIENCIA LABORAL 

# 1. Consultar las experiencias laborales de una hoja de vida

@app.route("/api/hojas-vida/<int:id>/experiencias", methods=["GET"])
def consultar_experiencias(id):

    conec = conectar_bd()
    cursor = conec.cursor(dictionary=True)

    # Verificar que la hoja de vida existe
    cursor.execute(
        "SELECT id FROM hojas_vida WHERE id = %s",
        (id,)
    )

    hoja = cursor.fetchone()

    if hoja is None:
        cursor.close()
        conec.close()

        return {
            "mensaje": "No se encontró la hoja de vida"
        }, 404

    # Consultar las experiencias de la hoja de vida
    cursor.execute(
        """
        SELECT id, hoja_vida_id, empresa, cargo, tiempo, funciones
        FROM experiencias
        WHERE hoja_vida_id = %s
        """,
        (id,)
    )

    experiencias = cursor.fetchall()

    cursor.close()
    conec.close()

    return experiencias, 200

# 2. Registrar una experiencia laboral

@app.route("/api/hojas-vida/<int:id>/experiencias", methods=["POST"])
def registrar_experiencia(id):

    datos = request.get_json()

    conec = conectar_bd()
    cursor = conec.cursor()

    # Verificar que la hoja de vida existe
    cursor.execute(
        "SELECT id FROM hojas_vida WHERE id = %s",
        (id,)
    )

    hoja = cursor.fetchone()

    if hoja is None:
        cursor.close()
        conec.close()

        return {
            "mensaje": "No se encontró la hoja de vida"
        }, 404

    # Registrar la experiencia
    sql = """
        INSERT INTO experiencias
        (hoja_vida_id, empresa, cargo, tiempo, funciones)
        VALUES (%s, %s, %s, %s, %s)
    """

    valores = (
        id,
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
        "hoja_vida_id": id
    }, 201


# 3. Consultar una experiencia específica

@app.route("/api/experiencias/<int:id>", methods=["GET"])
def consultar_experiencia(id):

    conec = conectar_bd()
    cursor = conec.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT id, hoja_vida_id, empresa, cargo, tiempo, funciones
        FROM experiencias
        WHERE id = %s
        """,
        (id,)
    )

    experiencia = cursor.fetchone()

    cursor.close()
    conec.close()

    if experiencia is None:
        return {
            "mensaje": "No se encontró la experiencia"
        }, 404

    return experiencia, 200

# 4. Actualizar una experiencia

@app.route("/api/experiencias/<int:id>", methods=["PUT"])
def actualizar_experiencia(id):

    datos = request.get_json()

    conec = conectar_bd()
    cursor = conec.cursor()

    # Verificar que la experiencia existe
    cursor.execute(
        "SELECT id FROM experiencias WHERE id = %s",
        (id,)
    )

    experiencia = cursor.fetchone()

    if experiencia is None:
        cursor.close()
        conec.close()

        return {
            "mensaje": "No se encontró la experiencia"
        }, 404

    # Actualizar los datos
    sql = """
        UPDATE experiencias
        SET empresa = %s,
            cargo = %s,
            tiempo = %s,
            funciones = %s
        WHERE id = %s
    """

    valores = (
        datos["empresa"],
        datos["cargo"],
        datos["tiempo"],
        datos["funciones"],
        id
    )

    cursor.execute(sql, valores)

    conec.commit()

    cursor.close()
    conec.close()

    return {
        "mensaje": "Experiencia actualizada correctamente",
        "id": id
    }, 200

# 5. Eliminar una experiencia

@app.route("/api/experiencias/<int:id>", methods=["DELETE"])
def eliminar_experiencia(id):

    conec = conectar_bd()
    cursor = conec.cursor()

    # Verificar que la experiencia existe
    cursor.execute(
        "SELECT id FROM experiencias WHERE id = %s",
        (id,)
    )

    experiencia = cursor.fetchone()

    if experiencia is None:
        cursor.close()
        conec.close()

        return {
            "mensaje": "No se encontró la experiencia"
        }, 404

    # Eliminar la experiencia
    cursor.execute(
        "DELETE FROM experiencias WHERE id = %s",
        (id,)
    )

    conec.commit()

    cursor.close()
    conec.close()

    return {
        "mensaje": "Experiencia eliminada correctamente",
        "id": id
    }, 200


# GESTION DE HABILIDADES

# 1. Consultar las habilidades de una experiencia

@app.route("/api/experiencias/<int:id>/habilidades", methods=["GET"])
def consultar_habilidades(id):

    conec = conectar_bd()
    cursor = conec.cursor(dictionary=True)

    # Verificar que la experiencia existe
    cursor.execute(
        "SELECT id FROM experiencias WHERE id = %s",
        (id,)
    )

    experiencia = cursor.fetchone()

    if experiencia is None:
        cursor.close()
        conec.close()

        return {
            "mensaje": "No se encontró la experiencia"
        }, 404

    # Consultar las habilidades de la experiencia
    cursor.execute(
        """
        SELECT id, experiencia_id, nombre
        FROM habilidades
        WHERE experiencia_id = %s
        """,
        (id,)
    )

    habilidades = cursor.fetchall()

    cursor.close()
    conec.close()

    return habilidades, 200

# 2. Registrar una habilidad
@app.route("/api/experiencias/<int:id>/habilidades", methods=["POST"])
def registrar_habilidad(id):

    datos = request.get_json()

    conec = conectar_bd()
    cursor = conec.cursor()

    cursor.execute(
        "SELECT id FROM experiencias WHERE id = %s",
        (id,)
    )

    experiencia = cursor.fetchone()

    if experiencia is None:
        cursor.close()
        conec.close()

        return {
            "mensaje": "No se encontró la experiencia"
        }, 404

    sql = """
        INSERT INTO habilidades
        (experiencia_id, nombre)
        VALUES (%s, %s)
    """

    valores = (
        id,
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
        "experiencia_id": id
    }, 201


# 3.Actualizar una habilidad
@app.route("/api/habilidades/<int:id>", methods=["PUT"])
def actualizar_habilidad(id):

    datos = request.get_json()

    conec = conectar_bd()
    cursor = conec.cursor()

    cursor.execute(
        "SELECT id FROM habilidades WHERE id = %s",
        (id,)
    )

    habilidad = cursor.fetchone()

    if habilidad is None:
        cursor.close()
        conec.close()

        return {
            "mensaje": "No se encontró la habilidad"
        }, 404

    sql = """
        UPDATE habilidades
        SET nombre = %s
        WHERE id = %s
    """

    valores = (
        datos["nombre"],
        id
    )

    cursor.execute(sql, valores)

    conec.commit()

    cursor.close()
    conec.close()

    return {
        "mensaje": "Habilidad actualizada correctamente",
        "id": id
    }, 200


# 4. Eliminar una habilidad
@app.route("/api/habilidades/<int:id>", methods=["DELETE"])
def eliminar_habilidad(id):

    conec = conectar_bd()
    cursor = conec.cursor()

    cursor.execute(
        "SELECT id FROM habilidades WHERE id = %s",
        (id,)
    )

    habilidad = cursor.fetchone()

    if habilidad is None:
        cursor.close()
        conec.close()

        return {
            "mensaje": "No se encontró la habilidad"
        }, 404

    cursor.execute(
        "DELETE FROM habilidades WHERE id = %s",
        (id,)
    )

    conec.commit()

    cursor.close()
    conec.close()

    return {
        "mensaje": "Habilidad eliminada correctamente",
        "id": id
    }, 200







if __name__ == "__main__":
    app.run(debug=True)