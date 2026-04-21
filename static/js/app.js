function atualizarStatus() {
    fetch('/api/status')
        .then(r => r.json())
        .then(data => {

            document.getElementById('status-text').textContent =
                `Status: ${data.running ? '✅ RODANDO' : '⏹️ PARADO'}`;

            document.getElementById('stat-arb').textContent =
                data.arbitragens ?? 0;

            document.getElementById('stat-alertas').textContent =
                data.alertas_hoje ?? 0;

            let html = '';

            if (data.alertas && data.alertas.length > 0) {
                data.alertas.forEach(alerta => {

                    const margem = Number(alerta.margem || 0).toFixed(2);
                    const lucro = Number(alerta.lucro || 0).toFixed(2);

                    html += `
                    <div class="alert alert-success">
                        <strong>${alerta.tipo || 'ALERTA'}</strong><br>
                        ${alerta.esporte || '-'}<br>
                        ${alerta.jogo || '-'}<br>
                        Margem: ${margem}% | Lucro: R$ ${lucro}<br>
                        <small>${alerta.data || ''}</small>
                    </div>`;
                });
            } else {
                html = '<p class="text-muted">Nenhum alerta ainda.</p>';
            }

            document.getElementById('alerts-container').innerHTML = html;

        })
        .catch(err => console.log("Erro JS:", err));
}

function iniciarBot() {
    fetch('/api/start', { method: 'POST' })
        .then(() => setTimeout(atualizarStatus, 1000));
}

function pararBot() {
    fetch('/api/stop', { method: 'POST' })
        .then(() => setTimeout(atualizarStatus, 1000));
}

setInterval(atualizarStatus, 3000);
atualizarStatus();
