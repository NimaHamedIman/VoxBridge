/*
 * VoxBridge - front end.
 *
 * Two ways in: record a clip and upload it to /voice, or type a message
 * and send it to /chat. Both answers are read out loud by the browser's
 * speech synthesis.
 *
 * The orb is driven from here: Orb.setState() for the four phases and
 * Orb.setLevel() for the loudness, twenty times a second.
 */

const micButton  = document.getElementById("mic");
const sendButton = document.getElementById("send");
const messageBox = document.getElementById("message");
const statusLine = document.getElementById("status");
const transcript = document.getElementById("transcript");
const stages     = document.querySelectorAll(".pipeline li");

const welcomeOverlay = document.getElementById("welcome");
const nameInput       = document.getElementById("your-name");
const botNameInput    = document.getElementById("bot-name");
const welcomeDone     = document.getElementById("welcome-done");
const langBadge       = document.getElementById("lang-badge");

const LABELS = {
    idle:      "Bereit",
    listening: "Ich höre zu",
    thinking:  "Einen Moment",
    speaking:  "Antwort läuft"
};

let sessionId = localStorage.getItem("voxbridge_session");

let userName      = localStorage.getItem("voxbridge_user");
let assistantName = localStorage.getItem("voxbridge_assistant");

let recorder = null;
let chunks = [];

let audioCtx = null;
let meterTimer = null;

let germanVoice = null;
let speakTimer = null;
let speakLevel = 0;
let speakGuard = null;
let gotBoundary = false;


/* ---------- shared state ---------- */

// A typed message skips the microphone and Whisper, so the two routes do
// not light up the same stages. Passing them in keeps the strip honest.
function setPhase(phase, active) {
    Orb.setState(phase);
    statusLine.textContent = LABELS[phase];

    const lit = active || [];
    stages.forEach(function (li) {
        li.classList.toggle("active", lit.indexOf(li.dataset.stage) !== -1);
    });
}


function say(text, muted) {
    transcript.textContent = text;
    transcript.classList.toggle("muted", Boolean(muted));
}


function setBusy(busy) {
    micButton.disabled = busy;
    sendButton.disabled = busy;
    messageBox.disabled = busy;
}


/* ---------- microphone ---------- */

function startMeter(stream) {
    audioCtx = new (window.AudioContext || window.webkitAudioContext)();

    const source = audioCtx.createMediaStreamSource(stream);
    const analyser = audioCtx.createAnalyser();
    analyser.fftSize = 512;
    source.connect(analyser);

    const bins = new Uint8Array(analyser.frequencyBinCount);

    meterTimer = setInterval(function () {
        analyser.getByteFrequencyData(bins);

        // Only the lower half of the spectrum is worth looking at - that
        // is where the energy of a human voice sits. Averaging the whole
        // range would drown the signal in hiss.
        const half = bins.length / 2;
        let sum = 0;
        for (let i = 0; i < half; i++) {
            sum += bins[i];
        }

        // 90 is not a magic number, it is a calibration: normal speech on
        // a laptop microphone lands around there.
        Orb.setLevel(Math.min(1, (sum / half) / 90));
    }, 50);
}


function stopMeter() {
    clearInterval(meterTimer);
    meterTimer = null;

    if (audioCtx) {
        audioCtx.close();
        audioCtx = null;
    }

    Orb.setLevel(0);
}


async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

        recorder = new MediaRecorder(stream);
        chunks = [];

        recorder.addEventListener("dataavailable", function (event) {
            chunks.push(event.data);
        });

        recorder.addEventListener("stop", function () {
            stream.getTracks().forEach(function (track) {
                track.stop();
            });
            stopMeter();
            sendClip();
        });

        recorder.start();
        startMeter(stream);

        micButton.classList.add("recording");
        micButton.setAttribute("aria-label", "Aufnahme beenden");
        setPhase("listening", ["record"]);
        say("");

    } catch (err) {
        setPhase("idle");
        say("Kein Zugriff auf das Mikrofon. Bitte im Browser erlauben.", true);
    }
}


