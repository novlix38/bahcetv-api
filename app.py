from flask import Flask, request, jsonify
import yt_dlp

app = Flask(__name__)

# NİHAİ HİBRİT KANAL HAVUZU
CHANNELS_CONFIG = {
    "1": {"name": "TRT 1", "type": "direct", "url": "https://tv-trt1.medya.trt.com.tr/master.m3u8"},
    "2": {"name": "ATV", "type": "direct", "url": "https://trku-mac-atv.ercdn.net/atvhd/atvhd.m3u8"},
    "3": {"name": "STAR TV", "type": "direct", "url": "https://dogus-live.daioncdn.net/startv/playlist.m3u8"},
    "4": {"name": "SHOW TV", "type": "direct", "url": "https://ciner-live.daioncdn.net/showtv/showtv.m3u8"},
    "5": {"name": "KANAL D", "type": "direct", "url": "https://demiroren.daioncdn.net/kanald/kanald.m3u8"},
    "6": {"name": "NOW TV", "type": "direct", "url": "https://uycyyuuzyh.turknet.ercdn.net/nphindgytw/nowtv/nowtv.m3u8"},
    "7": {"name": "TV8", "type": "direct", "url": "https://turkmedya-live.ercdn.net/tv4/tv4.m3u8"},
    "8": {"name": "TRT HABER", "type": "direct", "url": "https://tv-trthaber.medya.trt.com.tr/master.m3u8"},
    "10": {"name": "HALK TV", "type": "direct", "url": "https://halktv-live.daioncdn.net/halktv/halktv.m3u8"},
    "11": {"name": "SÖZCÜ TV", "type": "youtube", "id": "SozcuTelevizyonu"},
    "12": {"name": "NTV", "type": "youtube", "id": "ntv"},
    "13": {"name": "CNN TÜRK", "type": "youtube", "id": "cnnturk"},
    "14": {"name": "HABERTÜRK", "type": "youtube", "id": "haberturktv"}
}

