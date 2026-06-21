import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings

def enviar_correo_resolucion(to_email: str, estado: str, titulo_evento: str, dia: str, hora_inicio: str, hora_fin: str, comentario: str = ""):
    """
    Envía un correo de notificación simple y directo al usuario cuando su solicitud
    es aprobada o rechazada.
    """
    if not to_email:
        print("No se proporcionó correo para la solicitud. No se enviará notificación.")
        return

    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        print(f"ADVERTENCIA: Credenciales SMTP no configuradas. Correo simulado a {to_email} con estado {estado}.")
        return

    from_email = settings.FROM_EMAIL or settings.SMTP_USER

    # Determinar el asunto y mensaje base
    if estado == "aprobada":
        asunto = f"Solicitud Aprobada - {titulo_evento}"
        mensaje_texto = (
            f"Hola,\n\n"
            f"Tu solicitud para el evento '{titulo_evento}' ha sido APROBADA.\n\n"
            f"Detalles:\n"
            f"- Fecha: {dia}\n"
            f"- Horario: {hora_inicio} a {hora_fin}\n\n"
            f"Tu espacio en la agenda está confirmado.\n"
        )
    else:
        asunto = f"Solicitud Rechazada - {titulo_evento}"
        mensaje_texto = (
            f"Hola,\n\n"
            f"Tu solicitud para el evento '{titulo_evento}' ha sido RECHAZADA "
            f"por falta de disponibilidad u otros motivos administrativos.\n\n"
            f"Detalles de la solicitud original:\n"
            f"- Fecha: {dia}\n"
            f"- Horario: {hora_inicio} a {hora_fin}\n\n"
        )
        if comentario:
            mensaje_texto += f"Comentario adicional:\n{comentario}\n\n"

    mensaje_texto += "Saludos,\nAdministración de MODD."

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = asunto
    msg.attach(MIMEText(mensaje_texto, 'plain', 'utf-8'))

    try:
        # Algunos contenedores (como Render) fallan con IPv6 al contactar a Gmail (Errno 101)
        # La forma más segura de forzar IPv4 sin causar "Address family not supported" es 
        # filtrar los resultados de DNS temporalmente.
        import socket
        
        old_getaddrinfo = socket.getaddrinfo
        def ipv4_getaddrinfo(*args, **kwargs):
            responses = old_getaddrinfo(*args, **kwargs)
            return [r for r in responses if r[0] == socket.AF_INET]
            
        socket.getaddrinfo = ipv4_getaddrinfo
        
        try:
            if int(settings.SMTP_PORT) == 465:
                server = smtplib.SMTP_SSL(
                    settings.SMTP_SERVER, 
                    int(settings.SMTP_PORT), 
                    timeout=15
                )
            else:
                server = smtplib.SMTP(
                    settings.SMTP_SERVER, 
                    int(settings.SMTP_PORT), 
                    timeout=15
                )
                server.starttls()
                
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
            server.quit()
            print(f"Correo de resolución ({estado}) enviado a {to_email}")
        finally:
            # Restaurar el comportamiento normal de DNS
            socket.getaddrinfo = old_getaddrinfo
            
    except Exception as e:
        print(f"Error enviando correo a {to_email}: {str(e)}")

