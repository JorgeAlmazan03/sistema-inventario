import firebase_admin
from firebase_admin import credentials, firestore

from dotenv import load_dotenv
import os

from security import hash_password,verify_password
from google.cloud.firestore_v1 import FieldFilter
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from textwrap import wrap

load_dotenv()

def get_firestore():
    if not firebase_admin._apps:
        cred_path = os.getenv("FIREBASE_CREDENTIALS")
        
        if not cred_path:
            raise Exception("FIREBASE_CREDENTIALS no está configurado")

        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)

    return firestore.client()

NEGOCIO_ID='Prueba1'

#Crear negocio
def crear_negocio(negocio_id,nombre):
    db = get_firestore()
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
        negocio_ref.collection('sucursales').document('init').set({
            'init':'init'
        })
    except Exception as e:
        raise e
        

#Crear nuevas subcolecciones en el inventario base
def crear_subcoleccion(subcoleccion,negocio_id):
    '''
    Docstring for crear_subcoleccion
    
    :param db: base de datos
    :param subcoleccion: nombre de la subcoleccion
    '''
    try:
        inventario_ref(negocio_id,'base') \
        .collection(subcoleccion) \
        .document("init") \
        .set({
            "producto": True
        })
    except Exception as e:
         return e

#Prueba 2
def crear_subcoleccion_2(subcoleccion,negocio_id,sucursal):
    '''
    Docstring for crear_subcoleccion
    
    :param db: base de datos
    :param subcoleccion: nombre de la subcoleccion
    '''
    try:
        inventario_ref_2(negocio_id,sucursal,'base') \
        .collection(subcoleccion) \
        .document("init") \
        .set({
            "producto": True
        })
    except Exception as e:
         return e


#Funcion final a utilizar
def crear_subcoleccion_3(subcoleccion,negocio_id,):
    '''
    Docstring for crear_subcoleccion
    
    :param db: base de datos
    :param subcoleccion: nombre de la subcoleccion
    '''
    try:
        sucursales_ref = (
            negocio_ref(negocio_id)
            .collection('sucursales')
        )

        sucursales = sucursales_ref.stream()

        for sucursal_doc in sucursales:

            sucursal_id = sucursal_doc.id

            inventario_ref_2(
                negocio_id,
                sucursal_id,
                'base'
            ).collection(subcoleccion) \
             .document("init") \
             .set({
                 "producto": True
             })
        crear_subcoleccion(subcoleccion,negocio_id)
    except Exception as e:
        return e

#Crear producto en el inventario base del producto
def crear_producto(subcoleccion,producto,unidad,negocio_id,minimo,maximo):
    '''
    Docstring for crear_producto
    
    :param db: Base de datos
    :param subcoleccion: Subcoleccion donde va el producto
    :param producto: nombre del producto
    :param unidad: unidad de medida
    :param negocio_id: id del negocio donde se guarda
    :minimo: stock minimo
    :maximo: stock maximo
    '''
    minimo=float(minimo)
    maximo=float(maximo)
    if maximo<=minimo:
        maximo=minimo+1
        
    inventario_ref(negocio_id,'base')\
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
def crear_producto_2(subcoleccion,producto,unidad,negocio_id,sucursal,minimo,maximo):
    '''
    Docstring for crear_producto
    
    :param db: Description
    :param subcoleccion: Description
    :param producto: Description
    '''
    minimo=float(minimo)
    maximo=float(maximo)
    inventario_ref_2(negocio_id,sucursal,'base')\
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

