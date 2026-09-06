/* Kill-switch : l'app a déménagé dans src/. Ce service worker remplace
   l'ancien (même URL d'enregistrement), vide ses caches, se désinscrit,
   et recharge les pages ouvertes — qui suivront alors la redirection. */
self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", e => {
  e.waitUntil(
    caches.keys()
      .then(cles => Promise.all(cles.map(c => caches.delete(c))))
      .then(() => self.registration.unregister())
      .then(() => self.clients.matchAll({ type: "window" }))
      .then(cs => cs.forEach(c => c.navigate(c.url)))
  );
});
