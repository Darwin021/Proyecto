from flask import Flask, render_template, request, redirect, session, flash, send_file
from flask_mysqldb import MySQL
import hashlib
import os
import base64
from werkzeug.utils import secure_filename
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
from threading import Thread
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt



app = Flask(__name__, template_folder='template')

# Configuración de la clave secreta para la sesión
app.config['SECRET_KEY'] = 'tu_clave_secreta'

# Configuración de la base de datos MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'proyectoweb'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
mysql = MySQL(app)

# Carpeta de carga de archivos
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Función de filtro personalizada para realizar la codificación Base64
def b64encode_custom(image_bytes):
    return base64.b64encode(image_bytes).decode('utf-8')

# Agregar la función de filtro al entorno de Jinja2
app.jinja_env.filters['b64encode_custom'] = b64encode_custom

# Ruta de inicio
@app.route('/')
def home():
    return render_template('index.html')

# Ruta de inicio de sesión
@app.route('/acceso-login', methods=["POST"])
def login():
    if request.method == 'POST' and 'txtCorreo' in request.form and 'txtPassword' in request.form:
        correo = request.form['txtCorreo']
        password = request.form['txtPassword']
        
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM admins WHERE correo = %s AND contrasena = %s', (correo, hashed_password))
        account = cur.fetchone()
        
        if account:
            session['logueado'] = True
            session['idadmin'] = account['idadmin']
            return redirect('/inicio')
        else:
            return render_template('index.html', mensaje="Usuario o contraseña incorrectas")

# Ruta de registro
@app.route('/registro')
def registro():
    return render_template('registro.html')

# Ruta para crear un registro de usuario
@app.route('/crear-registro', methods=["POST"])
def crear_registro():
    correo = request.form['txtCorreo']
    password = request.form['txtPassword']
    
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO admins (correo, contrasena) VALUES (%s, %s)", (correo, hashed_password))
    mysql.connection.commit()
    flash('Usuario registrado exitosamente')
    
    return redirect('/')

# Ruta de inicio después del inicio de sesión
@app.route('/inicio')
def inicio():
    return render_template('inicio.html')

# Ruta para mostrar todas las actividades
@app.route('/actividades')
def actividades():
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM limpieza')
    actividades = cur.fetchall()

    # Codificar las imágenes en base64 antes de pasarlas a la plantilla
    for actividad in actividades:
        imagen_path = actividad['IMAGEN']
        if imagen_path is not None:
            with open(imagen_path, 'rb') as f:
                imagen_bytes = f.read()
                actividad['IMAGEN_BASE64'] = base64.b64encode(imagen_bytes).decode('utf-8')
        else:
            actividad['IMAGEN_BASE64'] = None

    cur.close()  # Cerrar el cursor después de la consulta

    return render_template('actividades.html', actividades=actividades)

# Ruta para obtener la página de edición de actividad
@app.route('/editar-actividad/<int:ID_SERVICIO>/<int:ID_COLONIAS>/<int:ID_CUADRILLA>')
def get_editA(ID_SERVICIO, ID_COLONIAS, ID_CUADRILLA):
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM limpieza WHERE ID_SERVICIO = %s AND ID_COLONIAS = %s AND ID_CUADRILLA = %s', (ID_SERVICIO, ID_COLONIAS, ID_CUADRILLA))
    data = cur.fetchone()
    cur.close()
    return render_template('editaractividades.html', actividadE=data)

# Ruta para eliminar una actividad específica
@app.route('/borrar-actividad/<int:ID_SERVICIO>/<int:ID_COLONIAS>/<int:ID_CUADRILLA>')
def get_borrarA(ID_SERVICIO, ID_COLONIAS, ID_CUADRILLA):
    cur = mysql.connection.cursor()
    cur.execute('DELETE FROM limpieza WHERE ID_SERVICIO = %s AND ID_COLONIAS = %s AND ID_CUADRILLA = %s', (ID_SERVICIO, ID_COLONIAS, ID_CUADRILLA))
    mysql.connection.commit()
    flash('Actividad removida con éxito!!')
    return redirect('/actividades')

