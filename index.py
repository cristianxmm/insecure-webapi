import json
import secrets
import mysql.connector
import base64
import shutil
from pathlib import Path
from bottle import route, run, template, post, request, static_file
from argon2 import PasswordHasher

ph = PasswordHasher()

def loadDatabaseSettings(pathjs):
	pathjs = Path(pathjs)
	sjson = False
	if pathjs.exists():
		with pathjs.open() as data:
			sjson = json.load(data)
	return sjson
	
"""
function loadDatabaseSettings(pathjs):
	string = file_get_contents(pathjs);
	json_a = json_decode(string, true);
	return json_a;

"""
def getToken():
	return secrets.token_hex(16)
"""
*/ 
# Registro
/*
 * Este Registro recibe un JSON con el siguiente formato
 * 
 * : 
 *		"uname": "XXX",
 *		"email": "XXX",
 * 		"password": "XXX"
 * 
 * */
"""
@post('/Registro')
def Registro():
	dbcnf = loadDatabaseSettings('db.json');
	db = mysql.connector.connect(
		host='localhost', port = dbcnf['port'],
		database = dbcnf['dbname'],
		user = dbcnf['user'],
		password = dbcnf['password']
	)
	####/ obtener el cuerpo de la peticion
	if not request.json:
		return {"R":-1}
	R = 'uname' in request.json and 'email' in request.json and 'password' in request.json
	# TODO checar si estan vacio los elementos del json
	if not R:
		return {"R":-1}
	# TODO validar correo en json
	# TODO Control de error de la DB
	R = False
	try:
		with db.cursor() as cursor:
			# consulta parametrizada para parchar el SQL inyection
			hash_pwd = ph.hash(request.json["password"])
			sql = "INSERT INTO Usuario VALUES (null, %s, %s, %s)"
			data = (request.json["uname"], request.json["email"], hash_pwd)
			cursor.execute(sql, data)
			R = cursor.lastrowid
			db.commit()
		db.close()
	except Exception as e:
		print("Error interno en /Registro. Sin detalles.") 
		return {"R":-2}
	return {"R":0,"D":R}




"""
/*
 * Este Registro recibe un JSON con el siguiente formato
 * 
 * : 
 *		"uname": "XXX",
 * 		"password": "XXX"
 * 
 * 
 * Debe retornar un Token 
 * */
"""

@post('/Login')
def Login():
	dbcnf = loadDatabaseSettings('db.json');
	db = mysql.connector.connect(
		host='localhost', port = dbcnf['port'],
		database = dbcnf['dbname'],
		user = dbcnf['user'],
		password = dbcnf['password']
	)
	###/ obtener el cuerpo de la peticion
	if not request.json:
		return {"R":-1}
	######/
	R = 'uname' in request.json  and 'password' in request.json
	# TODO checar si estan vacio los elementos del json
	if not R:
		return {"R":-1}
	
	# TODO validar correo en json
	# TODO Control de error de la DB
	R = False
	try:
		with db.cursor() as cursor:
			# consulta parametrizada para parchar el SQL inyection
			print(f'Select id from  Usuario where uname ="{request.json["uname"]}" and password = md5("{request.json["password"]}")') # El print se queda
			sql = "SELECT id, password FROM Usuario WHERE uname = %s"
			cursor.execute(sql, (request.json["uname"],))
			user_row = cursor.fetchone()
			
			if not user_row:
				db.close()
				return {"R": -3}
			id_usuario = user_row[0]
			hash_almacenado = user_row[1]
			try:
				ph.verify(hash_almacenado, request.json["password"])
				R=[[id_usuario]]
			except Exception:
				R=False

	except Exception as e: 
		print("Error interno en /Login (Paso 1). Sin detalles.")
		db.close()
		return {"R":-2}
	
	
	if not R:
		db.close()
		return {"R":-3}
	
	T = getToken();
	#file_put_contents('/tmp/log','insert into AccesoToken values('.R[0].',"'.T.'",now())');
	with open("/tmp/log","a") as log:
		log.write(f'Delete from AccesoToken where id_Usuario = "{R[0][0]}"\n')
		log.write(f'insert into AccesoToken values({R[0][0]},"{T}",now())\n')
	
	
	try:
		with db.cursor() as cursor:
			#Parcheo parametrizado SQL
			sql_del = "DELETE FROM AccesoToken WHERE id_Usuario = %s"
			cursor.execute(sql_del, (R[0][0],))
			sql_ins = "INSERT INTO AccesoToken VALUES (%s, %s, now())"
			cursor.execute(sql_ins, (R[0][0], T))
			db.commit()
		db.close()
		return {"R":0,"D":T}
	except Exception as e:
		print("Error interno en /Login (Paso 2). Sin detalles.")
		db.close()
		return {"R":-4}
