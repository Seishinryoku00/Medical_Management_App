const API_URL = 'http://localhost:8000/api';

let selectedSlot = null;
let appointmentToCancel = null;

// Check authentication
function checkAuth() {
    const token = localStorage.getItem('token');
    const userType = localStorage.getItem('user_type');
    
    if (!token || userType !== 'patient') {
        window.location.href = 'login.html';
        return false;
    }
    return true;
}

// Get auth headers
function getAuthHeaders() {
    const token = localStorage.getItem('token');
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
    };
}

// Logout function
function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user_type');
    localStorage.removeItem('user_id');
    localStorage.removeItem('user_name');
    window.location.href = 'login.html';
}

// Initialize - Check auth first
if (!checkAuth()) {
    throw new Error('Not authenticated');
}

// Utility Functions
function showAlert(message, type = 'info') {
    const container = document.getElementById('alert-container');
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.textContent = message;
    container.appendChild(alert);
    
    setTimeout(() => alert.remove(), 5000);
}

function showTab(tabName) {
    document.querySelectorAll('.tab-content').forEach(tab => tab.classList.add('hidden'));
    document.querySelectorAll('.nav-tabs button').forEach(btn => btn.classList.remove('active'));
    
    document.getElementById(`tab-${tabName}`).classList.remove('hidden');
    event.target.classList.add('active');
}

function formatDate(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleDateString('it-IT', { 
        weekday: 'long', 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric' 
    });
}

function formatTime(timeStr) {
    return timeStr.substring(0, 5);
}

function getStatusBadge(status) {
    const badges = {
        'programmato': '<span class="badge badge-info">Programmato</span>',
        'completato': '<span class="badge badge-success">Completato</span>',
        'cancellato': '<span class="badge badge-danger">Cancellato</span>',
        'in_attesa': '<span class="badge badge-warning">In Attesa</span>'
    };
    return badges[status] || status;
}

// Load Specializations
async function loadSpecializations() {
    try {
        const response = await fetch(`${API_URL}/doctors/`);
        const doctors = await response.json();
        
        const specializations = [...new Set(doctors.map(d => d.specializzazione))];
        const select = document.getElementById('specializzazione');
        
        specializations.forEach(spec => {
            const option = document.createElement('option');
            option.value = spec;
            option.textContent = spec;
            select.appendChild(option);
        });
    } catch (error) {
        showAlert('Errore nel caricamento delle specializzazioni', 'error');
    }
}

// Booking Form Handler
document.getElementById('booking-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const patientId = localStorage.getItem('user_id');
    const specializzazione = document.getElementById('specializzazione').value;
    
    try {
        const today = new Date().toISOString().split('T')[0];
        const endDate = new Date();
        endDate.setDate(endDate.getDate() + 30);
        const endDateStr = endDate.toISOString().split('T')[0];
        
        const response = await fetch(
            `${API_URL}/appointments/available-slots?specializzazione=${specializzazione}&start_date=${today}&end_date=${endDateStr}`,
            { headers: getAuthHeaders() }
        );
        const data = await response.json();
        
        if (data.available_slots.length === 0) {
            showAlert('Nessuna disponibilità trovata per questa specializzazione', 'warning');
            return;
        }
        
        displayAvailableSlots(data.available_slots);
        showAlert(`Trovati ${data.total} slot disponibili`, 'success');
    } catch (error) {
        showAlert('Errore nella ricerca delle disponibilità', 'error');
    }
});

// Display Available Slots
function displayAvailableSlots(slots) {
    const container = document.getElementById('slots-container');
    container.innerHTML = '';
    
    // Group by date
    const slotsByDate = {};
    slots.forEach(slot => {
        if (!slotsByDate[slot.data]) {
            slotsByDate[slot.data] = [];
        }
        slotsByDate[slot.data].push(slot);
    });
    
    // Display max 50 slots
    const limitedSlots = slots.slice(0, 50);
    
    limitedSlots.forEach(slot => {
        const slotDiv = document.createElement('div');
        slotDiv.className = 'slot';
        slotDiv.innerHTML = `
            <div class="slot-time">${formatTime(slot.ora)}</div>
            <div class="slot-info">${formatDate(slot.data)}</div>
            <div class="slot-info">${slot.nome_medico}</div>
        `;
        slotDiv.onclick = () => selectSlot(slotDiv, slot);
        container.appendChild(slotDiv);
    });
    
    document.getElementById('available-slots').classList.remove('hidden');
}

// Select Slot
function selectSlot(element, slot) {
    document.querySelectorAll('.slot').forEach(s => s.classList.remove('selected'));
    element.classList.add('selected');
    selectedSlot = slot;
}

// Confirm Booking
async function confirmBooking() {
    if (!selectedSlot) {
        showAlert('Seleziona un orario disponibile', 'warning');
        return;
    }
    
    const patientId = localStorage.getItem('user_id');
    const tipoVisita = document.getElementById('tipo-visita').value;
    const durata = parseInt(document.getElementById('durata').value);
    const note = document.getElementById('note').value;
    
    const appointment = {
        doctor_id: selectedSlot.doctor_id,
        patient_id: parseInt(patientId),
        data_appuntamento: selectedSlot.data,
        ora_inizio: selectedSlot.ora,
        durata_minuti: durata,
        tipo_visita: tipoVisita,
        note: note || null
    };
    
    try {
        const response = await fetch(`${API_URL}/appointments/`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify(appointment)
        });
        
        if (response.ok) {
            showAlert('Appuntamento prenotato con successo!', 'success');
            document.getElementById('booking-form').reset();
            document.getElementById('available-slots').classList.add('hidden');
            selectedSlot = null;
        } else {
            const error = await response.json();
            showAlert(error.detail || 'Errore nella prenotazione', 'error');
        }
    } catch (error) {
        showAlert('Errore nella prenotazione dell\'appuntamento', 'error');
    }
}

