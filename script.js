function showPage(id) {

  document.querySelectorAll('.page-section').forEach(s => s.classList.remove('active'));

  document.getElementById('page-' + id).classList.add('active');


  const titles = {
    'inicio': 'Início',
    'meus-emprestimos': 'Meus Empréstimos',
    'buscar': 'Buscar Livros',
    'historico': 'Histórico',
    'perfil': 'Meu Perfil'
  };
  document.getElementById('page-title').textContent = titles[id] || id;


  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  event.currentTarget.classList.add('active');
}

function toggleChat() {
  const box = document.getElementById('chat-box');
  box.classList.toggle('open');
}

function sendMsg() {
  const input = document.getElementById('chat-input');
  const text = input.value.trim();
  if (!text) return;

  const msgs = document.getElementById('chat-msgs');
  msgs.innerHTML += `<div class="msg user">${text}</div>`;
  input.value = '';
  msgs.scrollTop = msgs.scrollHeight;
}

function sendSug(el) {
  const msgs = document.getElementById('chat-msgs');
  msgs.innerHTML += `<div class="msg user">${el.textContent}</div>`;
  document.getElementById('chat-sugs').style.display = 'none';
  msgs.scrollTop = msgs.scrollHeight;
}