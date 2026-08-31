from flask import Flask
from database import conectar_bd 
app= Flask(__name__)



@app.route("/probar")
def probar_data():
    conec = conectar_bd
    if conec.is_connected():
        conec.close()
    return {
        "mensaje" : "conexion ok"
    }

@app.route("/")
def inicio():
    return "Api hoja de vina funcionando"

@app.route("/api/hojas-vida/<int:id>")
def obtener_hojasvidaid(id):
    return{
        "mensaje":"hoja de vida encontrada","id":id
    }



@app.route("/api/hojas-vida")
def obtener_hojasvida():
    #return{
     #   "mensaje":"Listado de hojas de vida"
    #}
    hojas_vida =[{
        "id":1,
        "nombre":"Johanna Cifuentes",
        "edad":50,
        "ciudad":"Bogota",
        "fotografia":"foto",
        "programa":"adso",
        "ficha":2323,
        "jornada":"diurna"
    },
    {
        "id": 2,
        "nombre": "jeison jimenez",
        "edad": 23,
        "ciudad": "Cali",
        "fotografia": "fotos",
        "programa": "tecnico",
        "ficha": 2424,
        "jornada": "nocturna"
    }


    ]
    return hojas_vida

if __name__== "__main__":
    app.run(debug=True)