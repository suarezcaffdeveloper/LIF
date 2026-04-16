from flask_mail import Message
from flask import current_app
from app import mail
import smtplib
from email.mime.text import MIMEText
from ..models.models import Partido
from flask import render_template
from sqlalchemy import func

def enviar_mail_bienvenida(destinatario, nombre):
    """
    Envía un mail de bienvenida a un nuevo usuario registrado.
    """
    asunto = "Bienvenid@ a la Liga Interprovincial de Fútbol"
 
    msg = Message(asunto, recipients=[destinatario])
 
    # Fallback texto plano
    msg.body = (
        f"Hola {nombre}, ¡bienvenid@!\n\n"
        f"Tu registro en la Liga Interprovincial de Fútbol fue exitoso.\n"
        f"Ya podés acceder a la plataforma y seguir toda la acción de la liga:\n\n"
        f"  · Fixture y resultados\n"
        f"  · Tabla de posiciones\n"
        f"  · Goleadores y estadísticas\n"
        f"  · Noticias y videos\n\n"
        f"https://lif-1.onrender.com\n\n"
        f"Liga Interprovincial de Fútbol — Temporada 2026"
    )
 
    msg.html = render_template(
        "emails/bienvenida.html",
        nombre=nombre
    )
 
    try:
        mail.send(msg)
        print("📧 Mail enviado correctamente a", destinatario)
        return True
    except Exception as e:
        print("❌ Error enviando mail:", e)
        return False


# --------------------------------------------------------------
# --------------------------------------------------------------
# --------------------------------------------------------------

def enviar_mail_periodista(destinatario, nombre, password):
    """
    Envía las credenciales de acceso a un nuevo usuario periodista.
    """
    asunto = "Credenciales de acceso — Panel Periodista LIF"
 
    msg = Message(asunto, recipients=[destinatario])
 
    # Fallback texto plano
    msg.body = (
        f"Hola {nombre},\n\n"
        f"Tu cuenta de periodista en la Liga Interprovincial de Fútbol "
        f"fue creada exitosamente.\n\n"
        f"USUARIO: {destinatario}\n"
        f"CONTRASEÑA: {password}\n\n"
        f"Podés iniciar sesión desde:\n"
        f"https://lif-1.onrender.com/login\n\n"
        f"Importante: no compartas estas credenciales con nadie.\n\n"
        f"Liga Interprovincial de Fútbol — Temporada 2026"
    )
 
    msg.html = render_template(
        "emails/credenciales_periodista.html",
        nombre=nombre,
        destinatario=destinatario,
        password=password
    )
 
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
        categorias_validas = ["primera", "reserva"]
    elif categoria == "inferiores":
        categorias_validas = ["quinta", "sexta", "septima"]
    else:
        return False

    try:
        # Obtener el torneo Apertura activo
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


# --------------------------------------------------------------
# AUTOMATIZAR ENVIO DE MAIL CUANDO SE CARGA JORNADA
# --------------------------------------------------------------

def enviar_mail_jornada(usuarios, jornada, categoria):
    """
    Envía un mail a los usuarios notificando que se cargó la jornada.
    usuarios: lista de objetos Usuario con atributo email y nombre_completo
    jornada: número de la jornada
    categoria: 'Mayores' o 'Inferiores'
    """
    subject = f"⚽ Jornada {jornada} de {categoria} — Resultados disponibles"
 
    for u in usuarios:
        msg = Message(
            subject=subject,
            recipients=[u.email]
        )
 
        # Fallback texto plano
        msg.body = (
            f"Hola {u.nombre_completo},\n\n"
            f"Los resultados de la Jornada {jornada} de {categoria} "
            f"ya están disponibles en la plataforma.\n\n"
            f"Podés ver el fixture completo, la tabla de posiciones actualizada "
            f"y los goleadores desde:\n"
            f"https://lif-1.onrender.com\n\n"
            f"Liga Interprovincial de Fútbol — Temporada 2026"
        )
 
        msg.html = render_template(
            "emails/jornada_cargada.html",
            nombre=u.nombre_completo,
            jornada=jornada,
            categoria=categoria
        )
 
        mail.send(msg)