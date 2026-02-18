// URL für die Abonnement-URL setzen
window.addEventListener('load', () => {
    const host = window.location.hostname;
    const port = window.location.port ? ':' + window.location.port : '';
    const protocol = window.location.protocol;
    const subscriptionUrl = `${protocol}//${host}${port}/TINF23B6.ics`;
    document.getElementById('urlInput').value = subscriptionUrl;
    
    loadModules();
});

// Module laden - NUR aus always_excluded
async function loadModules() {
    try {
        const response = await fetch('/api/modules');
        const rules = await response.json();
        
        const moduleList = document.getElementById('moduleList');
        moduleList.innerHTML = '';
        
        // Alle Events sammeln (aus ALLEN Quellen)
        const allEvents = new Set();
        
        // Always excluded
        rules.always_excluded.forEach(event => allEvents.add(event));
        
        // Time-based exclusions
        rules.time_based_exclusions.forEach(rule => {
            rule.events.forEach(event => allEvents.add(event));
        });
        
        // Sortiert anzeigen
        const sortedEvents = Array.from(allEvents).sort();
        
        if (sortedEvents.length === 0) {
            moduleList.innerHTML = '<div class="loading">Keine Module gefunden</div>';
            return;
        }
        
        sortedEvents.forEach(event => {
            // Checkbox ist ANGEHAKT, wenn das Modul in always_excluded ist (wird ausgeblendet)
            const isExcluded = rules.always_excluded.includes(event);
            
            const moduleItem = document.createElement('div');
            moduleItem.className = 'module-item';
            moduleItem.innerHTML = `
                <input type="checkbox" 
                       id="module-${escapeHtml(event)}" 
                       data-module="${event}"
                       title="Anhaken = aus dem Kalender entfernen"
                       ${isExcluded ? 'checked' : ''}>
                <label for="module-${escapeHtml(event)}">${escapeHtml(event)}</label>
            `;
            moduleList.appendChild(moduleItem);
        });
        
    } catch (error) {
        console.error('Fehler beim Laden der Module:', error);
        showToast('Fehler beim Laden der Module', 'error');
    }
}

// Einstellungen speichern
document.getElementById('saveBtn').addEventListener('click', async () => {
    try {
        // Alle ANGEKREUZTEN Module sammeln (diese werden ausgeblendet)
        const checkboxes = document.querySelectorAll('.module-item input[type="checkbox"]');
        const excludedModules = [];
        
        checkboxes.forEach(checkbox => {
            const module = checkbox.dataset.module;
            // ANGEKREUZTE Module werden ausgeblendet
            if (checkbox.checked) {
                excludedModules.push(module);
            }
        });
        
        // An Server senden
        const response = await fetch('/api/save-preferences', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                excluded_modules: excludedModules
            })
        });
        
        const data = await response.json().catch(() => null);
        
        if (!response.ok) {
            const message = data && data.message ? data.message : 'Speichern fehlgeschlagen';
            throw new Error(message);
        }
        
        showToast('✅ Einstellungen erfolgreich gespeichert!');
        
        // Module neu laden
        setTimeout(loadModules, 500);
        
    } catch (error) {
        console.error('Fehler beim Speichern:', error);
        showToast('Fehler beim Speichern der Einstellungen: ' + error.message, 'error');
    }
});

// Zurücksetzen - alle Module wieder anzeigen
document.getElementById('resetBtn').addEventListener('click', async () => {
    if (confirm('Alle ausgeblendeten Module wieder anzeigen?')) {
        try {
            const response = await fetch('/api/save-preferences', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    excluded_modules: []
                })
            });
            
            if (!response.ok) throw new Error('Zurücksetzen fehlgeschlagen');
            
            loadModules();
            showToast('Alle Module wieder aktiviert');
        } catch (error) {
            console.error('Fehler beim Zurücksetzen:', error);
            showToast('Fehler beim Zurücksetzen', 'error');
        }
    }
});

// Module von RAPLA aktualisieren
document.getElementById('refreshBtn').addEventListener('click', async () => {
    try {
        document.getElementById('refreshBtn').disabled = true;
        document.getElementById('refreshBtn').textContent = '⏳ Wird aktualisiert...';
        
        const response = await fetch('/api/refresh-modules', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const data = await response.json().catch(() => null);
        
        if (!response.ok) {
            const message = data && data.message ? data.message : 'Aktualisierung fehlgeschlagen';
            throw new Error(message);
        }
        
        showToast('✅ ' + (data.message || 'Module erfolgreich aktualisiert!'));
        
        // Module neu laden
        setTimeout(loadModules, 500);
        
    } catch (error) {
        console.error('Fehler beim Aktualisieren:', error);
        showToast('Fehler beim Aktualisieren der Module: ' + error.message, 'error');
    } finally {
        document.getElementById('refreshBtn').disabled = false;
        document.getElementById('refreshBtn').textContent = '🔃 Module aktualisieren';
    }
});

// Toast Notifikation anzeigen
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast show ${type}`;
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// URL kopieren
function copyToClipboard() {
    const urlInput = document.getElementById('urlInput');
    urlInput.select();
    document.execCommand('copy');
    showToast('📋 URL kopiert!');
}

// HTML escapen für Sicherheit
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}
