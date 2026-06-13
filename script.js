const API = 'https://projeto-igor.onrender.com';

// =========================================================================
// DADOS DO USUÁRIO LOGADO
// =========================================================================
function getUsuario() {
  const u = sessionStorage.getItem('usuario');
  return u ? JSON.parse(u) : null;
}

function carregarDadosUsuario() {
  const u = getUsuario();
  if (!u) return;

  // Sidebar e boas-vindas
  document.getElementById('nomeUsuario').textContent    = u.nome;
  document.getElementById('matriculaUsuario').textContent = u.cpf;
  document.getElementById('nomeBoasVindas').textContent = u.nome.split(' ')[0];

  // Perfil
  document.getElementById('perfilNomeCabecalho').textContent = u.nome;
  document.getElementById('perfilNome').textContent          = u.nome;
  document.getElementById('perfilEmail').textContent         = u.email;
  document.getElementById('perfilMatricula').textContent     = u.cpf;
  document.getElementById('perfilMatriculaCabecalho').textContent = u.cpf;
  document.getElementById('perfilSubtitulo').textContent     = u.tipo === 'professor' ? 'Professor' : 'Aluno';

  carregarLivros();
  carregarEmprestimosUsuario();
  carregarMensagensUsuario();
}

// =========================================================================
// NAVEGAÇÃO
// =========================================================================
function showPage(id) {
  document.querySelectorAll('.page-section').forEach(s => s.classList.remove('active'));
  document.getElementById('page-' + id).classList.add('active');
  const titles = {
    'inicio': 'Início', 'meus-emprestimos': 'Meus Empréstimos',
    'buscar': 'Buscar Livros', 'historico': 'Histórico', 'perfil': 'Meu Perfil'
  };
  document.getElementById('page-title').textContent = titles[id] || id;
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  if (event && event.currentTarget) event.currentTarget.classList.add('active');
}

// =========================================================================
// LIVROS
// =========================================================================
const cores  = ['c1','c2','c3','c4','c5','c6'];
const emojis = ['📚','📖','💻','🌍','🧠','⚗','✍','🚀','⚙','🌹','🧪','📝'];

async function carregarLivros() {
  try {
    const resp  = await fetch(`${API}/livros`);
    const livros = await resp.json();

    // Acervo completo
    const gridAcervo = document.getElementById('gridAcervo');
    if (gridAcervo) {
      gridAcervo.innerHTML = livros.length
        ? livros.map((l, i) => `
            <div class="book-card">
              <div class="book-cover ${cores[i % cores.length]}">${emojis[i % emojis.length]}</div>
              <div class="book-info">
                <div class="btitle">${l.titulo}</div>
                <div class="bauthor">${l.autor}</div>
                <div class="bavail ${l.disponiveis > 0 ? 'ok' : 'no'}">
                  ${l.disponiveis > 0 ? '✓ ' + l.disponiveis + ' disponível(is)' : '✗ Indisponível'}
                </div>
                ${l.disponiveis > 0
                  ? `<button class="btn-sm btn-primary" style="margin-top:6px;width:100%" onclick="solicitarEmprestimo(${l.id},'${l.titulo}')">Solicitar</button>`
                  : ''}
              </div>
            </div>`).join('')
        : '<div style="padding:20px;color:#aaa;text-align:center;grid-column:1/-1">Nenhum livro no acervo.</div>';
    }

    // Recomendados (início)
    const gridRec = document.getElementById('gridRecomendados');
    if (gridRec) {
      const disp = livros.filter(l => l.disponiveis > 0).slice(0, 4);
      gridRec.innerHTML = disp.length
        ? disp.map((l, i) => `
            <div class="book-card" onclick="showPage('buscar')">
              <div class="book-cover ${cores[i % cores.length]}">${emojis[i % emojis.length]}</div>
              <div class="book-info">
                <div class="btitle">${l.titulo}</div>
                <div class="bauthor">${l.autor}</div>
                <div class="bavail ok">Disponível</div>
              </div>
            </div>`).join('')
        : '<div style="color:#aaa;font-size:13px;grid-column:1/-1;text-align:center">Sem livros disponíveis.</div>';
    }
  } catch(e) { console.error('Erro ao carregar livros:', e); }
}

// =========================================================================
// EMPRÉSTIMOS DO USUÁRIO
// =========================================================================
async function solicitarEmprestimo(idLivro, titulo) {
  const u = getUsuario();
  if (!u) return alert('Faça login primeiro.');
  if (!confirm(`Solicitar empréstimo de "${titulo}"?`)) return;

  try {
    const resp = await fetch(`${API}/emprestimos`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ cpf_aluno: u.cpf, id_livro: idLivro })
    });
    const dados = await resp.json();
    alert(resp.ok ? '✅ ' + dados.message : '❌ ' + dados.detail);
    if (resp.ok) carregarEmprestimosUsuario();
  } catch(e) { alert('Erro ao conectar à API.'); }
}

