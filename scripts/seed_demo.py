import os
import sys
from datetime import date, time

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.core.database import SessionLocal
from app.models.salas import Evento, Requerimientos, Sala, Solicitante, Solicitud, sala_evento


SALAS = (
    (1, 30),
    (2, 45),
    (3, 70),
)


DEMO_DATA = (
    {
        "solicitante": ("Daniela", "Moreno", "daniela.moreno@unison.mx", "6621000001"),
        "solicitud": (date(2026, 6, 17), time(9, 0), "aprobada"),
        "requerimientos": ("Aula con filas", True, False, True),
        "evento": ("Clase de Bases de Datos", "Sesion practica con videoconferencia y equipo de sonido", date(2026, 6, 16), time(8, 0), time(10, 0), 28, [1]),
    },
    {
        "solicitante": ("Gabriel", "Mireles", "gabriel.mireles@unison.mx", "6621000002"),
        "solicitud": (date(2026, 6, 17), time(10, 0), "aprobada"),
        "requerimientos": ("Mesa ejecutiva", True, True, False),
        "evento": ("Reunion de Coordinacion", "Revision semanal de actividades y acuerdos", date(2026, 6, 17), time(11, 0), time(13, 0), 12, [2]),
    },
    {
        "solicitante": ("Lucia", "Navarro", "lucia.navarro@unison.mx", "6621000003"),
        "solicitud": (date(2026, 6, 18), time(8, 0), "aprobada"),
        "requerimientos": ("Teatro", True, False, True),
        "evento": ("Seminario de Investigacion", "Presentacion de avances de tesis", date(2026, 6, 18), time(8, 0), time(10, 0), 40, [1]),
    },
    {
        "solicitante": ("Martin", "Aguirre", "martin.aguirre@unison.mx", "6621000004"),
        "solicitud": (date(2026, 6, 18), time(9, 0), "aprobada"),
        "requerimientos": ("Laboratorio colaborativo", False, True, False),
        "evento": ("Taller de Prototipos", "Trabajo por equipos con servicio de cafeteria", date(2026, 6, 18), time(10, 0), time(12, 0), 24, [2]),
    },
    {
        "solicitante": ("Paola", "Rios", "paola.rios@unison.mx", "6621000005"),
        "solicitud": (date(2026, 6, 18), time(10, 0), "aprobada"),
        "requerimientos": ("Auditorio", True, True, True),
        "evento": ("Foro de Emprendimiento", "Foro con transmision y coffee break", date(2026, 6, 18), time(13, 0), time(15, 0), 60, [3]),
    },
    {
        "solicitante": ("Roberto", "Silva", "roberto.silva@empresa.mx", "6621000006"),
        "solicitud": (date(2026, 6, 19), time(9, 0), "pendiente"),
        "requerimientos": ("Grupos de trabajo", False, False, True),
        "evento": ("Workshop de Innovacion", "Sesion externa de innovacion", date(2026, 6, 19), time(9, 0), time(12, 0), 35, [1]),
    },
    {
        "solicitante": ("Personal", "UNISON", "mantenimiento@unison.mx", "6621000007"),
        "solicitud": (date(2026, 6, 19), time(11, 0), "aprobada"),
        "requerimientos": ("Mantenimiento", False, False, False),
        "evento": ("Mantenimiento Preventivo", "Revision de cableado, audio y videoconferencia", date(2026, 6, 20), time(8, 0), time(11, 0), 2, [2]),
    },
    {
        "solicitante": ("Sofia", "Valdez", "sofia.valdez@unison.mx", "6621000008"),
        "solicitud": (date(2026, 6, 20), time(12, 0), "rechazada"),
        "requerimientos": ("Herradura", False, False, False),
        "evento": ("Mesa de Analisis", "Solicitud rechazada visible para revisar solicitudes", date(2026, 6, 23), time(10, 0), time(12, 0), 18, [2]),
    },
    {
        "solicitante": ("Hector", "Salazar", "hector.salazar@unison.mx", "6621000009"),
        "solicitud": (date(2026, 6, 20), time(13, 0), "aprobada"),
        "requerimientos": ("Aula", True, False, False),
        "evento": ("Clase de Arquitectura", "Revision de proyectos finales", date(2026, 6, 24), time(12, 0), time(14, 0), 32, [1]),
    },
    {
        "solicitante": ("Mariana", "Cota", "mariana.cota@unison.mx", "6621000010"),
        "solicitud": (date(2026, 6, 21), time(8, 0), "aprobada"),
        "requerimientos": ("Teatro", True, True, True),
        "evento": ("Conferencia de Ciencia de Datos", "Conferencia con asistentes externos", date(2026, 6, 26), time(13, 0), time(16, 0), 68, [3]),
    },
    {
        "solicitante": ("Ivan", "Castro", "ivan.castro@unison.mx", "6621000012"),
        "solicitud": (date(2026, 6, 22), time(10, 0), "aprobada"),
        "requerimientos": ("Mesa ejecutiva", True, False, True),
        "evento": ("Comite Academico", "Sesion mensual del comite", date(2026, 6, 30), time(16, 0), time(18, 0), 14, [2]),
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


def clear_demo_data(db):
    db.execute(sala_evento.delete())
    db.query(Evento).delete(synchronize_session=False)
    db.query(Solicitud).delete(synchronize_session=False)
    db.query(Requerimientos).delete(synchronize_session=False)
    db.query(Solicitante).delete(synchronize_session=False)


def seed():
    db = SessionLocal()
    try:
        clear_demo_data(db)

        for numero_sala, capacidad in SALAS:
            get_or_create_sala(db, numero_sala, capacidad)
        db.flush()

        for item in DEMO_DATA:
            nombre, apellido, correo, telefono = item["solicitante"]
            fecha_solicitud, hora_solicitud, estado_solicitud = item["solicitud"]
            acomodo, sonido, cafeteria, videoconferencia = item["requerimientos"]
            titulo, descripcion, fecha_evento, inicio, fin, asistentes, salas_ids = item["evento"]

            solicitante = Solicitante(
                nombre=nombre,
                apellido=apellido,
                correo=correo,
                no_de_telefono=telefono,
            )
            solicitud = Solicitud(
                fecha_solicitud=fecha_solicitud,
                hora_de_solicitud=hora_solicitud,
                estado=estado_solicitud,
                solicitante=solicitante,
            )
            requerimientos = Requerimientos(
                acomodo=acomodo,
                equipo_de_sonido=sonido,
                cafeteria=cafeteria,
                videoconferencia=videoconferencia,
            )
            evento = Evento(
                titulo=titulo,
                descripcion=descripcion,
                fecha=fecha_evento,
                hora_de_inicio=inicio,
                hora_de_termino=fin,
                no_de_asistentes=asistentes,
                solicitud=solicitud,
                requerimientos=requerimientos,
                salas=[db.get(Sala, sala_id) for sala_id in salas_ids],
            )
            db.add(evento)

        db.commit()
        print(f"Base de datos reiniciada y llenada con {len(DEMO_DATA)} eventos demo de MODD.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()

