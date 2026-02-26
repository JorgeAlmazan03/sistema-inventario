import firebase_admin
from firebase_admin import credentials, firestore
from security import hash_password,verify_password
from google.cloud.firestore_v1 import FieldFilter
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from textwrap import wrap
cred = credentials.Certificate("inventariocred.json")
firebase_admin.initialize_app(cred)
print('Conectado a firestore')
DB = firestore.client()
print('Base de datos conectada')
NEGOCIO_ID='Prueba1'

#Crear negocio
def crear_negocio(db,negocio_id,nombre):
    try:
        negocio_ref=db.collection('negocios').document(negocio_id)
        negocio_ref.set({
            'nombre':nombre,
            'created_at':firestore.SERVER_TIMESTAMP,
            'activo':True
        })
        negocio_ref.collection('usuarios').document('init').set({
            'activo':True,
            'created_at':firestore.SERVER_TIMESTAMP,
            'nombre':'admin',
            'password':hash_password('admin'),
            'rol':'admin',
            'usuario':'admin'
            
        })
        negocio_ref.collection('inventarios').document('base').set({
            'init':'init'
        })
    except Exception as e:
        raise e
        

#Crear nuevas subcolecciones
def crear_subcoleccion(db,subcoleccion,negocio_id):
    '''
    Docstring for crear_subcoleccion
    
    :param db: base de datos
    :param subcoleccion: nombre de la subcoleccion
    '''
    try:
        inventario_ref(db,negocio_id,'base') \
        .collection(subcoleccion) \
        .document("init") \
        .set({
            "producto": True
        })
    except Exception as e:
         print('Error: ',e)

def crear_subcoleccion_2(db,subcoleccion,negocio_id,sucursal):
    '''
    Docstring for crear_subcoleccion
    
    :param db: base de datos
    :param subcoleccion: nombre de la subcoleccion
    '''
    try:
        inventario_ref_2(db,negocio_id,sucursal,'base') \
        .collection(subcoleccion) \
        .document("init") \
        .set({
            "producto": True
        })
    except Exception as e:
         print('Error: ',e)
         
def crear_subcoleccion_3(db,subcoleccion,negocio_id,):
    '''
    Docstring for crear_subcoleccion
    
    :param db: base de datos
    :param subcoleccion: nombre de la subcoleccion
    '''
    try:
        sucursales_ref = (
            negocio_ref(db, negocio_id)
            .collection('sucursales')
        )

        sucursales = sucursales_ref.stream()

        for sucursal_doc in sucursales:

            sucursal_id = sucursal_doc.id

            inventario_ref_2(
                db,
                negocio_id,
                sucursal_id,
                'base'
            ).collection(subcoleccion) \
             .document("init") \
             .set({
                 "producto": True
             })
        crear_subcoleccion(db,subcoleccion,negocio_id)
    except Exception as e:
        print('Error:', e)
def crear_producto(db,subcoleccion,producto,unidad,negocio_id,minimo,maximo):
    '''
    Docstring for crear_producto
    
    :param db: Description
    :param subcoleccion: Description
    :param producto: Description
    '''
    minimo=float(minimo)
    maximo=float(maximo)
    inventario_ref(db,negocio_id,'base')\
      .collection(subcoleccion) \
      .document(producto) \
      .set({
          "producto": producto,
          'existencia':0,
          'unidad':unidad,
          'urge':False,
          'minimo':minimo,
          'maximo':maximo
      })
    crear_producto(db,subcoleccion,producto,unidad,negocio_id,minimo,maximo)
def crear_producto_2(db,subcoleccion,producto,unidad,negocio_id,sucursal,minimo,maximo):
    '''
    Docstring for crear_producto
    
    :param db: Description
    :param subcoleccion: Description
    :param producto: Description
    '''
    minimo=float(minimo)
    maximo=float(maximo)
    inventario_ref_2(db,negocio_id,sucursal,'base')\
      .collection(subcoleccion) \
      .document(producto) \
      .set({
          "producto": producto,
          'existencia':0,
          'unidad':unidad,
          'urge':False,
          'minimo':minimo,
          'maximo':maximo
      })
      
