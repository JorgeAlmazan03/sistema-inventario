from datetime import datetime
from functools import wraps
from firebase_admin import credentials,firestore
from fastapi import FastAPI, Request,Body,HTTPException,Depends
from fastapi.responses import HTMLResponse,RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from funciones import DB, obtener_inventario_completo,eliminar_producto_base,crear_usuario,obtener_inventario_mas_reciente_2,obtener_penultimo_inventario
from funciones import eliminar_subcoleccion,copiar_inventario_base_a_sucursal,lista_negocios,eliminar_negocio
from funciones import obtener_empleados,inventario_ref,negocio_ref,autenticar_usuario,crear_sucursal,crear_negocio,enviar_correo
from funciones import inventario_a_texto,crear_pdf_inventario,crear_producto_3,crear_subcoleccion_3,editar_stocks_2,lista_sucursales,inventario_ref_2
from funciones import obtener_inventario_completo_2,agregar_existencia_producto_2,entrada_de_producto,eliminar_usuario,obtener_lista_inventarios_2
from pydantic import BaseModel
from typing import Dict, List,Optional
from security import hash_password
app = FastAPI(title="Agenda API")
app.add_middleware(
    SessionMiddleware,
    secret_key="Esta_clave_debe_Ser_seguraaa",
    session_cookie="session",
    max_age=60 * 60 * 24  # 1 día
)
templates = Jinja2Templates(directory="templates")
SESSION_TIMEOUT = 1800
class LoginPayload(BaseModel):
    negocio_id: str
    usuario: str
    password: str
    
class ProductoModel(BaseModel):
    producto:str
    existencia:float=0
    unidad:str
    urge:bool=False
    minimo:Optional[int]=None
    maximo:Optional[int]=None
    
class ProductoEntradaModel(BaseModel):
    producto: str
    entrada: float
    
class EntradaInventarioPayload(BaseModel):
    fecha: str
    notas: Optional[str] = None
    inventario: Dict[str, Dict[str, ProductoEntradaModel]]

class InventarioPayload(BaseModel):
    fecha: str
    sucursal: str
    notas: str
    inventario: Dict[str, Dict[str, ProductoModel]]

class UsuarioModel(BaseModel):
    usuario:str
    nombre:str
    password:str
    rol:str
class StockUpdate(BaseModel):
    minimo: Optional[int] = None
    maximo: Optional[int] = None
    unidad: Optional[str] = None
#Login
@app.get("/", response_class=HTMLResponse)
def vista_login(request: Request):
    return templates.TemplateResponse(
        "login.html",
        {
            "request": request
        }
    )
#Login
@app.post("/login")
def login(request: Request,payload: LoginPayload):
    user = autenticar_usuario(
        DB,
        payload.negocio_id,
        payload.usuario,
        payload.password
    )
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Credenciales inválidas"
        )
    doc=negocio_ref(DB,payload.negocio_id).get()
#    data=doc.to_dict()
#    if not data['activo']:
#        raise HTTPException(
#            status_code=401,
#            detail="Negocio inactivo, contacte a soporte"
#        )
    request.session.clear()
    # Guardar sesión
    request.session["negocio_id"] = payload.negocio_id
    request.session["usuario"] = user["usuario"]
    request.session["rol"] = user["rol"]
    request.session['nombre']=user['nombre']
    request.session["ultima_actividad"] = datetime.utcnow().timestamp()
    
    usuario_ref = (
        negocio_ref(DB, payload.negocio_id)
        .collection("usuarios")
        .document(user["usuario"])
    )

    usuario_ref.update({
        "ultimo_login": firestore.SERVER_TIMESTAMP
    })
    return {
        "mensaje": "Login correcto",
        "rol": request.session["rol"]
    }


def requiere_sesion(request: Request):
     if "negocio_id" not in request.session:
        raise HTTPException(status_code=401, detail="No autenticado")
    
     return request.session

