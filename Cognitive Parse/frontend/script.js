function htmlEscape(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
}

function formatDate(isoLike) {
    if (!isoLike) return "-";
    const safe = isoLike.replace(" ", "T") + "Z";
    const d = new Date(safe);
    if (Number.isNaN(d.getTime())) return isoLike;
    return d.toLocaleString();
}

function renderResult(data) {
    const box = document.getElementById("resultBox");
    if (!box) return;

    box.classList.remove("hidden", "ok", "error");

    if (data.ok) {
        const nodeCount = data.ast && typeof data.ast.node_count === "number"
            ? data.ast.node_count
            : Array.isArray(data.ast)
                ? data.ast.length
                : 0;
        box.classList.add("ok");
        box.innerHTML = `
            <strong>Valid Syntax</strong>
            <div class="result-grid">
                <div class="result-item"><strong>Status:</strong> Parsed successfully</div>
                <div class="result-item"><strong>Nodes:</strong> ${nodeCount}</div>
            </div>
            <pre>${htmlEscape(JSON.stringify(data.ast, null, 2))}</pre>
        `;
    } else {
        box.classList.add("error");
        box.innerHTML = `
            <strong>Syntax Issue Detected</strong>
            <div class="result-grid">
                <div class="result-item"><strong>Category:</strong> ${htmlEscape(data.category || "N/A")}</div>
                <div class="result-item"><strong>Line:</strong> ${htmlEscape(data.line || "N/A")}</div>
                <div class="result-item"><strong>Token:</strong> ${htmlEscape(data.token || "N/A")}</div>
                <div class="result-item"><strong>Suggestion:</strong> ${htmlEscape(data.suggestion || "N/A")}</div>
            </div>
            <p><strong>Explanation:</strong> ${htmlEscape(data.explanation || "N/A")}</p>
            <pre>${htmlEscape(data.error || "Unknown error")}</pre>
        `;
    }
}

async function handleAnalyzeSubmit(event) {
    event.preventDefault();
    const code = document.getElementById("codeInput").value;

    const response = await fetch("/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code }),
    });

    const data = await response.json();
    renderResult(data);
}

function drawBars(canvas, categories) {
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    const width = canvas.width;
    const height = canvas.height;
    ctx.clearRect(0, 0, width, height);

    if (!categories.length) {
        ctx.fillStyle = "#5a6f89";
        ctx.font = "16px Trebuchet MS";
        ctx.fillText("No errors logged yet.", 22, 36);
        return;
    }

    const max = Math.max(...categories.map((item) => item.count));
    const leftPad = 50;
    const bottomPad = 58;
    const chartHeight = height - bottomPad - 20;
    const slot = (width - leftPad - 26) / categories.length;

    ctx.strokeStyle = "#d3deec";
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i += 1) {
        const y = 20 + (chartHeight / 4) * i;
        ctx.beginPath();
        ctx.moveTo(leftPad, y);
        ctx.lineTo(width - 12, y);
        ctx.stroke();
    }

    categories.forEach((item, index) => {
        const x = leftPad + index * slot + 8;
        const barWidth = Math.max(20, slot - 16);
        const barHeight = Math.max(6, Math.floor((item.count / max) * chartHeight));
        const y = 20 + (chartHeight - barHeight);

        const grad = ctx.createLinearGradient(0, y, 0, y + barHeight);
        grad.addColorStop(0, "#1aa58f");
        grad.addColorStop(1, "#1f64af");

        ctx.fillStyle = grad;
        ctx.fillRect(x, y, barWidth, barHeight);

        ctx.fillStyle = "#122742";
        ctx.font = "12px Trebuchet MS";
        ctx.fillText(String(item.count), x + 4, y - 8);
        ctx.fillText(item.category.slice(0, 16), x + 2, height - 28);
    });
}

async function loadDashboard() {
    const canvas = document.getElementById("categoryChart");
    const body = document.querySelector("#errorsTable tbody");
    if (!canvas || !body) return;

    const [statsRes, errorsRes, reportRes] = await Promise.all([
        fetch("/api/stats"),
        fetch("/api/errors"),
        fetch("/api/report"),
    ]);

    const statsData = await statsRes.json();
    const errorsData = await errorsRes.json();
    const reportData = await reportRes.json();

    drawBars(canvas, statsData.categories || []);

    const totalNode = document.getElementById("totalErrors");
    const dominantNode = document.getElementById("dominantCategory");
    const generatedNode = document.getElementById("generatedAt");

    if (totalNode) totalNode.textContent = String(reportData.total_errors ?? 0);
    if (dominantNode) {
        dominantNode.textContent = reportData.category_distribution?.length
            ? reportData.category_distribution[0].category
            : "N/A";
    }
    if (generatedNode) generatedNode.textContent = reportData.generated_at || "N/A";

    body.innerHTML = "";
    (errorsData.errors || []).forEach((row) => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${htmlEscape(formatDate(row.created_at || ""))}</td>
            <td>${htmlEscape(row.category || "")}</td>
            <td>${htmlEscape(row.message || "")}</td>
            <td>${htmlEscape(row.suggestion || "")}</td>
        `;
        body.appendChild(tr);
    });
}

async function clearStoredErrors() {
    const response = await fetch("/api/errors/clear", {
        method: "POST",
    });
    const data = await response.json();
    if (!response.ok || !data.ok) {
        throw new Error(data.error || "Unable to clear stored errors.");
    }
}

function attachDashboardHandlers() {
    const refreshBtn = document.getElementById("refreshDashboardBtn");
    const clearBtn = document.getElementById("clearErrorsBtn");

    if (refreshBtn) {
        refreshBtn.addEventListener("click", async () => {
            refreshBtn.disabled = true;
            try {
                await loadDashboard();
            } finally {
                refreshBtn.disabled = false;
            }
        });
    }

    if (clearBtn) {
        clearBtn.addEventListener("click", async () => {
            const confirmed = window.confirm("Clear all stored error logs from dashboard analytics?");
            if (!confirmed) return;

            clearBtn.disabled = true;
            try {
                await clearStoredErrors();
                await loadDashboard();
            } catch (err) {
                window.alert(err.message || "Failed to clear stored errors.");
            } finally {
                clearBtn.disabled = false;
            }
        });
    }
}

function attachAnalyzerHandlers() {
    const form = document.getElementById("analyzeForm");
    if (!form) return;

    form.addEventListener("submit", handleAnalyzeSubmit);

    const sampleBtn = document.getElementById("sampleBtn");
    const clearBtn = document.getElementById("clearBtn");
    const input = document.getElementById("codeInput");

    sampleBtn.addEventListener("click", () => {
        input.value = "x = 8 +\nprint(x)\n";
    });

    clearBtn.addEventListener("click", () => {
        input.value = "";
        const box = document.getElementById("resultBox");
        box.classList.add("hidden");
        box.innerHTML = "";
    });
}

window.addEventListener("DOMContentLoaded", () => {
    attachAnalyzerHandlers();
    attachDashboardHandlers();
    loadDashboard();
});
