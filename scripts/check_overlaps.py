import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.core.database import SessionLocal
from app.models.salas import Evento


def main():
    db = SessionLocal()
    try:
        events = (
            db.query(Evento)
            .order_by(Evento.fecha, Evento.hora_de_inicio)
            .all()
        )
        overlaps = []

        for index, event in enumerate(events):
            event_rooms = {room.numero_sala for room in event.salas}
            for other in events[index + 1:]:
                if event.fecha != other.fecha:
                    continue
                other_rooms = {room.numero_sala for room in other.salas}
                shared_rooms = event_rooms & other_rooms
                if not shared_rooms:
                    continue
                if event.hora_de_inicio < other.hora_de_termino and event.hora_de_termino > other.hora_de_inicio:
                    overlaps.append((event, other, sorted(shared_rooms)))

        if not overlaps:
            print("No hay eventos solapados.")
            return

        print("Eventos solapados encontrados:")
        for event, other, rooms in overlaps:
            room_text = ", ".join(f"Sala {room}" for room in rooms)
            print(
                f"- {room_text} {event.fecha}: "
                f"#{event.id_evento} {event.titulo} ({event.hora_de_inicio}-{event.hora_de_termino}) "
                f"choca con #{other.id_evento} {other.titulo} ({other.hora_de_inicio}-{other.hora_de_termino})"
            )
    finally:
        db.close()


if __name__ == "__main__":
    main()