def requiere_sesion_html(request: Request):

    session = request.session

    if "negocio_id" not in session:
        return RedirectResponse("/", status_code=302)

    ahora = datetime.utcnow().timestamp()
    ultima_actividad = session.get("ultima_actividad")

    if ultima_actividad and ahora - ultima_actividad > SESSION_TIMEOUT:
        request.session.clear()
        return RedirectResponse("/", status_code=302)

    session["ultima_actividad"] = ahora

    return session


def requiere_admin_api(request: Request):
    session = request.session

    if "negocio_id" not in session:
        raise HTTPException(status_code=401, detail="Sesión expirada")

    if session.get("rol") != "admin":
        raise HTTPException(
            status_code=403,
            detail="Acceso solo para administradores"
        )

    return session

def requiere_admin_html(request: Request):
    session = request.session

    if "negocio_id" not in session:
        return RedirectResponse("/", status_code=302)

    if session.get("rol") != "admin":
        return RedirectResponse("/inventario", status_code=302)

    return session

def requiere_maestro_html(request:Request):
    session = request.session

    if "negocio_id" not in session:
        return RedirectResponse("/", status_code=302)

    if session.get("rol") != "masteradmin":
        return RedirectResponse("/maestro", status_code=302)

    return session

def requiere_maestro(request:Request):
    session = request.session

    if "negocio_id" not in session:
        raise HTTPException(status_code=401, detail="Sesión expirada")

    if session.get("rol") != "masteradmin":
        raise HTTPException(
            status_code=403,
            detail="Que haces aqui?"
        )

    return session

def verificar_negocio_activo(db, negocio_id):
    negocio_ref = db.collection("negocios").document(negocio_id).get()

    if not negocio_ref.exists:
        raise HTTPException(status_code=404, detail="Negocio no encontrado")

    negocio = negocio_ref.to_dict()

    if not negocio.get("activo", True):
        raise HTTPException(
            status_code=403,
            detail="Este negocio está desactivado"
        )
        
def requiere_negocio_activo(func):
    @wraps(func)
    def wrapper(*args, **kwargs):

        session = kwargs.get("session")

        negocio_id = session["negocio_id"]

        verificar_negocio_activo(DB, negocio_id)

        return func(*args, **kwargs)

    return wrapper

#Logout
@app.post("/logout")
def logout(request: Request):
    request.session.clear()

    response = RedirectResponse("/", status_code=303)

    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    return response
#Pagina principal admins
@app.get("/inventario")
def apiPaginaPrincipal(request: Request, session=Depends(requiere_admin_html)):

    if isinstance(session, RedirectResponse):
        return session

    negocio_id = session["negocio_id"]
    sucursales = lista_sucursales(DB, negocio_id)
    doc = negocio_ref(DB, negocio_id).get()

    if not doc.exists:
        raise HTTPException(404, "Negocio no encontrado")

    negocio = doc.to_dict()
    activo = negocio.get("activo", True)
    inventario_general = {}

    for sucursal in sucursales:
        inventario_general[sucursal] = obtener_inventario_completo_2(
            DB,
            negocio_id,
            sucursal,
            "base"
        )

    return templates.TemplateResponse(
        "inventario.html",
        {
            "request": request,
            "inventario_general": inventario_general,
            "sucursales": sucursales,
            'negocio_activo':activo
        }
    )

#Pagina principal empleado
@app.get("/inventario-empleado")
def panel_inventario(
    request: Request,
    session=Depends(requiere_sesion_html)
):

    if isinstance(session, RedirectResponse):
        return session

    negocio_id = session["negocio_id"]

    sucursales = lista_sucursales(DB, negocio_id)

    return templates.TemplateResponse(
        "inventario_empleado.html",
        {
            "request": request,
            "sucursales": sucursales
        }
    )


@app.get('/productos')
@requiere_negocio_activo
def apiVerProductos(request: Request,session=Depends(requiere_admin_html)):
    if isinstance(session, RedirectResponse):
        return session
    
    negocio_id = session["negocio_id"]
    inventario = obtener_inventario_completo(DB,negocio_id,'base')
    sucursales = lista_sucursales(DB, negocio_id)

    return templates.TemplateResponse(
        "productos.html",
        {
            "request": request,
            "inventario": inventario,
            "negocio_id": negocio_id,
            "sucursales": sucursales
        }
    )