function stopRecording() {
    micButton.classList.remove("recording");
    micButton.setAttribute("aria-label", "Aufnahme starten");
    recorder.stop();
}


/* ---------- server ---------- */

function rememberSession(data) {
    if (data.session_id) {
        sessionId = data.session_id;
        localStorage.setItem("voxbridge_session", sessionId);
    }
}


function describeFailure(status) {
    if (status === 429) {
        return "Zu viele Anfragen. Bitte einen Moment warten.";
    }
    if (status === 413) {
        return "Die Aufnahme ist zu lang. Bitte kürzer sprechen.";
    }
    return "Der Server antwortet gerade nicht.";
}


async function sendClip() {
    setPhase("thinking", ["stt", "llm"]);
    setBusy(true);

    try {
        const form = new FormData();
        form.append("audio", new Blob(chunks, { type: "audio/webm" }), "aufnahme.webm");
        form.append("language", "de");
        if (sessionId) {
            form.append("session_id", sessionId);
        }
        if (userName) {
            form.append("user_name", userName);
        }
        if (assistantName) {
            form.append("assistant_name", assistantName);
        }

        // Relative path on purpose: the same file has to work on
        // localhost during development and on the live domain.
        const res = await fetch("/voice", { method: "POST", body: form });
        if (!res.ok) {
            throw new Error(describeFailure(res.status));
        }

        const data = await res.json();
        rememberSession(data);

        if (data.error) {
            setPhase("idle");
            say(data.error, true);
            return;
        }

        say(data.response);
        speak(data.response);

    } catch (err) {
        setPhase("idle");
        say(err.message, true);
    } finally {
        setBusy(false);
    }
}


async function sendText() {
    const text = messageBox.value.trim();
    if (!text) {
        return;
    }

    messageBox.value = "";
    setPhase("thinking", ["llm"]);
    setBusy(true);

    try {
        const form = new FormData();
        form.append("message", text);
        if (sessionId) {
            form.append("session_id", sessionId);
        }
        if (userName) {
            form.append("user_name", userName);
        }
        if (assistantName) {
            form.append("assistant_name", assistantName);
        }

        const res = await fetch("/chat", { method: "POST", body: form });
        if (!res.ok) {
            throw new Error(describeFailure(res.status));
        }

        const data = await res.json();
        rememberSession(data);

        say(data.response);
        speak(data.response);

    } catch (err) {
        setPhase("idle");
        say(err.message, true);
    } finally {
        setBusy(false);
        messageBox.focus();
    }
}


/* ---------- speech output ---------- */

// Web Speech API quality depends entirely on what the operating system
// provides, so we pick the best available voice rather than trusting
// whatever the browser defaults to.
const VOICE_PREFERENCES = [
    "Google Deutsch",   // most natural, but generated remotely and only exists in Chrome
    "Katja",            // best locally installed Windows voice, works offline
    "Helena",           // macOS and iOS
    "Anna",             // older macOS
    "Hedda"             // older Windows
];

function pickGermanVoice() {
    const voices = window.speechSynthesis.getVoices();

    for (const name of VOICE_PREFERENCES) {
        const match = voices.find(function (v) {
            return v.name.toLowerCase().indexOf(name.toLowerCase()) !== -1
                && v.lang.indexOf("de") === 0;
        });
        if (match) {
            return match;
        }
    }

    return voices.find(function (v) { return v.lang === "de-DE"; })
        || voices.find(function (v) { return v.lang.indexOf("de") === 0; })
        || null;
}


