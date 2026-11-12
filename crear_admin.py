from flask import Flask, request
from database import conectar_bd
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from dotenv import load_dotenv
import os
from getpass import getpass

def crear_administrador():

    nombre = input("Ingresar nombre del rol reclutador")
    correo = input("Ingresar correo del rol reclutador")
    password = getpass("Contraseña")

    if len(password) < 8 :
        print("La contraseña debe tener minimo 8 caracteres")
        return

    conexion = conectar_bd()
    cursor = conexion.cursor()

    try:
        cursor.execute("SELECT id FROM USUARIOS WHERE correo = %s",(correo,))
        existente = cursor.fetchone()

        if existente: 
            print("Este correo ya esta registrado") 
            return
        #cifrar contraseña

        password_hash = generate_password_hash(password)

        sql = """INSERT INTO USUARIOS(nombre,correo,password,rol,estado)VALUES(%s,%s,%s,'reclutador', 1)"""

        cursor.execute(sql,(nombre, correo, password_hash))

        conexion.commit()
        print("Reclutador creado correctamente")
    except Exception as error:
        conexion.rollback()
        print("Error:",error)

    finally:
        cursor.close()
        conexion.close()
    

if __name__== "__main__":
    crear_administrador()