(function () {
  const rooms = [
    { id: 'sala1', name: 'Sala 1', color: '#24398A' },
    { id: 'sala2', name: 'Sala 2', color: '#5CA847' },
    { id: 'sala3', name: 'Sala 3', color: '#E1B73D' }
  ];

  const dayNames = ['Lun', 'Mar', 'Mie', 'Jue', 'Vie', 'Sab', 'Dom'];
  const START_MIN = 8 * 60;
  const END_MIN = 18 * 60;
  const STEP_MIN = 60;
  const HOUR_HEIGHT = 74;

  let events = [];
  let weekStart = getMonday(new Date());
  let visibleRooms = rooms.map((room) => room.id);
  let searchTerm = '';
  let fullCalendar = null;
  let activeView = 'week';
  let dragState = null;
  let activeGuide = null;
  let alertTimer = null;

  document.addEventListener('DOMContentLoaded', initCalendarModule);

  async function initCalendarModule() {
    await cargarEventosDesdeApi();
    bindControls();
    renderWeekCalendar();
    initFullCalendar();
    renderFullCalendarEvents();
  }

  async function cargarEventosDesdeApi() {
    try {
      const response = await fetch('/api/eventos/?solo_aprobadas=true');
      if (!response.ok) throw new Error('Error de red al cargar eventos');

      const eventosDB = await response.json();

      // Traducir el JSON de la base de datos al formato que espera FullCalendar
      events = eventosDB.map((evt) => {
        const solicitante = evt.solicitud?.solicitante || {};
        const responsable = [solicitante.nombre, solicitante.apellido].filter(Boolean).join(' ') || 'Solicitante no asignado';
        return {
          id: String(evt.id_evento),
          title: evt.titulo,
          // Unimos fecha y hora en formato ISO: "YYYY-MM-DDTHH:MM:SS"
          start: `${evt.fecha}T${evt.hora_de_inicio}`,
          end: `${evt.fecha}T${evt.hora_de_termino}`,
          // Convertimos [{numero_sala: 1}] a ['sala1']
          rooms: evt.salas.map((s) => `sala${s.numero_sala}`),
          responsible: responsable,
          requestFirstName: solicitante.nombre || '',
          requestLastName: solicitante.apellido || '',
          requestEmail: solicitante.correo || '',
          requestPhone: solicitante.no_de_telefono || '',
          notes: evt.descripcion || '',
          attendees: evt.no_de_asistentes || 0,
          requirements: evt.requerimientos || {}
        };
      });
      warnExistingConflicts();
    } catch (error) {
      console.error("Error al cargar eventos:", error);
      showAlert('No se pudieron cargar los eventos de la base de datos.', 'error');
    }
  }

  function bindControls() {
    document.getElementById('calendar-new-event')?.addEventListener('click', () => {
      openEventModal({
        date: toISODate(new Date()),
        rooms: ['sala1'],
        startTime: '09:00',
        endTime: '10:00'
      });
    });

    document.getElementById('quick-new-event')?.addEventListener('click', () => {
      openEventModal({
        date: toISODate(new Date()),
        rooms: ['sala1'],
        startTime: '09:00',
        endTime: '10:00'
      });
    });

    document.getElementById('calendar-search')?.addEventListener('input', (event) => {
      searchTerm = event.target.value.trim().toLowerCase();
      rerenderActiveViews();
    });

    document.querySelectorAll('.modd-room-filters input').forEach((input) => {
      input.addEventListener('change', () => {
        const checkedRooms = Array.from(document.querySelectorAll('.modd-room-filters input:checked')).map((item) => item.value);
        if (!checkedRooms.length) {
          input.checked = true;
          showAlert('Debe quedar al menos una sala visible.');
          return;
        }
        visibleRooms = checkedRooms;
        rerenderActiveViews();
      });
    });

    document.querySelectorAll('[data-calendar-view]').forEach((button) => {
      button.addEventListener('click', () => setCalendarView(button.dataset.calendarView));
    });

    document.querySelectorAll('[data-modal-close]').forEach((button) => {
      button.addEventListener('click', closeEventModal);
    });

    document.getElementById('event-form')?.addEventListener('submit', saveEventFromModal);
    document.getElementById('event-delete-button')?.addEventListener('click', deleteEventFromModal);
    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape') closeEventModal();
    });
  }

  function setCalendarView(view) {
    activeView = view;
    document.querySelectorAll('[data-calendar-view]').forEach((button) => {
      button.classList.toggle('active', button.dataset.calendarView === view);
    });

    const weekView = document.getElementById('week-calendar-view');
    const fullView = document.getElementById('fullcalendar-view');

    if (view === 'week') {
      weekView?.classList.remove('hidden');
      fullView?.classList.add('hidden');
      renderWeekCalendar();
      return;
    }

    weekView?.classList.add('hidden');
    fullView?.classList.remove('hidden');

    if (fullCalendar) {
      fullCalendar.changeView(view === 'month' ? 'dayGridMonth' : 'timeGridDay');
      fullCalendar.gotoDate(weekStart);
      fullCalendar.updateSize();
      renderFullCalendarEvents();
    }
  }

  function renderWeekCalendar() {
    const grid = document.getElementById('week-calendar-grid');
    if (!grid) return;

    const days = Array.from({ length: 7 }, (_, index) => addDays(weekStart, index));
    grid.style.setProperty('--day-count', String(days.length));
    grid.style.setProperty('--room-count', String(visibleRooms.length));
    grid.innerHTML = '';

    const corner = document.createElement('div');
    corner.className = 'modd-time-corner';
    corner.textContent = 'Hora';
    grid.appendChild(corner);

    days.forEach((date, index) => {
      const heading = document.createElement('div');
      heading.className = 'modd-day-heading';
      heading.style.gridColumn = String(index + 2);
      heading.innerHTML = `
        <div class="modd-day-title">${dayNames[index]} <span>${formatShortDate(date)}</span></div>
        <div class="modd-room-heading-row">
          ${visibleRooms.map((roomId) => {
            const room = findRoom(roomId);
            return `<div class="modd-room-heading" style="--room-color:${room.color}">${room.name}</div>`;
          }).join('')}
        </div>
      `;
      grid.appendChild(heading);
    });

    const timeRail = document.createElement('div');
    timeRail.className = 'modd-time-rail';
    for (let minutes = START_MIN; minutes < END_MIN; minutes += 60) {
      const slot = document.createElement('div');
      slot.className = 'modd-time-slot';
      slot.textContent = formatMinutes(minutes);
      timeRail.appendChild(slot);
    }
    grid.appendChild(timeRail);

    days.forEach((date, index) => {
      const dayColumn = document.createElement('div');
      dayColumn.className = 'modd-day-column';
      dayColumn.dataset.dayIndex = String(index);
      dayColumn.dataset.date = toISODate(date);
      dayColumn.style.gridColumn = String(index + 2);

      visibleRooms.forEach((roomId) => {
        const lane = document.createElement('div');
        lane.className = 'modd-room-lane';
        lane.dataset.room = roomId;
        lane.dataset.date = toISODate(date);
        dayColumn.appendChild(lane);
      });

      grid.appendChild(dayColumn);
    });

    activeGuide = document.createElement('div');
    activeGuide.className = 'modd-drag-guide';

    const dayColumns = Array.from(grid.querySelectorAll('.modd-day-column'));
    filteredEvents().forEach((eventItem) => renderWeekEvent(eventItem, dayColumns));
  }

  function renderWeekEvent(eventItem, dayColumns) {
    const date = getEventDate(eventItem);
    const dayIndex = dayDifference(weekStart, parseDate(date));
    if (dayIndex < 0 || dayIndex > 6) return;

    const shownRooms = eventItem.rooms.filter((roomId) => visibleRooms.includes(roomId));
    if (!shownRooms.length) return;

    const dayColumn = dayColumns[dayIndex];
    if (!dayColumn) return;

    const firstRoomIndex = Math.min(...shownRooms.map((roomId) => visibleRooms.indexOf(roomId)));
    const lastRoomIndex = Math.max(...shownRooms.map((roomId) => visibleRooms.indexOf(roomId)));
    const roomSpan = lastRoomIndex - firstRoomIndex + 1;
    const startMinutes = timeToMinutes(getEventTime(eventItem.start));
    const endMinutes = timeToMinutes(getEventTime(eventItem.end));
    const top = ((startMinutes - START_MIN) / 60) * HOUR_HEIGHT;
    const height = Math.max(42, ((endMinutes - startMinutes) / 60) * HOUR_HEIGHT - 6);
    const leftPercent = (firstRoomIndex / visibleRooms.length) * 100;
    const widthPercent = (roomSpan / visibleRooms.length) * 100;
    const eventColor = getEventColor(eventItem);

    const card = document.createElement('article');
    card.className = 'modd-event-card';
    card.dataset.eventId = eventItem.id;
    card.style.setProperty('--event-color', eventColor);
    card.style.top = `${top + 3}px`;
    card.style.height = `${height}px`;
    card.style.left = `calc(${leftPercent}% + 7px)`;
    card.style.width = `calc(${widthPercent}% - 14px)`;
    card.innerHTML = `
      <strong class="modd-event-title">${escapeHTML(eventItem.title)}</strong>
      <span class="modd-event-meta">${getEventTime(eventItem.start)} - ${getEventTime(eventItem.end)} - ${eventItem.rooms.map((roomId) => findRoom(roomId).name).join(', ')}</span>
      <span class="modd-event-responsible">${escapeHTML(eventItem.responsible)}</span>
      <span class="modd-resize-handle modd-room-resize-handle" title="Extender salas" aria-hidden="true"></span>
      <span class="modd-duration-resize-handle" title="Extender horas" aria-hidden="true"></span>
    `;

    card.addEventListener('dblclick', (event) => {
      event.stopPropagation();
      openEventModal(eventItem);
    });

    card.addEventListener('pointerdown', (event) => startPointerInteraction(event, eventItem, dayColumn));
    dayColumn.appendChild(card);
  }

  function startPointerInteraction(pointerEvent, eventItem, dayColumn) {
    if (pointerEvent.button !== 0) return;
    pointerEvent.preventDefault();
    pointerEvent.stopPropagation();

    let type = 'drag';
    if (pointerEvent.target.classList.contains('modd-room-resize-handle')) type = 'resize-room';
    if (pointerEvent.target.classList.contains('modd-duration-resize-handle')) type = 'resize-time';
    const card = pointerEvent.currentTarget;
    const original = cloneEvent(eventItem);
    const visibleEventRooms = original.rooms.filter((roomId) => visibleRooms.includes(roomId));
    const roomCount = Math.max(1, Math.min(visibleEventRooms.length || original.rooms.length, visibleRooms.length));

    dragState = {
      type,
      eventId: eventItem.id,
      original,
      card,
      roomCount,
      duration: timeToMinutes(getEventTime(original.end)) - timeToMinutes(getEventTime(original.start)),
      startRoomIndex: Math.max(0, visibleRooms.indexOf(visibleEventRooms[0] || original.rooms[0])),
      fixedDayColumn: dayColumn,
      originX: pointerEvent.clientX,
      originY: pointerEvent.clientY,
      activated: false
    };

    document.addEventListener('pointermove', handlePointerMove);
    document.addEventListener('pointerup', finishPointerInteraction, { once: true });
  }

  function handlePointerMove(pointerEvent) {
    if (!dragState) return;

    if (!dragState.activated) {
      const distance = Math.hypot(pointerEvent.clientX - dragState.originX, pointerEvent.clientY - dragState.originY);
      const threshold = dragState.type === 'drag' ? 8 : 4;
      if (distance < threshold) return;
      dragState.activated = true;
      dragState.card.classList.add('dragging');
    }

    const targetColumn = dragState.type === 'resize-room' || dragState.type === 'resize-time'
      ? dragState.fixedDayColumn
      : findDayColumnAtPoint(pointerEvent.clientX, pointerEvent.clientY);

    if (!targetColumn) {
      hideGuide();
      dragState.proposed = null;
      return;
    }

    const rect = targetColumn.getBoundingClientRect();
    const roomWidth = rect.width / visibleRooms.length;
    const rawRoomIndex = clamp(Math.floor((pointerEvent.clientX - rect.left) / roomWidth), 0, visibleRooms.length - 1);
    let proposed;

    if (dragState.type === 'resize-room') {
      const endIndex = clamp(rawRoomIndex, dragState.startRoomIndex, visibleRooms.length - 1);
      proposed = {
        ...dragState.original,
        rooms: visibleRooms.slice(dragState.startRoomIndex, endIndex + 1)
      };
    } else if (dragState.type === 'resize-time') {
      const startMinutes = timeToMinutes(getEventTime(dragState.original.start));
      let endMinutes = START_MIN + Math.round(((pointerEvent.clientY - rect.top) / HOUR_HEIGHT) * 60 / STEP_MIN) * STEP_MIN;
      endMinutes = clamp(endMinutes, startMinutes + STEP_MIN, END_MIN);

      proposed = {
        ...dragState.original,
        end: `${getEventDate(dragState.original)}T${formatMinutes(endMinutes)}:00`
      };
    } else {
      const maxRoomStart = Math.max(0, visibleRooms.length - dragState.roomCount);
      const roomStart = clamp(rawRoomIndex, 0, maxRoomStart);
      let startMinutes = START_MIN + Math.round(((pointerEvent.clientY - rect.top) / HOUR_HEIGHT) * 60 / STEP_MIN) * STEP_MIN;
      startMinutes = clamp(startMinutes, START_MIN, END_MIN - dragState.duration);

      const date = targetColumn.dataset.date;
      proposed = {
        ...dragState.original,
        start: `${date}T${formatMinutes(startMinutes)}:00`,
        end: `${date}T${formatMinutes(startMinutes + dragState.duration)}:00`,
        rooms: visibleRooms.slice(roomStart, roomStart + dragState.roomCount)
      };
    }

    dragState.proposed = proposed;
    const conflict = getConflictInfo(proposed, proposed.id);
    showGuide(targetColumn, proposed, conflict.hasConflict);
  }

  async function finishPointerInteraction() {
    document.removeEventListener('pointermove', handlePointerMove);

    if (!dragState) return;

    const eventItem = events.find((item) => item.id === dragState.eventId);
    const proposed = dragState.proposed;
    dragState.card.classList.remove('dragging');

    if (!dragState.activated) {
      dragState = null;
      hideGuide();
      return;
    }

    if (eventItem && proposed) {
      const conflict = getConflictInfo(proposed, proposed.id);
      if (conflict.hasConflict) {
        showAlert(buildConflictMessage(conflict, 'No se puede aplicar el cambio'));
      } else {
        Object.assign(eventItem, proposed);
        try {
          await persistEventToApi(eventItem);
        } catch (error) {
          Object.assign(eventItem, dragState.original);
          showAlert(`Error: ${error.message}`, 'error');
        }
      }
    }

    dragState = null;
    hideGuide();
    rerenderActiveViews();
  }

  function showGuide(dayColumn, eventItem, conflict) {
    if (!activeGuide || !dayColumn) return;

    if (activeGuide.parentElement !== dayColumn) dayColumn.appendChild(activeGuide);

    const shownRooms = eventItem.rooms.filter((roomId) => visibleRooms.includes(roomId));
    if (!shownRooms.length) {
      hideGuide();
      return;
    }

    const firstRoomIndex = Math.min(...shownRooms.map((roomId) => visibleRooms.indexOf(roomId)));
    const lastRoomIndex = Math.max(...shownRooms.map((roomId) => visibleRooms.indexOf(roomId)));
    const startMinutes = timeToMinutes(getEventTime(eventItem.start));
    const endMinutes = timeToMinutes(getEventTime(eventItem.end));

    activeGuide.style.display = 'block';
    activeGuide.style.top = `${((startMinutes - START_MIN) / 60) * HOUR_HEIGHT + 3}px`;
    activeGuide.style.height = `${Math.max(42, ((endMinutes - startMinutes) / 60) * HOUR_HEIGHT - 6)}px`;
    activeGuide.style.left = `calc(${(firstRoomIndex / visibleRooms.length) * 100}% + 7px)`;
    activeGuide.style.width = `calc(${(((lastRoomIndex - firstRoomIndex) + 1) / visibleRooms.length) * 100}% - 14px)`;
    activeGuide.classList.toggle('conflict', conflict);
  }

  function hideGuide() {
    if (activeGuide) {
      activeGuide.style.display = 'none';
      activeGuide.classList.remove('conflict');
    }
  }

  function findDayColumnAtPoint(x, y) {
    const element = document.elementFromPoint(x, y);
    return element?.closest?.('.modd-day-column') || null;
  }

  function initFullCalendar() {
    const fullCalendarElement = document.getElementById('modd-fullcalendar');
    if (!fullCalendarElement || typeof FullCalendar === 'undefined') return;

    fullCalendar = new FullCalendar.Calendar(fullCalendarElement, {
      initialView: 'dayGridMonth',
      locale: 'es',
      height: 'auto',
      editable: true,
      selectable: false,
      nowIndicator: true,
      allDaySlot: false,
      slotMinTime: '08:00:00',
      slotMaxTime: '18:00:00',
      slotDuration: '01:00:00',
      snapDuration: '01:00:00',
      defaultTimedEventDuration: '01:00:00',
      headerToolbar: false,
      eventDidMount(info) {
        info.el.addEventListener('dblclick', () => {
          const eventItem = events.find((item) => item.id === info.event.id);
          if (eventItem) openEventModal(eventItem);
        });
      },
      eventDrop(info) {
        updateFromFullCalendarChange(info);
      },
      eventResize(info) {
        updateFromFullCalendarChange(info);
      }
    });

    fullCalendar.render();
  }

  async function updateFromFullCalendarChange(info) {
    const eventItem = events.find((item) => item.id === info.event.id);
    if (!eventItem) return;

    const proposed = {
      ...eventItem,
      start: toLocalDateTime(info.event.start),
      end: toLocalDateTime(info.event.end || addMinutes(info.event.start, 60))
    };

    const conflict = getConflictInfo(proposed, proposed.id);
    if (conflict.hasConflict) {
      info.revert();
      showAlert(buildConflictMessage(conflict, 'No se puede aplicar el cambio'));
      return;
    }

    Object.assign(eventItem, proposed);
    try {
      await persistEventToApi(eventItem);
      renderWeekCalendar();
      renderFullCalendarEvents();
    } catch (error) {
      info.revert();
      showAlert(`Error: ${error.message}`, 'error');
      await cargarEventosDesdeApi();
      rerenderActiveViews();
    }
  }

  function renderFullCalendarEvents() {
    if (!fullCalendar) return;
    fullCalendar.removeAllEvents();
    filteredEvents().forEach((eventItem) => {
      fullCalendar.addEvent({
        id: eventItem.id,
        title: `${eventItem.title} - ${eventItem.rooms.map((roomId) => findRoom(roomId).name).join(', ')}`,
        start: eventItem.start,
        end: eventItem.end,
        backgroundColor: getEventColor(eventItem),
        borderColor: getEventColor(eventItem),
        extendedProps: {
          rooms: eventItem.rooms,
          responsible: eventItem.responsible
        }
      });
    });
  }

  function openEventModal(eventData) {
    const modal = document.getElementById('event-modal');
    const title = document.getElementById('event-modal-title');
    const isExisting = Boolean(eventData.id);
    const date = eventData.date || getEventDate(eventData) || toISODate(new Date());

    if (!modal) return;
    hideModalAlert();

    title.textContent = isExisting ? 'Editar evento' : 'Nueva solicitud';
    document.getElementById('event-id').value = eventData.id || '';
    document.getElementById('request-first-name').value = eventData.requestFirstName || '';
    document.getElementById('request-last-name').value = eventData.requestLastName || '';
    document.getElementById('request-email').value = eventData.requestEmail || '';
    document.getElementById('request-phone').value = eventData.requestPhone || '';
    document.getElementById('event-title').value = eventData.title || '';
    document.getElementById('event-date').value = date;
    document.getElementById('event-start').value = eventData.startTime || getEventTime(eventData.start) || '09:00';
    document.getElementById('event-end').value = eventData.endTime || getEventTime(eventData.end) || '10:00';
    document.getElementById('event-notes').value = eventData.notes || '';
    document.getElementById('event-attendees').value = eventData.attendees || 0;
    document.getElementById('event-layout').value = eventData.requirements?.acomodo || '';
    document.getElementById('event-audio').checked = Boolean(eventData.requirements?.equipo_de_sonido);
    document.getElementById('event-catering').checked = Boolean(eventData.requirements?.cafeteria);
    document.getElementById('event-video').checked = Boolean(eventData.requirements?.videoconferencia);
    document.getElementById('event-delete-button')?.classList.toggle('hidden', !isExisting);

    const selectedRooms = eventData.rooms?.length ? eventData.rooms : ['sala1'];
    document.getElementById('event-room-single').value = selectedRooms[0]?.replace('sala', '') || '1';
    ['request-first-name', 'request-last-name', 'request-email', 'request-phone'].forEach((id) => {
      const input = document.getElementById(id);
      if (input) input.disabled = isExisting;
    });

    modal.classList.remove('hidden');
    modal.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
    setTimeout(() => document.getElementById('event-title')?.focus(), 0);
  }

  function closeEventModal() {
    const modal = document.getElementById('event-modal');
    if (!modal || modal.classList.contains('hidden')) return;

    hideModalAlert();
    modal.classList.add('hidden');
    modal.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
  }

  async function saveEventFromModal(event) {
    event.preventDefault();

    const id = document.getElementById('event-id').value;
    const date = document.getElementById('event-date').value;
    const startTime = document.getElementById('event-start').value;
    const endTime = document.getElementById('event-end').value;
    const selectedRooms = [`sala${document.getElementById('event-room-single').value}`];

    if (!selectedRooms.length) {
      showAlert('Selecciona al menos una sala.');
      return;
    }

    if (timeToMinutes(startTime) >= timeToMinutes(endTime)) {
      showAlert('La hora de fin debe ser posterior a la hora de inicio.');
      return;
    }

    if (!isWholeHour(startTime) || !isWholeHour(endTime)) {
      showAlert('Solo se permiten bloques por hora completa. Usa horas como 08:00, 09:00 o 10:00.');
      return;
    }

    // 1. Armamos el JSON con los nombres exactos que espera tu schema EventoCreate en FastAPI
    const cargaUtilAPI = {
      titulo: document.getElementById('event-title').value.trim(),
      descripcion: document.getElementById('event-notes').value.trim(),
      fecha: date, // "YYYY-MM-DD"
      hora_de_inicio: `${startTime}:00`, // Pydantic espera formato "HH:MM:SS"
      hora_de_termino: `${endTime}:00`,
      // Convertimos los IDs del HTML ['sala1', 'sala2'] a una lista de enteros [1, 2]
      salas_ids: selectedRooms.map(room => parseInt(room.replace('sala', ''))),
      no_de_asistentes: Number(document.getElementById('event-attendees').value || 0)
    };

    // Validacion visual de conflictos antes de guardar.
    const tempProposed = {
      start: `${date}T${startTime}:00`,
      end: `${date}T${endTime}:00`,
      rooms: selectedRooms,
    };
    const conflict = getConflictInfo(tempProposed, id);
    if (conflict.hasConflict) {
      showAlert(buildConflictMessage(conflict, 'No se puede guardar'));
      return;
    }

    // 2. Enviamos los datos al backend
    try {
      const response = id
        ? await fetch(`/api/eventos/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(cargaUtilAPI)
          })
        : await createRequestFromModal(date, startTime, endTime, selectedRooms);

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Error al guardar el evento');
      }

      // 3. Si se guardo bien, volvemos a descargar todos los eventos para que se pinten correctamente.
      await cargarEventosDesdeApi();

      closeEventModal();
      showAlert(id ? 'Evento actualizado correctamente.' : 'Solicitud creada correctamente. Apruebala en la seccion Solicitudes para que aparezca en el calendario.', 'success');
      rerenderActiveViews();

    } catch (error) {
      console.error("Error al guardar:", error);
      showAlert(`Error: ${error.message}`, 'error');
    }
  }

  function hasConflict(proposed, ignoredId) {
    return getConflictInfo(proposed, ignoredId).hasConflict;
  }

  function getConflictInfo(proposed, ignoredId) {
    const proposedStart = new Date(proposed.start).getTime();
    const proposedEnd = new Date(proposed.end).getTime();
    const proposedDate = getEventDate(proposed);
    const occupiedRooms = new Set();
    const conflictingRooms = new Set();

    events.forEach((eventItem) => {
      if (eventItem.id === ignoredId) return;
      if (getEventDate(eventItem) !== proposedDate) return;

      const eventStart = new Date(eventItem.start).getTime();
      const eventEnd = new Date(eventItem.end).getTime();
      if (!(proposedStart < eventEnd && proposedEnd > eventStart)) return;

      eventItem.rooms.forEach((roomId) => {
        occupiedRooms.add(roomId);
        if (proposed.rooms.includes(roomId)) conflictingRooms.add(roomId);
      });
    });

    const availableRooms = rooms
      .map((room) => room.id)
      .filter((roomId) => !occupiedRooms.has(roomId));

    return {
      hasConflict: conflictingRooms.size > 0,
      conflictingRooms: Array.from(conflictingRooms),
      availableRooms
    };
  }

  function buildConflictMessage(conflict, prefix) {
    const base = `${prefix}: el evento se solapa con otro en la misma sala y horario.`;
    if (!conflict.availableRooms.length) {
      return `${base} No hay otra sala disponible en ese bloque.`;
    }
    const suggestions = conflict.availableRooms.map((roomId) => findRoom(roomId).name).join(', ');
    return `${base} Puedes usar ${suggestions} en ese horario.`;
  }

  async function deleteEventFromModal() {
    const id = document.getElementById('event-id').value;
    if (!id) return;

    const confirmed = window.confirm('Eliminar este evento definitivamente?');
    if (!confirmed) return;

    try {
      const response = await fetch(`/api/eventos/${id}`, { method: 'DELETE' });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'No se pudo eliminar el evento.');
      }

      await cargarEventosDesdeApi();
      closeEventModal();
      showAlert('Evento eliminado correctamente.', 'success');
      rerenderActiveViews();
    } catch (error) {
      showAlert(`Error: ${error.message}`, 'error');
    }
  }

  async function createRequestFromModal(date, startTime, endTime, selectedRooms) {
    const payload = {
      solicitante_nombre: document.getElementById('request-first-name').value.trim(),
      solicitante_apellido: document.getElementById('request-last-name').value.trim(),
      solicitante_correo: document.getElementById('request-email').value.trim(),
      solicitante_telefono: document.getElementById('request-phone').value.trim() || null,
      evento_titulo: document.getElementById('event-title').value.trim(),
      evento_descripcion: document.getElementById('event-notes').value.trim() || null,
      evento_fecha: date,
      evento_inicio: `${startTime}:00`,
      evento_fin: `${endTime}:00`,
      evento_asistentes: Number(document.getElementById('event-attendees').value || 0),
      sala_id: parseInt(selectedRooms[0].replace('sala', ''), 10),
      acomodo: document.getElementById('event-layout').value.trim() || null,
      equipo_de_sonido: document.getElementById('event-audio').checked,
      cafeteria: document.getElementById('event-catering').checked,
      videoconferencia: document.getElementById('event-video').checked
    };

    return fetch('/api/solicitudes/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
  }

  function warnExistingConflicts() {
    const conflict = events.some((eventItem, index) => {
      return events.slice(index + 1).some((otherEvent) => {
        if (getEventDate(eventItem) !== getEventDate(otherEvent)) return false;
        if (!eventItem.rooms.some((roomId) => otherEvent.rooms.includes(roomId))) return false;
        const eventStart = new Date(eventItem.start).getTime();
        const eventEnd = new Date(eventItem.end).getTime();
        const otherStart = new Date(otherEvent.start).getTime();
        const otherEnd = new Date(otherEvent.end).getTime();
        return eventStart < otherEnd && eventEnd > otherStart;
      });
    });

    if (conflict) {
      showAlert('Hay eventos ya guardados que se solapan. Mueve o edita uno de ellos para liberar el horario.');
    }
  }

  async function persistEventToApi(eventItem) {
    const response = await fetch(`/api/eventos/${eventItem.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(eventToApiPayload(eventItem))
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'No se pudo guardar el cambio.');
    }
  }

  function eventToApiPayload(eventItem) {
    return {
      titulo: eventItem.title,
      descripcion: eventItem.notes || '',
      fecha: getEventDate(eventItem),
      hora_de_inicio: `${getEventTime(eventItem.start)}:00`,
      hora_de_termino: `${getEventTime(eventItem.end)}:00`,
      no_de_asistentes: eventItem.attendees || eventItem.no_de_asistentes || 0,
      salas_ids: eventItem.rooms.map((room) => parseInt(room.replace('sala', ''), 10))
    };
  }

  function filteredEvents() {
    return events.filter((eventItem) => {
      const matchesSearch = !searchTerm
        || eventItem.title.toLowerCase().includes(searchTerm)
        || eventItem.responsible.toLowerCase().includes(searchTerm);
      const matchesRoom = eventItem.rooms.some((roomId) => visibleRooms.includes(roomId));
      return matchesSearch && matchesRoom;
    });
  }

  function rerenderActiveViews() {
    renderWeekCalendar();
    renderFullCalendarEvents();
    if (activeView !== 'week' && fullCalendar) fullCalendar.updateSize();
  }

  function showAlert(message, type) {
    const modal = document.getElementById('event-modal');
    const modalIsOpen = modal && !modal.classList.contains('hidden');
    const alert = modalIsOpen && type !== 'success'
      ? document.getElementById('event-modal-alert')
      : document.getElementById('calendar-alert');
    if (!alert) return;

    alert.textContent = message;
    alert.classList.add('show');
    alert.classList.toggle('success', type === 'success');
    if (alert.id === 'calendar-alert') {
      alert.style.background = type === 'success' ? '#F0FDF4' : '';
      alert.style.borderColor = type === 'success' ? '#BBF7D0' : '';
      alert.style.color = type === 'success' ? '#166534' : '';
    }
    alert.scrollIntoView({ block: 'nearest', behavior: 'smooth' });

    window.clearTimeout(alertTimer);
    alertTimer = window.setTimeout(() => {
      alert.classList.remove('show');
      alert.classList.remove('success');
      alert.textContent = '';
      alert.removeAttribute('style');
    }, 4200);
  }

  function hideModalAlert() {
    const alert = document.getElementById('event-modal-alert');
    if (!alert) return;
    alert.classList.remove('show', 'success');
    alert.textContent = '';
  }


  function getEventColor(eventItem) {
    return findRoom(eventItem.rooms[0])?.color || '#24398A';
  }

  function findRoom(roomId) {
    return rooms.find((room) => room.id === roomId) || rooms[0];
  }

  function getMonday(date) {
    const copy = new Date(date);
    const day = copy.getDay();
    const diff = copy.getDate() - day + (day === 0 ? -6 : 1);
    copy.setDate(diff);
    copy.setHours(0, 0, 0, 0);
    return copy;
  }

  function addDays(date, days) {
    const copy = new Date(date);
    copy.setDate(copy.getDate() + days);
    return copy;
  }

  function addMinutes(date, minutes) {
    const copy = new Date(date);
    copy.setMinutes(copy.getMinutes() + minutes);
    return copy;
  }

  function parseDate(dateString) {
    const [year, month, day] = dateString.split('-').map(Number);
    return new Date(year, month - 1, day);
  }

  function dayDifference(start, end) {
    const startDate = new Date(start.getFullYear(), start.getMonth(), start.getDate());
    const endDate = new Date(end.getFullYear(), end.getMonth(), end.getDate());
    return Math.round((endDate - startDate) / 86400000);
  }

  function toISODate(date) {
    const copy = new Date(date);
    const year = copy.getFullYear();
    const month = String(copy.getMonth() + 1).padStart(2, '0');
    const day = String(copy.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  }

  function toLocalDateTime(date) {
    return `${toISODate(date)}T${formatMinutes(date.getHours() * 60 + date.getMinutes())}:00`;
  }

  function formatShortDate(date) {
    return `${String(date.getDate()).padStart(2, '0')}/${String(date.getMonth() + 1).padStart(2, '0')}`;
  }

  function formatMinutes(minutes) {
    const hour = Math.floor(minutes / 60);
    const minute = minutes % 60;
    return `${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}`;
  }

  function timeToMinutes(time) {
    const [hour, minute] = time.split(':').map(Number);
    return hour * 60 + minute;
  }

  function isWholeHour(time) {
    return timeToMinutes(time) % STEP_MIN === 0;
  }

  function getEventDate(eventItem) {
    return eventItem?.start?.slice(0, 10);
  }

  function getEventTime(dateTime) {
    return dateTime ? dateTime.slice(11, 16) : '';
  }

  function clamp(value, min, max) {
    return Math.min(Math.max(value, min), max);
  }

  function cloneEvent(eventItem) {
    return {
      ...eventItem,
      rooms: [...eventItem.rooms]
    };
  }

  function escapeHTML(value) {
    return String(value)
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;')
      .replaceAll("'", '&#039;');
  }
})();