"""
/*
 * Este subir imagen recibe un JSON con el siguiente formato
 * 
 * 
 * 		"token: "XXX"
 *		"name": "XXX",
 * 		"data": "XXX",
 * 		"ext": "PNG"
 * 
 * 
 * Debe retornar codigo de estado
 * */
"""
@post('/Imagen')
def Imagen():
	#Directorio
	tmp = Path('tmp')
	if not tmp.exists():
		tmp.mkdir()
	img = Path('img')
	if not img.exists():
		img.mkdir()
	
	###/ obtener el cuerpo de la peticion
	if not request.json:
		return {"R":-1}
	######/
	R = 'name' in request.json  and 'data' in request.json and 'ext' in request.json  and 'token' in request.json
	# TODO checar si estan vacio los elementos del json
	if not R:
		return {"R":-1}
	
	dbcnf = loadDatabaseSettings('db.json');
	db = mysql.connector.connect(
		host='localhost', port = dbcnf['port'],
		database = dbcnf['dbname'],
		user = dbcnf['user'],
		password = dbcnf['password']
	)

	# Validar si el usuario esta en la base de datos
	TKN = request.json['token'];
	
	R = False
	try:
		with db.cursor() as cursor:
		#Parcheo SQL inyection con consulta parametrizada.
			sql = "SELECT id_Usuario FROM AccesoToken WHERE token = %s"
			cursor.execute(sql, (TKN,))
			R = cursor.fetchall()
			if not R:
				db.close()
				return {"R"-2}
	except Exception as e: 
		print("Error interno en /Imagen (Paso 1). Sin detalles.")
		db.close()
		return {"R":-2}
	
	
	id_Usuario = R[0][0];
	with open(f'tmp/{id_Usuario}',"wb") as imagen:
		imagen.write(base64.b64decode(request.json['data'].encode()))
	
	############################
	############################
	# Guardar info del archivo en la base de datos
	try:
		with db.cursor() as cursor:
       			#Parcheo con consulta parametrizada
			sql_ins = "INSERT INTO Imagen VALUES (null, %s, 'img/', %s)"
			data_ins = (request.json["name"], id_Usuario)	
			cursor.execute(sql_ins, data_ins)
       			#Parcheo con consulta parametrizada
			sql_max = "SELECT max(id) as idImagen FROM Imagen WHERE id_Usuario = %s"
			cursor.execute(sql_max, (id_Usuario,))
			R = cursor.fetchall()
			idImagen = R[0][0];
       			#Parcheo con consulta parametrizada
			nueva_ruta = f"img/{idImagen}.{request.json['ext']}"	
			sql_upd = "UPDATE Imagen SET ruta = %s WHERE id = %s"
			data_upd = (nueva_ruta, idImagen)
			cursor.execute(sql_upd, data_upd)
			db.commit()
			# Mover archivo a su nueva locacion
			shutil.move('tmp/'+str(id_Usuario),'img/'+str(idImagen)+'.'+str(request.json['ext']))
			return {"R":0,"D":idImagen}
	except Exception as e: 
		print("Error interno en /Imagen (Paso 2). Sin detalles.")
		db.close()
		return {"R":-3}
	
"""
/*
 * Este Registro recibe un JSON con el siguiente formato
 * 
 * : 
 * 		"token: "XXX",
 * 		"id": "XXX"
 * 
 * 
 * Debe retornar un Token 
 * */
"""

@post('/Descargar')
def Descargar():
	dbcnf = loadDatabaseSettings('db.json');
	db = mysql.connector.connect(
		host='localhost', port = dbcnf['port'],
		database = dbcnf['dbname'],
		user = dbcnf['user'],
		password = dbcnf['password']
	)
	
	
	###/ obtener el cuerpo de la peticion
	if not request.json:
		return {"R":-1}
	######/
	R = 'token' in request.json and 'id' in request.json  
	# TODO checar si estan vacio los elementos del json
	if not R:
		return {"R":-1}
	
	# TODO validar correo en json
	# Comprobar que el usuario sea valido
	TKN = request.json['token'];
	idImagen = request.json['id'];
	try:
		idImagen = int(idImagen)
	except ValueError:
		return {"R":-10, "D":"ID de imagen invalido"}
	R = False
	id_usuario_del_token = None
	try:
		with db.cursor() as cursor:
       		#Parcheo con consulta parametrizada
			sql = "SELECT id_Usuario FROM AccesoToken WHERE token = %s"
			cursor.execute(sql, (TKN,))
			R = cursor.fetchall()
			if not R:
				db.close()
				return{"R":-2}
			id_usuario_del_token = R[0][0]
	except Exception as e: 
		print("Error interno en /Descargar (Paso 1). Sin detalles.")
		db.close()
		return {"R":-2}
	# Buscar imagen y enviarla
	
	try:
		with db.cursor() as cursor:
			#Parcheo con consulta parametrizada
			sql = "SELECT name, ruta FROM Imagen WHERE id = %s AND id_Usuario =%s"
			data=(idImagen, id_usuario_del_token)
			cursor.execute(sql, data)
			R = cursor.fetchall()
			
			if not R:
				db.close()
				return{"R":-3}


	except Exception as e: 
		print("Error interno en /Descargar (Paso 2).Sin detalles")
		db.close()
		return {"R":-3}
	print(Path("img").resolve(),R[0][1])
	return static_file(R[0][1],Path(".").resolve())

if __name__ == '__main__':
    run(host='localhost', port=8080, debug=True)
