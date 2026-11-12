const search = document.getElementById('search');
if (search) search.addEventListener('input', () => {
  const q = search.value.toLowerCase();
  document.querySelectorAll('#patient-table tbody tr').forEach(row => {
    row.style.display = row.innerText.toLowerCase().includes(q) ? '' : 'none';
  });
});
async function loadInsights(){
  const text = document.getElementById('insight-text');
  const list = document.getElementById('risk-list');
  try {
    const response = await fetch('/api/insights');
    const data = await response.json();
    text.textContent = data.message;
    list.innerHTML = data.priority_patients.length
      ? '<h3>Patients flagged by demo heuristic</h3>' + data.priority_patients.map(p => `<p class="note"><b>${escapeHtml(p.name)}</b> · T${p.triage} · Risk ${p.risk}/100</p>`).join('')
      : '<p class="note">No patient currently reaches the demo high-risk threshold.</p>';
  } catch (e) { text.textContent = 'Could not load the local analysis. Refresh the page and try again.'; }
}
function escapeHtml(value){return String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
document.getElementById('refresh-insights')?.addEventListener('click', loadInsights);
loadInsights();