HTML_INTERFACE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bahçe TV</title>
    <script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
    <style>
        body { margin: 0; padding: 0; background-color: #000; overflow: hidden; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; user-select: none; }
        
        #tv-wrapper { position: relative; width: 100vw; height: 100vh; background-color: black; }
        
        video, iframe { position: absolute; top: 0; left: 0; width: 100vw; height: 100vh; border: none; background-color: black; object-fit: contain; z-index: 1; }
        
        #channel-info { position: absolute; top: 30px; left: 50%; transform: translateX(-50%); background: rgba(0, 0, 0, 0.8); color: #00ffcc; padding: 15px 30px; border-radius: 10px; font-size: 32px; font-weight: bold; text-transform: uppercase; box-shadow: 0 0 15px rgba(0, 255, 204, 0.3); opacity: 0; transition: opacity 0.4s ease-in-out; pointer-events: none; z-index: 10; }
        .show-info { opacity: 1 !important; }
        
        #virtual-remote { position: absolute; bottom: 40px; left: 40px; display: grid; grid-template-columns: 60px 60px 60px; grid-template-rows: 60px 60px 60px; gap: 10px; z-index: 20; opacity: 0; transition: opacity 0.5s ease-in-out; }
        
        /* Kumandaya özel z-index ile tıklanabilirliği sağladık */
        #virtual-remote.show-remote { opacity: 0.9 !important; pointer-events: auto !important; }
        
        .remote-btn { background: rgba(0, 0, 0, 0.6); border: 2px solid #00ffcc; color: #00ffcc; border-radius: 50%; font-size: 24px; display: flex; justify-content: center; align-items: center; cursor: pointer; box-shadow: 0 0 10px rgba(0, 255, 204, 0.2); transition: background 0.2s; }
        .remote-btn:active { background: #00ffcc; color: #000; }
        
        #btn-up { grid-column: 2; grid-row: 1; }
        #btn-left { grid-column: 1; grid-row: 2; }
        #btn-ok { grid-column: 2; grid-row: 2; font-size: 16px; font-weight: bold; }
        #btn-right { grid-column: 3; grid-row: 2; }
        #btn-down { grid-column: 2; grid-row: 3; }
        
        #fs-btn { position: absolute; top: 30px; right: 40px; background: rgba(0, 0, 0, 0.6); border: 2px solid #00ffcc; color: #00ffcc; padding: 10px 15px; border-radius: 10px; font-size: 18px; font-weight: bold; cursor: pointer; z-index: 30; box-shadow: 0 0 10px rgba(0, 255, 204, 0.2); }
        #fs-btn:active { background: #00ffcc; color: #000; }

        #loading { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); color: #00ffcc; font-size: 28px; font-weight: bold; z-index: 5; display: none; }
        
        /* Overlay artık tıklamaları engellemiyor (pointer-events: none), dokunuşlar doğrudan ekrana geçiyor */
        #interaction-overlay { position: absolute; top:0; left:0; width: 100vw; height: 100vh; background: rgba(0,0,0,0.9); color: #00ffcc; display: flex; justify-content: center; align-items: center; font-size: 30px; font-weight: bold; z-index: 50; pointer-events: none; transition: opacity 0.5s ease-in-out; text-align: center; padding: 20px;}
    </style>
</head>
<body>
    
    <div id="tv-wrapper">
        <div id="interaction-overlay">SİSTEMİ BAŞLATMAK İÇİN EKRANA DOKUNUN<br>VEYA KUMANDADAN BİR TUŞA BASIN</div>
        <button id="fs-btn" onclick="toggleFullscreen()">[\ ] TAM EKRAN</button>
        
        <div id="loading">Sinyal Aranıyor...</div>
        
        <video id="hls-player" muted></video>
        <div id="yt-container"></div>
        
        <div id="channel-info">Kanal Yükleniyor...</div>

        <div id="virtual-remote">
            <div class="remote-btn" id="btn-up" onclick="handleAction('UP')">▲</div>
            <div class="remote-btn" id="btn-left" onclick="handleAction('LEFT')">◀</div>
            <div class="remote-btn" id="btn-ok" onclick="handleAction('OK')">OK</div>
            <div class="remote-btn" id="btn-right" onclick="handleAction('RIGHT')">▶</div>
            <div class="remote-btn" id="btn-down" onclick="handleAction('DOWN')">▼</div>
        </div>
    </div>

    <script>
        const channels = [
            { id: 1, name: "TRT 1" }, { id: 2, name: "ATV" }, { id: 3, name: "STAR TV" },
            { id: 4, name: "SHOW TV" }, { id: 5, name: "KANAL D" }, { id: 6, name: "NOW TV" },
            { id: 7, name: "TV8" }, { id: 8, name: "TRT HABER" }, { id: 10, name: "HALK TV" },
            { id: 11, name: "SÖZCÜ TV" }, { id: 12, name: "NTV" },
            { id: 13, name: "CNN TÜRK" }, { id: 14, name: "HABERTÜRK" }
        ];

        let currentChannelIndex = 0;
        let hasInteracted = false;
        let remoteTimeout = null;
        let currentStreamType = null;
        
        const wrapper = document.getElementById('tv-wrapper');
        const hlsVideo = document.getElementById('hls-player');
        const ytContainer = document.getElementById('yt-container');
        const infoBox = document.getElementById('channel-info');
        const loading = document.getElementById('loading');
        const overlay = document.getElementById('interaction-overlay');
        const remote = document.getElementById('virtual-remote');
        
        let hideInfoTimeout, hlsInstance = null;

        // Evrensel Uyanma Fonksiyonu (Ekrana Tıklama veya Kumanda Tuşu)
        function wakeUp() {
            if (!hasInteracted) {
                hasInteracted = true;
                overlay.style.opacity = '0'; // Pürüzsüz kaybolma
                setTimeout(() => { overlay.style.display = 'none'; }, 500);
                loadChannel(currentChannelIndex);
                return true; // Yeni uyandığını belirtir
            }
            return false;
        }

        // Kumandayı gösteren ve 5 saniye sonra gizleyen fonksiyon
        function showRemoteTemporarily() {
            if (!hasInteracted) return;
            remote.classList.add('show-remote');
            clearTimeout(remoteTimeout);
            remoteTimeout = setTimeout(() => {
                remote.classList.remove('show-remote');
            }, 5000); 
        }

        // Tüm Ekrana Tıklama Dinleyicisi
        document.addEventListener('click', (e) => {
            // Eğer tam ekran butonuna basıldıysa uyandırma işlemini bölme
            if(e.target.id === 'fs-btn') return;
            
            if (!hasInteracted) {
                wakeUp();
            } else {
                showRemoteTemporarily(); // Zaten açıksa sadece kumandayı göster
            }
        });

        async function loadChannel(index) {
            if (!hasInteracted) return; 
            showRemoteTemporarily(); 
            
            const channel = channels[index];
            showChannelInfo("Yükleniyor: " + channel.name);
            
            hlsVideo.style.display = "none";
            ytContainer.style.display = "none";
            if(hlsInstance) { hlsInstance.destroy(); }
            hlsVideo.pause();
            ytContainer.innerHTML = ""; 
            currentStreamType = null;
            
            loading.style.display = "block";
            
            try {
                const response = await fetch(window.location.origin + "/resolver?id=" + channel.id);
                const data = await response.json();
                
                loading.style.display = "none";
                currentStreamType = data.type;

                if (data.type === "direct") {
                    hlsVideo.style.display = "block";
                    hlsVideo.muted = false; 
                    
                    if (Hls.isSupported()) {
                        hlsInstance = new Hls({ maxBufferLength: 15 }); 
                        hlsInstance.loadSource(data.url); 
                        hlsInstance.attachMedia(hlsVideo);
                        hlsInstance.on(Hls.Events.MANIFEST_PARSED, function() { hlsVideo.play(); });
                    } else if (hlsVideo.canPlayType('application/vnd.apple.mpegurl')) {
                        hlsVideo.src = data.url;
                        hlsVideo.addEventListener('loadedmetadata', function() { hlsVideo.play(); });
                    }
                    showChannelInfo(channel.id + " - " + channel.name);
                    
                } else if (data.type === "youtube" && data.video_id) {
                    ytContainer.style.display = "block";
                    const iframeHTML = `<iframe src="https://www.youtube.com/embed/${data.video_id}?autoplay=1&mute=0&controls=1&modestbranding=1" allow="autoplay; encrypted-media" allowfullscreen></iframe>`;
                    ytContainer.innerHTML = iframeHTML;
                    showChannelInfo(channel.id + " - " + channel.name);
                }
            } catch (err) {
                loading.innerText = "BAĞLANTI HATASI";
                loading.style.display = "block";
            }
        }

        function showChannelInfo(text) {
            infoBox.innerText = text; infoBox.classList.add('show-info'); clearTimeout(hideInfoTimeout);
            hideInfoTimeout = setTimeout(() => { infoBox.classList.remove('show-info'); }, 4000);
        }

        function handleAction(action) {
            showRemoteTemporarily();
            
            if (action === 'UP') { currentChannelIndex = (currentChannelIndex + 1) % channels.length; loadChannel(currentChannelIndex); } 
            else if (action === 'DOWN') { currentChannelIndex = (currentChannelIndex - 1 + channels.length) % channels.length; loadChannel(currentChannelIndex); }
            else if (action === 'RIGHT') {
                if (currentStreamType === 'direct') {
                    hlsVideo.volume = Math.min(hlsVideo.volume + 0.1, 1);
                    showChannelInfo("SES: %" + Math.round(hlsVideo.volume * 100));
                } else { showChannelInfo("SESİ CİHAZDAN AYARLAYIN"); }
            }
            else if (action === 'LEFT') {
                if (currentStreamType === 'direct') {
                    hlsVideo.volume = Math.max(hlsVideo.volume - 0.1, 0);
                    showChannelInfo("SES: %" + Math.round(hlsVideo.volume * 100));
                } else { showChannelInfo("SESİ CİHAZDAN AYARLAYIN"); }
            }
            else if (action === 'OK') { showChannelInfo(channels[currentChannelIndex].name); }
        }

        function toggleFullscreen() {
            wakeUp(); // Tam ekrana basılırsa da sistemi uyandır
            if (!document.fullscreenElement) {
                wrapper.requestFullscreen().catch(err => {});
                document.getElementById('fs-btn').innerText = "[ ] KÜÇÜLT";
            } else {
                document.exitFullscreen();
                document.getElementById('fs-btn').innerText = "[\ ] TAM EKRAN";
            }
        }

        // Kumanda / Klavye Dinleyicisi
        document.addEventListener('keydown', (event) => {
            // Eğer sistem uykudaysa önce uyandır, uyanırsa işlemi kesme devam et
            wakeUp();
            showRemoteTemporarily();
            
            if (event.key === 'ArrowUp') handleAction('UP'); else if (event.key === 'ArrowDown') handleAction('DOWN'); else if (event.key === 'Enter') handleAction('OK');
            else if (event.key === 'ArrowRight') handleAction('RIGHT'); else if (event.key === 'ArrowLeft') handleAction('LEFT');
            else if (!isNaN(event.key) && event.key !== " ") {
                numpadBuffer += event.key; showChannelInfo("KANAL " + numpadBuffer + "..."); clearTimeout(numpadTimeout);
                numpadTimeout = setTimeout(() => {
                    let targetId = parseInt(numpadBuffer); let foundIndex = channels.findIndex(ch => ch.id === targetId);
                    if(foundIndex !== -1) { currentChannelIndex = foundIndex; loadChannel(currentChannelIndex); } else { showChannelInfo("KANAL BULUNAMADI"); }
                    numpadBuffer = ""; 
                }, 1500); 
            }
        });
    </script>
</body>
</html>
"""

@app.route('/')
def ana_sayfa():
    return HTML_INTERFACE

@app.route('/resolver')
def resolver():
    ch_id = request.args.get('id')
    if ch_id not in CHANNELS_CONFIG:
        return jsonify({"error": "Kanal bulunamadi"}), 404
        
    config = CHANNELS_CONFIG[ch_id]
    
    if config["type"] == "direct":
        return jsonify({"type": "direct", "url": config["url"]})
        
    elif config["type"] == "youtube":
        youtube_url = f"https://www.youtube.com/@{config['id']}/live"
        ydl_opts = {'quiet': True}
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=False)
                video_id = info.get('id')
                
            if video_id:
                return jsonify({"type": "youtube", "video_id": video_id})
            else:
                return jsonify({"error": "Canli yayin ID'si bulunamadi"}), 404
                
        except Exception as e:
            return jsonify({"error": str(e)}), 500

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
