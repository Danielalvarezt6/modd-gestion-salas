"""
API Router para la analítica y generación de reportes PDF.

Contiene los endpoints encargados de calcular las estadísticas de ocupación
(usadas en el Dashboard principal) y un motor interno minimalista para dibujar 
documentos PDF nativos de resúmenes operativos sin dependencias externas pesadas.
"""

import io
import unicodedata
from datetime import date, timedelta
from textwrap import wrap
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.models.salas import Evento, Solicitud
from app.schemas.salas import ReporteResumenOut

router = APIRouter(prefix="/api/reportes", tags=["Reportes"])


def _normalize_pdf_text(value) -> str:
    text = "" if value is None else str(value)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _eventos_filtrados(
    db: Session,
    fecha_inicio: Optional[date] = None,
    fecha_fin: Optional[date] = None,
    sala: Optional[int] = None,
):
    stmt = select(Evento).outerjoin(Solicitud).options(
        selectinload(Evento.salas),
        selectinload(Evento.requerimientos),
        selectinload(Evento.solicitud).selectinload(Solicitud.solicitante),
    ).where(
        (Evento.id_solicitud.is_(None)) | (Solicitud.estado == "aprobada")
    )

    if fecha_inicio:
        stmt = stmt.where(Evento.fecha >= fecha_inicio)
    if fecha_fin:
        stmt = stmt.where(Evento.fecha <= fecha_fin)

    eventos = db.execute(stmt.order_by(Evento.fecha, Evento.hora_de_inicio)).scalars().all()
    if sala:
        eventos = [evento for evento in eventos if any(item.numero_sala == sala for item in evento.salas)]
    return eventos


def _resumen_eventos(eventos):
    """
    Agrega los eventos por sala para producir conteos de eventos y asistentes.
    Devuelve un diccionario estructurado apto para las tarjetas del Dashboard y
    para la tabla resumen del PDF.
    """
    uso_por_sala = []
    for numero_sala in (1, 2, 3):
        eventos_sala = [evento for evento in eventos if any(s.numero_sala == numero_sala for s in evento.salas)]
        uso_por_sala.append(
            {
                "sala": f"Sala {numero_sala}",
                "eventos": len(eventos_sala),
                "asistentes": sum(evento.no_de_asistentes or 0 for evento in eventos_sala),
            }
        )

    return {
        "total_eventos": len(eventos),
        "total_asistentes": sum(evento.no_de_asistentes or 0 for evento in eventos),
        "uso_por_sala": uso_por_sala,
    }


def _wrapped_lines(label, value, width_chars=96):
    text = "" if value is None else str(value)
    prefix = f"{label}: " if label else ""
    full_text = prefix + text
    lines = []
    for part in full_text.split('\n'):
        lines.extend(wrap(part, width=width_chars) or [part])
    return lines


