// Comportamentos da interface. O site funciona sem JavaScript; este arquivo
// só deixa algumas ações mais práticas. As preferências (contraste, tamanho
// da letra, checklist) ficam guardadas só no navegador do visitante (RNF10).

// Lê e grava no armazenamento do navegador sem quebrar se ele estiver bloqueado.
const preferencias = {
  ler(chave) {
    try { return localStorage.getItem(chave); } catch (erro) { return null; }
  },
  gravar(chave, valor) {
    try { localStorage.setItem(chave, valor); } catch (erro) { /* segue sem lembrar */ }
  },
};

// Roda antes de a página ser desenhada: avisa o CSS que o JavaScript está
// ativo e aplica o contraste e o tamanho da letra escolhidos antes.
(function aplicarPreferencias() {
  const raiz = document.documentElement;
  raiz.classList.add("js");
  if (preferencias.ler("altoContraste") === "ativo") raiz.classList.add("alto-contraste");
  const nivel = Number(preferencias.ler("tamanhoLetra") || 0);
  if (nivel) raiz.dataset.letra = String(nivel);
})();

document.addEventListener("DOMContentLoaded", () => {
  ativarAcessibilidade();
  ativarTopo();
  ativarMenuCelular();
  ativarBuscaTelaCheia();
  ativarAnimacoes();
  ativarVoltarAoTopo();
  mostrarData();
  ativarChecklist();
  ativarProgresso();
  focarResultadoGolpe();
  ativarFerramentasConteudo();
  ativarAvaliacao();
  ativarConfirmacoes();
  ativarFontes();
  registrarServiceWorker();
});

// Barra de acessibilidade: tamanho da letra (4 níveis) e alto contraste.
function ativarAcessibilidade() {
  const controles = document.getElementById("controles-acessibilidade");
  if (!controles) return;
  controles.hidden = false;
  const raiz = document.documentElement;

  controles.querySelectorAll("[data-fonte]").forEach((botao) => {
    botao.addEventListener("click", () => {
      const atual = Number(raiz.dataset.letra || 0);
      const passo = Number(botao.dataset.fonte);
      const novo = passo === 0 ? 0 : Math.max(-1, Math.min(2, atual + passo));
      if (novo) raiz.dataset.letra = String(novo); else delete raiz.dataset.letra;
      preferencias.gravar("tamanhoLetra", String(novo));
    });
  });

  const contraste = document.getElementById("contrast-toggle");
  const marcar = () => {
    const ativo = raiz.classList.contains("alto-contraste");
    contraste.setAttribute("aria-pressed", String(ativo));
    contraste.querySelector(".mode-icon").textContent = ativo ? "◑" : "◐";
  };
  marcar();
  contraste.addEventListener("click", () => {
    const ativo = raiz.classList.toggle("alto-contraste");
    preferencias.gravar("altoContraste", ativo ? "ativo" : "inativo");
    marcar();
  });
}

// Topo fixo: ganha sombra ao rolar e se esconde ao descer a página.
function ativarTopo() {
  const topo = document.getElementById("site-header");
  if (!topo) return;
  let ultimo = window.scrollY;

  window.addEventListener("scroll", () => {
    const atual = window.scrollY;
    const menuAberto = document.querySelector(".main-nav.menu-open");
    topo.classList.toggle("scrolled", atual > 80);
    topo.classList.toggle("header-hidden", !menuAberto && atual > ultimo && atual > 240);
    ultimo = atual;
  }, { passive: true });
}

