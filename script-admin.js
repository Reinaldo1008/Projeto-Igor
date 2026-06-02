// NAVEGAÇÃO
function showPage(id) {
  document.querySelectorAll('.page-section').forEach(s => s.classList.remove('active'));

  const target = document.getElementById('page-' + id);
  if (target) target.classList.add('active');

  const titles = {
    'dashboard':   'Dashboard',
    'emprestimos': 'Empréstimos',
    'acervo':      'Acervo',
    'alunos':      'Alunos',
    'professores': 'Professores',
    'atrasos':     'Atrasos',
    'historico':   'Histórico de Empréstimos',
    'relatorios':  'Relatórios'
  };

  const titleEl = document.getElementById('page-title');
  if (titleEl) titleEl.textContent = titles[id] || id;

  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => {
    if (n.getAttribute('onclick') && n.getAttribute('onclick').includes("'" + id + "'")) {
      n.classList.add('active');
    }
  });
}

// TABS (seção empréstimos)
function filterTab(el, filtro) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  el.classList.add('active');
}

// MODAIS
function openModal(id) {
  const el = document.getElementById('modal-' + id);
  if (el) { el.style.display = 'flex'; setTimeout(() => el.classList.add('open'), 10); }
}

function closeModal(id) {
  const el = document.getElementById('modal-' + id);
  if (el) { el.classList.remove('open'); setTimeout(() => el.style.display = 'none', 250); }
}

document.addEventListener('click', function(e) {
  if (e.target.classList.contains('modal-overlay')) {
    const id = e.target.id.replace('modal-', '');
    closeModal(id);
  }
});

// CHAT
function toggleChat() {
  const box = document.getElementById('chat-box');
  if (box) box.classList.toggle('open');
}

function sendMsg() {
  const input = document.getElementById('chat-input');
  const text = input.value.trim();
  if (!text) return;
  const msgs = document.getElementById('chat-msgs');
  msgs.innerHTML += '<div class="msg user">' + text + '</div>';
  input.value = '';
  msgs.scrollTop = msgs.scrollHeight;
}

function sendSug(el) {
  const msgs = document.getElementById('chat-msgs');
  msgs.innerHTML += '<div class="msg user">' + el.textContent + '</div>';
  const sugs = document.getElementById('chat-sugs');
  if (sugs) sugs.style.display = 'none';
  msgs.scrollTop = msgs.scrollHeight;
}

function carregarDadosAdmin() {}