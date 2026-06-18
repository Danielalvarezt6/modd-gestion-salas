from sqlalchemy import Column, Integer, String, Date, Time, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.core.database import Base

sala_evento = Table(
    "sala_evento",
    Base.metadata,
    Column("numero_sala", Integer, ForeignKey("sala.numero_sala"), primary_key=True),
    Column("id_evento", Integer, ForeignKey("evento.id_evento"), primary_key=True),
)


class Sala(Base):
    __tablename__ = "sala"

    numero_sala = Column(Integer, primary_key=True, index=True)
    capacidad = Column(Integer, nullable=False)

    eventos = relationship("Evento", secondary=sala_evento, back_populates="salas")


class Solicitante(Base):
    __tablename__ = "solicitante"

    id_solicitante = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    apellido = Column(String, nullable=False)
    correo = Column(String, unique=True, index=True, nullable=False)
    no_de_telefono = Column(String)

    solicitudes = relationship("Solicitud", back_populates="solicitante")


class Solicitud(Base):
    __tablename__ = "solicitud"

    id_solicitud = Column(Integer, primary_key=True, index=True)
    fecha_solicitud = Column(Date, nullable=False)
    hora_de_solicitud = Column(Time, nullable=False)

    estado = Column(String)

    id_solicitante = Column(Integer, ForeignKey("solicitante.id_solicitante"))

    solicitante = relationship("Solicitante", back_populates="solicitudes")
    eventos = relationship("Evento", back_populates="solicitud")


class Requerimientos(Base):
    __tablename__ = "requerimientos"

    id_requerimientos = Column(Integer, primary_key=True, index=True)
    acomodo = Column(String)
    equipo_de_sonido = Column(Boolean, default=False)
    cafeteria = Column(Boolean, default=False)
    videoconferencia = Column(Boolean, default=False)

    eventos = relationship("Evento", back_populates="requerimientos")


class Evento(Base):
    __tablename__ = "evento"

    id_evento = Column(Integer, primary_key=True, index=True)
    titulo = Column(String, nullable=False)
    descripcion = Column(String)
    fecha = Column(Date, nullable=False)
    hora_de_inicio = Column(Time, nullable=False)
    hora_de_termino = Column(Time, nullable=False)
    no_de_asistentes = Column(Integer)

    id_solicitud = Column(Integer, ForeignKey("solicitud.id_solicitud"))
    id_requerimientos = Column(Integer, ForeignKey("requerimientos.id_requerimientos"))

    solicitud = relationship("Solicitud", back_populates="eventos")
    requerimientos = relationship("Requerimientos", back_populates="eventos")
    salas = relationship("Sala", secondary=sala_evento, back_populates="eventos")
