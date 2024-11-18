const API_URL = 'http://127.0.0.1:5000/denuncias';
const UPLOADS_URL = 'http://127.0.0.1:5000/uploads';

// Função para carregar o feed
async function loadFeed() {
    const response = await fetch(API_URL);
    const denuncias = await response.json();
    console.log(denuncias);

    const feed = document.getElementById('feed');
    feed.innerHTML = '';
    denuncias.forEach(denuncia => {
        const fotoUrl = denuncia.foto ? `${UPLOADS_URL}/${denuncia.foto}` : 'placeholder.jpg';
        feed.innerHTML += `
            <div class="col">
                <div class="card">
                    <img src="${fotoUrl}" class="card-img-top" alt="Foto da Denúncia">
                    <div class="card-body">
                        <h5 class="card-title">${denuncia.descricao}</h5>
                        <p class="card-text">Latitude: ${denuncia.latitude}, Longitude: ${denuncia.longitude}</p>
                    </div>
                </div>
            </div>
        `;
    });
}

// Função para adicionar uma denúncia
document.getElementById('addForm').addEventListener('submit', async function(event) {
    event.preventDefault();

    const descricao = document.getElementById('descricao').value;
    const latitude = document.getElementById('latitude').value;
    const longitude = document.getElementById('longitude').value;
    const foto = document.getElementById('foto').files[0];

    const formData = new FormData();
    formData.append('descricao', descricao);
    formData.append('latitude', latitude);
    formData.append('longitude', longitude);
    if (foto) formData.append('foto', foto);

    await fetch(API_URL, {
        method: 'POST',
        body: formData
    });

    alert('Denúncia criada com sucesso!');
    window.location.href = 'feed.html';
});

// Função para obter a localização atual do usuário
function getLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition((position) => {
            document.getElementById('latitude').value = position.coords.latitude;
            document.getElementById('longitude').value = position.coords.longitude;
        });
    } else {
        alert("Geolocalização não é suportada pelo navegador.");
    }
}

// Função para carregar o mapa com marcadores
async function loadMap() {
    const response = await fetch(API_URL);
    const denuncias = await response.json();

    const map = new google.maps.Map(document.getElementById('map'), {
        zoom: 12,
        center: { lat: -15.7942, lng: -47.8822 }, // Defina as coordenadas de centro inicial
    });

    denuncias.forEach(denuncia => {
        new google.maps.Marker({
            position: { lat: parseFloat(denuncia.latitude), lng: parseFloat(denuncia.longitude) },
            map: map,
            title: denuncia.descricao,
        });
    });
}





var video = document.querySelector('video');

navigator.mediaDevices.getUserMedia({video:true})
.then(stream => {
    video.srcObject = stream;
    video.play();
})
.catch(error => {
    console.log(error);
})

document.querySelector('button').addEventListener('click', () => {
    var canvas = document.querySelector('canvas');
    canvas.height = video.videoHeight;
    canvas.width = video.videoWidth;
    var context = canvas.getContext('2d');
    context.drawImage(video, 0, 0);
    var link = document.createElement('a');
    link.download = 'foto.png';
    link.href = canvas.toDataURL();
    link.textContent = 'Clique para baixar a imagem';
    document.body.appendChild(link);
});