#Crea el producto en el inventario de todas las sucursales
def crear_producto_3(subcoleccion,producto,unidad,minimo,maximo,negocio_id):
    '''
    Docstring for crear_producto
    
    :param db: Description
    :param subcoleccion: Description
    :param producto: Description
    '''
    # Obtener todas las sucursales
    minimo=float(minimo)
    maximo=float(maximo)
    sucursales_ref = negocio_ref(negocio_id).collection('sucursales')
    sucursales = sucursales_ref.stream()
    for sucursal_doc in sucursales:
        sucursal_id=sucursal_doc.id
        inventario_base_ref=inventarios_collection_ref_2(
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
    crear_producto(subcoleccion,producto,unidad,negocio_id,minimo,maximo)
def agregar_producto_inventario(negocio_id,dia,subcoleccion,producto,existencia,unidad,urge=False):
    existencia=float(existencia)
    inventario_ref(negocio_id, inventario_id=dia)\
        .collection(subcoleccion)\
        .document(producto)\
        .set({
            'producto':producto,
            'existencia':existencia,
            'unidad':unidad,
            'urge':urge
        })

def agregar_producto_inventario_2(negocio_id,sucursal,dia,subcoleccion,producto,existencia,unidad,urge=False):
    existencia=float(existencia)
    inventario_ref_2(negocio_id,sucursal, inventario_id=dia)\
        .collection(subcoleccion)\
        .document(producto)\
        .set({
            'producto':producto,
            'existencia':existencia,
            'unidad':unidad,
            'urge':urge
        })

def agregar_existencia_producto_2(negocio_id,sucursal,subcoleccion,producto,existencia):
    '''
    Se agrega la existencia actual del producto
    :param db: Database
    :param negocio_id: Negocio id
    :param sucursal: Sucursal
    :param subcoleccion: Subcoleccion o categoria
    :param producto: Producto
    :param existencia: Existencia actual del producto
    '''
    inventario_ref_2(negocio_id,sucursal,'base')\
        .collection(subcoleccion)\
        .document(producto)\
        .update({'existencia':existencia})

def entrada_de_producto(negocio_id,sucursal,subcoleccion,producto,entrada:float):
    '''
    Al entrar un producto se suma con la existencia actual
    
    :param db: Database
    :param negocio_id: Id del negocio
    :param sucursal: Sucursal
    :param subcoleccion: Subcoleccion o categoria del producto
    :param producto: Producto
    :param entrada: Cantidad de producto que entra
    
    Actualiza la existencia de producto en el inventario base de la sucursal
    '''
    producto_ref=inventario_ref_2(negocio_id,sucursal,'base')\
        .collection(subcoleccion)\
        .document(producto)
    doc=producto_ref.get()
    if not doc.exists:
        return None
    prod_dic = doc.to_dict()
    existencia=prod_dic['existencia']
    total=existencia+entrada
    producto_ref.update({'existencia':total})
    
def comparar_existencia_con_inventario(negocio_id,sucursal,subcoleccion,producto,dia):
    base_ref=(inventario_ref_2(negocio_id,sucursal)
    .collection(subcoleccion)
    .document(producto)
    .get())
    if not base_ref.exists:
        return None
    base=base_ref.to_dict()
    existencia_base=base['existencia']
    
    inventario_actual_ref=(inventario_ref_2(negocio_id,sucursal,dia)
                           .collection(subcoleccion)
                           .document(producto)
                           .get())
    if not inventario_actual_ref.exists:
        return None
    inventario_actual=inventario_actual_ref.to_dict()
    existencia_inventario=inventario_actual['existencia']
    se_acabo=existencia_base-existencia_inventario
    return se_acabo
    
def comparar_inventario_completo(negocio_id,sucursal,dia):
    inventario_base=obtener_inventario_base_2(negocio_id,sucursal)
    inventario_actual=obtener_inventario_completo_2(negocio_id,sucursal,dia)
    
    resultado={}
    
    for subcoleccion,productos_base in inventario_base.items():
        resultado[subcoleccion]=[]
        productos_actual_dict = {
            p["id"]: p
            for p in inventario_actual.get(subcoleccion, [])
        }
        for producto_base in productos_base:

            producto_id = producto_base["id"]
            existencia_base = producto_base.get("existencia", 0)
            producto_actual = productos_actual_dict.get(producto_id)
            existencia_actual = 0
            if producto_actual:
                existencia_actual = producto_actual['existencia']
            se_acabo = existencia_base - existencia_actual
            resultado[subcoleccion].append({
                "id": producto_id,
                "se_acabo": se_acabo
            })

    return resultado
def crear_nuevo_inventario(fecha,elaborado_por,negocio_id,sucursal,notas=''):
    '''
    db:database
    fecha:fecha de elaboracion
    elaborado_por:quien lo hizo
    sucursal:sucursal
    notas:nota opcional
    '''

    nombre_documento = f"{fecha}-{sucursal}"
    nuevo_ref = inventario_ref(negocio_id, inventario_id=nombre_documento)
    
    nuevo_ref.set({
    "fecha": fecha,
    "elaborado_por": elaborado_por,
    "sucursal": sucursal,
    "notas": notas,
    "created_at": firestore.SERVER_TIMESTAMP
}) 
    return nuevo_ref

def crear_nuevo_inventario_2(fecha,elaborado_por,negocio_id,sucursal,notas=''):
    '''
    db:database
    fecha:fecha de elaboracion
    elaborado_por:quien lo hizo
    sucursal:sucursal
    notas:nota opcional
    '''

    nombre_documento = f"{fecha}-{sucursal}"
    nuevo_ref = inventario_ref_2(negocio_id,sucursal,inventario_id=nombre_documento)
    
    nuevo_ref.set({
    "fecha": fecha,
    "elaborado_por": elaborado_por,
    "sucursal": sucursal,
    "notas": notas,
    "created_at": firestore.SERVER_TIMESTAMP
}) 
    return nuevo_ref

def editar_stocks(negocio_id,subcoleccion,producto,minimo,maximo,unidad):
    data={}
    
    if minimo is not None:
        data["minimo"] = minimo
    if maximo is not None:
        data["maximo"] = maximo
    if unidad is not None:
        data["unidad"] = unidad

    if not data:
        return
    sucursales=lista_sucursales(negocio_id)
    for sucursal in sucursales:
        inventario_ref_2(negocio_id,sucursal,'base')\
        .collection(subcoleccion) \
        .document(producto) \
        .update(data)

def editar_stocks_2(negocio_id,sucursal,subcoleccion,producto,minimo,maximo,unidad):
    data={}
    if maximo<=minimo:
        maximo=minimo+1
    if minimo is not None:
        data["minimo"] = minimo
    if maximo is not None:
        data["maximo"] = maximo
    if unidad is not None:
        data["unidad"] = unidad

    if not data:
        return
    
    doc_ref = (
        inventario_ref_2(negocio_id, sucursal, 'base')
            .collection(subcoleccion)
            .document(producto)
    )

    #Crea si no existe, actualiza si ya existe
    doc_ref.set(data, merge=True)

def obtener_lista_inventarios(negocio_id):
    inventarios_ref = inventario_ref(negocio_id).parent.stream()
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

def obtener_lista_inventarios_2(negocio_id,sucursal):
    inventarios_ref = inventario_ref_2(negocio_id,sucursal).parent.stream()
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
def obtener_productos(subcoleccion,negocio_id,dia:str):
    '''
    Docstring for obtener_productos
    
    :param db: Database
    :param subcoleccion: Subcoleccion de firebase
    '''
    subcoleccion_ref = (
        inventario_ref(negocio_id,dia)  #Id del dia del inventario
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
            "existencia": data.get("existencia", "0"),
            'unidad':data.get('unidad','Unidades'),
            'urge':data.get('urge',False),
            'minimo':data.get('minimo',0),
            'maximo':data.get('maximo',1000)
        })

    return productos

