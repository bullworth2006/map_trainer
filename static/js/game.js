let map, marker, correctMarker;
let session_id = null;
let current_location = null;
let timerInterval = null;
let sprintInterval = null;
let startTime = null;
let score = 0;
let canClick = false;

// Параметры из URL
const params = new URLSearchParams(window.location.search);
const mode = params.get('mode') || 'training';
const difficulty = params.get('difficulty') || 'easy';
const extra = params.get('extra') || '';

const EXAM_ROUNDS = 10;
const SPRINT_SECONDS = 60;
let roundsPlayed = 0;
let sprintTimeLeft = SPRINT_SECONDS;
let sprintActive = false;

// Инициализация карты
map = L.map('map').setView([42.8746, 74.5698], 13);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors'
}).addTo(map);

// Режим без зума — после инициализации карты
if (extra === 'nozoom') {
    map.touchZoom.disable();
    map.doubleClickZoom.disable();
    map.scrollWheelZoom.disable();
    map.boxZoom.disable();
    map.keyboard.disable();
    document.querySelector('.leaflet-control-zoom').style.display = 'none';
}


document.getElementById('modeLabel').textContent = {
    training: 'Тренировка',
    exam: `Экзамен (${EXAM_ROUNDS} заданий)`,
    sprint: `Спринт (${SPRINT_SECONDS} сек)`
}[mode];

// Клик по карте
map.on('click', function(e) {
    if (!canClick) return;

    const lat = e.latlng.lat;
    const lng = e.latlng.lng;

    if (marker) map.removeLayer(marker);
    marker = L.marker([lat, lng]).addTo(map);

    canClick = false;
    stopTimer();

    const time_seconds = (Date.now() - startTime) / 1000;
    submitAnswer(lat, lng, time_seconds);
});

document.getElementById('startBtn').addEventListener('click', startGame);
document.getElementById('nextBtn').addEventListener('click', nextRound);

async function startGame() {
    const response = await fetch('/api/session/start/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify({ mode: mode, difficulty: difficulty })
    });
    const data = await response.json();
    session_id = data.session_id;

    document.getElementById('startBtn').style.display = 'none';
    score = 0;
    roundsPlayed = 0;
    document.getElementById('scoreValue').textContent = score;

    if (mode === 'sprint') {
        startSprintTimer();
    }

    await loadLocation();
}

function startSprintTimer() {
    sprintActive = true;
    sprintTimeLeft = SPRINT_SECONDS;
    document.getElementById('sprintCard').style.display = 'block';
    document.getElementById('sprintValue').textContent = sprintTimeLeft;

    sprintInterval = setInterval(() => {
        sprintTimeLeft--;
        document.getElementById('sprintValue').textContent = sprintTimeLeft;

        if (sprintTimeLeft <= 0) {
            clearInterval(sprintInterval);
            sprintActive = false;
            endSession();
        }
    }, 1000);
}

async function loadLocation() {
    document.getElementById('resultCard').classList.remove('show');
    document.getElementById('nextBtn').classList.remove('show');

    if (marker) { map.removeLayer(marker); marker = null; }
    if (correctMarker) { map.removeLayer(correctMarker); correctMarker = null; }

    let url = `/api/location/?difficulty=${difficulty}`;
    if (current_location) {
        url += `&exclude_id=${current_location.id}`;
    }

    const response = await fetch(url);
    const data = await response.json();
    current_location = data;

    document.getElementById('addressCard').style.display = 'block';
    document.getElementById('addressText').textContent = data.address;
    document.getElementById('timerCard').style.display = 'block';

    canClick = true;
    startTimer();
}

function startTimer() {
    startTime = Date.now();
    document.getElementById('timerValue').textContent = '00.0';
    document.getElementById('timerValue').classList.remove('danger');

    timerInterval = setInterval(() => {
        const elapsed = (Date.now() - startTime) / 1000;
        document.getElementById('timerValue').textContent = elapsed.toFixed(1);

        if (elapsed > 20) {
            document.getElementById('timerValue').classList.add('danger');
        }
    }, 100);
}

function stopTimer() {
    clearInterval(timerInterval);
}

async function submitAnswer(lat, lng, time_seconds) {
    const response = await fetch('/api/answer/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify({
            session_id: session_id,
            location_id: current_location.id,
            user_lat: lat,
            user_lng: lng,
            time_seconds: time_seconds,
        })
    });
    const data = await response.json();
    showResult(data);
}

function showResult(data) {
    score += data.score;
    roundsPlayed++;
    document.getElementById('scoreValue').textContent = score;

    if (data.combo_multiplier > 1) {
        document.getElementById('comboValue').textContent = `Комбо x${data.combo_multiplier}`;
    } else {
        document.getElementById('comboValue').textContent = '';
    }

    correctMarker = L.marker([data.correct_lat, data.correct_lng], {
        icon: L.icon({
            iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-green.png',
            iconSize: [25, 41],
            iconAnchor: [12, 41],
        })
    }).addTo(map);

    L.polyline([marker.getLatLng(), correctMarker.getLatLng()], {color: '#F5A623', dashArray: '5,5'}).addTo(map);

    const resultCard = document.getElementById('resultCard');
    const resultDistance = document.getElementById('resultDistance');
    const resultScore = document.getElementById('resultScore');

    resultDistance.textContent = `${data.distance_meters} м`;

    if (data.distance_meters <= 5) {
        resultDistance.className = 'result-distance good';
    } else if (data.distance_meters <= 50) {
        resultDistance.className = 'result-distance ok';
    } else {
        resultDistance.className = 'result-distance bad';
    }

    resultScore.textContent = `+${data.score} очков`;
    resultCard.classList.add('show');

    if (mode === 'exam' && roundsPlayed >= EXAM_ROUNDS) {
        document.getElementById('nextBtn').textContent = 'Завершить экзамен';
        document.getElementById('nextBtn').classList.add('show');
        document.getElementById('nextBtn').dataset.final = 'true';
        return;
    }

    if (mode === 'sprint') {
        if (sprintActive) {
            setTimeout(() => loadLocation(), 800);
        }
        return;
    }

    document.getElementById('nextBtn').classList.add('show');
}

async function nextRound() {
    if (document.getElementById('nextBtn').dataset.final === 'true') {
        endSession();
        return;
    }
    await loadLocation();
}

async function endSession() {
    stopTimer();
    canClick = false;

    const response = await fetch('/api/session/finish/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify({ session_id: session_id })
    });
    const data = await response.json();

    document.getElementById('addressCard').style.display = 'none';
    document.getElementById('timerCard').style.display = 'none';
    document.getElementById('sprintCard').style.display = 'none';
    document.getElementById('resultCard').classList.remove('show');
    document.getElementById('nextBtn').classList.remove('show');

    document.getElementById('finalCard').style.display = 'block';
    document.getElementById('finalScore').textContent = data.total_score;
    document.getElementById('finalRounds').textContent = data.total_rounds;
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Hotkeys
document.addEventListener('keydown', function(e) {
    switch(e.key) {
        case 'Enter':
            const startBtn = document.getElementById('startBtn');
            const nextBtn = document.getElementById('nextBtn');
            if (startBtn.style.display !== 'none') {
                startBtn.click();
            } else if (nextBtn.classList.contains('show')) {
                nextBtn.click();
            }
            break;
        case '+':
            map.zoomIn();
            break;
        case '-':
            map.zoomOut();
            break;
        case 'r':
        case 'R':
            map.setView([42.8746, 74.5698], 13);
            break;
    }
});