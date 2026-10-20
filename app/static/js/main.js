// Comportamentos da interface. O site funciona sem JavaScript; este arquivo
// só deixa algumas ações mais práticas.

document.addEventListener("DOMContentLoaded", () => {
  ativarAvaliacao();
  ativarConfirmacoes();
  ativarFontes();
});

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