class SimplePDF:
    """
    Mini-motor de generación de PDF construyendo las primitivas directamente
    en la sintaxis de PDF 1.4.
    
    Evita depender de librerías como xhtml2pdf o ReportLab para tener control total
    sobre el peso, la paginación y la paleta de colores del reporte.
    """
    def __init__(self):
        self.pages: list[str] = []
        self.lines: list[str] = []
        self.y = 780
        self.page_width = 612
        self.left = 46
        self.right = 566

    def _cmd(self, text: str):
        self.lines.append(text)

    def add_page(self):
        if self.lines:
            self.pages.append("\n".join(self.lines))
        self.lines = []
        self.y = 780

    def ensure_space(self, needed=24):
        if self.y < 52 + needed:
            self.add_page()

    def color(self, rgb=(0.08, 0.12, 0.23)):
        r, g, b = rgb
        self._cmd(f"{r} {g} {b} rg")

    def rect(self, x, y, width, height, fill=(1, 1, 1), stroke=None):
        self._cmd(f"{fill[0]} {fill[1]} {fill[2]} rg {x} {y} {width} {height} re f")
        if stroke:
            self._cmd(f"{stroke[0]} {stroke[1]} {stroke[2]} RG {x} {y} {width} {height} re S")

    def text(self, value, x=None, size=10, bold=False, gap=15, color=(0.08, 0.12, 0.23)):
        self.ensure_space(gap)
        font = "F2" if bold else "F1"
        safe = _normalize_pdf_text(value)
        x = self.left if x is None else x
        self.color(color)
        self._cmd(f"BT /{font} {size} Tf {x} {self.y} Td ({safe}) Tj ET")
        self.y -= gap

    def text_at(self, value, x, y, size=10, bold=False, color=(0.08, 0.12, 0.23)):
        font = "F2" if bold else "F1"
        safe = _normalize_pdf_text(value)
        self.color(color)
        self._cmd(f"BT /{font} {size} Tf {x} {y} Td ({safe}) Tj ET")

    def rule(self):
        self.ensure_space(10)
        self._cmd(f"0.82 0.86 0.92 RG {self.left} {self.y} 520 0.8 re f")
        self.y -= 12

    def row(self, values, widths, size=8.5, gap=18, bold=False):
        self.ensure_space(gap)
        x = self.left
        for value, width in zip(values, widths):
            safe = _normalize_pdf_text(value)
            if len(safe) > int(width / 4.8):
                safe = safe[: max(0, int(width / 4.8) - 3)] + "..."
            font = "F2" if bold else "F1"
            self.color((0.08, 0.12, 0.23))
            self._cmd(f"BT /{font} {size} Tf {x} {self.y} Td ({safe}) Tj ET")
            x += width
        self.y -= gap

    def wrapped_text(self, label, value, x=None, width_chars=96, size=8.5, bold_label=True, color=(0.08, 0.12, 0.23)):
        text = "" if value is None else str(value)
        if not text:
            return
        prefix = f"{label}: " if label else ""
        lines = wrap(prefix + text, width=width_chars) or [prefix + text]
        for index, line in enumerate(lines):
            self.text(line, x=x, size=size, bold=bold_label and index == 0, gap=11, color=color)

    def header(self, title, subtitle):
        self.rect(0, 724, 612, 68, fill=(0.14, 0.22, 0.54))
        self.rect(0, 724, 612, 5, fill=(0.88, 0.72, 0.24))
        self.text_at("MODD", 46, 762, size=18, bold=True, color=(1, 1, 1))
        self.text_at("GESTION DE SALAS", 46, 746, size=8, bold=True, color=(0.88, 0.92, 1))
        self.text_at(title, 250, 762, size=15, bold=True, color=(1, 1, 1))
        self.text_at(subtitle, 250, 746, size=9, color=(0.88, 0.92, 1))
        self.y = 700

    def metric_card(self, x, y, width, label, value, accent=(0.14, 0.22, 0.54)):
        self.rect(x, y, width, 52, fill=(0.96, 0.97, 0.99), stroke=(0.86, 0.89, 0.94))
        self.rect(x, y, 4, 52, fill=accent)
        self.text_at(str(value), x + 14, y + 27, size=18, bold=True, color=accent)
        self.text_at(label, x + 14, y + 12, size=8.5, bold=True, color=(0.36, 0.42, 0.54))

    def section_title(self, value):
        self.ensure_space(28)
        self.text(value, size=12, bold=True, gap=8, color=(0.14, 0.22, 0.54))
        self.rect(self.left, self.y, 520, 1, fill=(0.88, 0.72, 0.24))
        self.y -= 16

    def info_line(self, label, value, x, y, width_chars=34):
        self.text_at(label.upper(), x, y + 12, size=6.8, bold=True, color=(0.40, 0.47, 0.62))
        lines = wrap(str(value or "Sin dato"), width=width_chars) or ["Sin dato"]
        cursor = y
        for line in lines[:3]:
            self.text_at(line, x, cursor, size=8.3, bold=False, color=(0.08, 0.12, 0.23))
            cursor -= 10

    def build(self) -> bytes:
        if self.lines:
            self.pages.append("\n".join(self.lines))

        objects = []
        objects.append("<< /Type /Catalog /Pages 2 0 R >>")
        page_kids = " ".join(f"{3 + index * 2} 0 R" for index in range(len(self.pages)))
        objects.append(f"<< /Type /Pages /Kids [{page_kids}] /Count {len(self.pages)} >>")

        for index, content in enumerate(self.pages):
            page_obj = 3 + index * 2
            content_obj = page_obj + 1
            stream = content.encode("latin-1", "replace")
            objects.append(
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                f"/Resources << /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> "
                f"/F2 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >> >> >> "
                f"/Contents {content_obj} 0 R >>"
            )
            objects.append(f"<< /Length {len(stream)} >>\nstream\n{stream.decode('latin-1')}\nendstream")

        buffer = io.BytesIO()
        buffer.write(b"%PDF-1.4\n")
        offsets = [0]
        for number, obj in enumerate(objects, start=1):
            offsets.append(buffer.tell())
            buffer.write(f"{number} 0 obj\n{obj}\nendobj\n".encode("latin-1", "replace"))
        xref = buffer.tell()
        buffer.write(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode("ascii"))
        for offset in offsets[1:]:
            buffer.write(f"{offset:010d} 00000 n \n".encode("ascii"))
        buffer.write(
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF".encode("ascii")
        )
        return buffer.getvalue()


