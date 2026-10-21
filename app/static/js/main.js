// Comportamentos da interface. O site funciona sem JavaScript; este arquivo
// só deixa algumas ações mais práticas. O visual (alto contraste, menu,
// busca em tela cheia, animações) segue o protótipo da pasta gcddp.

// Avisa o CSS que o JavaScript está ativo (o menu do celular e as animações
// dependem disso). Roda antes de a página ser desenhada.
document.documentElement.classList.add("js");

document.addEventListener("DOMContentLoaded", () => {
  ativarAltoContraste();
  ativarTopo();
  ativarMenuCelular();
  ativarBuscaTelaCheia();
  ativarAnimacoes();
  ativarVoltarAoTopo();
  mostrarData();
  ativarAvaliacao();
  ativarConfirmacoes();
  ativarFontes();
});

// Alto contraste. A escolha fica guardada só no navegador do visitante.
function ativarAltoContraste() {
  const botao = document.getElementById("contrast-toggle");
  if (!botao) return;

  const aplicar = (ativo) => {
    document.body.classList.toggle("alto-contraste", ativo);
    botao.setAttribute("aria-pressed", String(ativo));
    botao.querySelector(".mode-icon").textContent = ativo ? "◑" : "◐";
  };

  try {
    aplicar(localStorage.getItem("altoContraste") === "ativo");
  } catch (erro) { /* navegador sem armazenamento: segue sem lembrar */ }

  botao.addEventListener("click", () => {
    const ativo = !document.body.classList.contains("alto-contraste");
    aplicar(ativo);
    try {
      localStorage.setItem("altoContraste", ativo ? "ativo" : "inativo");
    } catch (erro) { /* idem */ }
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
    topo.classList.toggle("header-hidden", !menuAberto && atual > ultimo && atual > 200);
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

// A lupa do topo abre a busca em tela cheia. Sem JavaScript ela é só um
// link para a página /busca. A busca em si é feita no servidor (RF03).
function ativarBuscaTelaCheia() {
  const botao = document.getElementById("search-btn");
  const modal = document.getElementById("search-modal");
  if (!botao || !modal) return;
  const campo = modal.querySelector("#search-input");

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
