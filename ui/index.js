const API_URL = 'http://localhost:5000/api';
let scene, camera, renderer, servos = [];
let anglesChart, errorChart;
let servoData = {};

// Inicializar escena 3D
function init3DScene() {
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0xffffff); // FONDO BLANCO

    camera = new THREE.PerspectiveCamera(75, 1, 0.1, 1000);
    camera.position.set(0, 8, 15);
    camera.lookAt(0, 0, 0);

    const container = document.getElementById('scene-container');
    renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    container.appendChild(renderer.domElement);

    // Iluminación mejorada
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.7);
    scene.add(ambientLight);
    
    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.9);
    directionalLight.position.set(10, 15, 10);
    directionalLight.castShadow = true;
    directionalLight.shadow.mapSize.width = 2048;
    directionalLight.shadow.mapSize.height = 2048;
    scene.add(directionalLight);

    crearPiernasRealistas();

    // Grid con fondo blanco y líneas grises oscuras
    const gridHelper = new THREE.GridHelper(20, 20, 0x888888, 0xcccccc);
    scene.add(gridHelper);

    animate3D();
}

function crearPiernasRealistas() {
    const legPositions = [
        { x: -3, name: 'Pierna Izquierda' },
        { x: 3, name: 'Pierna Derecha' }
    ];

    legPositions.forEach((legPos, legIndex) => {
        // Grupo principal de la pierna
        const piernaGrupo = new THREE.Group();
        piernaGrupo.position.x = legPos.x;
        piernaGrupo.position.y = 0;
        scene.add(piernaGrupo);

        // SERVO 1: CADERA (Hip)
        const caderaGeometry = new THREE.BoxGeometry(1.2, 0.8, 1.2);
        const caderaMaterial = new THREE.MeshPhongMaterial({ color: 0x00ff00 });
        const cadera = new THREE.Mesh(caderaGeometry, caderaMaterial);
        cadera.position.y = 0;
        cadera.castShadow = true;
        piernaGrupo.add(cadera);

        // SERVO 2: MUSLO (Thigh)
        const musloGroup = new THREE.Group();
        musloGroup.position.y = -1.5; // Posicionado debajo de la cadera
        
        const musloGeometry = new THREE.BoxGeometry(0.8, 3, 0.8);
        const musloMaterial = new THREE.MeshPhongMaterial({ color: 0x0066ff });
        const muslo = new THREE.Mesh(musloGeometry, musloMaterial);
        muslo.position.y = -1.5;
        muslo.castShadow = true;
        musloGroup.add(muslo);
        
        cadera.add(musloGroup); // El muslo es hijo de la cadera

        // SERVO 3: PANTORRILLA (Shin)
        const pantorrillaGroup = new THREE.Group();
        pantorrillaGroup.position.y = -3; // Posicionado debajo del muslo
        
        const pantorrillaGeometry = new THREE.BoxGeometry(0.6, 3, 0.6);
        const pantorrillaMaterial = new THREE.MeshPhongMaterial({ color: 0xff6600 });
        const pantorrilla = new THREE.Mesh(pantorrillaGeometry, pantorrillaMaterial);
        pantorrilla.position.y = -1.5;
        pantorrilla.castShadow = true;
        pantorrillaGroup.add(pantorrilla);
        
        musloGroup.add(pantorrillaGroup); // La pantorrilla es hija del muslo

        // SERVO 4: PIE (Foot)
        const pieGeometry = new THREE.BoxGeometry(0.8, 0.4, 1.5);
        const pieMaterial = new THREE.MeshPhongMaterial({ color: 0xff0000 });
        const pie = new THREE.Mesh(pieGeometry, pieMaterial);
        pie.position.y = -3.5;
        pie.castShadow = true;
        pantorrillaGroup.add(pie); // El pie es hijo de la pantorrilla

        // Guardar referencias para animación
        servos.push({ 
            mesh: cadera, 
            group: musloGroup, 
            id: legIndex * 3 + 1,
            tipo: 'cadera'
        });
        servos.push({ 
            mesh: musloGroup, 
            group: pantorrillaGroup, 
            id: legIndex * 3 + 2,
            tipo: 'muslo'
        });
        servos.push({ 
            mesh: pantorrillaGroup, 
            group: pie, 
            id: legIndex * 3 + 3,
            tipo: 'pantorrilla'
        });
    });
}