// Menu do celular (botão com três linhas).
function ativarMenuCelular() {
  const botao = document.getElementById("menu-toggle");
  const menu = document.getElementById("main-nav");
  if (!botao || !menu) return;

  const fechar = () => {
    menu.classList.remove("menu-open");
    botao.setAttribute("aria-expanded", "false");
    botao.setAttribute("aria-label", "Abrir menu");
  };

  botao.addEventListener("click", () => {
    const aberto = menu.classList.toggle("menu-open");
    botao.setAttribute("aria-expanded", String(aberto));
    botao.setAttribute("aria-label", aberto ? "Fechar menu" : "Abrir menu");
  });
  menu.querySelectorAll("a").forEach((link) => link.addEventListener("click", fechar));
  window.addEventListener("resize", () => { if (window.innerWidth > 768) fechar(); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") fechar(); });
}

// A lupa do topo abre a busca em tela cheia, com resultados enquanto se
// digita (vindos da API /api/v1/conteudos). Sem JavaScript ela é só um link
// para a página /busca. A busca em si é feita no servidor (RF03).
function ativarBuscaTelaCheia() {
  const botao = document.getElementById("search-btn");
  const modal = document.getElementById("search-modal");
  if (!botao || !modal) return;
  const campo = modal.querySelector("#search-input");
  const lista = modal.querySelector("#search-results");
  const status = modal.querySelector("#search-status");
  const textoInicial = status.textContent;
  let espera = null;
  let controle = null;

  const abrir = () => {
    modal.hidden = false;
    document.body.style.overflow = "hidden";
    requestAnimationFrame(() => modal.classList.add("active"));
    setTimeout(() => campo.focus(), 150);
  };
  const fechar = () => {
    modal.classList.remove("active");
    document.body.style.overflow = "";
    setTimeout(() => { modal.hidden = true; }, 300);
    botao.focus();
  };

  // Monta os resultados com textContent (nunca HTML), contra XSS.
  const mostrar = (itens, total, termo) => {
    lista.replaceChildren();
    itens.forEach((item) => {
      const li = document.createElement("li");
      const a = document.createElement("a");
      a.href = item.url;
      const cat = document.createElement("span");
      cat.className = "category-label category--destaque";
      cat.textContent = item.categoria.nome;
      const titulo = document.createElement("strong");
      titulo.textContent = item.titulo;
      const resumo = document.createElement("span");
      resumo.className = "search-modal__resumo";
      resumo.textContent = item.resumo;
      a.append(cat, titulo, resumo);
      li.append(a);
      lista.append(li);
    });
    status.textContent = total
      ? `${total} resultado(s) para "${termo}".`
      : `Nada encontrado para "${termo}". Tente outra palavra.`;
  };

  const buscar = async (termo) => {
    if (controle) controle.abort();
    controle = new AbortController();
    try {
      const url = `${modal.dataset.api}?limite=6&q=${encodeURIComponent(termo)}`;
      const resposta = await fetch(url, { signal: controle.signal });
      if (!resposta.ok) throw new Error(resposta.status);
      const dados = await resposta.json();
      mostrar(dados.conteudos, dados.total, termo);
    } catch (erro) {
      if (erro.name !== "AbortError") status.textContent = "Não foi possível buscar agora. Aperte Enter.";
    }
  };

  campo.addEventListener("input", () => {
    clearTimeout(espera);
    const termo = campo.value.trim();
    if (termo.length < 2) {
      lista.replaceChildren();
      status.textContent = textoInicial;
      return;
    }
    espera = setTimeout(() => buscar(termo), 250);
  });

  botao.addEventListener("click", (e) => {
    e.preventDefault();
    abrir();
  });
  modal.querySelector("#search-close").addEventListener("click", fechar);
  modal.querySelector(".search-modal__overlay").addEventListener("click", fechar);
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !modal.hidden) fechar();
  });
}

// Os blocos aparecem suavemente quando entram na tela.
function ativarAnimacoes() {
  const elementos = document.querySelectorAll(".fade-in-up");
  if (!("IntersectionObserver" in window)) {
    elementos.forEach((el) => el.classList.add("visible"));
    return;
  }
  const observador = new IntersectionObserver((entradas) => {
    entradas.forEach((entrada, i) => {
      if (!entrada.isIntersecting) return;
      entrada.target.style.transitionDelay = `${(i % 4) * 0.1}s`;
      entrada.target.classList.add("visible");
      observador.unobserve(entrada.target);
    });
  }, { threshold: 0.1 });
  elementos.forEach((el) => observador.observe(el));
}

function ativarVoltarAoTopo() {
  const botao = document.getElementById("back-to-top");
  if (!botao) return;
  window.addEventListener("scroll", () => {
    botao.classList.toggle("visible", window.scrollY > 500);
  }, { passive: true });
  botao.addEventListener("click", () => window.scrollTo({ top: 0, behavior: "smooth" }));
}

// Data de hoje no topo (só em telas largas).
function mostrarData() {
  const el = document.getElementById("data-atual");
  if (!el) return;
  const texto = new Date().toLocaleDateString("pt-BR", {
    weekday: "long", day: "numeric", month: "long", year: "numeric",
  });
  el.textContent = texto.charAt(0).toUpperCase() + texto.slice(1);
}

