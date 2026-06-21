import httpx
from app.core.config import settings

def enviar_correo_resolucion(to_email: str, estado: str, titulo_evento: str, dia: str, hora_inicio: str, hora_fin: str, comentario: str = ""):
    """
    Envía un correo mediante un Webhook de Google Apps Script.
    Esta es la técnica definitiva para usar tu propio Gmail personal
    desde Render sin que bloqueen los puertos y sin necesitar un dominio privado.
    """
    if not to_email:
        print("No se proporcionó correo para la solicitud.", flush=True)
        return

    # Usaremos la variable SMTP_SERVER o SMTP_PASSWORD para guardar la URL del Webhook
    # (La URL larga que te dará Google). Si no está, simulamos el correo.
    webhook_url = getattr(settings, "GOOGLE_SCRIPT_URL", settings.SMTP_SERVER)
    
    if not webhook_url or not webhook_url.startswith("https://script.google.com"):
        print(f"ADVERTENCIA: Webhook de Google no configurado. Correo simulado a {to_email} con estado {estado}.", flush=True)
        return

    # Determinar el asunto y mensaje base
    if estado == "aprobada":
        asunto = f"Solicitud Aprobada - {titulo_evento}"
        mensaje_texto = (
            f"Hola,\n\n"
            f"Tu solicitud para el evento '{titulo_evento}' ha sido APROBADA.\n\n"
            f"Detalles:\n"
            f"- Fecha: {dia}\n"
            f"- Horario: {hora_inicio} a {hora_fin}\n\n"
            f"Tu espacio en la agenda está confirmado.\n\n"
            f"Saludos,\nAdministración de MODD."
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

    payload = {
        "to_email": to_email,
        "subject": asunto,
        "body": mensaje_texto
    }

    try:
        print(f"Intentando enviar correo a {to_email} vía Google Apps Script...", flush=True)
        # Sigue las redirecciones porque Google Script siempre redirige la primera vez
        with httpx.Client(timeout=20.0, follow_redirects=True) as client:
            response = client.post(webhook_url, json=payload)
            
            if response.status_code == 200:
                print(f"Correo de resolución ({estado}) enviado a {to_email} exitosamente por Google.", flush=True)
            else:
                print(f"Google Script devolvió error HTTP {response.status_code}: {response.text}", flush=True)
                
    except Exception as e:
        print(f"Error enviando correo por Google Script a {to_email}: {str(e)}", flush=True)