function animate3D() {
    requestAnimationFrame(animate3D);
    
    servos.forEach((servo) => {
        const servoId = `servo${servo.id}`;
        if (servoData[servoId]) {
            const angle = (servoData[servoId].angle - 90) * Math.PI / 180;
            
            // Rotar cada segmento en su eje Z (movimiento hacia adelante/atrás)
            if (servo.tipo === 'cadera') {
                servo.mesh.rotation.z = angle;
            } else if (servo.tipo === 'muslo') {
                servo.mesh.rotation.z = angle;
            } else if (servo.tipo === 'pantorrilla') {
                servo.mesh.rotation.z = angle;
            }
        }
    });

    renderer.render(scene, camera);
}
// Inicializar cámara
async function initCamera() {
    try {
        // Intentar verificar si hay cámara WebSocket disponible
        const cameraStatus = await fetch(`${API_URL}/camera/status`).then(r => r.json());
        
        if (cameraStatus.available) {
            // Usar WebSocket de Python (implementar según tu servidor)
            document.getElementById('camera-status').textContent = 'Cámara WebSocket';
            document.getElementById('camera-status').className = 'camera-status camera-active';
        } else {
            // Usar cámara local del navegador
            const stream = await navigator.mediaDevices.getUserMedia({ 
                video: { width: 1280, height: 720 } 
            });
            document.getElementById('camera-feed').srcObject = stream;
            document.getElementById('camera-status').textContent = 'Cámara Local';
            document.getElementById('camera-status').className = 'camera-status camera-active';
        }
    } catch (err) {
        console.error('Error al inicializar cámara:', err);
        document.getElementById('camera-status').textContent = 'Sin Cámara';
    }
}

// Crear controles de servos
function createServoControls() {
    const container = document.getElementById('servo-controls');
    for (let i = 1; i <= 6; i++) {
        const servoId = `servo${i}`;
        const div = document.createElement('div');
        div.className = 'servo-item';
        div.innerHTML = `
            <h3>Servo ${i}</h3>
            <div class="slider-group">
                <label>Ángulo: <span class="value-display" id="${servoId}-angle-val">90°</span></label>
                <input type="range" id="${servoId}-angle" min="0" max="180" value="90" 
                        oninput="updateServo('${servoId}', 'angle', this.value)">
            </div>
            <div class="slider-group">
                <label>Kp: <span class="value-display" id="${servoId}-kp-val">1.0</span></label>
                <input type="range" id="${servoId}-kp" min="0" max="5" step="0.1" value="1.0"
                        oninput="updateServo('${servoId}', 'kp', this.value)">
            </div>
            <div class="slider-group">
                <label>Ki: <span class="value-display" id="${servoId}-ki-val">0.0</span></label>
                <input type="range" id="${servoId}-ki" min="0" max="2" step="0.1" value="0.0"
                        oninput="updateServo('${servoId}', 'ki', this.value)">
            </div>
            <div class="slider-group">
                <label>Kd: <span class="value-display" id="${servoId}-kd-val">0.0</span></label>
                <input type="range" id="${servoId}-kd" min="0" max="2" step="0.1" value="0.0"
                        oninput="updateServo('${servoId}', 'kd', this.value)">
            </div>
        `;
        container.appendChild(div);
    }
}

