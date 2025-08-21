// sw.js — Falowen PWA service worker (enhanced minimal)
const CACHE_NAME = "falowen-cache-v2";
const OFFLINE_URL = "/offline.html";
const PRECACHE = [
  OFFLINE_URL,
  "/static/icons/falowen-192.png",
  "/static/icons/falowen-512.png"
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(PRECACHE))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil((async () => {
    // Speed up navigations when online
    if (self.registration.navigationPreload) {
      await self.registration.navigationPreload.enable();
    }
    // Clean old caches
    const keys = await caches.keys();
    await Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)));
    await self.clients.claim();
  })());
});

// Fetch strategy:
// - Navigations: network-first (+ nav preload), fallback to cached page or offline.html
// - Same-origin static assets: cache-first with background fill
self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;

  // Handle navigations (HTML/doc requests)
  if (req.mode === "navigate") {
    event.respondWith((async () => {
      try {
        // Use preload response if available
        const preload = await event.preloadResponse;
        if (preload) return preload;

        const fresh = await fetch(req);
        // Optionally cache last good HTML for bfcache-like UX
        const cache = await caches.open(CACHE_NAME);
        cache.put(req, fresh.clone()).catch(() => {});
        return fresh;
      } catch {
        const cached = await caches.match(req);
        return cached || caches.match(OFFLINE_URL);
      }
    })());
    return;
  }

  // Only cache same-origin static assets
  const url = new URL(req.url);
  if (url.origin === self.location.origin && ["style", "script", "image", "font"].includes(req.destination)) {
    event.respondWith((async () => {
      const cached = await caches.match(req);
      if (cached) return cached;
      const res = await fetch(req);
      const clone = res.clone();
      caches.open(CACHE_NAME).then((c) => c.put(req, clone)).catch(() => {});
      return res;
    })());
  }
});

// Optional: allow immediate activation from the page
self.addEventListener("message", (e) => {
  if (e.data === "SKIP_WAITING") self.skipWaiting();
});
