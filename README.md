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

1. Cadastro provavelmente não funciona

No cadastro.html você faz:

fetch('https://projeto-igor.onrender.com/login', {
    method: 'POST',
    body: JSON.stringify({ cpf, senha, email, nome, tipo })
});

Você está enviando o cadastro para:

/login

que normalmente é uma rota de autenticação, não de cadastro.

Se o backend tiver uma rota como:

/usuarios
/register
/cadastro

o cadastro nunca será salvo.

2. Envio de mensagem pode estar quebrado

No painel do usuário existe o chat:

<input type="text" id="chat-input">
<button onclick="sendMsg()">

Mas no arquivo enviado eu não encontrei a implementação do envio porque ela está em:

<script src="script.js"></script>

Ou seja:

usuario.html depende de script.js

e você não enviou esse arquivo.

É muito provável que o problema esteja nele.

3. Chat do administrador depende da API

O admin busca mensagens usando:

fetch(`${API}/mensagens`)

e responde usando:

fetch(`${API}/mensagens/${id}/responder`)

Se a API não possuir:

GET /mensagens
PUT /mensagens/{id}/responder

o chat nunca vai funcionar.

4. Página de atrasos não é preenchida

Existe a tabela:

<tbody id="tabelaAtrasos"></tbody>

Mas não existe nenhuma função:

carregarAtrasos()

nem:

renderAtrasos()

Resultado:

Página Atrasos sempre vazia
5. Histórico não é preenchido

Existe:

<tbody id="tabelaHistorico"></tbody>

Mas não achei nenhuma função carregando dados nela.

Resultado:

Histórico vazio
6. Dashboard incompleto

Você criou elementos:

statDevolucoesHoje
legendDisp
legendEmp
legendAtr
barCategorias
feedAtividade
ringPct

Mas não encontrei código preenchendo vários deles.

Provavelmente aparecem:

—
Carregando...
Vazio
7. Página do usuário depende de script.js

O maior problema é esse.

Em usuario.html existe:

<script src="script.js"></script>

e logo depois:

carregarDadosUsuario();

Então toda a lógica de:

empréstimos do usuário
histórico
busca de livros
envio de mensagens
perfil
dashboard do usuário

está dentro do script.js.

Sem ele não dá para descobrir por que a Ana não consegue enviar mensagens.

O próximo passo

Envie também:

script.js
os arquivos Python da API (FastAPI/Flask)
principalmente as rotas:
/login
/mensagens
/usuarios
/emprestimos