def crear_producto_3(db,subcoleccion,producto,unidad,negocio_id,minimo,maximo):
    '''
    Docstring for crear_producto
    
    :param db: Description
    :param subcoleccion: Description
    :param producto: Description
    '''
    minimo=float(minimo)
    maximo=float(maximo)
    # Obtener todas las sucursales
    sucursales_ref = negocio_ref(db, negocio_id).collection('sucursales')
    sucursales = sucursales_ref.stream()
    for sucursal_doc in sucursales:
        sucursal_id=sucursal_doc.id
        inventario_base_ref=inventarios_collection_ref_2(
            db,
            negocio_id,
            sucursal_id
        ).document('base')

        inventario_base_ref.collection(subcoleccion).document(producto).set({
          "producto": producto,
          'existencia':0,
          'unidad':unidad,
          'urge':False,
          'minimo':minimo,
          'maximo':maximo
        })
def agregar_producto_inventario(db,negocio_id,dia,subcoleccion,producto,existencia,unidad,urge=False):
    existencia=float(existencia)
    inventario_ref(db, negocio_id, inventario_id=dia)\
        .collection(subcoleccion)\
        .document(producto)\
        .set({
            'producto':producto,
            'existencia':existencia,
            'unidad':unidad,
            'urge':urge
        })

def agregar_producto_inventario_2(db,negocio_id,sucursal,dia,subcoleccion,producto,existencia,unidad,urge=False):
    existencia=float(existencia)
    inventario_ref_2(db, negocio_id,sucursal, inventario_id=dia)\
        .collection(subcoleccion)\
        .document(producto)\
        .set({
            'producto':producto,
            'existencia':existencia,
            'unidad':unidad,
            'urge':urge
        })

def agregar_existencia_producto(db,negocio_id,subcoleccion,producto,existencia):
    inventario_ref(db,negocio_id,'base')\
        .collection(subcoleccion)\
        .document(producto)\
        .update({'existencia':existencia})      
        
def agregar_existencia_producto_2(db,negocio_id,sucursal,subcoleccion,producto,existencia):
    inventario_ref_2(db,sucursal,negocio_id,'base')\
        .collection(subcoleccion)\
        .document(producto)\
        .update({'existencia':existencia})  
def crear_nuevo_inventario(db,fecha,elaborado_por,negocio_id,sucursal,notas=''):
    '''
    db:database
    fecha:fecha de elaboracion
    elaborado_por:quien lo hizo
    sucursal:sucursal
    notas:nota opcional
    '''

    nombre_documento = f"{fecha}-{sucursal}"
    nuevo_ref = inventario_ref(db, negocio_id, inventario_id=nombre_documento)
    
    nuevo_ref.set({
    "fecha": fecha,
    "elaborado_por": elaborado_por,
    "sucursal": sucursal,
    "notas": notas,
    "created_at": firestore.SERVER_TIMESTAMP
}) 
    return nuevo_ref

def crear_nuevo_inventario_2(db,fecha,elaborado_por,negocio_id,sucursal,notas=''):
    '''
    db:database
    fecha:fecha de elaboracion
    elaborado_por:quien lo hizo
    sucursal:sucursal
    notas:nota opcional
    '''

    nombre_documento = f"{fecha}-{sucursal}"
    nuevo_ref = inventario_ref_2(db, negocio_id,sucursal,inventario_id=nombre_documento)
    
    nuevo_ref.set({
    "fecha": fecha,
    "elaborado_por": elaborado_por,
    "sucursal": sucursal,
    "notas": notas,
    "created_at": firestore.SERVER_TIMESTAMP
}) 
    return nuevo_ref

def editar_stocks(db,negocio_id,subcoleccion,producto,minimo,maximo,unidad):
    data={}
    
    if minimo is not None:
        data["minimo"] = minimo
    if maximo is not None:
        data["maximo"] = maximo
    if unidad is not None:
        data["unidad"] = unidad

    if not data:
        return
    
    inventario_ref(db,negocio_id,'base')\
      .collection(subcoleccion) \
      .document(producto) \
      .update(data)

def editar_stocks_2(db,negocio_id,sucursal,subcoleccion,producto,minimo,maximo,unidad):
    data={}
    
    if minimo is not None:
        data["minimo"] = minimo
    if maximo is not None:
        data["maximo"] = maximo
    if unidad is not None:
        data["unidad"] = unidad

    if not data:
        return
    
    inventario_ref_2(db,negocio_id,sucursal,'base')\
      .collection(subcoleccion) \
      .document(producto) \
      .update(data)