// Actualizar servo
async function updateServo(servoId, param, value) {
    document.getElementById(`${servoId}-${param}-val`).textContent = 
        param === 'angle' ? `${value}°` : value;
    
    const data = { [param]: parseFloat(value) };
    try {
        await fetch(`${API_URL}/servo/${servoId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
    } catch (err) {
        console.error('Error al actualizar servo:', err);
    }
}

// Enviar comando de movimiento
async function sendCommand(command) {
    try {
        const response = await fetch(`${API_URL}/command`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command })
        });
        const data = await response.json();
        updateServoData(data.servos);
    } catch (err) {
        console.error('Error al enviar comando:', err);
    }
}

// Actualizar datos de servos
function updateServoData(data) {
    servoData = data;
    let totalAngle = 0;
    for (const [servoId, values] of Object.entries(data)) {
        totalAngle += values.angle;
        document.getElementById(`${servoId}-angle`).value = values.angle;
        document.getElementById(`${servoId}-angle-val`).textContent = `${values.angle}°`;
    }
    document.getElementById('total-angle').textContent = `${Math.round(totalAngle)}°`;
}

// Inicializar gráficas
function initCharts() {
    const commonOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { labels: { color: '#fff' } } },
        scales: {
            y: { ticks: { color: '#fff' }, grid: { color: 'rgba(255,255,255,0.1)' } },
            x: { ticks: { color: '#fff' }, grid: { color: 'rgba(255,255,255,0.1)' } }
        }
    };

    anglesChart = new Chart(document.getElementById('angles-chart'), {
        type: 'line',
        data: {
            labels: [],
            datasets: Array.from({ length: 6 }, (_, i) => ({
                label: `Servo ${i + 1}`,
                data: [],
                borderColor: `hsl(${i * 60}, 70%, 60%)`,
                tension: 0.4
            }))
        },
        options: commonOptions
    });

    errorChart = new Chart(document.getElementById('error-chart'), {
        type: 'bar',
        data: {
            labels: ['S1', 'S2', 'S3', 'S4', 'S5', 'S6'],
            datasets: [{
                label: 'Error',
                data: [0, 0, 0, 0, 0, 0],
                backgroundColor: 'rgba(255, 99, 132, 0.5)'
            }]
        },
        options: commonOptions
    });
}

// Actualizar gráficas
async function updateCharts() {
    try {
        const telemetry = await fetch(`${API_URL}/telemetry`).then(r => r.json());
        
        // Actualizar gráfica de ángulos
        if (anglesChart.data.labels.length > 20) {
            anglesChart.data.labels.shift();
            anglesChart.data.datasets.forEach(ds => ds.data.shift());
        }
        
        anglesChart.data.labels.push(new Date().toLocaleTimeString());
        anglesChart.data.datasets.forEach((ds, i) => {
            ds.data.push(telemetry.angles[i]);
        });
        anglesChart.update('none');

        // Actualizar gráfica de errores
        errorChart.data.datasets[0].data = telemetry.errors;
        errorChart.update('none');
    } catch (err) {
        console.error('Error al actualizar gráficas:', err);
    }
}

// Polling de datos
async function pollData() {
    try {
        const data = await fetch(`${API_URL}/servos`).then(r => r.json());
        updateServoData(data);
        document.getElementById('status-indicator').className = 'status-indicator status-connected';
        document.getElementById('connection-status').textContent = 'Conectado';
    } catch (err) {
        document.getElementById('status-indicator').className = 'status-indicator status-disconnected';
        document.getElementById('connection-status').textContent = 'Desconectado';
    }
}

// Control con teclado
document.addEventListener('keydown', (e) => {
    const key = e.key.toUpperCase();
    if (['W', 'A', 'S', 'D'].includes(key)) {
        sendCommand(key);
        e.preventDefault();
    }
});

// Inicialización
window.addEventListener('load', () => {
    init3DScene();
    initCamera();
    createServoControls();
    initCharts();
    
    // Polling cada 100ms
    setInterval(pollData, 100);
    setInterval(updateCharts, 1000);
    
    // Cargar datos iniciales
    pollData();
});

// Responsive
window.addEventListener('resize', () => {
    const container = document.getElementById('scene-container');
    camera.aspect = container.clientWidth / container.clientHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(container.clientWidth, container.clientHeight);
});