// RF07: envia a avaliação sem recarregar a página.
function ativarAvaliacao() {
  const form = document.querySelector("[data-avaliacao]");
  if (!form || !window.fetch) return;

  form.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    const botao = evento.submitter;
    const dados = new FormData(form);
    if (botao && botao.name) dados.set(botao.name, botao.value);

    form.querySelectorAll("button").forEach((b) => (b.disabled = true));
    try {
      const resposta = await fetch(form.action, {
        method: "POST",
        body: dados,
        headers: { "X-Requested-With": "fetch" },
      });
      if (!resposta.ok) throw new Error(resposta.status);
      const json = await resposta.json();
      const aviso = form.nextElementSibling;
      aviso.textContent = json.mensagem;
      aviso.hidden = false;
      form.remove();
      aviso.focus?.();
    } catch (erro) {
      // Se algo falhar, envia o formulário do jeito normal.
      form.querySelectorAll("button").forEach((b) => (b.disabled = false));
      HTMLFormElement.prototype.submit.call(form);
    }
  });
}

// Pede confirmação antes de excluir.
function ativarConfirmacoes() {
  document.querySelectorAll("form[data-confirmar]").forEach((form) => {
    form.addEventListener("submit", (evento) => {
      if (!window.confirm(form.dataset.confirmar)) evento.preventDefault();
    });
  });
}

// RF11: adicionar e remover linhas de fonte oficial no formulário de conteúdo.
function ativarFontes() {
  const lista = document.getElementById("lista-fontes");
  const adicionar = document.getElementById("adicionar-fonte");
  if (!lista || !adicionar) return;

  let contador = lista.children.length;

  adicionar.addEventListener("click", () => {
    const modelo = lista.querySelector(".fonte-linha");
    const nova = modelo.cloneNode(true);
    contador += 1;
    nova.querySelectorAll("input").forEach((input) => {
      input.value = "";
      const novoId = input.id.replace(/\d+$/, contador);
      nova.querySelector(`label[for="${input.id}"]`).setAttribute("for", novoId);
      input.id = novoId;
    });
    lista.appendChild(nova);
    nova.querySelector("input").focus();
  });

  lista.addEventListener("click", (evento) => {
    const botao = evento.target.closest("[data-remover-fonte]");
    if (!botao) return;
    const linha = botao.closest(".fonte-linha");
    if (lista.children.length > 1) {
      linha.remove();
    } else {
      linha.querySelectorAll("input").forEach((input) => (input.value = ""));
    }
    adicionar.focus();
  });
}

// Aviso rápido no canto da tela (ex.: "Link copiado").
function avisar(texto) {
  const toast = document.getElementById("aviso-toast");
  if (!toast) return;
  toast.textContent = texto;
  toast.hidden = false;
  clearTimeout(avisar.espera);
  avisar.espera = setTimeout(() => { toast.hidden = true; }, 3000);
}

// Checklist de documentos: o visitante marca o que já separou. Sem conta, a
// marcação fica só neste navegador, ligada ao endereço do conteúdo. Com conta
// (data-conta), quem guarda é o servidor: veja ativarProgresso().
function ativarChecklist() {
  const lista = document.querySelector("[data-checklist]");
  if (!lista) return;
  const naConta = "conta" in lista.dataset;
  const chave = `checklist:${lista.dataset.checklist}`;
  const caixas = [...lista.querySelectorAll("input[type=checkbox]")];
  const contador = document.getElementById("checklist-contador");

  const atualizar = () => {
    const feitos = caixas.filter((c) => c.checked).length;
    if (contador) contador.textContent = `${feitos} de ${caixas.length} separados`;
    lista.classList.toggle("checklist--completo", feitos === caixas.length);
  };
  const salvar = () => {
    if (!naConta) {
      const escolhidos = caixas.map((c, n) => (c.checked ? n : -1)).filter((n) => n >= 0);
      preferencias.gravar(chave, JSON.stringify(escolhidos));
    }
    atualizar();
  };

  if (!naConta) {
    let marcados = [];
    try { marcados = JSON.parse(preferencias.ler(chave) || "[]"); } catch (erro) { marcados = []; }
    caixas.forEach((caixa, i) => { caixa.checked = marcados.includes(i); });
  }
  caixas.forEach((caixa) => caixa.addEventListener("change", salvar));

  const limpar = document.getElementById("checklist-limpar");
  if (limpar) {
    limpar.hidden = false;
    limpar.addEventListener("click", () => {
      caixas.forEach((c) => { c.checked = false; });
      // Um "change" só: atualiza o contador e, com conta, envia uma vez.
      caixas[0]?.dispatchEvent(new Event("change"));
    });
  }
  atualizar();
}