def _generar_pdf(titulo: str, eventos, fecha_inicio=None, fecha_fin=None, sala=None, operativo=False) -> bytes:
    resumen = _resumen_eventos(eventos)
    pdf = SimplePDF()
    periodo = f"{fecha_inicio or 'Sin inicio'} a {fecha_fin or 'Sin fin'}"
    sala_texto = "Todas las salas" if not sala else f"Sala {sala}"
    
    subtitle = "Documento operativo para preparacion de salas" if operativo else "Documento para informar eventos y preparar salas"
    if sala:
        titulo = f"Reporte Exclusivo - Sala {sala}"

    pdf.header(titulo, subtitle)

    pdf.text(f"Generado: {date.today().isoformat()}   |   Periodo: {periodo}   |   Filtro: {sala_texto}", size=8.5, gap=24)
    pdf.metric_card(46, pdf.y - 52, 150, "Eventos", resumen["total_eventos"], accent=(0.14, 0.22, 0.54))
    pdf.metric_card(214, pdf.y - 52, 150, "Asistentes", resumen["total_asistentes"], accent=(0.09, 0.42, 0.17))
    salas_usadas = sum(1 for item in resumen["uso_por_sala"] if item["eventos"])
    pdf.metric_card(382, pdf.y - 52, 150, "Salas con uso", salas_usadas, accent=(0.55, 0.38, 0.00))
    pdf.y -= 76

    pdf.section_title("Uso por sala")
    pdf.row(["Sala", "Eventos programados", "Asistentes estimados"], [160, 170, 170], bold=True)
    for item in resumen["uso_por_sala"]:
        pdf.row([item["sala"], item["eventos"], item["asistentes"]], [160, 170, 170])

    pdf.section_title("Detalle operativo de eventos")
    if not eventos:
        pdf.text("No hay eventos para los filtros seleccionados.", size=10)
    for evento in eventos:
        salas = ", ".join(f"Sala {sala.numero_sala}" for sala in evento.salas) or "Sin sala"
        solicitante = evento.solicitud.solicitante if evento.solicitud else None
        responsable = (
            f"{solicitante.nombre} {solicitante.apellido}".strip()
            if solicitante
            else "Solicitante no asignado"
        )
            
        horario = f"{evento.hora_de_inicio.strftime('%H:%M')} - {evento.hora_de_termino.strftime('%H:%M')}"

        req = evento.requerimientos
        preparacion = []
        if req and req.acomodo:
            preparacion.append(f"Acomodo: {req.acomodo}")
        if req and req.equipo_de_sonido:
            preparacion.append("Equipo de sonido")
        if req and req.cafeteria:
            preparacion.append("Cafeteria")
        if req and req.videoconferencia:
            preparacion.append("Videoconferencia")
        preparacion_texto = ", ".join(preparacion) if preparacion else "Sin requerimientos especiales"

        descripcion_lineas = _wrapped_lines("Descripcion", evento.descripcion or "Sin descripcion", width_chars=88)
        preparacion_lineas = _wrapped_lines("Preparacion de sala", preparacion_texto, width_chars=88)
        
        # Calculate dynamic height based on lines
        contenido_alto = (len(descripcion_lineas) + len(preparacion_lineas)) * 12
        card_height = max(178, 140 + contenido_alto)

        pdf.ensure_space(card_height + 24)
        card_top = pdf.y
        card_bottom = card_top - card_height
        pdf.rect(46, card_bottom, 520, card_height + 6, fill=(0.98, 0.99, 1), stroke=(0.84, 0.87, 0.93))
        pdf.rect(46, card_bottom, 6, card_height + 6, fill=(0.14, 0.22, 0.54))
        pdf.text_at(str(evento.titulo), 62, card_top - 18, size=12, bold=True, color=(0.05, 0.09, 0.20))
        pdf.text_at(f"{evento.fecha}  |  {horario}", 62, card_top - 34, size=9, bold=True, color=(0.14, 0.22, 0.54))

        pdf.info_line("Sala", salas, 62, card_top - 62, width_chars=24)
        pdf.info_line("Asistentes", evento.no_de_asistentes or 0, 190, card_top - 62, width_chars=18)
        pdf.info_line("Responsable / solicitante", responsable, 300, card_top - 62, width_chars=34)
        
        if not operativo:
            correo = solicitante.correo if solicitante else "Sin correo"
            telefono = solicitante.no_de_telefono if solicitante else "Sin telefono"
            pdf.info_line("Contacto", f"{correo} | {telefono}", 62, card_top - 104, width_chars=58)

        pdf.y = card_top - 116
        for index, line in enumerate(descripcion_lineas):
            pdf.text(line, x=62, size=8.2, bold=index == 0, gap=11)
        pdf.y -= 2
        for index, line in enumerate(preparacion_lineas):
            pdf.text(line, x=62, size=8.2, bold=index == 0, gap=11)
        if evento.requerimientos:
            checklist = [
                ("Acomodo", bool(evento.requerimientos.acomodo)),
                ("Audio", bool(evento.requerimientos.equipo_de_sonido)),
                ("Cafeteria", bool(evento.requerimientos.cafeteria)),
                ("Videoconferencia", bool(evento.requerimientos.videoconferencia)),
            ]
            x = 62
            y = max(pdf.y - 4, card_top - 144)
            for label, enabled in checklist:
                mark = "SI" if enabled else "NO"
                color = (0.09, 0.42, 0.17) if enabled else (0.55, 0.58, 0.66)
                pdf.text_at(f"{label}: {mark}", x, y, size=7.2, bold=True, color=color)
                x += 115
        pdf.y = card_bottom - 14
    return pdf.build()