def obtener_lista_inventarios(db, negocio_id):
    inventarios_ref = inventario_ref(db, negocio_id).parent.stream()
    lista = []

    for doc in inventarios_ref:
        data = doc.to_dict() or {}

        if doc.id == "base":
            continue

        if "created_at" not in data:
            continue

        lista.append(doc.id)

    lista.sort(reverse=False)
    return lista

def obtener_lista_inventarios_2(db, negocio_id,sucursal):
    inventarios_ref = inventario_ref_2(db, negocio_id,sucursal).parent.stream()
    lista = []

    for doc in inventarios_ref:
        data = doc.to_dict() or {}

        if doc.id == "base":
            continue

        if "created_at" not in data:
            continue

        lista.append(doc.id)

    lista.sort(reverse=False)
    return lista

#Obtener productos de una subcoleccion
def obtener_productos(db,subcoleccion,negocio_id,dia:str):
    '''
    Docstring for obtener_productos
    
    :param db: Database
    :param subcoleccion: Subcoleccion de firebase
    '''
    subcoleccion_ref = (
        inventario_ref(db,negocio_id,dia)  #Id del dia del inventario
          .collection(subcoleccion)
    )

    docs = subcoleccion_ref.stream()

    productos = []

    for doc in docs:
        #Con esta linea evitamos que se vea el init en el inventario
        if doc.id=='init':
            continue
        data = doc.to_dict() or {}

        productos.append({
            "id": doc.id,
            "producto": data.get("producto", 0),
            "existencia": data.get("existencia", "Nada"),
            'unidad':data.get('unidad','Unidades'),
            'urge':data.get('urge',False),
            'minimo':data.get('minimo',0),
            'maximo':data.get('maximo',1000)
        })

    return productos

def obtener_productos_2(db,subcoleccion,negocio_id,sucursal,dia:str):
    '''
    Docstring for obtener_productos
    
    :param db: Database
    :param subcoleccion: Subcoleccion de firebase
    '''
    subcoleccion_ref = (
        inventario_ref_2(db,negocio_id,sucursal,dia)  #Id del dia del inventario
          .collection(subcoleccion)
    )

    docs = subcoleccion_ref.stream()

    productos = []

    for doc in docs:
        #Con esta linea evitamos que se vea el init en el inventario
        if doc.id=='init':
            continue
        data = doc.to_dict() or {}

        productos.append({
            "id": doc.id,
            "producto": data.get("producto", 0),
            "existencia": data.get("existencia", "Nada"),
            'unidad':data.get('unidad','Unidades'),
            'urge':data.get('urge',False),
            'minimo':data.get('minimo',0),
            'maximo':data.get('maximo',1000)
        })

    return productos

def obtener_inventario_completo(db,negocio_id,dia):
    base_ref = inventario_ref(db,negocio_id,dia)

    inventario = {}

    for col in base_ref.collections():
        productos = obtener_productos(db,col.id,negocio_id,dia)
        inventario[col.id] = productos

    return inventario
def obtener_inventario_completo_2(db,negocio_id,sucursal,dia):
    base_ref = inventario_ref_2(db,negocio_id,sucursal,dia)

    inventario = {}

    for col in base_ref.collections():
        productos = obtener_productos(db,col.id,negocio_id,dia)
        inventario[col.id] = productos

    return inventario
def obtener_inventario_base(db,negocio_id):
    inventario = {}

    subcols = (
        inventario_ref(db,negocio_id,'base')
          .collections()
    )

    for sub in subcols:
        productos = []
        for doc in sub.stream():
            data = doc.to_dict()
            if doc.id == "init":
                continue

            productos.append({
                "id": doc.id,
                "existencia": 0,  # siempre empieza en 0
                "unidad": data.get("unidad", "")
            })

        inventario[sub.id] = productos

    return inventario

def obtener_inventario_base_2(db,negocio_id,sucursal):
    inventario = {}

    subcols = (
        inventario_ref_2(db,negocio_id,sucursal,'base')
          .collections()
    )

    for sub in subcols:
        productos = []
        for doc in sub.stream():
            data = doc.to_dict()
            if doc.id == "init":
                continue

            productos.append({
                "id": doc.id,
                "existencia": 0,  # siempre empieza en 0
                "unidad": data.get("unidad", "")
            })

        inventario[sub.id] = productos

    return inventario
