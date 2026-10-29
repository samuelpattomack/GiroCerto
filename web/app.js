// Tela do sistema (clientes, veículos, serviços, ordens com anexos e relatórios)
// consumindo a API do GiroCerto.
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
  // Checkbox desmarcado não entra no FormData
  form.querySelectorAll("input[type=checkbox]").forEach((c) => (d[c.name] = c.checked));
  return d;
}

function preencher(form, obj) {
  for (const el of form.elements) {
    if (!el.name || !(el.name in obj)) continue;
    if (el.type === "checkbox") el.checked = Boolean(obj[el.name]);
    else el.value = obj[el.name] ?? "";
  }
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
document.querySelectorAll(".form").forEach((form) => {
  if (!form.elements.id) return;
  form.addEventListener("reset", () => {
    form.elements.id.value = "";
    modoEdicao(form, null);
  });
});

const moeda = (v) => Number(v || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
const dataBr = (iso) => (iso ? iso.slice(0, 10).split("-").reverse().join("/") : "");
const ROTULOS = {
  ABERTA: "Aberta", EM_ANDAMENTO: "Em andamento", CONCLUIDA: "Concluída", CANCELADA: "Cancelada",
  PENDENTE: "Processando", PROCESSADO: "Processado", ERRO: "Erro",
};
const selo = (s) => `<span class="selo ${esc(s)}">${esc(ROTULOS[s] || s)}</span>`;
const STATUS = ["ABERTA", "EM_ANDAMENTO", "CONCLUIDA", "CANCELADA"];

function tamanhoArquivo(bytes) {
  if (!bytes) return "";
  return bytes < 1024 * 1024 ? `${Math.ceil(bytes / 1024)} KB` : `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

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

// ---------- serviços (HU-04) ----------

let servicos = [];

async function carregarServicos() {
  servicos = await api("GET", "/servicos");
  $("#lista-servicos").innerHTML = servicos.map((s) => `
    <tr class="${s.ativo ? "" : "inativo"}">
      <td class="mono">${s.id}</td><td>${esc(s.nome)}</td><td>${esc(s.categoria)}</td>
      <td>${moeda(s.precoReferencia)}</td><td>${s.ativo ? "Ativo" : "Inativo"}</td>
      <td><button class="link" data-editar-servico="${s.id}">Editar</button>
          <button class="link" data-excluir-servico="${s.id}">Excluir</button></td>
    </tr>`).join("") || `<tr><td colspan="6" class="muted">Nenhum serviço cadastrado.</td></tr>`;
}

$("#form-servico").addEventListener("submit", (ev) => {
  ev.preventDefault();
  salvar(ev.target, "servicos", carregarServicos);
});

$("#lista-servicos").addEventListener("click", (ev) => {
  const { editarServico, excluirServico } = ev.target.dataset;
  if (editarServico) preencher($("#form-servico"), servicos.find((s) => s.id == editarServico));
  if (excluirServico) excluir("servicos", excluirServico, carregarServicos);
});

// ---------- ordens de serviço (HU-03) ----------

let ordens = [];
let ordemAberta = null;

async function carregarOrdens() {
  const status = $("#filtro-status").value;
  ordens = await api("GET", "/ordens" + (status ? `?status=${status}` : ""));
  $("#lista-ordens").innerHTML = ordens.map((o) => `
    <tr class="${ordemAberta && ordemAberta.id === o.id ? "destaque" : ""}">
      <td class="mono">${o.id}</td><td>${dataBr(o.dataEntrada)}</td>
      <td class="mono">${esc(o.placa)} <span class="muted">${esc(o.modelo)}</span></td>
      <td>${esc(o.clienteNome)}</td><td>${selo(o.status)}</td><td>${moeda(o.total)}</td>
      <td><button class="link" data-abrir-ordem="${o.id}">Abrir</button></td>
    </tr>`).join("") || `<tr><td colspan="7" class="muted">Nenhuma ordem encontrada.</td></tr>`;
}

async function carregarVeiculosDaOrdem() {
  const todos = await api("GET", "/veiculos");
  $("#form-ordem [name=veiculoId]").innerHTML = todos.map((v) =>
    `<option value="${v.id}">${esc(v.placa)} - ${esc(v.modelo)} (${esc(v.clienteNome)})</option>`).join("");
}

$("#form-ordem").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  try {
    const ordem = await api("POST", "/ordens", dadosDoForm(ev.target));
    avisar(`Ordem nº ${ordem.id} aberta.`);
    ev.target.reset();
    await abrirOrdem(ordem.id);
  } catch (e) {
    avisar(e.message, true);
  }
});

$("#filtro-status").addEventListener("change", () => carregarOrdens().catch((e) => avisar(e.message, true)));

$("#lista-ordens").addEventListener("click", (ev) => {
  const { abrirOrdem: id } = ev.target.dataset;
  if (id) abrirOrdem(Number(id)).catch((e) => avisar(e.message, true));
});

async function abrirOrdem(id) {
  const [ordem, anexos] = await Promise.all([
    api("GET", `/ordens/${id}`),
    api("GET", `/ordens/${id}/anexos`),
    servicos.length ? null : carregarServicos(),
  ]);
  ordemAberta = ordem;
  renderOrdem(ordem, anexos);
  await carregarOrdens();
  $("#detalhe-ordem").scrollIntoView({ behavior: "smooth" });
}

function renderOrdem(o, anexos) {
  const editavel = !["CONCLUIDA", "CANCELADA"].includes(o.status);
  const ativos = servicos.filter((s) => s.ativo);
  const el = $("#detalhe-ordem");
  el.hidden = false;
  el.innerHTML = `
    <div class="detalhe-cab">
      <div>
        <h3>Ordem nº ${o.id} ${selo(o.status)}</h3>
        <p class="muted">${esc(o.placa)} · ${esc(o.marca)} ${esc(o.modelo)} · ${esc(o.clienteNome)} ·
          entrada ${dataBr(o.dataEntrada)}${o.dataSaida ? ` · saída ${dataBr(o.dataSaida)}` : ""}</p>
      </div>
      <div class="total">${moeda(o.total)}</div>
    </div>

    ${editavel ? `
    <form id="form-ordem-dados" class="form compacto">
      <label>Status<select name="status">${STATUS.map((s) =>
        `<option value="${s}" ${s === o.status ? "selected" : ""}>${ROTULOS[s]}</option>`).join("")}</select></label>
      <label>Quilometragem<input name="quilometragem" type="number" min="0" required value="${o.quilometragem}"></label>
      <label class="largo">Problema relatado<input name="descricao" required maxlength="2000" value="${esc(o.descricao)}"></label>
      <div class="acoes">
        <button type="submit" class="botao">Salvar ordem</button>
        ${o.status === "ABERTA" ? `<button type="button" class="botao sec" data-excluir-ordem="${o.id}">Excluir</button>` : ""}
        <button type="button" class="botao sec" data-fechar-ordem>Fechar</button>
      </div>
    </form>` : `
    <p><strong>Quilometragem:</strong> ${o.quilometragem} km · <strong>Problema:</strong> ${esc(o.descricao)}</p>
    <p class="muted">Ordem ${o.status === "CONCLUIDA" ? "concluída" : "cancelada"}: não aceita mais alterações.
      <button type="button" class="link" data-fechar-ordem>Fechar</button></p>`}

    <h4>Serviços</h4>
    <table class="tabela">
      <thead><tr><th>Serviço</th><th>Categoria</th><th>Qtd.</th><th>Valor unit.</th><th>Subtotal</th><th></th></tr></thead>
      <tbody>${o.itens.map((i) => `
        <tr><td>${esc(i.nome)}</td><td>${esc(i.categoria)}</td><td>${i.quantidade}</td>
          <td>${moeda(i.valorUnitario)}</td><td>${moeda(i.subtotal)}</td>
          <td>${editavel ? `<button class="link" data-remover-item="${i.servicoId}">Remover</button>` : ""}</td></tr>`).join("")
        || `<tr><td colspan="6" class="muted">Nenhum serviço adicionado.</td></tr>`}</tbody>
    </table>
    ${editavel ? `
    <form id="form-item" class="form compacto">
      <label class="largo">Serviço<select name="servicoId" required>${ativos.map((s) =>
        `<option value="${s.id}" data-preco="${s.precoReferencia}">${esc(s.nome)} (${moeda(s.precoReferencia)})</option>`).join("")}</select></label>
      <label>Quantidade<input name="quantidade" type="number" min="1" value="1" required></label>
      <label>Valor unitário (R$)<input name="valorUnitario" type="number" min="0" step="0.01"
        placeholder="${ativos[0] ? ativos[0].precoReferencia : ""}"></label>
      <div class="acoes"><button type="submit" class="botao">Adicionar serviço</button></div>
    </form>` : ""}

    <h4>Fotos e documentos</h4>
    <form id="form-anexo" class="form compacto">
      <label class="largo">Foto (JPG, PNG) ou PDF de até 10 MB
        <input name="arquivo" type="file" accept="image/jpeg,image/png,application/pdf" required></label>
      <div class="acoes"><button type="submit" class="botao">Enviar arquivo</button></div>
    </form>
    <div id="lista-anexos" class="anexos"></div>`;
  renderAnexos(anexos);
}

function renderAnexos(anexos) {
  const el = $("#lista-anexos");
  if (!el) return;
  el.innerHTML = anexos.map((a) => {
    let previa = a.tipo === "application/pdf" ? "PDF" : "Processando...";
    if (a.urlMiniatura) previa = `<img src="${esc(a.urlMiniatura)}" alt="Miniatura de ${esc(a.nomeOriginal)}">`;
    else if (a.situacao === "ERRO") previa = "Sem miniatura";
    const nome = a.url ? `<a href="${esc(a.url)}" target="_blank" rel="noopener">${esc(a.nomeOriginal)}</a>` : esc(a.nomeOriginal);
    return `
      <div class="anexo">
        <div class="miniatura">${previa}</div>
        <div><strong>${nome}</strong></div>
        <div class="muted">${tamanhoArquivo(a.tamanhoBytes)}${a.largura ? ` · ${a.largura}x${a.altura}` : ""} · ${dataBr(a.enviadoEm)}</div>
        <div>${selo(a.situacao)}</div>
      </div>`;
  }).join("") || `<p class="muted">Nenhum arquivo anexado.</p>`;
}

// A Lambda processa-anexo roda logo depois do upload (RF-03): consulta de
// 3 em 3 segundos até sair de PENDENTE, por no máximo 1 minuto (HU-05)
function acompanharAnexos(ordemId, tentativas = 20) {
  setTimeout(async () => {
    if (!ordemAberta || ordemAberta.id !== ordemId) return;
    try {
      const anexos = await api("GET", `/ordens/${ordemId}/anexos`);
      renderAnexos(anexos);
      if (anexos.some((a) => a.situacao === "PENDENTE") && tentativas > 1) acompanharAnexos(ordemId, tentativas - 1);
    } catch (e) {
      avisar(e.message, true);
    }
  }, 3000);
}

async function enviarAnexo(form) {
  const arquivo = form.arquivo.files[0];
  if (!arquivo) return;
  if (!["image/jpeg", "image/png", "application/pdf"].includes(arquivo.type)) {
    return avisar("Só são aceitos arquivos JPG, PNG e PDF.", true);
  }
  if (arquivo.size > 10 * 1024 * 1024) return avisar("O arquivo deve ter no máximo 10 MB.", true);

  const botao = form.querySelector("[type=submit]");
  botao.disabled = true;
  botao.textContent = "Enviando...";
  const ordemId = ordemAberta.id;
  try {
    // 1) o backend registra o anexo e devolve a URL pré-assinada (RF-02)
    const { uploadUrl, headers } = await api("POST", `/ordens/${ordemId}/anexos/upload-url`,
      { nomeArquivo: arquivo.name, tipo: arquivo.type, tamanho: arquivo.size });
    // 2) o navegador envia o arquivo direto para o S3, sem passar pela API
    let resp;
    try {
      resp = await fetch(uploadUrl, { method: "PUT", headers, body: arquivo });
    } catch (e) {
      throw new Error("Não foi possível enviar ao S3. Confira o CORS do bucket de anexos.");
    }
    if (!resp.ok) throw new Error(`O S3 recusou o arquivo (HTTP ${resp.status}).`);
    avisar("Arquivo enviado. Gerando miniatura...");
    form.reset();
    renderAnexos(await api("GET", `/ordens/${ordemId}/anexos`));
    acompanharAnexos(ordemId);
  } catch (e) {
    avisar(e.message, true);
  } finally {
    botao.disabled = false;
    botao.textContent = "Enviar arquivo";
  }
}

$("#detalhe-ordem").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const form = ev.target;
  const id = ordemAberta.id;
  try {
    if (form.id === "form-anexo") return await enviarAnexo(form);
    if (form.id === "form-ordem-dados") {
      await api("PUT", `/ordens/${id}`, dadosDoForm(form));
      avisar(`Ordem nº ${id} atualizada.`);
    }
    if (form.id === "form-item") {
      await api("POST", `/ordens/${id}/itens`, dadosDoForm(form));
      avisar("Serviço adicionado.");
    }
    await abrirOrdem(id);
  } catch (e) {
    avisar(e.message, true);
  }
});

$("#detalhe-ordem").addEventListener("change", (ev) => {
  // Sugere o preço de referência do serviço escolhido (HU-04)
  if (ev.target.name !== "servicoId") return;
  const preco = ev.target.selectedOptions[0].dataset.preco;
  ev.target.form.valorUnitario.placeholder = preco;
});

$("#detalhe-ordem").addEventListener("click", async (ev) => {
  const { removerItem, excluirOrdem } = ev.target.dataset;
  const id = ordemAberta && ordemAberta.id;
  try {
    if ("fecharOrdem" in ev.target.dataset) {
      ordemAberta = null;
      $("#detalhe-ordem").hidden = true;
      await carregarOrdens();
    }
    if (removerItem) {
      await api("DELETE", `/ordens/${id}/itens/${removerItem}`);
      avisar("Serviço removido.");
      await abrirOrdem(id);
    }
    if (excluirOrdem && confirm(`Excluir a ordem nº ${id}?`)) {
      await api("DELETE", `/ordens/${id}`);
      avisar(`Ordem nº ${id} excluída.`);
      ordemAberta = null;
      $("#detalhe-ordem").hidden = true;
      await carregarOrdens();
    }
  } catch (e) {
    avisar(e.message, true);
  }
});

// ---------- relatórios (HU-06, RF-04) ----------

function datasPadrao() {
  const form = $("#form-relatorio");
  if (form.fim.value) return;
  const hoje = new Date();
  const inicio = new Date(hoje.getFullYear(), hoje.getMonth() - 11, 1);
  const iso = (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  form.inicio.value = iso(inicio);
  form.fim.value = iso(hoje);
}

async function carregarRelatorios() {
  datasPadrao();
  const f = $("#form-relatorio");
  const q = `?inicio=${f.inicio.value}&fim=${f.fim.value}`;
  const [fat, top] = await Promise.all([
    api("GET", "/relatorios/faturamento-mensal" + q),
    api("GET", "/relatorios/servicos-mais-realizados" + q),
  ]);
  $("#resumo-faturamento").innerHTML = `
    <div><span class="muted">Faturado no período</span><strong>${moeda(fat.totalFaturado)}</strong></div>
    <div><span class="muted">Ordens concluídas</span><strong>${fat.totalOrdens}</strong></div>`;
  const maior = Math.max(...fat.meses.map((m) => m.total), 1);
  $("#lista-faturamento").innerHTML = fat.meses.map((m) => `
    <tr><td class="mono">${m.mes.split("-").reverse().join("/")}</td><td>${m.ordens}</td><td>${moeda(m.total)}</td>
      <td><div class="barra" style="width:${(m.total / maior) * 100}%"></div></td></tr>`).join("")
    || `<tr><td colspan="4" class="muted">Nenhuma ordem concluída no período.</td></tr>`;
  $("#lista-top-servicos").innerHTML = top.servicos.map((s, i) => `
    <tr><td>${i + 1}</td><td>${esc(s.nome)}</td><td>${esc(s.categoria)}</td><td>${s.quantidade}</td>
      <td>${s.ordens}</td><td>${moeda(s.receita)}</td></tr>`).join("")
    || `<tr><td colspan="6" class="muted">Nenhum serviço realizado no período.</td></tr>`;
}

$("#form-relatorio").addEventListener("submit", (ev) => {
  ev.preventDefault();
  carregarRelatorios().catch((e) => avisar(e.message, true));
});

// ---------- abas ----------

const ABAS = {
  clientes: carregarClientes,
  veiculos: carregarVeiculos,
  servicos: carregarServicos,
  ordens: () => Promise.all([carregarOrdens(), carregarVeiculosDaOrdem(), servicos.length ? null : carregarServicos()]),
  relatorios: carregarRelatorios,
};

function mostrarAba() {
  const pedida = location.hash.slice(1);
  const aba = pedida in ABAS ? pedida : "clientes";
  document.querySelectorAll(".aba").forEach((s) => (s.hidden = s.id !== `aba-${aba}`));
  document.querySelectorAll("nav a").forEach((a) => a.classList.toggle("ativa", a.dataset.aba === aba));
  return aba;
}

window.addEventListener("hashchange", () => {
  const aba = mostrarAba();
  if (API) ABAS[aba]().catch((e) => avisar(e.message, true));
});

(async function iniciar() {
  const aba = mostrarAba();
  $("#api-url").textContent = API || "(não configurada: crie web/config.js)";
  if (!API) return avisar("URL da API não configurada. Veja o README.", true);
  try {
    // Clientes alimenta os selects de cliente usados na aba de veículos
    await carregarClientes();
    if (aba !== "clientes") await ABAS[aba]();
  } catch (e) {
    avisar("Não foi possível falar com a API: " + e.message, true);
  }
})();