# Ruta para editar una actividad
@app.route('/editarA/<ID_SERVICIO>,<ID_COLONIAS>,<ID_CUADRILLA>', methods=['POST'])
def editarA(ID_SERVICIO, ID_COLONIAS, ID_CUADRILLA):
    if request.method == 'POST':
        servicio = request.form['id_servicio']
        colonia = request.form['id_colonia']
        cuadrilla = request.form['id_cuadrilla']
        fecha = request.form['fecha_limpieza']
        observaciones = request.form['observaciones']
        imagen_nueva = request.files['imagen'] if 'imagen' in request.files else None

        # Obtener la actividad actual de la base de datos
        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM limpieza WHERE ID_SERVICIO = %s AND ID_COLONIAS = %s AND ID_CUADRILLA = %s', (ID_SERVICIO, ID_COLONIAS, ID_CUADRILLA))
        actividad_actual = cur.fetchone()

        # Si se proporciona una nueva imagen, guardarla y actualizar la ruta en la base de datos
        if imagen_nueva:
            # Guardar la nueva imagen en el sistema de archivos
            filename = secure_filename(imagen_nueva.filename)
            imagen_nueva.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            imagen_url_nueva = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            # Actualizar la ruta de la imagen en la base de datos
            cur.execute("""
                UPDATE limpieza
                SET IMAGEN = %s
                WHERE ID_SERVICIO = %s AND ID_COLONIAS = %s AND ID_CUADRILLA = %s
            """, (imagen_url_nueva, ID_SERVICIO, ID_COLONIAS, ID_CUADRILLA))
            mysql.connection.commit()

            # Eliminar la imagen anterior si existe
            if actividad_actual['IMAGEN']:
                os.remove(actividad_actual['IMAGEN'])

        # Actualizar los demás campos en la base de datos
        cur.execute("""
            UPDATE limpieza
            SET ID_SERVICIO = %s,
                ID_COLONIAS = %s,
                ID_CUADRILLA = %s,
                FECHA_LIMPIEZA = %s,
                OBSERVACIONES = %s
            WHERE ID_SERVICIO = %s AND ID_COLONIAS = %s AND ID_CUADRILLA = %s
        """, (servicio, colonia, cuadrilla, fecha, observaciones, ID_SERVICIO, ID_COLONIAS, ID_CUADRILLA))
        mysql.connection.commit()
        cur.close()

        flash('Actividad modificada con éxito!!')

    return redirect('/actividades')

# Ruta para agregar una nueva actividad
@app.route('/agregar-actividad', methods=['POST'])
def agregara():
    if request.method == 'POST':
        servicio = request.form['id_servicio']
        colonia = request.form['id_colonia']
        cuadrilla = request.form['id_cuadrilla']
        fecha = request.form['fecha_limpieza']
        observaciones = request.form['observaciones']
        
        imagen_url = None
        if 'imagen' in request.files:
            imagen = request.files['imagen']
            if imagen.filename != '':
                filename = secure_filename(imagen.filename)
                imagen.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                imagen_url = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        cur = mysql.connection.cursor()
        cur.execute('INSERT INTO limpieza (ID_SERVICIO, ID_COLONIAS, ID_CUADRILLA, FECHA_LIMPIEZA, OBSERVACIONES, IMAGEN) VALUES (%s, %s, %s, %s, %s, %s)',
                    (servicio, colonia, cuadrilla, fecha, observaciones, imagen_url))
        mysql.connection.commit()
        cur.close()
        flash('Actividad agregada con éxito')
    return redirect('/actividades')

# Ruta para mostrar las asignaciones de cuadrillas
@app.route('/cuadrillas')
def cuadrillas():
    cur = mysql.connection.cursor()
    cur.execute('''
        SELECT
            sa.ID_CUADRILLA,
            p.NOMBRE AS NOMBRE_PERSONAL,
            pu.NOMBRE_PUESTO AS PUESTO_PERSONAL
        FROM
            se_asigna_a sa
        JOIN
            personal p ON sa.ID_PERSONAL = p.ID_PERSONAL
        JOIN
            puestos pu ON p.ID_PUESTO = pu.ID_PUESTO
        ORDER BY
            sa.ID_CUADRILLA
    ''')
    data = cur.fetchall()
    cur.close()  # Cerrar el cursor después de la consulta

    return render_template('cuadrillas.html', asignaciones=data)