function speak(text) {
    if (!("speechSynthesis" in window)) {
        setPhase("idle");
        return;
    }

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "de-DE";
    // Tuned by ear: slightly slower and slightly higher reads as warmer,
    // while the default sounds clipped.
    utterance.rate = 0.95;
    utterance.pitch = 1.05;

    if (germanVoice) {
        utterance.voice = germanVoice;
    }

    gotBoundary = false;

    function finish() {
        clearTimeout(speakGuard);
        clearInterval(speakTimer);
        speakTimer = null;
        Orb.setLevel(0);
        setPhase("idle");
    }

    utterance.addEventListener("start", function () {
        clearTimeout(speakGuard);
        setPhase("speaking", ["tts"]);

        // Speech synthesis hands us no audio stream to analyse, so the
        // orb is driven by word timing instead: each boundary is a beat,
        // and the level decays in between.
        speakLevel = 0.5;
        const speakStart = Date.now();
        speakTimer = setInterval(function () {
            if (gotBoundary) {
                speakLevel *= 0.8;
                Orb.setLevel(Math.max(0.1, speakLevel));
            } else {
                // Remote voices (e.g. Google's) usually never fire
                // "boundary", so we get no timing signal at all. A
                // synthetic pulse is the honest fallback here — it does
                // not pretend to follow the words.
                const elapsed = Date.now() - speakStart;
                Orb.setLevel(Math.max(0.1, 0.3 + Math.sin(elapsed / 190) * 0.18));
            }
        }, 60);
    });

    utterance.addEventListener("boundary", function () {
        gotBoundary = true;
        speakLevel = 0.55 + Math.random() * 0.3;
    });

    utterance.addEventListener("end", finish);
    utterance.addEventListener("error", finish);

    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);

    // Some browsers silently drop an utterance and never fire "start".
    // Without this the interface would wait forever.
    speakGuard = setTimeout(function () {
        if (!window.speechSynthesis.speaking) {
            finish();
        }
    }, 2500);
}


/* ---------- personalisation ---------- */

function saveNames() {
    userName = nameInput.value.trim();
    assistantName = botNameInput.value.trim() || "VoxBridge";

    localStorage.setItem("voxbridge_user", userName);
    localStorage.setItem("voxbridge_assistant", assistantName);

    welcomeOverlay.hidden = true;
    say(`Hallo ${userName}. Ich bin ${assistantName}.`);
}


function showWelcome() {
    nameInput.value = "";
    botNameInput.value = "";
    welcomeOverlay.hidden = false;
    nameInput.focus();
}


/* ---------- wiring ---------- */

micButton.addEventListener("click", function () {
    window.speechSynthesis.cancel();

    if (!recorder || recorder.state === "inactive") {
        startRecording();
    } else {
        stopRecording();
    }
});

sendButton.addEventListener("click", sendText);

messageBox.addEventListener("keydown", function (event) {
    if (event.key === "Enter") {
        sendText();
    }
});

// Space toggles the microphone, but not while the text field has focus.
document.addEventListener("keydown", function (event) {
    if (event.code === "Space" && event.target === document.body) {
        event.preventDefault();
        micButton.click();
    }
});

welcomeDone.addEventListener("click", saveNames);

nameInput.addEventListener("keydown", function (event) {
    if (event.key === "Enter") {
        saveNames();
    }
});

botNameInput.addEventListener("keydown", function (event) {
    if (event.key === "Enter") {
        saveNames();
    }
});

langBadge.addEventListener("click", function () {
    localStorage.removeItem("voxbridge_user");
    localStorage.removeItem("voxbridge_assistant");
    userName = null;
    assistantName = null;
    showWelcome();
});

langBadge.addEventListener("keydown", function (event) {
    if (event.key === "Enter" || event.code === "Space") {
        event.preventDefault();
        langBadge.click();
    }
});

// Chrome loads the voice list asynchronously - the first call usually
// returns an empty array, so we ask again once it is ready.
germanVoice = pickGermanVoice();
window.speechSynthesis.addEventListener("voiceschanged", function () {
    germanVoice = pickGermanVoice();
});

if (!userName) {
    welcomeOverlay.hidden = false;
    nameInput.focus();
}

setPhase("idle");