def obtener_inventario_mas_reciente(db,negocio_id):
    docs = (
        inventarios_collection_ref(db,negocio_id)
        .order_by("created_at", direction=firestore.Query.DESCENDING)
        .limit(1)
        .stream()
    )

    for doc in docs:
        return doc.id  # nombre del documento (ej: "2026-01-06-cerritos")

    return None
def obtener_inventario_mas_reciente_2(db,negocio_id,sucursal):
    docs = (
        inventarios_collection_ref_2(db,negocio_id,sucursal)
        .order_by("created_at", direction=firestore.Query.DESCENDING)
        .limit(1)
        .stream()
    )

    for doc in docs:
        return doc.id  # nombre del documento (ej: "2026-01-06-cerritos")

    return None
#Eliminar
def eliminar_producto_base(db,negocio_id:str, subcoleccion: str, producto_id: str):
    """
    Elimina un producto específico de la colección 'base'
    """
    ref = inventario_ref(db,negocio_id,'base')\
            .collection(subcoleccion) \
            .document(producto_id)

    if not ref.get().exists:
        raise ValueError("El producto no existe")

    ref.delete()

#Eliminar subcolecciones
def eliminar_subcoleccion(db, negocio_id:str,subcoleccion: str):
    """
    Elimina una subcolección solo si contiene únicamente el documento 'init'
    db:database
    subcoleccion: subcoleccion a eliminar
    """
    ref = (
        inventario_ref(db,negocio_id,'base')
          .collection(subcoleccion)
    )

    docs = list(ref.stream())

    # Solo debe existir el doc "init"
    if len(docs) != 1 or docs[0].id != "init":
        raise ValueError("La categoría no está vacía")

    # Borrar el documento init
    ref.document("init").delete()

def crear_usuario(db,negocio_id,usuario,nombre,password,rol):
    '''
    Docstring for crear usuario
    '''
    password_hash = hash_password(password)
    ref = (
        negocio_ref(db, negocio_id)
        .collection("usuarios")
        .document(usuario)
    )

    if ref.get().exists:
        raise ValueError("El usuario ya existe")

    ref.set({
        "usuario": usuario,
        "nombre": nombre,
        "password": password_hash,
        "rol": rol,
        "activo": True,
        "created_at": firestore.SERVER_TIMESTAMP
    })
    
def obtener_empleados(db, negocio_id):
    ref = (
        negocio_ref(db, negocio_id)
        .collection("usuarios")
        .where(filter=FieldFilter("rol", "==", "empleado"))
        .where(filter=FieldFilter("activo", "==", True))
        .stream()
    )

    usuarios = []
    for doc in ref:
        data = doc.to_dict() or {}
        usuarios.append({
            "usuario": doc.id,
            "nombre": data.get("nombre"),
            "rol": data.get("rol")
        })

    return usuarios

#Expansion del proyecto
#Regresa el id del negocio
def negocio_ref(db, negocio_id):
    return db.collection("negocios").document(negocio_id)
#Regresa el inventario que se necesita
def inventario_ref(db, negocio_id, inventario_id="base"):
    return (
        negocio_ref(db, negocio_id)
        .collection("inventarios")
        .document(inventario_id)
    )
def inventario_ref_2(db,negocio_id,sucursal,inventario_id='base'):
    return(
        negocio_ref(db,negocio_id)
        .collection('sucursales')
        .document(sucursal)
        .collection('inventarios')
        .document(inventario_id)
    )

def inventarios_collection_ref(db, negocio_id):
    return (
        negocio_ref(db, negocio_id)
        .collection("inventarios")
    )
def inventarios_collection_ref_2(db,negocio_id,sucursal):
    return(
        negocio_ref(db,negocio_id)
        .collection('sucursales')
        .document(sucursal)
        .collection('inventarios')
    )
def autenticar_usuario(db, negocio_id, usuario, password):
    ref = (
        db.collection("negocios")
          .document(negocio_id)
          .collection("usuarios")
          .document(usuario)
    )

    doc = ref.get()
    if not doc.exists:
        return None

    data = doc.to_dict()

    if not verify_password(password, data["password"]):
        return None

    return {
        "usuario": data["usuario"],
        "nombre": data["nombre"],
        "rol": data["rol"],
        'activo':data['activo']
    }
    
