// Service worker do Guia do Cidadão Perdido (PWA).
// - Arquivos fixos (CSS, JS, fontes, imagens): usa o que está guardado e
//   atualiza em segundo plano.
// - Páginas: busca na internet primeiro; sem internet, mostra a última versão
//   guardada ou a página /offline.
// A área administrativa, a conta do cidadão, a API, os formulários (POST) e
// as páginas marcadas com "no-store" nunca são guardadas.

const VERSAO = "guia-v5";
const ESSENCIAIS = [
  "/",
  "/offline",
  "/static/css/estilo.css",
  "/static/js/main.js",
  "/static/img/icone.svg",
  "/static/fonts/source-serif-4-normal.woff2",
  "/static/fonts/inter-normal.woff2",
];

self.addEventListener("install", (evento) => {
  evento.waitUntil(caches.open(VERSAO).then((cache) => cache.addAll(ESSENCIAIS)));
  self.skipWaiting();
});

self.addEventListener("activate", (evento) => {
  evento.waitUntil(
    caches.keys().then((nomes) =>
      Promise.all(nomes.filter((n) => n !== VERSAO).map((n) => caches.delete(n)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (evento) => {
  const pedido = evento.request;
  const url = new URL(pedido.url);
  if (pedido.method !== "GET" || url.origin !== self.location.origin) return;
  if (["/admin", "/conta", "/api/"].some((p) => url.pathname.startsWith(p))) return;

  if (url.pathname.startsWith("/static/")) {
    evento.respondWith(
      caches.open(VERSAO).then(async (cache) => {
        const guardado = await cache.match(pedido);
        const daRede = fetch(pedido).then((resposta) => {
          if (resposta.ok) cache.put(pedido, resposta.clone());
          return resposta;
        }).catch(() => guardado);
        return guardado || daRede;
      })
    );
    return;
  }

  if (pedido.mode === "navigate") {
    evento.respondWith(
      fetch(pedido)
        .then((resposta) => {
          // Páginas com "no-store" (ex.: conteúdo com o andamento de quem está
          // logado) não ficam guardadas no aparelho.
          const semGuardar = (resposta.headers.get("Cache-Control") || "").includes("no-store");
          if (resposta.ok && !semGuardar) {
            const copia = resposta.clone();
            caches.open(VERSAO).then((cache) => cache.put(pedido, copia));
          }
          return resposta;
        })
        .catch(async () => (await caches.match(pedido)) || caches.match("/offline"))
    );
  }
});
