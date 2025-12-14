from flask_mail import Message
from flask import current_app
from app import mail
import smtplib
from email.mime.text import MIMEText

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