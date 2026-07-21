const chatBox = document.getElementById("chat-box");
const input   = document.getElementById("message-input");
const button  = document.getElementById("send-button");


const API_URL = "https://voice.nimaserver.xyz/chat";
let sessionId = localStorage.getItem("voxbridge_session");


function addMessage(text, sender) {
    const bubble = document.createElement("div");
    bubble.className = "message " + sender;
    bubble.textContent = text;
    chatBox.appendChild(bubble);
    chatBox.scrollTop = chatBox.scrollHeight;
}


async function sendMessage() {
    const text = input.value.trim();
    if (!text) return;

    addMessage(text, "user");
    input.value = "";
    button.disabled = true;

    try {
        const formData = new FormData();
        formData.append("message", text);
        if (sessionId) {
            formData.append("session_id", sessionId);
        }

        const response = await fetch(API_URL, {
            method: "POST",
            body: formData
        });

        if (!response.ok) {
            throw new Error("Server-Fehler: " + response.status);
        }

        const data = await response.json();

        sessionId = data.session_id;
        localStorage.setItem("voxbridge_session", sessionId);

        addMessage(data.response, "assistant");

    } catch (error) {
        addMessage("⚠️ Fehler: " + error.message, "assistant");
    } finally {
        button.disabled = false;
        input.focus();
    }
}


button.addEventListener("click", sendMessage);
input.addEventListener("keydown", function (event) {
    if (event.key === "Enter") sendMessage();
});

// ---------- ضبط صدا ----------
 const micButton = document.getElementById("mic-button");
 let mediaRecorder = null;
 let audioChunks = [];

 micButton.addEventListener("click", async function () {
       // حالت ۱: هنوز ضبط نمی‌کنیم → شروع کن
 if (!mediaRecorder || mediaRecorder.state === "inactive") {
 try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);
    audioChunks = [];

    mediaRecorder.addEventListener("dataavailable", function (event) {
        audioChunks.push(event.data);
    });

    mediaRecorder.addEventListener("stop", sendAudio);

    mediaRecorder.start();
    micButton.classList.add("recording");
    micButton.textContent = "⏹️";
 } catch (err) {
    addMessage("⚠️ Mikrofonzugriff verweigert: " + err.message, "assistant");
 }
}
   // حالت ۲: در حال ضبطیم → تمومش کن
  else {
mediaRecorder.stop();
mediaRecorder.stream.getTracks().forEach(track => track.stop());
micButton.classList.remove("recording");
micButton.textContent = "🎙️";
      }
     });

 async function sendAudio() {
    const audioBlob = new Blob(audioChunks, { type: "audio/webm" });

    addMessage("🎙️ ...", "user");
    micButton.disabled = true;

    try {
        const formData = new FormData();
        formData.append("audio", audioBlob, "recording.webm");
        formData.append("language", document.getElementById("langSelect").value);
        if (sessionId) formData.append("session_id", sessionId);

        const response = await fetch("/voice", { method: "POST", body: formData });
        if (!response.ok) throw new Error("Server-Fehler: " + response.status);

        const data = await response.json();

        if (data.error) {
            addMessage("⚠️ " + data.error, "assistant");
            return;
        }

        sessionId = data.session_id;
        localStorage.setItem("voxbridge_session", sessionId);

        chatBox.lastChild.textContent = data.transcription;
        addMessage(data.response, "assistant");

    } catch (error) {
        addMessage("⚠️ Fehler: " + error.message, "assistant");
    } finally {
        micButton.disabled = false;
    }
}
