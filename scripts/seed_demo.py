import os
import sys
from datetime import date, time

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.core.database import SessionLocal
from app.models.salas import Evento, Requerimientos, Sala, Solicitante, Solicitud


SALAS = (
    (1, 30),
    (2, 45),
    (3, 70),
)


DEMO_DATA = (
    {
        "solicitante": ("Ana", "Torres", "ana.torres@unison.mx", "6621000001", "Depto. de Letras"),
        "solicitud": (date(2026, 6, 18), time(9, 0), "pendiente"),
        "requerimientos": ("Teatro", True, False, False),
        "evento": ("Seminario de Posgrado", "Seminario con proyector y registro de asistentes", date(2026, 6, 22), time(8, 0), time(10, 0), 45, "seminario", "pendiente", [2]),
    },
    {
        "solicitante": ("Veronica", "Cruz", "v.cruz@unison.mx", "6621000002", "Depto. de Ciencias"),
        "solicitud": (date(2026, 6, 18), time(10, 0), "aprobada"),
        "requerimientos": ("Aula filas", True, False, True),
        "evento": ("Clase Medicina", "Clase con videoconferencia", date(2026, 6, 23), time(9, 0), time(11, 0), 25, "clase", "confirmado", [3]),
    },
    {
        "solicitante": ("Diana", "Morales", "diana.morales@gmail.com", "6621000003", "Empresa externa"),
        "solicitud": (date(2026, 6, 18), time(11, 0), "pendiente"),
        "requerimientos": ("U / Herradura", False, False, False),
        "evento": ("Clase Literatura", "Sesion externa de literatura", date(2026, 6, 26), time(9, 0), time(12, 0), 22, "clase", "pendiente", [2]),
    },
    {
        "solicitante": ("Sandra", "Lopez", "sandra.lopez@unison.mx", "6621000004", "Depto. de Economia"),
        "solicitud": (date(2026, 6, 19), time(8, 30), "rechazada"),
        "requerimientos": ("Teatro", True, True, False),
        "evento": ("Conferencia de Finanzas", "Conferencia con servicio de cafeteria", date(2026, 6, 26), time(13, 0), time(16, 0), 70, "conferencia", "cancelado", [3]),
    },
    {
        "solicitante": ("Roberto", "Silva", "rsilva@empresa.mx", "6621000005", "Empresa externa"),
        "solicitud": (date(2026, 6, 19), time(9, 30), "aprobada"),
        "requerimientos": ("Grupos de trabajo", True, False, True),
        "evento": ("Workshop de Innovacion", "Trabajo por equipos con pizarrones", date(2026, 6, 25), time(8, 0), time(12, 0), 35, "taller", "confirmado", [1]),
    },
    {
        "solicitante": ("Luis", "Ramos", "luis.ramos@unison.mx", "6621000006", "Direccion Academica"),
        "solicitud": (date(2026, 6, 19), time(10, 30), "aprobada"),
        "requerimientos": ("Mesa ejecutiva", True, False, True),
        "evento": ("Reunion de Decanos", "Reunion de coordinacion institucional", date(2026, 6, 24), time(12, 0), time(14, 0), 12, "reunion", "confirmado", [1]),
    },
    {
        "solicitante": ("Personal", "UNISON", "mantenimiento@unison.mx", "6621000007", "Universidad de Sonora"),
        "solicitud": (date(2026, 6, 20), time(8, 0), "aprobada"),
        "requerimientos": ("Mantenimiento", False, False, False),
        "evento": ("Mantenimiento preventivo", "Revision de equipo y cableado", date(2026, 6, 22), time(8, 0), time(12, 0), 2, "mantenimiento", "confirmado", [3]),
    },
)


def get_or_create_sala(db, numero_sala, capacidad):
    sala = db.get(Sala, numero_sala)
    if sala:
        sala.capacidad = capacidad
        return sala

    sala = Sala(numero_sala=numero_sala, capacidad=capacidad)
    db.add(sala)
    return sala


def get_or_create_solicitante(db, data):
    nombre, apellido, correo, telefono, institucion = data
    solicitante = db.query(Solicitante).filter(Solicitante.correo == correo).first()
    if not solicitante:
        solicitante = Solicitante(correo=correo)
        db.add(solicitante)

    solicitante.nombre = nombre
    solicitante.apellido = apellido
    solicitante.no_de_telefono = telefono
    solicitante.institucion = institucion
    return solicitante


def find_event(db, titulo, fecha):
    return db.query(Evento).filter(Evento.titulo == titulo, Evento.fecha == fecha).first()


def seed():
    db = SessionLocal()
    try:
        for numero_sala, capacidad in SALAS:
            get_or_create_sala(db, numero_sala, capacidad)
        db.flush()

        for item in DEMO_DATA:
            solicitante = get_or_create_solicitante(db, item["solicitante"])
            fecha_solicitud, hora_solicitud, estado_solicitud = item["solicitud"]
            acomodo, sonido, cafeteria, videoconferencia = item["requerimientos"]
            titulo, descripcion, fecha_evento, inicio, fin, asistentes, tipo, estado_evento, salas_ids = item["evento"]

            evento = find_event(db, titulo, fecha_evento)
            if not evento:
                solicitud = Solicitud(
                    fecha_solicitud=fecha_solicitud,
                    hora_de_solicitud=hora_solicitud,
                    estado=estado_solicitud,
                    solicitante=solicitante,
                )
                requerimientos = Requerimientos()
                evento = Evento(solicitud=solicitud, requerimientos=requerimientos)
                db.add(evento)
            else:
                solicitud = evento.solicitud or Solicitud(solicitante=solicitante)
                requerimientos = evento.requerimientos or Requerimientos()
                evento.solicitud = solicitud
                evento.requerimientos = requerimientos

            evento.solicitud.fecha_solicitud = fecha_solicitud
            evento.solicitud.hora_de_solicitud = hora_solicitud
            evento.solicitud.estado = estado_solicitud
            evento.solicitud.solicitante = solicitante

            evento.requerimientos.acomodo = acomodo
            evento.requerimientos.equipo_de_sonido = sonido
            evento.requerimientos.cafeteria = cafeteria
            evento.requerimientos.videoconferencia = videoconferencia

            evento.titulo = titulo
            evento.descripcion = descripcion
            evento.fecha = fecha_evento
            evento.hora_de_inicio = inicio
            evento.hora_de_termino = fin
            evento.no_de_asistentes = asistentes
            evento.tipo = tipo
            evento.estado_evento = estado_evento
            evento.salas = [db.get(Sala, sala_id) for sala_id in salas_ids]

        db.commit()
        print("Base de datos llenada con datos demo de MODD.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
