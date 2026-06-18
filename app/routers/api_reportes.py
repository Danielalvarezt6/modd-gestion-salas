import io
import unicodedata
from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.models.salas import Evento
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
    stmt = select(Evento).options(selectinload(Evento.salas), selectinload(Evento.requerimientos))

    if fecha_inicio:
        stmt = stmt.where(Evento.fecha >= fecha_inicio)
    if fecha_fin:
        stmt = stmt.where(Evento.fecha <= fecha_fin)

    eventos = db.execute(stmt.order_by(Evento.fecha, Evento.hora_de_inicio)).scalars().all()
    if sala:
        eventos = [evento for evento in eventos if any(item.numero_sala == sala for item in evento.salas)]
    return eventos


def _resumen_eventos(eventos):
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


class SimplePDF:
    def __init__(self):
        self.pages: list[str] = []
        self.lines: list[str] = []
        self.y = 780
        self.page_width = 612
        self.left = 46

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

    def text(self, value, x=None, size=10, bold=False, gap=15):
        self.ensure_space(gap)
        font = "F2" if bold else "F1"
        safe = _normalize_pdf_text(value)
        x = self.left if x is None else x
        self._cmd(f"BT /{font} {size} Tf {x} {self.y} Td ({safe}) Tj ET")
        self.y -= gap

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
            self._cmd(f"BT /{font} {size} Tf {x} {self.y} Td ({safe}) Tj ET")
            x += width
        self.y -= gap

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


def _generar_pdf(titulo: str, eventos, fecha_inicio=None, fecha_fin=None, sala=None) -> bytes:
    resumen = _resumen_eventos(eventos)
    pdf = SimplePDF()
    pdf.text("MODD - Gestion de Salas", size=16, bold=True, gap=22)
    pdf.text(titulo, size=14, bold=True, gap=18)
    pdf.text(f"Generado: {date.today().isoformat()}", size=9)
    pdf.text(f"Periodo: {fecha_inicio or 'Sin inicio'} a {fecha_fin or 'Sin fin'}", size=9)
    pdf.text(f"Sala: {'Todas' if not sala else 'Sala ' + str(sala)}", size=9)
    pdf.rule()
    pdf.text("Resumen", size=12, bold=True)
    pdf.row(
        ["Eventos", "Asistentes"],
        [120, 120],
        bold=True,
    )
    pdf.row(
        [
            resumen["total_eventos"],
            resumen["total_asistentes"],
        ],
        [120, 120],
    )
    pdf.rule()
    pdf.text("Uso por sala", size=12, bold=True)
    pdf.row(["Sala", "Eventos", "Asistentes"], [180, 130, 130], bold=True)
    for item in resumen["uso_por_sala"]:
        pdf.row([item["sala"], item["eventos"], item["asistentes"]], [180, 130, 130])
    pdf.rule()
    pdf.text("Detalle de eventos", size=12, bold=True)
    pdf.row(["Fecha", "Horario", "Evento", "Sala"], [72, 78, 240, 100], bold=True)
    if not eventos:
        pdf.text("No hay eventos para los filtros seleccionados.", size=10)
    for evento in eventos:
        salas = ", ".join(f"Sala {sala.numero_sala}" for sala in evento.salas) or "Sin sala"
        pdf.row(
            [
                evento.fecha,
                f"{evento.hora_de_inicio.strftime('%H:%M')}-{evento.hora_de_termino.strftime('%H:%M')}",
                evento.titulo,
                salas,
            ],
            [72, 78, 240, 100],
        )
        pdf.row(
            [
                "",
                "",
                f"{evento.no_de_asistentes or 0} asistentes",
                "",
            ],
            [72, 78, 240, 100],
            size=7.5,
        )
        if evento.requerimientos:
            extras = []
            if evento.requerimientos.acomodo:
                extras.append(f"Acomodo: {evento.requerimientos.acomodo}")
            if evento.requerimientos.equipo_de_sonido:
                extras.append("Equipo de sonido")
            if evento.requerimientos.cafeteria:
                extras.append("Cafeteria")
            if evento.requerimientos.videoconferencia:
                extras.append("Videoconferencia")
            if extras:
                pdf.row(["", "", " | ".join(extras), ""], [72, 78, 240, 100], size=7.2)
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
    db: Session = Depends(get_db),
):
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
    elif tipo == "sala":
        titulo = "Informe por sala"
        filename = f"informe_sala_{sala or 'todas'}.pdf"
    else:
        titulo = "Reporte personalizado"
        filename = "reporte_personalizado_modd.pdf"

    eventos = _eventos_filtrados(db, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, sala=sala)
    content = _generar_pdf(titulo, eventos, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, sala=sala)
    return _pdf_response(filename, content)