// Meu acompanhamento (só com conta): cada caixinha de documento ou de passo
// pertence ao formulário #form-progresso. A cada mudança, o andamento é
// enviado sem recarregar a página. Marcar o passo 3 marca o 1 e o 2; desmarcar
// o passo 2 desmarca os que vêm depois.
function ativarProgresso() {
  const form = document.querySelector("[data-progresso]");
  if (!form || !window.fetch) return;
  const caixas = [...document.querySelectorAll('input[form="form-progresso"]')];
  const passos = caixas.filter((c) => c.name === "passos");
  const contadorPassos = document.getElementById("passos-contador");
  const falhou = "Não deu para salvar. Recarregue a página e tente de novo.";
  // Tema ainda não salvo: depois do primeiro envio a página recarrega para
  // mostrar a caixa "Tema salvo" igual ao servidor desenha.
  const temaNovo = Boolean(document.querySelector(".acompanhamento__salvar"));
  // Cada clique envia na hora, mas um de cada vez (em fila), para o último
  // estado sempre chegar por último no servidor.
  let fila = Promise.resolve();

  const enviar = async () => {
    try {
      const resposta = await fetch(form.action, {
        method: "POST",
        body: new FormData(form),
        headers: { "X-Requested-With": "fetch" },
        keepalive: true, // termina de enviar mesmo se a pessoa sair da página
      });
      const json = await resposta.json().catch(() => ({}));
      if (!resposta.ok || !json.ok) {
        avisar(json.mensagem || falhou);
        return;
      }
      if (temaNovo) {
        window.location.reload();
        return;
      }
      if (contadorPassos) contadorPassos.textContent = `${json.passo_atual} de ${passos.length}`;
      avisar(json.mensagem);
    } catch (erro) {
      avisar(falhou);
    }
  };
  const agendar = () => { fila = fila.then(enviar); };

  passos.forEach((caixa, i) => {
    caixa.addEventListener("change", () => {
      passos.forEach((outra, j) => {
        if (caixa.checked && j < i) outra.checked = true;
        if (!caixa.checked && j > i) outra.checked = false;
      });
    });
  });
  caixas.forEach((caixa) => caixa.addEventListener("change", agendar));
}

// Verificador de golpe: depois de verificar, leva a tela (e o leitor de tela) até o resultado.
function focarResultadoGolpe() {
  const resultado = document.getElementById("resultado");
  if (!resultado) return;
  resultado.scrollIntoView({ block: "start" });
  resultado.focus({ preventScroll: true });
}

// Barra do conteúdo: imprimir e compartilhar.
function ativarFerramentasConteudo() {
  const barra = document.getElementById("ferramentas-conteudo");
  if (!barra) return;
  barra.hidden = false;

  barra.querySelector("[data-imprimir]")?.addEventListener("click", () => {
    // Abre todas as partes antes de imprimir, para nada ficar escondido.
    document.querySelectorAll("details.bloco").forEach((d) => { d.open = true; });
    window.print();
  });

  barra.querySelector("[data-compartilhar]")?.addEventListener("click", async () => {
    const dados = { title: document.title, url: window.location.href.split("#")[0] };
    if (navigator.share) {
      try { await navigator.share(dados); } catch (erro) { /* cancelado */ }
      return;
    }
    try {
      await navigator.clipboard.writeText(dados.url);
      avisar("Link copiado. É só colar no WhatsApp ou onde quiser.");
    } catch (erro) {
      avisar("Copie o endereço na barra do navegador.");
    }
  });

  // Se o endereço tiver #parte, abre essa parte do conteúdo.
  const abrirAncora = () => {
    const alvo = window.location.hash && document.getElementById(window.location.hash.slice(1));
    if (alvo && alvo.tagName === "DETAILS") alvo.open = true;
  };
  window.addEventListener("hashchange", abrirAncora);
  abrirAncora();
}

// Aplicativo (PWA): guarda as páginas visitadas para abrir sem internet.
function registrarServiceWorker() {
  if (!("serviceWorker" in navigator) || !window.isSecureContext) return;
  navigator.serviceWorker.register("/sw.js").catch(() => { /* segue sem modo offline */ });
}
