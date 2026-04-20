function atualizarStatus() {
    fetch('/api/status')
        .then(r => r.json())
        .then(data => {
            document.getElementById('status-text').textContent = 
                `Status: ${data.running ? '✅ RODANDO' : '⏹️ PARADO'}`;
            
            document.getElementById('stat-arb').textContent = data.arbitragens || 0;
            document.getElementById('stat-alertas').textContent = data.alertas_hoje || 0;
            
            let html = '';
            if (data.alertas && data.alertas.length > 0) {
                data.alertas.forEach(alerta => {
                    html += `
                    <div class="alert alert-${alerta.tipo === 'arb' ? 'success' : 'warning'}">
                        <strong>${alerta.tipo.toUpperCase()}</strong><br>
                        ${alerta.mensagem}<br>
                        <small>${alerta.data}</small>
                    </div>`;
                });
            } else {
                html = '<p class="text-muted">Nenhum alerta ainda</p>';
            }
            document.getElementById('alerts-container').innerHTML = html;
        });
}

function iniciarBot() {
    fetch('/api/start', {method: 'POST'})
        .then(r => r.json())
        .then(d => {
            console.log("Bot iniciado!");
            atualizarStatus();
        });
}

function pararBot() {
    fetch('/api/stop', {method: 'POST'})
        .then(r => r.json())
        .then(d => {
            console.log("Bot parado!");
            atualizarStatus();
        });
}

setInterval(atualizarStatus, 2000);
atualizarStatus();