def crear_sucursal(db,negocio_id,sucursal,encargado):
    '''
    Docstring for crear_producto
    
    :param db: Description
    :param subcoleccion: Description
    :param producto: Description
    '''
    negocio_ref(db,negocio_id)\
      .collection('sucursales') \
      .document(sucursal) \
      .set({
          "sucursal": sucursal,
          'encargado':encargado
      })

def lista_sucursales(db,negocio_id):
    '''
    Docstring for lista_sucursales
    
    :param db: Description
    :param negocio_id: Description
    '''
    ref = (
        negocio_ref(db, negocio_id)
        .collection("sucursales")
        .stream()
    )

    usuarios = []
    for doc in ref:
        data = doc.to_dict() or {}
        usuarios.append({
            "sucursal": doc.id,
            'encargado':data.get('engargado')
        })

    return usuarios

def inventario_a_texto(fecha,sucursal,elaborador,notas,inventario: dict) -> str:

    lineas = []

    lineas.append(f'{fecha}  {sucursal}')
    lineas.append(f'Elaborado por: {elaborador}')
    lineas.append(f'Notas: {notas}')
    lineas.append("")

    for categoria, productos in inventario.items():

        lineas.append(f"CATEGORIA: {categoria.upper()}")
        lineas.append("-" * 40)

        for p in productos:

            linea = (
                f"Producto: {p['producto']}\n"
                f"Existencia: {p['existencia']} {p['unidad']}\n"
            )

            if p["urge"]:
                linea += "⚠ URGE\n"

            lineas.append(linea)

        lineas.append("")
    resultado="\n".join(lineas)
    return resultado

def crear_pdf_inventario(info: str, ruta_pdf: str):

    margen_x = 50
    margen_superior = 60
    margen_inferior = 60

    max_chars = 85

    c = canvas.Canvas(ruta_pdf, pagesize=letter)

    width, height = letter

    y = height - margen_superior

    def nueva_pagina():
        nonlocal y
        c.showPage()
        y = height - margen_superior

    def escribir_linea(texto, font, size, salto):

        nonlocal y

        c.setFont(font, size)

        lineas = wrap(texto, max_chars) if texto else [""]

        for linea in lineas:

            if y <= margen_inferior:
                nueva_pagina()
                c.setFont(font, size)

            c.drawString(margen_x, y, linea)

            y -= salto

    lineas = info.split("\n")
    primera_categoria = True

    for i, linea in enumerate(lineas):

        linea = linea.strip()

        if i == 0:
            escribir_linea(linea, "Courier-Bold", 22, 30)

        elif linea.startswith("Elaborado por"):
            escribir_linea(linea, "Courier", 16, 24)

        elif linea.startswith("Notas"):
            escribir_linea(linea, "Courier", 16, 24)

        elif linea.startswith("CATEGORIA"):
            if not primera_categoria:
                nueva_pagina()

            primera_categoria = False
            escribir_linea("", "Courier", 10, 10)
            escribir_linea(linea, "Courier-Bold", 18, 26)

        elif linea.startswith("----"):
            escribir_linea(linea, "Courier", 14, 20)

        elif linea.startswith("Producto"):
            escribir_linea(linea, "Courier", 16, 22)

        elif linea.startswith("Existencia"):
            escribir_linea(linea, "Courier", 16, 22)

        elif "URGE" in linea:
            escribir_linea(linea, "Courier-Bold", 16, 22)

        else:
            escribir_linea(linea, "Courier", 16, 22)

    c.save()

#Primero tenemos que crear una contrasena de aplicaciones en el gmail
def enviar_correo(email,contra,recipent,info,ruta_pdf):
    mensaje=MIMEMultipart()  #De aqui a la linea 11 comienza la configuracion del correo
    mensaje['From']=email
    mensaje['To']=recipent
    mensaje['Subject']='Envio de inventario'  #Asunto
    #Adjuntar una imagen al correooooo
    body=f"""\
    <html>
        <body>
            <h1>Correo desde Python</h1>
            <p>{info}</p>
        </body>
    </html>
    """
    mensaje.attach(MIMEText(body,'html')) #Este es plain porque es solo texto, pero lo puedo poner como html
    # Adjuntar PDF
    with open(ruta_pdf, "rb") as archivo:
        parte = MIMEBase("application", "octet-stream")
        parte.set_payload(archivo.read())
    encoders.encode_base64(parte)

    parte.add_header(
        "Content-Disposition",
        "attachment",
        filename= ruta_pdf,
    )

    mensaje.attach(parte)
    
    smtp_server=smtplib.SMTP('smtp.gmail.com',587)  #Servidor de gmail
    smtp_server.starttls()
    smtp_server.login(email,contra)  #iniciar sesion
    smtp_server.sendmail(email,recipent,mensaje.as_string())
    smtp_server.quit()
    print('Email enviado')