async function carregarEmprestimosUsuario() {
  const u = getUsuario();
  if (!u) return;
  try {
    const resp = await fetch(`${API}/emprestimos/usuario/${u.cpf}`);
    const emps = await resp.json();

    const ativos     = emps.filter(e => e.status === 'ativo');
    const historico  = emps.filter(e => e.status === 'devolvido' || e.status === 'rejeitado');

    // Badge e texto boas-vindas
    const badge = document.getElementById('badgeEmprestimos');
    if (badge) badge.textContent = ativos.length;
    const qtd = document.getElementById('qtdEmprestimosTexto');
    if (qtd) qtd.textContent = ativos.length;
    const statAtivos = document.getElementById('statAtivos');
    if (statAtivos) statAtivos.textContent = ativos.length;
    const statDev = document.getElementById('statDevolvidos');
    if (statDev) statDev.textContent = historico.filter(e => e.status === 'devolvido').length;

    // Tabela meus empréstimos
    const tbody = document.getElementById('tabelaEmprestimos');
    if (tbody) {
      tbody.innerHTML = emps.length
        ? emps.map(e => `
            <tr>
              <td>${e.titulo_livro}</td>
              <td>${e.autor_livro}</td>
              <td>${e.data_solicitacao}</td>
              <td>${e.data_devolucao_prevista || '—'}</td>
              <td><span style="color:${statusCor(e.status)};font-weight:600">${statusLabel(e.status)}</span></td>
            </tr>`).join('')
        : '<tr><td colspan="5" style="text-align:center;color:#aaa">Nenhum empréstimo encontrado.</td></tr>';
    }

    // Lista home
    const listaHome = document.getElementById('listaEmprestimosHome');
    if (listaHome) {
      listaHome.innerHTML = ativos.length
        ? ativos.map(e => `
            <div style="padding:10px 0;border-bottom:1px solid var(--cream-dark)">
              <div style="font-weight:600;font-size:13px">${e.titulo_livro}</div>
              <div style="font-size:12px;color:var(--text-light)">Devolução: ${e.data_devolucao_prevista || 'Aguardando aprovação'}</div>
            </div>`).join('')
        : '<div style="padding:16px;color:#aaa;font-size:13px;text-align:center">Nenhum empréstimo ativo.</div>';
    }

    // Histórico
    const tbodyHist = document.getElementById('tabelaHistorico');
    if (tbodyHist) {
      tbodyHist.innerHTML = historico.length
        ? historico.map(e => `
            <tr>
              <td>${e.titulo_livro}</td>
              <td>${e.data_solicitacao}</td>
              <td>${e.data_devolucao_prevista || '—'}</td>
              <td><span style="color:${statusCor(e.status)}">${statusLabel(e.status)}</span></td>
            </tr>`).join('')
        : '<tr><td colspan="4" style="text-align:center;color:#aaa">Sem histórico.</td></tr>';
    }
  } catch(e) { console.error('Erro ao carregar empréstimos:', e); }
}

function statusLabel(s) {
  return { pendente: 'Pendente', ativo: 'Ativo', devolvido: 'Devolvido', rejeitado: 'Rejeitado' }[s] || s;
}
function statusCor(s) {
  return { pendente: '#f0a030', ativo: '#4caf7d', devolvido: '#7aaace', rejeitado: '#e05c5c' }[s] || '#888';
}

// =========================================================================
// CHAT DO USUÁRIO
// =========================================================================
function toggleChat() {
  document.getElementById('chat-box').classList.toggle('open');
}

async function carregarMensagensUsuario() {
  const u = getUsuario();
  if (!u) return;
  try {
    const resp = await fetch(`${API}/mensagens/usuario/${u.cpf}`);
    const msgs = await resp.json();
    const container = document.getElementById('chat-msgs');
    if (!container) return;

    const extras = msgs.map(m => `
      <div class="msg user">${m.mensagem}</div>
      <div class="msg-time">${m.data_envio}</div>
      ${m.resposta ? `<div class="msg bot">${m.resposta}</div>` : ''}
    `).join('');

    container.innerHTML = `
      <div class="msg bot">Olá! 😊 Posso te ajudar a encontrar livros, checar prazos ou tirar dúvidas.</div>
      ${extras}
    `;
    container.scrollTop = container.scrollHeight;
  } catch(e) {}
}

async function sendMsg() {
  const input = document.getElementById('chat-input');
  const text  = input.value.trim();
  if (!text) return;
  const u = getUsuario();
  if (!u) return;

  const msgs = document.getElementById('chat-msgs');
  msgs.innerHTML += `<div class="msg user">${text}</div>`;
  input.value = '';
  msgs.scrollTop = msgs.scrollHeight;

  try {
    await fetch(`${API}/mensagens`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        cpf_remetente: u.cpf,
        nome_remetente: u.nome,
        tipo_remetente: u.tipo,
        mensagem: text
      })
    });
  } catch(e) { console.error('Erro ao enviar mensagem:', e); }
}

function sendSug(el) {
  document.getElementById('chat-input').value = el.textContent;
  sendMsg();
  const sugs = document.getElementById('chat-sugs');
  if (sugs) sugs.style.display = 'none';
}
