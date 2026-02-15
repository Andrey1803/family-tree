/* Service Worker для PWA «Семейное древо» */
const CACHE_NAME = "family-tree-v1";

self.addEventListener("install", (e) => {
  self.skipWaiting();
});

self.addEventListener("activate", (e) => {
  e.waitUntil(self.clients.claim());
});