#Crear producto
@app.post("/inventario/base/producto/{subcoleccion}")
@requiere_negocio_activo
def apiAgregarProducto(
    subcoleccion: str,
    producto: str = Body(...),
    unidad: str = Body(...),
    minimo:str=Body(...),
    maximo:str=Body(...),
    session=Depends(requiere_admin_api)
):
    negocio_id = session["negocio_id"]
    producto_id=producto.lower()
    inventario_id='base'
    try:
        ref = (
            inventario_ref(DB,negocio_id,inventario_id)
              .collection(subcoleccion)
              .document(producto_id)
        )
#Validar que el producto todavia no exista
        if ref.get().exists:
            raise HTTPException(
                status_code=409,
                detail="El producto ya existe"
            )

        crear_producto_3(DB, subcoleccion, producto_id,unidad,minimo,maximo,negocio_id)

        return {
            "mensaje": "Producto creado correctamente",
            "subcoleccion": subcoleccion,
            "producto": producto_id
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stocks/completo")
def obtener_stocks_completos(session=Depends(requiere_admin_api)):
    negocio_id = session["negocio_id"]

    resultado = {}

    sucursales_ref = (
        negocio_ref(DB, negocio_id)
        .collection("sucursales")
        .stream()
    )

    for suc_doc in sucursales_ref:
        sucursal = suc_doc.id

        inventario_ref_suc = inventario_ref_2(DB, negocio_id, sucursal, "base")

        categorias = inventario_ref_suc.collections()

        for categoria_ref in categorias:
            categoria = categoria_ref.id

            if categoria not in resultado:
                resultado[categoria] = {}

            for producto_doc in categoria_ref.stream():
                producto = producto_doc.id
                data = producto_doc.to_dict() or {}

                if producto not in resultado[categoria]:
                    resultado[categoria][producto] = {}

                resultado[categoria][producto][sucursal] = {
                    "minimo": data.get("minimo", ""),
                    "maximo": data.get("maximo", ""),
                    "unidad": data.get("unidad", "")
                }

    return resultado
@app.put("/stocks/{subcoleccion}/{producto}/{sucursal}/inventario")
@requiere_negocio_activo
def apiEditarStock(
    subcoleccion: str,
    producto:str,
    sucursal:str,
    data:StockUpdate,
    session=Depends(requiere_admin_api)):
    negocio_id = session["negocio_id"]
    producto_id=producto.lower()
    inventario_id='base'
    try:
        ref = (
            inventario_ref(DB,negocio_id,inventario_id)
              .collection(subcoleccion)
              .document(producto_id)
        )
#Validar que el producto todavia no exista
        if not ref.get().exists:
            raise HTTPException(status_code=404, detail="Producto no existe")

        editar_stocks_2(
            DB,
            negocio_id,
            sucursal,
            subcoleccion,
            producto_id,
            data.minimo,
            data.maximo,
            data.unidad
        )

        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
#Render html para crear producto
@app.get("/inventario/base/crear-producto")
@requiere_negocio_activo
def vista_crear_producto(
    request: Request,
    inventario_id: str='base',
    session=Depends(requiere_admin_html),
):
    if isinstance(session, RedirectResponse):
        return session
    
    negocio_id = session["negocio_id"]
    inventario_id='base'
    return templates.TemplateResponse(
        "crear_producto.html",
        {
            "request": request,
            "negocio_id": negocio_id,
            "inventario_id": inventario_id
        }
    )

#Crear Subcoleccion
@app.post("/inventario_base/crear-subcoleccion")
@requiere_negocio_activo
def apiAgregarSubcoleccion(
    inventario_id:str='base',
    subcoleccion: str=Body(..., embed=True),
    session=Depends(requiere_admin_api)
):
    negocio_id = session["negocio_id"]
    inventario_id='base'
    try:
        ref = (
            inventario_ref(DB,negocio_id,inventario_id)
              .collection(subcoleccion)
        )
#Validar que la subcoleccion todavia no exista
        docs = list(ref.limit(1).stream())

        if docs:
            raise HTTPException(
                status_code=409,
                detail="La subcolección ya existe"
            )

        crear_subcoleccion_3(DB,subcoleccion,negocio_id)

        return {
            "mensaje": "Subcoleccion creada correctamente",
            "subcoleccion": subcoleccion,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
#Obtener subcolecciones
@app.get("/inventario_base/obtener-subcoleccion")
def listar_subcolecciones(session=Depends(requiere_sesion)):
    if isinstance(session, RedirectResponse):
        return session
    
    negocio_id = session["negocio_id"]
    inventario_id='base'
    try:
        colecciones = (
            inventario_ref(DB,negocio_id,inventario_id)
              .collections()
        )

        resultado = []
        for col in colecciones:
            resultado.append(col.id)

        return resultado

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

#Eliminar subcoleccion
@app.delete("/inventario_base/eliminar-subcoleccion/{subcoleccion}")
@requiere_negocio_activo
def apiEliminarSubcoleccion(subcoleccion: str,session=Depends(requiere_admin_api)):
    negocio_id = session["negocio_id"]
    try:
        eliminar_subcoleccion(DB, negocio_id,subcoleccion)

        return {
            "mensaje": "Categoría eliminada correctamente",
            "subcoleccion": subcoleccion
        }

    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

#Render crear subcoleccion
@app.get("/inventario/crear-subcoleccion")
@requiere_negocio_activo
def vista_crear_subcoleccion(
    request: Request,
    inventario_id='base',
    session=Depends(requiere_admin_html)
):
    if isinstance(session, RedirectResponse):
        return session
    
    negocio_id = session["negocio_id"]
    return templates.TemplateResponse(
        "crear_subcoleccion.html",
        {
            "request": request,
            "negocio_id": negocio_id,
            "inventario_id": inventario_id
        }
    )

#Crear hoja de inventario
@app.get("/inventario/nuevo")
@requiere_negocio_activo
def nuevo_inventario(
    request: Request,
    inventario_id: str = "base",
    session=Depends(requiere_sesion_html)
):
    if isinstance(session, RedirectResponse):
        return session
    
    negocio_id = session["negocio_id"]
    inventario = obtener_inventario_completo(DB, negocio_id, inventario_id)

    return templates.TemplateResponse(
        "hoja_inventario.html",
        {
            "request": request,
            "negocio_id": negocio_id,
            "inventario_id": inventario_id,
            "inventario": inventario,
            'rol':session['rol'],
            'nombre':session['nombre']
        }
    )

#Crear inventario
# Crear inventario usando la función existente

@app.post("/inventario/crear-inventario")
@requiere_negocio_activo
def api_crear_inventario(payload: InventarioPayload,session=Depends(requiere_sesion)):

    negocio_id = session["negocio_id"]
    sucursal=payload.sucursal.strip()
    sucursal_nombre = payload.sucursal.strip().lower().replace(" ", "-")
    elaborado_por = session['nombre']
    notas = payload.notas.strip()
    inventario = payload.inventario
    fecha_real = datetime.now().strftime("%d-%m-%Y")
    inventario_id = f"{fecha_real}-{sucursal_nombre}"

    doc_ref = inventario_ref_2(DB, negocio_id,sucursal, inventario_id)

    if doc_ref.get().exists:
        raise HTTPException(
            status_code=409,
            detail="Ya existe un inventario con esa fecha y sucursal"
        )

    # Crear inventario principal
    doc_ref.set({
        "fecha": fecha_real,
        "sucursal": sucursal,
        "elaborado_por": elaborado_por,
        "notas": notas,
        "activo": True,
        "created_at": firestore.SERVER_TIMESTAMP
    })
    comparaciones = {}
    # Subcolecciones y productos
    for subcoleccion, productos in inventario.items():
        
        if subcoleccion not in comparaciones:
            comparaciones[subcoleccion] = []

        
        for producto in productos.values():

            base_ref = (
                inventario_ref_2(DB, negocio_id, sucursal, 'base')
                .collection(subcoleccion)
                .document(producto.producto)
            )

            base_doc = base_ref.get()

            existencia_base_anterior = 0
            minimo = None

            if base_doc.exists:
                base_data = base_doc.to_dict()
                existencia_base_anterior = base_data.get("existencia", 0)
                minimo = base_data.get("minimo")

            se_acabo = existencia_base_anterior - producto.existencia

            comparaciones[subcoleccion].append({
                "id": producto.producto,
                "se_acabo": se_acabo
            })

            urge = minimo is not None and producto.existencia <= minimo + 1

            doc_ref.collection(subcoleccion).document(producto.producto).set({
                "producto": producto.producto,
                "existencia": producto.existencia,
                "unidad": producto.unidad,
                "urge": urge
            })

            agregar_existencia_producto_2(
                DB,
                negocio_id,
                sucursal,
                subcoleccion,
                producto.producto,
                producto.existencia
            )
                
    inventario=obtener_inventario_completo_2(DB,negocio_id,sucursal,inventario_id)
    print(inventario)
    print(comparaciones)
    info=inventario_a_texto(fecha_real,sucursal,elaborado_por,notas,inventario)
    
    ruta=f'{inventario_id}.pdf'
    crear_pdf_inventario(info,ruta)
    apiEnviarCorreo('Hola',ruta,session)
    return {
        "mensaje": "Inventario creado correctamente",
        "inventario_id": inventario_id
    }

#Ver ultimo inventario
@app.get("/inventario/{sucursal}/ultimo")
def ver_ultimo_inventario(
    request: Request,
    sucursal: str,
    session=Depends(requiere_sesion_html)
):

    if isinstance(session, RedirectResponse):
        return session

    negocio_id = session["negocio_id"]

    inventario_id = obtener_inventario_mas_reciente_2(DB, negocio_id, sucursal)

    if not inventario_id:
            return templates.TemplateResponse(
        "inventario_dia.html",
        {
            "request": request,
            "inventario": None,
            "dia": None,
            "mensaje": "No se encontró inventario para esta sucursal."
        }
    )

    inventario = obtener_inventario_completo_2(
        DB,
        negocio_id,
        sucursal,
        inventario_id
    )

    return templates.TemplateResponse(
        "inventario_dia.html",
        {
            "request": request,
            "inventario": inventario,
            "dia": inventario_id
        }
    )
#Obtener penultimo inventario
@app.get("/inventario/{sucursal}/penultimo")
def ver_penultimo_inventario(
    request: Request,
    sucursal: str,
    session=Depends(requiere_sesion_html)
):

    if isinstance(session, RedirectResponse):
        return session

    negocio_id = session["negocio_id"]

    inventario_id = obtener_penultimo_inventario(DB, negocio_id, sucursal)

    if not inventario_id:
        return templates.TemplateResponse(
                "inventario_dia.html",
                {
                    "request": request,
                    "inventario": None,
                    "dia": None,
                    "mensaje": "No se encontró inventario para esta sucursal."
                }
            )

    inventario = obtener_inventario_completo_2(
        DB,
        negocio_id,
        sucursal,
        inventario_id
    )

    return templates.TemplateResponse(
        "inventario_dia.html",
        {
            "request": request,
            "inventario": inventario,
            "dia": inventario_id
        }
    )
    
#Entrada de producto
@app.post('/inventario/{sucursal}/entrada')
@requiere_negocio_activo
def apiEntradaProducto(payload: EntradaInventarioPayload,sucursal:str,session=Depends(requiere_sesion)):
    negocio_id = session["negocio_id"]
    sucursal=sucursal.strip()
    inventario=payload.inventario
    
    for subcoleccion, productos in inventario.items():
        
        for producto in productos.values():

            entrada_de_producto(DB,
                                negocio_id,
                                sucursal,
                                subcoleccion,
                                producto.producto,
                                producto.entrada)

@app.get("/inventario/{sucursal}/entrada")
@requiere_negocio_activo
def EntradaSucursal(
    request: Request,
    sucursal:str,
    inventario_id: str = "base",
    session=Depends(requiere_sesion_html)
):
    if isinstance(session, RedirectResponse):
        return session
    
    negocio_id = session["negocio_id"]
    inventario = obtener_inventario_completo_2(DB, negocio_id,sucursal, inventario_id)
    if not inventario:
        raise HTTPException(status_code=404, detail="Sucursal no encontrada")
    return templates.TemplateResponse(
        "entrada.html",
        {
            "request": request,
            "negocio_id": negocio_id,
            "inventario_id": inventario_id,
            'sucursal':sucursal,
            "inventario": inventario,
            'rol':session['rol'],
            'nombre':session['nombre']
        }
    )

#Existencia productos
@app.get("/inventario/{sucursal}/existencia")
def ExistenciaSucursal(
    request: Request,
    sucursal:str,
    inventario_id: str = "base",
    session=Depends(requiere_sesion_html)
):
    if isinstance(session, RedirectResponse):
        return session
    
    negocio_id = session["negocio_id"]
    doc = negocio_ref(DB, negocio_id).get()

    if not doc.exists:
        raise HTTPException(404, "Negocio no encontrado")
    negocio = doc.to_dict()
    activo = negocio.get("activo", True)
    inventario = obtener_inventario_completo_2(DB, negocio_id,sucursal, inventario_id)
    if not inventario:
        raise HTTPException(status_code=404, detail="Sucursal no encontrada")
    return templates.TemplateResponse(
        "existencia.html",
        {
            "request": request,
            "negocio_id": negocio_id,
            "inventario_id": inventario_id,
            'sucursal':sucursal,
            "inventario": inventario,
            'rol':session['rol'],
            'nombre':session['nombre'],
            'negocio_activo':activo
        }
    )

#Lista de inventarios por sucursal
@app.get("/inventario/{sucursal}/historial")
def ver_historial_inventarios(
    request: Request,
    sucursal: str,
    session=Depends(requiere_admin_html)
):

    if isinstance(session, RedirectResponse):
        return session

    negocio_id = session["negocio_id"]

    inventarios = obtener_lista_inventarios_2(DB, negocio_id, sucursal)

    meses = [
        "Enero","Febrero","Marzo","Abril","Mayo","Junio",
        "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"
    ]

    inventarios_formateados = []

    for inv in inventarios:

        try:
            partes = inv.split("-")

            dia = int(partes[0])
            mes = int(partes[1])
            año = partes[2]

            fecha_formateada = f"{dia} de {meses[mes-1]} del {año}"

        except:
            fecha_formateada = inv

        inventarios_formateados.append({
            "id": inv,
            "fecha": fecha_formateada
        })

    return templates.TemplateResponse(
        "inventarios_lista.html",
        {
            "request": request,
            "inventarios": inventarios_formateados,
            "sucursal": sucursal
        }
    )
#Mostrar inventario por dia
@app.get("/inventario/{sucursal}/mostrar/{dia}")
def apiVerInventarioDia(dia:str,sucursal:str,request: Request,session=Depends(requiere_admin_html)):
    if isinstance(session, RedirectResponse):
        return session
    
    dia=dia.strip().lower()

    negocio_id = session["negocio_id"]
    inventario = obtener_inventario_completo_2(DB,negocio_id,sucursal,dia)
    if not inventario:
        raise HTTPException(
        status_code=404,
        detail="Inventario no encontrado"
    )
    return templates.TemplateResponse(
        "inventario_dia.html",
        {
            "request": request,
            "inventario": inventario,
            'dia':dia
        }
    )
@app.delete("/inventario/base/producto/{subcoleccion}/{producto_id}")
def eliminar_producto(
    subcoleccion: str,
    producto_id: str,
    session=Depends(requiere_admin_api)
):
    negocio_id = session["negocio_id"]
    try:
        eliminar_producto_base(DB,negocio_id,subcoleccion, producto_id)
        return {
            "status": "ok",
            "mensaje": f"Producto '{producto_id}' eliminado de '{subcoleccion}'"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@app.get("/administrativo")
@requiere_negocio_activo
def apiPanelAdministrativo(request: Request,session=Depends(requiere_admin_html)):
    if isinstance(session, RedirectResponse):
        return session
    
    negocio_id = session["negocio_id"]
    return templates.TemplateResponse(
        "administrativo.html",
        {
            "request": request,
            'negocio_id':negocio_id,
            'usuario_actual':session['usuario']

        }
    )
#Endpoint para crear usuario
@app.post('/administrativo/crear-usuario')
@requiere_negocio_activo
def apiCrearUsuario(usuario:UsuarioModel,session=Depends(requiere_admin_api)):
    negocio_id = session["negocio_id"]
    user=usuario.usuario.strip()
    nombre=usuario.nombre.strip()
    password=usuario.password
    rol=usuario.rol
    try:
        ref = (
            DB.collection("negocios")
              .document(negocio_id)
              .collection('usuarios')
              .document(user.lower())
        )
#Validar que el usuario no exista
        if ref.get().exists:
            raise HTTPException(
                status_code=409,
                detail="El usuario ya existe"
            )

        crear_usuario(DB,negocio_id,user,nombre,password,rol)
#Eliminar el usuario creado al momento de crear un usuario
        init=negocio_ref(DB,negocio_id).collection('usuarios').document('init')
        if init is not None:
            negocio_ref(DB,negocio_id).collection('usuarios').document('init').delete()
        return {
            "mensaje": "Producto creado correctamente",
            'usuario':usuario,
            'rol':rol
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
#Obtener usuarios
@app.get('/administrativo/usuarios-existentes')
def apiListarUsuarios(session=Depends(requiere_admin_api)):
    if isinstance(session, RedirectResponse):
        return session
    
    negocio_id = session["negocio_id"]
    try:
        return obtener_empleados(DB,negocio_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
#Reestablecer contra
@app.put("/administrativo/reset-password")
def apiResetearPassword(
    usuario: str = Body(...),
    nueva_password: str = Body(...),
    session=Depends(requiere_admin_api)
):
    negocio_id = session["negocio_id"]
    try:
        ref = (
            DB.collection("negocios")
              .document(negocio_id)
              .collection("usuarios")
              .document(usuario)
        )

        if not ref.get().exists:
            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado"
            )

        ref.update({
            "password": hash_password(nueva_password)
        })

        return {"mensaje": "Contraseña actualizada correctamente"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete('/administrativo/eliminar-usuario')
def apiBorrarUsuario(
    usuario: str,
    session = Depends(requiere_admin_api)
):

    negocio_id = session['negocio_id']
    usuario_actual = session['usuario']

    try:
        eliminar_usuario(DB, negocio_id, usuario, usuario_actual)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        'ok':True,
        "mensaje": "Usuario eliminado correctamente"}
#Obtener nombre sucursales
@app.get("/inventario_base/obtener-sucursales")
def listar_sucursales(session=Depends(requiere_sesion_html)):
    if isinstance(session, RedirectResponse):
        return session
    
    negocio_id = session["negocio_id"]
    try:
        suc_ref= (
            negocio_ref(DB,negocio_id)
              .collection('sucursales').stream()
        )

        resultado = []
        for suc in suc_ref:
            resultado.append(suc.id)

        return resultado

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/administrativo/configurar-correo")
def apiAgregarCorreo(correo:str=Body(...),
                     password:str=Body(...),
                     destino:str=Body(...),
                     session=Depends(requiere_admin_api)
):
    negocio_id=session['negocio_id']
    try:
        ref=(
            DB.collection('negocios')
            .document(negocio_id)
        )
        if not ref.get().exists:
            raise HTTPException(
                status_code=404,
                detail="Algo ha fallado"
            )
        update_data = {}

        if correo is not None:
            update_data['correo'] = correo
        if password is not None:
            update_data['password'] = password
        if destino is not None:
            update_data['destino'] = destino

        if not update_data:
            raise HTTPException(status_code=400, detail="No se enviaron datos para actualizar")

        ref.update(update_data)

        return {"mensaje": "Datos de correo actualizados"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
@app.get("/administrativo/configuracion-correo")
def obtenerConfiguracionCorreo(session=Depends(requiere_admin_api)):
    negocio_id = session['negocio_id']

    ref = DB.collection('negocios').document(negocio_id)
    doc = ref.get()

    if not doc.exists:
        raise HTTPException(status_code=404, detail="Negocio no encontrado")

    datos = doc.to_dict()

    return {
        "correo": datos.get("correo", ""),
        "destino": datos.get("destino", ""),
        'password':datos.get('password','')
    } 
@app.post('/function/enviar-correo')
def apiEnviarCorreo(mensaje:str,ruta_pdf:str,session=Depends(requiere_sesion)):
    negocio_id=session['negocio_id']
    ref=(DB.collection('negocios')
        .document(negocio_id))
    doc=ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Negocio no encontrado")        
    datos=doc.to_dict()
    user=datos.get('correo')
    password=datos.get('password')
    destino=datos.get('destino')
    if not user or not password or not destino:
        raise HTTPException(
            status_code=400,
            detail="Faltan datos de configuración de correo"
        )
    try:
        enviar_correo(user, password, destino, mensaje,ruta_pdf)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al enviar correo: {str(e)}"
        )

    return {"mensaje": "Correo enviado correctamente"}

#Crear sucursales
@app.post('/administrativo/crear-sucursal')
def apiCrearSucursal(sucursal:str=Body(...),encargado:str=Body(...),session=Depends(requiere_admin_api)):
    negocio_id = session["negocio_id"]
    try:
        ref = (
            negocio_ref(DB,negocio_id)
              .collection('sucursales')
              .document(sucursal)
        )
#Validar que el producto todavia no exista
        if ref.get().exists:
            raise HTTPException(
                status_code=409,
                detail="La sucursal ya existe"
            )

        crear_sucursal(DB,negocio_id,sucursal,encargado)
        #Inventario base
        inventario=obtener_inventario_completo(DB,negocio_id,'base')

        #Copiar el inventario base a la nueva sucursal
        copiar_inventario_base_a_sucursal(DB,negocio_id,sucursal,inventario)
        return {
                "mensaje": "Sucursal creada correctamente",
                "sucursal": sucursal,
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

#Template ver maestro
@app.get("/maestro")
def view_crear_negocio(request: Request, session=Depends(requiere_maestro_html)):
    if isinstance(session, RedirectResponse):
        return session
    negocios=lista_negocios(DB)
    return templates.TemplateResponse(
        'maestro_template.html',
        {'request':request,
         'negocios':negocios}
    )


#Crear negocio
@app.post('/madmin/crear-negocio')
def apiCrearNegocio(nombre:str=Body(...),negocio_id:str=Body(...),session=Depends(requiere_maestro)):

    try:
        negocio_ref=DB.collection('negocios').document(negocio_id)
        if negocio_ref.get().exists:
            raise HTTPException(
                status_code=409,
                detail="Ya existe un negocio con ese id")
        
        crear_negocio(DB,negocio_id,nombre)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor")

#Actualizar estado de negocio
@app.put('/madmin/actualizar-estado')
def actualizarEstado(
    negocio_id:str=Body(...),
    activo:bool=Body(...),
    session=Depends(requiere_maestro)
):

    data={'activo':activo}
    try:
        doc_ref=negocio_ref(DB,negocio_id)
    
        if not doc_ref.get().exists:
            raise HTTPException(status_code=404, detail="Producto no existe")

        doc_ref.set(data, merge=True)
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

#Eliminar negocio
@app.delete('/madmin/eliminar')
def eliminarNegocio(negocio_id:str=Body(...,embed=True),
                    session=Depends(requiere_maestro)):
    try:
        if negocio_id == "Adminsupreme":
            raise HTTPException(403, "No se puede eliminar este negocio")
        eliminar_negocio(DB,negocio_id)
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail='Error en el senvidor')    

@app.post("/debug")
async def debug_payload(request: Request):
    body = await request.json()
    return body