def obtener_productos_2(subcoleccion,negocio_id,sucursal,dia:str):
    '''
    Docstring for obtener_productos
    
    :param db: Database
    :param subcoleccion: Subcoleccion de firebase
    '''
    subcoleccion_ref = (
        inventario_ref_2(negocio_id,sucursal,dia)  #Id del dia del inventario
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
            "existencia": data.get("existencia", 0),
            'unidad':data.get('unidad','Unidades'),
            'urge':data.get('urge',False),
            'minimo':data.get('minimo',0),
            'maximo':data.get('maximo',1000)
        })

    return productos

def obtener_inventario_completo(negocio_id,dia):
    base_ref = inventario_ref(negocio_id,dia)

    inventario = {}

    for col in base_ref.collections():
        productos = obtener_productos(col.id,negocio_id,dia)
        inventario[col.id] = productos

    return inventario
def obtener_inventario_completo_2(negocio_id,sucursal,dia):
    base_ref = inventario_ref_2(negocio_id,sucursal,dia)

    inventario = {}

    for col in base_ref.collections():
        productos = obtener_productos_2(col.id,negocio_id,sucursal,dia)
        inventario[col.id] = productos

    return inventario
def obtener_inventario_base(negocio_id):
    inventario = {}

    subcols = (
        inventario_ref(negocio_id,'base')
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

def obtener_inventario_base_2(negocio_id,sucursal):
    inventario = {}

    subcols = (
        inventario_ref_2(negocio_id,sucursal,'base')
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
                "existencia": data.get('existencia',0),  
                "unidad": data.get("unidad", ""),
                'minimo':data.get('minimo','')
            })

        inventario[sub.id] = productos

    return inventario



