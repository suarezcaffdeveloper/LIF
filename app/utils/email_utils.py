from flask_mail import Message
from flask import current_app
from app import mail
import smtplib
from email.mime.text import MIMEText
from ..models.models import Partido
from flask import render_template
from sqlalchemy import func

def enviar_mail_bienvenida(destinatario, nombre):
    asunto = "¡Bienvenido a la LigaInterprovincial de Futbol!"
    cuerpo = f"""
    Hola {nombre}, ¡bienvenido!

    Tu registro se realizó correctamente.
    Desde ahora ya podés acceder a la plataforma.

    Gracias por ser parte de la Liga Interprovincial de Futbol.
    
    """

    msg = Message(asunto, recipients=[destinatario])
    msg.body = cuerpo

    try:
        mail.send(msg)
        print("📧 Mail enviado correctamente a", destinatario)
        return True
    except Exception as e:
        print("❌ Error enviando mail:", e)
        return False
    
#--------------------------------------------------------------
#--------------------------------------------------------------
#--------------------------------------------------------------

def enviar_mail_periodista(destinatario, nombre, password):
    asunto = "Credenciales de acceso - Periodista"
    cuerpo = f"""
Hola {nombre},

Tu cuenta de periodista ha sido creada exitosamente.

📝 USUARIO: {destinatario}
🔐 CONTRASEÑA: {password}

Puedes iniciar sesión desde:
https://tusitio.com/login

No compartas esta información.

Saludos,
Administrador del Sistema
"""

    msg = Message(asunto, recipients=[destinatario])
    msg.body = cuerpo

    try:
        mail.send(msg)
        print("📧 Mail enviado correctamente a", destinatario)
        return True
    except Exception as e:
        print("❌ Error enviando mail:", e)
        return False
    
    
def jornada_completa(jornada, categoria):
    """
    Retorna True si todos los partidos existentes de la jornada están jugados
    en el TORNEO ACTIVO (Apertura).
    Solo considera la categoría indicada ('Mayores' o 'Inferiores').
    Normaliza categorías a minúsculas y sin espacios.
    """
    from ..models.models import Temporada, Torneo
    
    categoria = categoria.lower().strip()

    if categoria == "mayores":
        categorias_validas = ["primera", "reserva"]  # Solo mayores
    elif categoria == "inferiores":
        categorias_validas = ["quinta", "sexta", "septima"]  # Inferiores
    else:
        return False

    try:
        # 🔥 Obtener el torneo Apertura activo
        temporada_activa = Temporada.query.filter_by(activa=True).first()
        if not temporada_activa:
            print("⚠️ No hay temporada activa")
            return False

        torneo_activo = Torneo.query.filter_by(
            nombre="Apertura",
            temporada_id=temporada_activa.id
        ).first()
        
        if not torneo_activo:
            print("⚠️ No hay torneo Apertura en la temporada activa")
            return False

        # Traer partidos de la jornada para estas categorías (normalizando)
        partidos = Partido.query.filter(
            Partido.jornada == jornada,
            Partido.torneo_id == torneo_activo.id,
            func.lower(func.trim(Partido.categoria)).in_(categorias_validas)
        ).all()

        if not partidos:
            print(f"⚠️ No hay partidos de jornada {jornada} en el torneo activo para {categoria}")
            return False

        # Verificar que TODOS los partidos estén jugados
        todos_jugados = all(p.jugado for p in partidos)
        
        if todos_jugados:
            print(f"✅ Jornada {jornada} de {categoria} COMPLETA ({len(partidos)} partidos)")
        else:
            partidos_pendientes = [p.id for p in partidos if not p.jugado]
            print(f"⏳ Jornada {jornada} INCOMPLETA: Faltan {len(partidos_pendientes)} partidos: {partidos_pendientes}")
        
        return todos_jugados

    except Exception as e:
        print(f"❌ Error en jornada_completa(): {e}")
        return False

    
#--------------------------------------------------------------
#AUTOMATIZAR ENVIO DE MAIL CUANDO SE CARGA JORNADA
#--------------------------------------------------------------
def enviar_mail_jornada(usuarios, jornada, categoria):
    """
    Envia un mail a los usuarios notificando que se cargó la jornada.
    usuarios: lista de objetos Usuario con atributo email y nombre_completo
    jornada: número de la jornada
    categoria: 'Mayores' o 'Inferiores'
    """

    subject = f"Jornada {jornada} de {categoria} cargada"

    for u in usuarios:
        msg = Message(
            subject=subject,
            recipients=[u.email]
        )

        msg.body = (
            f"Hola {u.nombre_completo},\n\n"
            f"Se han cargado los resultados de la jornada {jornada} "
            f"de la categoría {categoria}.\n\n"
            f"Podés ver todos los detalles en la web.\n\n"
            f"¡Gracias por seguirnos!"
        )

        msg.html = render_template(
            "emails/jornada_cargada.html",
            nombre=u.nombre_completo,
            jornada=jornada,
            categoria=categoria
        )

        mail.send(msg)