def _pdf_response(filename: str, content: bytes):
    return StreamingResponse(
        io.BytesIO(content),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/resumen", response_model=ReporteResumenOut)
async def obtener_resumen_reportes(
    fecha_inicio: Optional[date] = Query(default=None),
    fecha_fin: Optional[date] = Query(default=None),
    sala: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
):
    """
    Endpoint para consumir métricas de ocupación en JSON.
    Permite filtrar por rangos de fecha y salas, devolviendo totales de asistentes
    y cantidad de eventos programados (aprobados).
    """
    eventos = _eventos_filtrados(db, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, sala=sala)
    resumen = _resumen_eventos(eventos)

    return ReporteResumenOut(
        total_eventos=resumen["total_eventos"],
        total_asistentes=resumen["total_asistentes"],
        uso_por_sala=resumen["uso_por_sala"],
        eventos=eventos,
    )


@router.get("/pdf")
async def descargar_reporte_pdf(
    tipo: str = Query(default="personalizado"),
    fecha_inicio: Optional[date] = Query(default=None),
    fecha_fin: Optional[date] = Query(default=None),
    sala: Optional[int] = Query(default=None),
    operativo: bool = Query(default=False),
    db: Session = Depends(get_db),
):
    """
    Endpoint principal de exportación PDF.
    Soporta generación automática determinando periodos (semanal, mensual) o permitiendo
    filtros arbitrarios por fecha/sala.
    Retorna un flujo binario (StreamingResponse) con el documento PDF construido al vuelo.
    """
    today = date.today()
    filename = "reporte_modd.pdf"
    titulo = "Reporte personalizado"

    if tipo == "semanal":
        fecha_inicio = today - timedelta(days=today.weekday())
        fecha_fin = fecha_inicio + timedelta(days=6)
        titulo = "Reporte semanal"
        filename = f"reporte_semanal_{fecha_inicio.isoformat()}.pdf"
    elif tipo == "mensual":
        fecha_inicio = today.replace(day=1)
        next_month = (fecha_inicio.replace(day=28) + timedelta(days=4)).replace(day=1)
        fecha_fin = next_month - timedelta(days=1)
        titulo = "Reporte mensual"
        filename = f"reporte_mensual_{fecha_inicio.strftime('%Y_%m')}.pdf"
    elif tipo == "sala" or sala:
        titulo = f"Reporte Exclusivo - Sala {sala}"
        filename = f"informe_sala_{sala or 'todas'}.pdf"
    else:
        titulo = "Reporte personalizado"
        filename = "reporte_personalizado_modd.pdf"

    eventos = _eventos_filtrados(db, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, sala=sala)
    content = _generar_pdf(titulo, eventos, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, sala=sala, operativo=operativo)
    return _pdf_response(filename, content)