# Ruta para mostrar el personal
@app.route('/personalL')
def personal():
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM personal')
    data = cur.fetchall()
    cur.close()  # Cerrar el cursor después de la consulta

    return render_template('personalL.html', personales=data)

# Ruta para agregar nuevo personal
@app.route('/agregar-personal', methods=['POST'])
def agregar():
    if request.method == 'POST':
        puesto = request.form['id_puesto']
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        telefono = request.form['telefono']
        email = request.form['email']
        cur = mysql.connection.cursor()
        cur.execute('INSERT INTO personal (ID_PUESTO, NOMBRE, APELLIDO, TELEFONO, EMAIL) VALUES (%s, %s, %s, %s, %s)',
                    (puesto, nombre, apellido, telefono, email))
        mysql.connection.commit()
        cur.close()
        flash('Personal agregado con éxito')
        
    return redirect('/personalL')

# Ruta para obtener la página de edición de personal
@app.route('/editar-personal/<ID_PERSONAL>')
def get_edit(ID_PERSONAL):
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM personal WHERE ID_PERSONAL = %s', ID_PERSONAL)
    data = cur.fetchall()
    print(data[0])
    return render_template('editarpersonal.html', personal=data[0])

# Ruta para editar personal
@app.route('/editarP/<ID_PERSONAL>', methods=['POST'])
def editar(ID_PERSONAL):
    if request.method == 'POST':
        puesto = request.form['id_puesto']
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        telefono = request.form['telefono']
        email = request.form['email']

    cur = mysql.connection.cursor()
    cur.execute("""
      UPDATE personal
      SET ID_PUESTO = %s,
          NOMBRE = %s,
          APELLIDO = %s,
          TELEFONO = %s,
          EMAIL = %s
      WHERE ID_PERSONAL = %s 
    """, (puesto, nombre, apellido, telefono, email, ID_PERSONAL))
    mysql.connection.commit()
    flash('Personal modificado con éxito!!')
    return redirect('/personalL')

# Ruta para borrar personal
@app.route('/borrar-personal/<string:ID_PERSONAL>')
def borrar(ID_PERSONAL):
    cur = mysql.connection.cursor()
    cur.execute('DELETE FROM personal WHERE ID_PERSONAL = {0}'.format(ID_PERSONAL))
    mysql.connection.commit()
    flash('Personal removido con éxito!!')
    return redirect('/personalL')

# Ruta para mostrar las colonias
@app.route('/colonias')
def index():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM colonias")
    data = cursor.fetchall()
    return render_template('colonias.html', data=data)

@app.route('/dashboard')
def dashboard():
    def generate_plot():
        # Consulta SQL para obtener el número de actividades por cuadrilla
        consulta = """
            SELECT ID_CUADRILLA, COUNT(ID_SERVICIO) AS Numero_Actividades
            FROM limpieza
            GROUP BY ID_CUADRILLA
        """

        # Ejecutar la consulta y obtener los resultados
        cursor = mysql.connection.cursor()
        cursor.execute(consulta)
        resultados = cursor.fetchall()

        # Crear un DataFrame de Pandas con los resultados
        df = pd.DataFrame(resultados, columns=['ID_CUADRILLA', 'Numero_Actividades'])

        # Crear un gráfico de barras con Matplotlib
        plt.bar(df['ID_CUADRILLA'], df['Numero_Actividades'])
        plt.xlabel('ID Cuadrilla')
        plt.ylabel('Número de Actividades')
        plt.title('Actividades por Cuadrilla')

        # Guardar el gráfico en un buffer de BytesIO
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png')
        img_buffer.seek(0)

        # Cerrar el cursor de la base de datos
        cursor.close()

        # Devolver el buffer de la imagen
        return img_buffer

    # Crear un hilo para generar el gráfico
    thread = Thread(target=generate_plot)
    thread.start()
    thread.join()

    # Obtener la imagen del hilo y enviarla como respuesta
    img_buffer = generate_plot()
    return send_file(img_buffer, mimetype='image/png')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)