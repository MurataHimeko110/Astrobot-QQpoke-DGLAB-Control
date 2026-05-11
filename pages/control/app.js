const bridge = window.AstrBotPluginPage;

async function loadStatus() {
    const data = await bridge.apiGet("status");
    document.getElementById("status-text").textContent = data.connected ? "已连接" : "未连接";
    const dot = document.getElementById("status-indicator");
    dot.className = "dot " + (data.connected ? "connected" : "disconnected");
    document.getElementById("channel").textContent = data.channel;
    document.getElementById("strength-range").textContent = `${data.strength_min} - ${data.strength_max}`;

    const qrContainer = document.getElementById("qr-container");
    if (data.connected || !data.qr_url) {
        qrContainer.style.display = "none";
    } else {
        qrContainer.style.display = "block";
        document.getElementById("qr-img").src = data.qr_url;
    }
}

document.getElementById("shock-btn").addEventListener("click", async () => {
    await bridge.apiPost("shock");
    alert("电击指令已发送");
});

await bridge.ready();
loadStatus();
setInterval(loadStatus, 10000);

bridge.onContext(loadStatus);