// Load My Appointments
async function loadMyAppointments() {
    const patientId = localStorage.getItem('user_id');
    
    const container = document.getElementById('appointments-list');
    container.innerHTML = '<div class="loading">Caricamento in corso...</div>';
    
    try {
        const today = new Date().toISOString().split('T')[0];
        const response = await fetch(
            `${API_URL}/appointments/detailed?patient_id=${patientId}`,
            { headers: getAuthHeaders() }
        );
        const appointments = await response.json();
        
        const future = appointments.filter(a => 
            a.data_appuntamento >= today && a.stato === 'programmato'
        );
        
        if (future.length === 0) {
            container.innerHTML = '<div class="empty-state">Nessun appuntamento programmato</div>';
            return;
        }
        
        let html = '<table><thead><tr>';
        html += '<th>Data</th><th>Ora</th><th>Medico</th><th>Tipo Visita</th><th>Stato</th><th>Azioni</th>';
        html += '</tr></thead><tbody>';
        
        future.forEach(apt => {
            html += `<tr>
                <td>${formatDate(apt.data_appuntamento)}</td>
                <td>${formatTime(apt.ora_inizio)}</td>
                <td>${apt.nome_medico}<br><small>${apt.specializzazione}</small></td>
                <td>${apt.tipo_visita}</td>
                <td>${getStatusBadge(apt.stato)}</td>
                <td>
                    <button class="btn btn-danger btn-sm" onclick="openCancelModal(${apt.id})">
                        Cancella
                    </button>
                </td>
            </tr>`;
        });
        
        html += '</tbody></table>';
        container.innerHTML = html;
    } catch (error) {
        container.innerHTML = '<div class="alert alert-error">Errore nel caricamento degli appuntamenti</div>';
    }
}

// Load Patient History
async function loadPatientHistory() {
    const patientId = localStorage.getItem('user_id');
    
    const container = document.getElementById('history-list');
    container.innerHTML = '<div class="loading">Caricamento in corso...</div>';
    
    try {
        const response = await fetch(
            `${API_URL}/patients/${patientId}/history`,
            { headers: getAuthHeaders() }
        );
        const data = await response.json();
        
        if (data.history.length === 0) {
            container.innerHTML = '<div class="empty-state">Nessuna visita registrata</div>';
            return;
        }
        
        let html = '<table><thead><tr>';
        html += '<th>Data</th><th>Medico</th><th>Specializzazione</th><th>Tipo Visita</th><th>Stato</th><th>Note</th>';
        html += '</tr></thead><tbody>';
        
        data.history.forEach(visit => {
            html += `<tr>
                <td>${formatDate(visit.data)}</td>
                <td>${visit.medico}</td>
                <td>${visit.specializzazione}</td>
                <td>${visit.tipo_visita}</td>
                <td>${getStatusBadge(visit.stato)}</td>
                <td>${visit.note || '-'}</td>
            </tr>`;
        });
        
        html += '</tbody></table>';
        html += `<p class="mt-2 text-center"><strong>Totale visite: ${data.total_visits}</strong></p>`;
        container.innerHTML = html;
    } catch (error) {
        container.innerHTML = '<div class="alert alert-error">Errore nel caricamento dello storico</div>';
    }
}

// Cancel Appointment Modal
function openCancelModal(appointmentId) {
    appointmentToCancel = appointmentId;
    document.getElementById('cancel-modal').classList.add('active');
}

function closeCancelModal() {
    document.getElementById('cancel-modal').classList.remove('active');
    appointmentToCancel = null;
    document.getElementById('cancel-reason').value = '';
}

async function confirmCancel() {
    if (!appointmentToCancel) return;
    
    const reason = document.getElementById('cancel-reason').value;
    
    try {
        const url = `${API_URL}/appointments/${appointmentToCancel}${reason ? '?motivo=' + encodeURIComponent(reason) : ''}`;
        const response = await fetch(url, {
            method: 'DELETE',
            headers: getAuthHeaders()
        });
        
        if (response.ok) {
            showAlert('Appuntamento cancellato con successo', 'success');
            closeCancelModal();
            loadMyAppointments();
        } else {
            const error = await response.json();
            showAlert(error.detail || 'Errore nella cancellazione', 'error');
        }
    } catch (error) {
        showAlert('Errore nella cancellazione dell\'appuntamento', 'error');
    }
}

// Initialize
window.addEventListener('DOMContentLoaded', () => {
    // Display user name
    const userName = localStorage.getItem('user_name');
    if (userName) {
        const header = document.querySelector('header p');
        header.textContent = `Benvenuto, ${userName}`;
    }
    
    loadSpecializations();
    
    // Auto-load appointments
    loadMyAppointments();
});