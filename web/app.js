// Tela de cadastros (clientes e veículos) consumindo a API do GiroCerto.
// A URL da API vem de config.js, gerado no deploy (RNF-03).

const API = (window.GIROCERTO_CONFIG && window.GIROCERTO_CONFIG.apiUrl || "").replace(/\/$/, "");
const $ = (sel) => document.querySelector(sel);

async function api(metodo, caminho, corpo) {
  const resp = await fetch(API + caminho, {
    method: metodo,
    headers: corpo ? { "Content-Type": "application/json" } : {},
    body: corpo ? JSON.stringify(corpo) : undefined,
  });
  const dados = resp.status === 204 ? null : await resp.json();
  if (!resp.ok) throw new Error(dados && dados.erro || `Erro ${resp.status}`);
  return dados;
}

function avisar(texto, erro = false) {
  const el = $("#aviso");
  el.textContent = texto;
  el.className = erro ? "aviso erro" : "aviso";
  el.hidden = false;
  clearTimeout(avisar.t);
  avisar.t = setTimeout(() => (el.hidden = true), 5000);
}

function esc(v) {
  return String(v == null ? "" : v).replace(/[&<>"']/g, (c) => `&#${c.charCodeAt(0)};`);
}

function dadosDoForm(form) {
  const d = Object.fromEntries(new FormData(form));
  Object.keys(d).forEach((k) => d[k] === "" && (d[k] = null));
  return d;
}

function preencher(form, obj) {
  for (const el of form.elements) if (el.name && el.name in obj) el.value = obj[el.name] ?? "";
  modoEdicao(form, obj.id);
  form.scrollIntoView({ behavior: "smooth" });
  form.querySelector("input:not([type=hidden])").focus();
}

// Deixa visível que o formulário está editando um registro, e não criando
function modoEdicao(form, id) {
  const botao = form.querySelector("[type=submit]");
  botao.dataset.texto = botao.dataset.texto || botao.textContent;
  botao.textContent = id ? `Salvar alterações (#${id})` : botao.dataset.texto;
  form.querySelector("[type=reset]").textContent = id ? "Cancelar edição" : "Limpar";
  form.classList.toggle("editando", Boolean(id));
}

// reset() não limpa input hidden (o value dele é o próprio atributo), então
// sem isso o próximo "novo" cadastro viraria um PUT no registro editado
document.querySelectorAll(".form").forEach((form) =>
  form.addEventListener("reset", () => {
    form.elements.id.value = "";
    modoEdicao(form, null);
  }));

async function salvar(form, recurso, depois) {
  const d = dadosDoForm(form);
  const id = d.id;
  delete d.id;
  try {
    const salvo = await api(id ? "PUT" : "POST", id ? `/${recurso}/${id}` : `/${recurso}`, d);
    avisar(id ? `Registro #${salvo.id} atualizado.` : `Registro #${salvo.id} criado.`);
    form.reset();
    await depois();
    destacarLinha(form.getAttribute("id").replace("form-", ""), salvo.id);
  } catch (e) {
    avisar(e.message, true);
  }
}

function destacarLinha(tipo, id) {
  const botao = document.querySelector(`[data-editar-${tipo}="${id}"]`);
  if (!botao) return;
  const linha = botao.closest("tr");
  linha.classList.add("destaque");
  linha.scrollIntoView({ behavior: "smooth", block: "center" });
  setTimeout(() => linha.classList.remove("destaque"), 2500);
}

async function excluir(recurso, id, depois) {
  if (!confirm(`Excluir o registro ${id}?`)) return;
  try {
    await api("DELETE", `/${recurso}/${id}`);
    avisar("Registro excluído.");
    await depois();
  } catch (e) {
    avisar(e.message, true);
  }
}

// ---------- clientes ----------

let clientes = [];

async function carregarClientes() {
  const busca = $("#busca").value.trim();
  clientes = await api("GET", "/clientes" + (busca ? `?busca=${encodeURIComponent(busca)}` : ""));
  $("#lista-clientes").innerHTML = clientes.map((c) => `
    <tr>
      <td class="mono">${c.id}</td><td>${esc(c.nome)}</td><td class="mono">${esc(c.telefone)}</td>
      <td>${esc(c.email)}</td><td>${c.totalVeiculos}</td>
      <td><button class="link" data-editar-cliente="${c.id}">Editar</button>
          <button class="link" data-excluir-cliente="${c.id}">Excluir</button></td>
    </tr>`).join("") || `<tr><td colspan="6" class="muted">Nenhum cliente encontrado.</td></tr>`;
  if (!busca) atualizarSelectsDeCliente();
}

function atualizarSelectsDeCliente() {
  const opcoes = clientes.map((c) => `<option value="${c.id}">${esc(c.nome)}</option>`).join("");
  const filtro = $("#filtro-cliente");
  const atual = filtro.value;
  filtro.innerHTML = `<option value="">Todos os clientes</option>` + opcoes;
  filtro.value = atual;
  $("#form-veiculo [name=clienteId]").innerHTML = opcoes;
}

$("#form-cliente").addEventListener("submit", (ev) => {
  ev.preventDefault();
  salvar(ev.target, "clientes", carregarClientes);
});

$("#lista-clientes").addEventListener("click", (ev) => {
  const { editarCliente, excluirCliente } = ev.target.dataset;
  if (editarCliente) preencher($("#form-cliente"), clientes.find((c) => c.id == editarCliente));
  if (excluirCliente) excluir("clientes", excluirCliente, carregarClientes);
});

let tBusca;
$("#busca").addEventListener("input", () => {
  clearTimeout(tBusca);
  tBusca = setTimeout(() => carregarClientes().catch((e) => avisar(e.message, true)), 300);
});

// ---------- veículos ----------

let veiculos = [];

async function carregarVeiculos() {
  const clienteId = $("#filtro-cliente").value;
  veiculos = await api("GET", "/veiculos" + (clienteId ? `?clienteId=${clienteId}` : ""));
  $("#lista-veiculos").innerHTML = veiculos.map((v) => `
    <tr>
      <td class="mono">${v.id}</td><td class="mono">${esc(v.placa)}</td>
      <td>${esc(v.marca)} ${esc(v.modelo)}</td><td>${v.ano}</td><td>${esc(v.clienteNome)}</td>
      <td><button class="link" data-editar-veiculo="${v.id}">Editar</button>
          <button class="link" data-excluir-veiculo="${v.id}">Excluir</button></td>
    </tr>`).join("") || `<tr><td colspan="6" class="muted">Nenhum veículo cadastrado.</td></tr>`;
}

$("#form-veiculo").addEventListener("submit", (ev) => {
  ev.preventDefault();
  salvar(ev.target, "veiculos", async () => { await carregarVeiculos(); await carregarClientes(); });
});

$("#lista-veiculos").addEventListener("click", (ev) => {
  const { editarVeiculo, excluirVeiculo } = ev.target.dataset;
  if (editarVeiculo) preencher($("#form-veiculo"), veiculos.find((v) => v.id == editarVeiculo));
  if (excluirVeiculo) excluir("veiculos", excluirVeiculo, async () => { await carregarVeiculos(); await carregarClientes(); });
});

$("#filtro-cliente").addEventListener("change", () => carregarVeiculos().catch((e) => avisar(e.message, true)));

// ---------- abas ----------

function mostrarAba() {
  const aba = location.hash === "#veiculos" ? "veiculos" : "clientes";
  document.querySelectorAll(".aba").forEach((s) => (s.hidden = s.id !== `aba-${aba}`));
  document.querySelectorAll("nav a").forEach((a) => a.classList.toggle("ativa", a.dataset.aba === aba));
}
window.addEventListener("hashchange", mostrarAba);

(async function iniciar() {
  mostrarAba();
  $("#api-url").textContent = API || "(não configurada: crie web/config.js)";
  if (!API) return avisar("URL da API não configurada. Veja o README.", true);
  try {
    await carregarClientes();
    await carregarVeiculos();
  } catch (e) {
    avisar("Não foi possível falar com a API: " + e.message, true);
  }
})();