#Ojo, si quiero mandarlo masivo pues puedo hacer una funcion o en recipients hago una lista con todos los correos
#recipients=[]
#mensaje['To']=','.join(recipients)
#smtp_server.sendmail(email,recipients,mensaje.as_string()) 
#obtener_datos(DB)
#print(obtener_carne(DB))
#crear_subcoleccion(DB,'desechable')
#crear_subcoleccion(DB,'sams')
#crear_subcoleccion(DB,'carne')
#crear_subcoleccion(DB,'refresco')
#crear_subcoleccion(DB,'verdura')
#crear_subcoleccion(DB,'tortillas_queso')
#crear_producto(DB,'desechable','contenedor 7x7')
#print(obtener_inventario_base(DB))
#crear_inventario(DB,'Prueba','Jorge','Cerritos','Sin nota')
#print(obtener_inventario_completo(DB,'Prueba6-cerritos'))
#crear_usuario(DB,'Jorge03','Jorge Almazan','prueba','admin')
#print(obtener_empleados(DB))
#crear_subcoleccion(DB,'prueba subcoleccion',NEGOCIO_ID)
#crear_producto(DB,'prueba subcoleccion','prueba producto','prueba unidad',NEGOCIO_ID)
#agregar_producto_inventario(DB,NEGOCIO_ID,'Prueba dia','Prueba subcoleccion','Prueba producto',10,'kg')
#crear_nuevo_inventario(DB,'Prueba fecha2','Prueba elaborado2',NEGOCIO_ID,'Prueba sucursal2','Prueba notas2')
#print(obtener_lista_inventarios(DB,NEGOCIO_ID))
#print(obtener_productos(DB,'Prueba subcoleccion',NEGOCIO_ID,'Prueba fecha-Prueba sucursal'))
#print(obtener_inventario_completo(DB,NEGOCIO_ID,'Prueba fecha-Prueba sucursal'))
#print(obtener_inventario_base(DB,NEGOCIO_ID))
#print(obtener_inventario_mas_reciente(DB,NEGOCIO_ID))
#eliminar_producto_base(DB,NEGOCIO_ID,'ejemplo_categoria','ejemplo_producto')
#eliminar_subcoleccion(DB,NEGOCIO_ID,'ejemplo_categoria')
#crear_usuario(DB,NEGOCIO_ID,'Caro','Caro','Jorgito','empleado')
#print(obtener_empleados(DB,NEGOCIO_ID))
#editar_stocks(DB,NEGOCIO_ID,'salsas','salsa de anguila',4,100)
#crear_negocio(DB,'Prueba2id','Prueba2')
#agregar_existencia_producto(DB,NEGOCIO_ID,'salsas','salsa de anguila','10')
#crear_usuario(DB,'Adminsupreme','Adminsupremo03','Jorgito','Narnia2003','masteradmin')
#enviar_correo('kokkito03@gmail.com','cabc miyi oavo wxrm','carolinarly23@gmail.com','Pruebaaaaaaaaaaaa')
#inventario_prueba=obtener_inventario_completo(DB,NEGOCIO_ID,'15-02-2026-cerritos')
#info=inventario_a_texto(inventario_prueba)
#crear_subcoleccion_2(DB,'prueba subcoleccion',NEGOCIO_ID,'cerritos')
#crear_producto_2(DB,'prueba subcoleccion','prueba producto','kg',NEGOCIO_ID,'cerritos',10,100)
#crear_subcoleccion_3(DB,'subcoleccion para todos',NEGOCIO_ID)
#crear_producto_3(DB,'subcoleccion para todos','Caronini','piezas',NEGOCIO_ID,10,100)