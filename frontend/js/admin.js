const API_URL = 'http://localhost:8000/api';

// Check authentication
function checkAuth() {
    const token = localStorage.getItem('token');
    const userType = localStorage.getItem('user_type');
    
    if (!token || userType !== 'doctor') {
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
    
    // Load data for specific tabs
    if (tabName === 'sale') loadRooms();
    if (tabName === 'attesa') loadWaitingList();
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

function getPriorityBadge(priority) {
    const badges = {
        'urgente': '<span class="badge badge-danger">Urgente</span>',
        'alta': '<span class="badge badge-warning">Alta</span>',
        'media': '<span class="badge badge-info">Media</span>',
        'bassa': '<span class="badge" style="background: #e5e7eb; color: #374151;">Bassa</span>'
    };
    return badges[priority] || priority;
}

// Load Doctors for dropdown
async function loadDoctors() {
    try {
        const response = await fetch(`${API_URL}/doctors/`, {
            headers: getAuthHeaders()
        });
        const doctors = await response.json();
        
        const select = document.getElementById('agenda-doctor');
        doctors.forEach(doctor => {
            const option = document.createElement('option');
            option.value = doctor.id;
            option.textContent = `${doctor.nome} ${doctor.cognome} - ${doctor.specializzazione}`;
            select.appendChild(option);
        });
        
        // Pre-select current doctor
        const currentDoctorId = localStorage.getItem('user_id');
        if (currentDoctorId) {
            select.value = currentDoctorId;
        }
    } catch (error) {
        showAlert('Errore nel caricamento dei medici', 'error');
    }
}

// Load Agenda
async function loadAgenda() {
    const doctorId = document.getElementById('agenda-doctor').value;
    const date = document.getElementById('agenda-date').value;
    
    if (!doctorId || !date) {
        showAlert('Seleziona un medico e una data', 'warning');
        return;
    }
    
    const container = document.getElementById('agenda-content');
    container.innerHTML = '<div class="loading">Caricamento agenda...</div>';
    
    try {
        const response = await fetch(
            `${API_URL}/appointments/detailed?doctor_id=${doctorId}&data=${date}`,
            { headers: getAuthHeaders() }
        );
        const appointments = await response.json();
        
        if (appointments.length === 0) {
            container.innerHTML = '<div class="empty-state">Nessun appuntamento per questa data</div>';
            return;
        }
        
        let html = '<table><thead><tr>';
        html += '<th>Ora</th><th>Paziente</th><th>Tipo Visita</th><th>Durata</th><th>Sala</th><th>Stato</th><th>Contatto</th><th>Azioni</th>';
        html += '</tr></thead><tbody>';
        
        appointments.forEach(apt => {
            html += `<tr>
                <td><strong>${formatTime(apt.ora_inizio)}</strong></td>
                <td>${apt.nome_paziente}</td>
                <td>${apt.tipo_visita}</td>
                <td>${apt.durata_minuti} min</td>
                <td>${apt.sala_numero || 'Non assegnata'}</td>
                <td>${getStatusBadge(apt.stato)}</td>
                <td><small>${apt.telefono_paziente}</small></td>
                <td>
                    <button class="btn btn-sm btn-primary" onclick="viewPatientDetails('${apt.nome_paziente}', ${apt.id})">
                        Dettagli
                    </button>
                </td>
            </tr>`;
        });
        
        html += '</tbody></table>';
        html += `<p class="mt-2"><strong>Totale appuntamenti: ${appointments.length}</strong></p>`;
        container.innerHTML = html;
    } catch (error) {
        container.innerHTML = '<div class="alert alert-error">Errore nel caricamento dell\'agenda</div>';
    }
}

// Load All Appointments
async function loadAllAppointments() {
    const dateFrom = document.getElementById('filter-date-from').value;
    const dateTo = document.getElementById('filter-date-to').value;
    const status = document.getElementById('filter-status').value;
    
    const container = document.getElementById('all-appointments-list');
    container.innerHTML = '<div class="loading">Caricamento appuntamenti...</div>';
    
    try {
        let url = `${API_URL}/appointments/detailed?`;
        if (dateFrom) url += `data_from=${dateFrom}&`;
        if (dateTo) url += `data_to=${dateTo}&`;
        if (status) url += `stato=${status}&`;
        
        const response = await fetch(url, { headers: getAuthHeaders() });
        const appointments = await response.json();
        
        if (appointments.length === 0) {
            container.innerHTML = '<div class="empty-state">Nessun appuntamento trovato</div>';
            return;
        }
        
        let html = '<table><thead><tr>';
        html += '<th>Data</th><th>Ora</th><th>Medico</th><th>Paziente</th><th>Tipo Visita</th><th>Sala</th><th>Stato</th>';
        html += '</tr></thead><tbody>';
        
        appointments.forEach(apt => {
            html += `<tr>
                <td>${formatDate(apt.data_appuntamento)}</td>
                <td>${formatTime(apt.ora_inizio)}</td>
                <td>${apt.nome_medico}<br><small>${apt.specializzazione}</small></td>
                <td>${apt.nome_paziente}</td>
                <td>${apt.tipo_visita}</td>
                <td>${apt.sala_numero || '-'}</td>
                <td>${getStatusBadge(apt.stato)}</td>
            </tr>`;
        });
        
        html += '</tbody></table>';
        html += `<p class="mt-2"><strong>Totale: ${appointments.length} appuntamenti</strong></p>`;
        container.innerHTML = html;
    } catch (error) {
        container.innerHTML = '<div class="alert alert-error">Errore nel caricamento degli appuntamenti</div>';
    }
}

// Load Patients
async function loadPatients() {
    const search = document.getElementById('search-patient').value;
    const container = document.getElementById('patients-list');
    container.innerHTML = '<div class="loading">Ricerca in corso...</div>';
    
    try {
        let url = `${API_URL}/patients/`;
        if (search) url += `?search=${encodeURIComponent(search)}`;
        
        const response = await fetch(url, { headers: getAuthHeaders() });
        const patients = await response.json();
        
        if (patients.length === 0) {
            container.innerHTML = '<div class="empty-state">Nessun paziente trovato</div>';
            return;
        }
        
        let html = '<table><thead><tr>';
        html += '<th>Nome</th><th>Codice Fiscale</th><th>Data Nascita</th><th>Contatti</th><th>Azioni</th>';
        html += '</tr></thead><tbody>';
        
        patients.forEach(patient => {
            html += `<tr>
                <td><strong>${patient.nome} ${patient.cognome}</strong></td>
                <td>${patient.codice_fiscale}</td>
                <td>${new Date(patient.data_nascita).toLocaleDateString('it-IT')}</td>
                <td>
                    ${patient.telefono}<br>
                    <small>${patient.email}</small>
                </td>
                <td>
                    <button class="btn btn-sm btn-primary" onclick="viewPatientHistory(${patient.id})">
                        Storico
                    </button>
                </td>
            </tr>`;
        });
        
        html += '</tbody></table>';
        container.innerHTML = html;
    } catch (error) {
        container.innerHTML = '<div class="alert alert-error">Errore nella ricerca dei pazienti</div>';
    }
}

// View Appointment/Patient Details from Agenda
function viewPatientDetails(nomePaziente, appointmentId) {
    // Cerca l'appuntamento nei dati già caricati
    const container = document.getElementById('agenda-content');
    const table = container.querySelector('table');
    
    if (!table) {
        showAlert('Nessun dato disponibile', 'warning');
        return;
    }
    
    // Recupera i dettagli dall'appuntamento tramite API
    fetch(`${API_URL}/appointments/${appointmentId}`, {
        headers: getAuthHeaders()
    })
    .then(response => response.json())
    .then(apt => {
        let html = `
            <div class="mb-2">
                <h4>Dettagli Appuntamento #${appointmentId}</h4>
                <hr style="margin: 1rem 0;">
                <p><strong>Paziente:</strong> ${nomePaziente}</p>
                <p><strong>Tipo Visita:</strong> ${apt.tipo_visita || 'N/A'}</p>
                <p><strong>Data:</strong> ${apt.data_appuntamento ? formatDate(apt.data_appuntamento) : 'N/A'}</p>
                <p><strong>Orario:</strong> ${apt.ora_inizio ? formatTime(apt.ora_inizio) : 'N/A'}</p>
                <p><strong>Durata:</strong> ${apt.durata_minuti || 'N/A'} minuti</p>
                <p><strong>Stato:</strong> ${apt.stato ? getStatusBadge(apt.stato) : 'N/A'}</p>
                <p><strong>Note:</strong> ${apt.note || 'Nessuna nota'}</p>
            </div>
        `;
        
        document.getElementById('patient-details').innerHTML = html;
        document.getElementById('patient-modal').classList.add('active');
    })
    .catch(error => {
        // Fallback: mostra solo il nome del paziente
        let html = `
            <div class="mb-2">
                <h4>Paziente: ${nomePaziente}</h4>
                <p>ID Appuntamento: ${appointmentId}</p>
                <p><em>Dettagli completi non disponibili</em></p>
            </div>
        `;
        document.getElementById('patient-details').innerHTML = html;
        document.getElementById('patient-modal').classList.add('active');
    });
}

// View Patient History
async function viewPatientHistory(patientId) {
    try {
        const response = await fetch(
            `${API_URL}/patients/${patientId}/history`,
            { headers: getAuthHeaders() }
        );
        const data = await response.json();
        
        let html = `
            <div class="mb-2">
                <h4>Paziente: ${data.patient.nome}</h4>
                <p>Codice Fiscale: ${data.patient.codice_fiscale}</p>
                <p><strong>Totale visite: ${data.total_visits}</strong></p>
            </div>
        `;
        
        if (data.history.length > 0) {
            html += '<table><thead><tr>';
            html += '<th>Data</th><th>Medico</th><th>Tipo Visita</th><th>Stato</th><th>Note</th>';
            html += '</tr></thead><tbody>';
            
            data.history.forEach(visit => {
                html += `<tr>
                    <td>${formatDate(visit.data)}</td>
                    <td>${visit.medico}<br><small>${visit.specializzazione}</small></td>
                    <td>${visit.tipo_visita}</td>
                    <td>${getStatusBadge(visit.stato)}</td>
                    <td>${visit.note || '-'}</td>
                </tr>`;
            });
            
            html += '</tbody></table>';
        }
        
        document.getElementById('patient-details').innerHTML = html;
        document.getElementById('patient-modal').classList.add('active');
    } catch (error) {
        showAlert('Errore nel caricamento dello storico paziente', 'error');
    }
}

function closePatientModal() {
    document.getElementById('patient-modal').classList.remove('active');
}

// Load Rooms
async function loadRooms() {
    const container = document.getElementById('rooms-list');
    
    try {
        const response = await fetch(`${API_URL}/rooms/`, { headers: getAuthHeaders() });
        const rooms = await response.json();
        
        let html = '<div class="grid">';
        
        rooms.forEach(room => {
            const attrezzature = room.attrezzature ? JSON.parse(room.attrezzature) : [];
            
            html += `
                <div class="card">
                    <h3>Sala ${room.numero}</h3>
                    <p><strong>${room.nome}</strong></p>
                    <p>Piano: ${room.piano}</p>
                    <p>Capienza: ${room.capienza} persone</p>
                    <p>Stato: ${room.attiva ? 
                        '<span class="badge badge-success">Attiva</span>' : 
                        '<span class="badge badge-danger">Non attiva</span>'}
                    </p>
                    <div class="mt-1">
                        <strong>Attrezzature:</strong>
                        <ul style="margin-top: 8px; padding-left: 20px;">
                            ${attrezzature.map(a => `<li>${a}</li>`).join('')}
                        </ul>
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
        container.innerHTML = html;
    } catch (error) {
        container.innerHTML = '<div class="alert alert-error">Errore nel caricamento delle sale</div>';
    }
}

// Load Waiting List
async function loadWaitingList() {
    const container = document.getElementById('waiting-list');
    
    try {
        const response = await fetch(`${API_URL}/appointments/waiting-list`, { headers: getAuthHeaders() });
        const waitingList = await response.json();
        
        if (waitingList.length === 0) {
            container.innerHTML = '<div class="empty-state">Nessun paziente in lista d\'attesa</div>';
            return;
        }
        
        let html = '<table><thead><tr>';
        html += '<th>Paziente</th><th>Telefono</th><th>Tipo Visita</th><th>Specializzazione</th><th>Medico</th><th>Priorità</th><th>Data Richiesta</th>';
        html += '</tr></thead><tbody>';
        
        waitingList.forEach(item => {
            html += `<tr>
                <td><strong>${item.paziente}</strong></td>
                <td>${item.telefono}</td>
                <td>${item.tipo_visita}</td>
                <td>${item.specializzazione || '-'}</td>
                <td>${item.medico || 'Non specificato'}</td>
                <td>${getPriorityBadge(item.priorita)}</td>
                <td>${new Date(item.data_richiesta).toLocaleDateString('it-IT')}</td>
            </tr>`;
        });
        
        html += '</tbody></table>';
        container.innerHTML = html;
    } catch (error) {
        container.innerHTML = '<div class="alert alert-error">Errore nel caricamento della lista d\'attesa</div>';
    }
}

// Initialize
window.addEventListener('DOMContentLoaded', () => {
    // Display user name
    const userName = localStorage.getItem('user_name');
    if (userName) {
        const header = document.querySelector('header p');
        header.textContent = `Benvenuto, Dr. ${userName}`;
    }
    
    // Set today's date
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('agenda-date').value = today;
    
    // Load doctors
    loadDoctors();
    
    // Auto-load today's agenda for current doctor
    const currentDoctorId = localStorage.getItem('user_id');
    if (currentDoctorId) {
        setTimeout(() => {
            document.getElementById('agenda-doctor').value = currentDoctorId;
            loadAgenda();
        }, 500);
    }
});