def obtener_inventario_mas_reciente(negocio_id):
    docs = (
        inventarios_collection_ref(negocio_id)
        .order_by("created_at", direction=firestore.Query.DESCENDING)
        .limit(1)
        .stream()
    )

    for doc in docs:
        return doc.id  # nombre del documento (ej: "2026-01-06-cerritos")

    return None
def obtener_inventario_mas_reciente_2(negocio_id,sucursal):
    docs = (
        inventarios_collection_ref_2(negocio_id,sucursal)
        .order_by("created_at", direction=firestore.Query.DESCENDING)
        .limit(1)
        .stream()
    )

    for doc in docs:
        return doc.id  # nombre del documento (ej: "2026-01-06-cerritos")

    return None

def obtener_penultimo_inventario(negocio_id, sucursal):

    docs = (
        inventarios_collection_ref_2(negocio_id, sucursal)
        .order_by("created_at", direction=firestore.Query.DESCENDING)
        .limit(2)
        .stream()
    )

    docs = list(docs)

    if len(docs) < 2:
        return None

    return docs[1].id

#Eliminar
def eliminar_producto_base(negocio_id:str, subcoleccion: str, producto_id: str):
    """
    Elimina un producto específico de la colección 'base'
    """
    ref = inventario_ref(negocio_id,'base')\
            .collection(subcoleccion) \
            .document(producto_id)
    
    if not ref.get().exists:
        raise ValueError("El producto no existe")

    ref.delete()
    
    sucursales_ref = negocio_ref(negocio_id).collection('sucursales')
    sucursales = sucursales_ref.stream()
    for sucursal_doc in sucursales:
        sucursal_id=sucursal_doc.id
        inventario_base_ref=inventarios_collection_ref_2(
            negocio_id,
            sucursal_id
        ).document('base')

        inventario_base_ref.collection(subcoleccion).document(producto_id).delete()

#Eliminar subcolecciones
def eliminar_subcoleccion(negocio_id:str,subcoleccion: str):
    """
    Elimina una subcolección solo si contiene únicamente el documento 'init'
    db:database
    subcoleccion: subcoleccion a eliminar
    """
    ref = (
        inventario_ref(negocio_id,'base')
          .collection(subcoleccion)
    )

    docs = list(ref.stream())

    # Solo debe existir el doc "init"
    if len(docs) != 1 or docs[0].id != "init":
        raise ValueError("La categoría no está vacía")

    # Borrar el documento init
    ref.document("init").delete()
    
    sucursales_ref = negocio_ref(negocio_id).collection('sucursales')
    sucursales = sucursales_ref.stream()
    for sucursal_doc in sucursales:
        sucursal_id=sucursal_doc.id
        inventario_base_ref=inventarios_collection_ref_2(
            negocio_id,
            sucursal_id
        ).document('base').collection(subcoleccion)

        inventario_base_ref.document('init').delete()

