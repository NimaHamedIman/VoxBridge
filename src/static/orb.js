/*
 * VoxBridge - orb renderer.
 *
 * Draws an animated sphere on a canvas. It reacts to two inputs that the
 * rest of the app feeds in:
 *
 *   Orb.setState("listening")   one of idle | listening | thinking | speaking
 *   Orb.setLevel(0.7)           current audio loudness, 0 to 1
 *
 * Plain Canvas 2D, no libraries.
 */

const canvas = document.getElementById("orb");
const ctx = canvas.getContext("2d");

// One colour per state, stored as raw RGB so we can build rgba() strings
// with a varying alpha further down.
const PALETTE = {
    idle:      [124,  58, 237],
    listening: [192,  38, 211],
    thinking:  [147,  51, 234],
    speaking:  [236,  72, 153]
};

// How strongly each state deforms the outline, before audio is added.
const WOBBLE = {
    idle:      0.05,
    listening: 0.16,
    thinking:  0.10,
    speaking:  0.20
};

const SEGMENTS = 140;   // number of points used to trace the outline

const calm = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

let state = "idle";
let targetLevel = 0;    // written from outside
let liveLevel = 0;      // smoothed version of targetLevel
let clock = 0;          // seconds since start, advanced every frame
let lastFrame = 0;

let viewW = 0, viewH = 0;
let cx = 0, cy = 0, unit = 0;


function resize() {
    const dpr = window.devicePixelRatio || 1;
    const box = canvas.getBoundingClientRect();

    // A canvas has two sizes: the CSS size the user sees, and the pixel
    // buffer we actually paint into. On a phone with dpr = 3 they differ
    // by a factor of three. Ignoring that is what makes canvas art blurry.
    canvas.width  = Math.round(box.width  * dpr);
    canvas.height = Math.round(box.height * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

    viewW = box.width;
    viewH = box.height;
    cx = viewW / 2;
    cy = viewH / 2;
    unit = Math.min(viewW, viewH) / 2;
}


function outlineRadius(angle, base, amp) {
    // A single sine wave makes the orb look like a cog. Three waves with
    // different frequencies, drifting at different speeds, never line up
    // the same way twice - that is what reads as "alive".
    const a = Math.sin(angle * 3 + clock * 1.10);
    const b = Math.sin(angle * 5 - clock * 0.70);
    const c = Math.sin(angle * 7 + clock * 1.90);

    return base * (1 + (a * 0.5 + b * 0.3 + c * 0.2) * amp);
}


function traceOutline(base, amp) {
    ctx.beginPath();

    for (let i = 0; i <= SEGMENTS; i++) {
        const angle = (i / SEGMENTS) * Math.PI * 2;
        const r = outlineRadius(angle, base, amp);
        const x = cx + Math.cos(angle) * r;
        const y = cy + Math.sin(angle) * r;

        if (i === 0) {
            ctx.moveTo(x, y);
        } else {
            ctx.lineTo(x, y);
        }
    }

    ctx.closePath();
}


function draw(now) {
    const dt = lastFrame ? Math.min((now - lastFrame) / 1000, 0.05) : 0;
    lastFrame = now;
    clock += dt;

    // Ease towards the target instead of jumping to it. Without this the
    // orb twitches on every microphone sample. The factor 9 is tuned by
    // eye: higher reacts faster and more nervously.
    liveLevel += (targetLevel - liveLevel) * Math.min(1, dt * 9);

    const rgb = PALETTE[state];
    const r = rgb[0], g = rgb[1], b = rgb[2];

    const breath = 1 + Math.sin(clock * 1.3) * 0.028;
    const base = unit * 0.46 * breath * (1 + liveLevel * 0.22);
    const amp = (WOBBLE[state] + liveLevel * 0.22) * (calm ? 0.3 : 1);

    ctx.clearRect(0, 0, viewW, viewH);

    // 1. Halo - a soft cloud behind everything, brighter when loud.
    const halo = ctx.createRadialGradient(cx, cy, base * 0.3,
                                          cx, cy, base * 2.3);
    halo.addColorStop(0,    "rgba(" + r + "," + g + "," + b + ","
                            + (0.30 + liveLevel * 0.22) + ")");
    halo.addColorStop(0.42, "rgba(" + r + "," + g + "," + b + ",0.09)");
    halo.addColorStop(1,    "rgba(" + r + "," + g + "," + b + ",0)");
    ctx.fillStyle = halo;
    ctx.fillRect(0, 0, viewW, viewH);

    // 2. Two outer rings. Offset from the body so the orb reads as a
    //    sphere with atmosphere rather than a flat disc.
    for (let k = 1; k <= 2; k++) {
        traceOutline(base * (1 + k * 0.17), amp * 0.55);
        ctx.strokeStyle = "rgba(" + r + "," + g + "," + b + ","
                          + (0.26 / k) + ")";
        ctx.lineWidth = 1.4;
        ctx.stroke();
    }

    // 3. The body. The gradient centre is pushed up and left so the light
    //    appears to come from one direction.
    const body = ctx.createRadialGradient(
        cx - base * 0.32, cy - base * 0.34, base * 0.08,
        cx, cy, base * 1.12
    );
    body.addColorStop(0,    "rgba(255,255,255,0.92)");
    body.addColorStop(0.28, "rgba(" + r + "," + g + "," + b + ",0.95)");
    body.addColorStop(1,    "rgba(" + Math.round(r * 0.30) + ","
                            + Math.round(g * 0.16) + ","
                            + Math.round(b * 0.45) + ",0.92)");

    traceOutline(base, amp);
    ctx.fillStyle = body;
    ctx.fill();

    // 4. While the model is generating there is nothing to visualise, so
    //    an orbiting arc carries the waiting time instead.
    if (state === "thinking" && !calm) {
        const start = clock * 2.4;
        ctx.beginPath();
        ctx.arc(cx, cy, base * 1.5, start, start + Math.PI * 0.5);
        ctx.strokeStyle = "rgba(255,255,255,0.8)";
        ctx.lineWidth = 2.5;
        ctx.lineCap = "round";
        ctx.stroke();
    }

    requestAnimationFrame(draw);
}


const Orb = {
    setState: function (next) {
        if (PALETTE[next]) {
            state = next;
        }
    },

    setLevel: function (value) {
        targetLevel = Math.max(0, Math.min(1, value));
    },

    getState: function () {
        return state;
    }
};


window.addEventListener("resize", resize);
resize();
requestAnimationFrame(draw);
