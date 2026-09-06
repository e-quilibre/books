/* Service worker de la bibliothèque.
   Stratégie : le HTML passe d'abord par le réseau (les mises à jour arrivent
   seules), le cache prend le relais hors ligne. Le reste (icônes, manifest)
   est servi depuis le cache. Les requêtes vers Google Books ne sont pas
   interceptées : elles exigent une connexion, par nature. */

const CACHE = "biblio-pwa-v1";
const FICHIERS = [
  "ma-bibliotheque.html",
  "manifest.webmanifest",
  "icone-180.png",
  "icone-192.png",
  "icone-512.png"
];

self.addEventListener("install", e => {
  e.waitUntil(
    caches.open(CACHE).then(c => c.addAll(FICHIERS)).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", e => {
  e.waitUntil(
    caches.keys()
      .then(cles => Promise.all(cles.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", e => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET" || url.origin !== location.origin) return;

  if (e.request.mode === "navigate" || url.pathname.endsWith(".html")) {
    e.respondWith(
      fetch(e.request)
        .then(rep => {
          const copie = rep.clone();
          caches.open(CACHE).then(c => c.put(e.request, copie));
          return rep;
        })
        .catch(() =>
          caches.match(e.request).then(r => r || caches.match("ma-bibliotheque.html"))
        )
    );
    return;
  }

  e.respondWith(
    caches.match(e.request).then(r => r || fetch(e.request).then(rep => {
      const copie = rep.clone();
      caches.open(CACHE).then(c => c.put(e.request, copie));
      return rep;
    }))
  );
});
