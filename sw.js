// Service Worker for ThermoIAA PWA
const CACHE_NAME = 'thermoiaa-v1.0';
const urlsToCache = [
  '/',
  '/static/css/style.css',
  '/static/js/main.js'
];

// Install Service Worker
self.addEventListener('install', function(event) {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(function(cache) {
        return cache.addAll(urlsToCache);
      })
  );
});

// Fetch from cache
self.addEventListener('fetch', function(event) {
  event.respondWith(
    caches.match(event.request)
      .then(function(response) {
        return response || fetch(event.request);
      }
    )
  );
});