def crear_usuario(negocio_id,usuario,nombre,password,rol):
    '''
    Docstring for crear usuario
    '''
    password_hash = hash_password(password)
    ref = (
        negocio_ref(negocio_id)
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
    
def copiar_inventario_base_a_sucursal(negocio_id, sucursal, inventario_base):

    base_ref = inventario_ref_2(negocio_id, sucursal)

    for categoria, productos in inventario_base.items():

        categoria_ref = base_ref.collection(categoria)

        for prod in productos:

            categoria_ref.document(prod["id"]).set({
                "existencia": 1,
                "unidad": prod["unidad"],
                "urge": False,
                "producto": prod["producto"],
                "minimo": 0,
                "maximo": 10
            })
def obtener_empleados(negocio_id):
    ref = (
        negocio_ref(negocio_id)
        .collection("usuarios")
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
def negocio_ref(negocio_id):
    db = get_firestore()
    return db.collection("negocios").document(negocio_id)
#Regresa el inventario que se necesita
def inventario_ref(negocio_id, inventario_id="base"):
    return (
        negocio_ref(negocio_id)
        .collection("inventarios")
        .document(inventario_id)
    )
def inventario_ref_2(negocio_id,sucursal,inventario_id='base'):
    return(
        negocio_ref(negocio_id)
        .collection('sucursales')
        .document(sucursal)
        .collection('inventarios')
        .document(inventario_id)
    )

def inventarios_collection_ref(negocio_id):

    return (
        negocio_ref(db, negocio_id)
        .collection("inventarios")
    )
def inventarios_collection_ref_2(negocio_id,sucursal):
    return(
        negocio_ref(negocio_id)
        .collection('sucursales')
        .document(sucursal)
        .collection('inventarios')
    )
def autenticar_usuario(negocio_id, usuario, password):
    db = get_firestore()
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
    
def crear_sucursal(negocio_id,sucursal,encargado):
    '''
    Docstring for crear_producto
    
    :param db: Description
    :param subcoleccion: Description
    :param producto: Description
    '''
    sucursales=lista_sucursales(negocio_id)
    negocio_ref(negocio_id)\
      .collection('sucursales') \
      .document(sucursal) \
      .set({
          "sucursal": sucursal,
          'encargado':encargado
      })
    for sucursal in sucursales:
        if sucursal=='init':
            negocio_ref(negocio_id)\
            .collection('sucursales') \
            .document(sucursal) \
            .delete()
            break
def lista_sucursales(negocio_id):
    '''
    Docstring for lista_sucursales
    
    :param db: Description
    :param negocio_id: Description
    '''
    ref = (
        negocio_ref(negocio_id)
        .collection("sucursales")
        .stream()
    )
    return [doc.id for doc in ref]
def lista_negocios():
    '''
    Docstring for lista_negocios
    
    :param db: base de datos
    '''
    db = get_firestore()
    ref = db.collection('negocios').stream()

    negocios = []

    for doc in ref:
        if doc.id == 'Adminsupreme':
            continue

        data = doc.to_dict()

        negocios.append({
            'id': doc.id,
            'nombre': data.get('nombre'),
            'activo': data.get('activo', False)
        })

    return negocios


def inventario_a_texto(fecha, sucursal, elaborador, notas, inventario: dict) -> str:

    lineas = []

    # Encabezado
    lineas.append(f"{fecha}     SUCURSAL: {sucursal.upper()}")
    lineas.append(f"Elaborado por: {elaborador}")
    lineas.append(f"Notas: {notas}")
    lineas.append("=" * 55)
    lineas.append("")

    for categoria, productos in inventario.items():

        lineas.append(f"{categoria.upper()}")
        lineas.append("-" * 55)

        # Encabezados de tabla
        lineas.append(f"{'Producto':<20} {'Existencia':<15} {'Se acabó':<15}")
        lineas.append("-" * 55)

        for p in productos:

            producto = p["producto"][:20]
            existencia = f"{p['existencia']} {p['unidad']}"
            se_acabo = f"{p.get('se_acabo', 0)} {p['unidad']}"

            linea = f"{producto:<20} {existencia:<15} {se_acabo:<15}"

            if p.get("urge"):
                linea += "¡URGE!"

            lineas.append(linea)

        lineas.append("")

    return "\n".join(lineas)
def crear_pdf_inventario(info: str, ruta_pdf: str):

    margen_x = 50
    margen_superior = 60
    margen_inferior = 60

    max_chars = 95 

    c = canvas.Canvas(ruta_pdf, pagesize=letter)

    width, height = letter

    y = height - margen_superior

    def nueva_pagina():
        nonlocal y
        c.showPage()
        y = height - margen_superior
    def escribir_centrado(texto, font, size, salto):
        nonlocal y

        c.setFont(font, size)

        if y <= margen_inferior:
            nueva_pagina()
            c.setFont(font, size)

        text_width = c.stringWidth(texto, font, size)
        x = (width - text_width) / 2

        c.drawString(x, y, texto)
        y -= salto
    def escribir_linea(texto, font, size, salto):

        nonlocal y

        if y <= margen_inferior:
            nueva_pagina()

        c.setFont(font, size)

        # 🔥 IMPORTANTE: color después del cambio de página
        if "URGE" in texto:
            c.setFillColor(colors.red)
        else:
            c.setFillColor(colors.black)

        c.drawString(margen_x, y, texto)

        y -= salto
    lineas = info.split("\n")
    primera_categoria = True

    for i, linea in enumerate(lineas):

        linea = linea.strip()

        # Encabezado principal
        if i == 0:
            escribir_centrado(linea, "Courier-Bold", 22, 30)

        elif linea.startswith("Elaborado por"):
            escribir_linea(linea, "Courier", 16, 24)

        elif linea.startswith("Notas"):
            escribir_linea(linea, "Courier", 16, 24)

        # Categorías
        elif linea.isupper() and len(linea) < 30:
            if not primera_categoria:
                nueva_pagina()

            primera_categoria = False
            escribir_linea("", "Courier", 10, 10)
            escribir_linea(linea, "Courier-Bold", 18, 26)

        elif linea.startswith("----"):
            escribir_linea(linea, "Courier", 14, 20)

        # Producto
        elif "Producto" in linea and "Existencia" in linea:
            escribir_linea(linea, "Courier-Bold", 16, 22)

        elif linea.startswith("Existencia"):
            escribir_linea(linea, "Courier", 16, 22)

        # NUEVO: Se acabó
        elif linea.startswith("Se acabó"):
            escribir_linea(linea, "Courier", 16, 22)

        #URGE destacado
        elif "URGE" in linea:
            escribir_linea(linea, "Courier-Bold", 16, 22)

        else:
            escribir_linea(linea, "Courier", 16, 22)

    c.save()

def enviar_correo_backend(negocio_id, mensaje, ruta_pdf):

    db = get_firestore()
    ref = negocio_ref(negocio_id)
    doc = ref.get()
    if not doc.exists:
        raise Exception("Negocio no encontrado")

    datos = doc.to_dict()

    user = datos.get('correo')
    password = datos.get('password')
    destino = datos.get('destino')

    if not user or not password or not destino:
        raise Exception("Faltan datos de configuración de correo")
    enviar_correo(user, password, destino, mensaje, ruta_pdf)

#Primero tenemos que crear una contrasena de aplicaciones en el gmail
def enviar_correo(email,contra,recipent,info,ruta_pdf):
    try:
        mensaje=MIMEMultipart()  #De aqui a la linea 11 comienza la configuracion del correo
        mensaje['From']=email
        mensaje['To']=recipent
        mensaje['Subject']='Envio de inventario'  #Asunto
        #Adjuntar una imagen al correooooo
        body = f"""
        <html>
            <body>
                <h2>Inventario generado</h2>
                <p>{info}</p>
                <p>Adjunto encontrarás el inventario en PDF.</p>
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
            f'attachment; filename="{os.path.basename(ruta_pdf)}"'
        )
        mensaje.attach(parte)
        
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
                    smtp.login(email, contra)
                    smtp.send_message(mensaje)
    except Exception as e:
        print(e)
        raise e

#Eliminar usuario
#Eliminar
def eliminar_usuario(negocio_id: str, usuario: str, usuario_actual: str):

    usuarios_ref = (
        negocio_ref(negocio_id)
        .collection('usuarios')
    )

    usuario_ref = usuarios_ref.document(usuario)
    doc = usuario_ref.get()

    if not doc.exists:
        raise ValueError("El usuario no existe")

    data = doc.to_dict()

    # impedir eliminarse a sí mismo
    if usuario == usuario_actual:
        raise ValueError("No puedes eliminar tu propio usuario")

    # obtener todos los usuarios
    docs = usuarios_ref.stream()

    admins = []

    for d in docs:
        u = d.to_dict()
        if u.get("rol") == "admin":
            admins.append(d.id)

    # impedir eliminar último admin
    if data.get("rol") == "admin" and len(admins) == 1:
        raise ValueError("Debe existir al menos un administrador")

    usuario_ref.delete()
def eliminar_negocio(negocio_id):
    ref=negocio_ref(negocio_id)
    if not ref.get().exists:
        raise ValueError('El negocio no existe')
    ref.delete() 

