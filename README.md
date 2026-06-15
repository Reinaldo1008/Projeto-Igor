Na sua página adm.html, a função que é chamada ao clicar nas abas é:

function filterTab(el, filtro) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  el.classList.add('active');
}

Ela só muda a aparência do botão selecionado. Não existe nenhuma lógica para filtrar os empréstimos.

Quando você clica em:

<button class="tab" onclick="filterTab(this,'ativos')">Ativos</button>
<button class="tab" onclick="filterTab(this,'atrasados')">Atrasados</button>
<button class="tab" onclick="filterTab(this,'devolvidos')">Devolvidos</button>

o parâmetro filtro é recebido, mas nunca é usado.

Por isso:

"Todos" mostra tudo.
"Ativos" continua mostrando tudo.
"Atrasados" continua mostrando tudo.
"Devolvidos" continua mostrando tudo.

A tabela nunca é reconstruída.

Como corrigir

Você precisa guardar os empréstimos carregados pela API em uma variável global:

let emprestimosCache = [];

Dentro de carregarEmprestimosAdmin():

const resp = await fetch(`${API}/emprestimos`);
const emps = await resp.json();

emprestimosCache = emps;

Crie uma função para renderizar a tabela:

function renderTabelaEmprestimos(lista) {
  const tbody = document.getElementById('tabelaEmprestimos');

  tbody.innerHTML = lista.map(e => `
    <tr>
      <td>${e.nome_aluno}</td>
      <td>${e.cpf_aluno}</td>
      <td>${e.titulo_livro}</td>
      <td>${e.data_solicitacao}</td>
      <td>${e.data_devolucao_prevista || '—'}</td>
      <td>
        <span style="color:${statusCor(e.status)};font-weight:600">
          ${statusLabel(e.status)}
        </span>
      </td>
      <td>${botoesAcao(e)}</td>
    </tr>
  `).join('');
}

E substituir a função atual por:

function filterTab(el, filtro) {
  document.querySelectorAll('.tab')
    .forEach(t => t.classList.remove('active'));

  el.classList.add('active');

  let filtrados = emprestimosCache;

  if (filtro === 'ativos') {
    filtrados = emprestimosCache.filter(
      e => e.status === 'ativo'
    );
  }

  if (filtro === 'devolvidos') {
    filtrados = emprestimosCache.filter(
      e => e.status === 'devolvido'
    );
  }

  if (filtro === 'atrasados') {
    filtrados = emprestimosCache.filter(
      e => e.status === 'pendente'
    );
  }

  renderTabelaEmprestimos(filtrados);
}

Tem mais uma coisa que me chamou atenção:

No seu código não existe status "atrasado".

Os status encontrados são:

pendente
ativo
devolvido
rejeitado

Então o botão "Atrasados" provavelmente está errado. Ele está sendo usado visualmente, mas o sistema não possui empréstimos com status "atrasado".
