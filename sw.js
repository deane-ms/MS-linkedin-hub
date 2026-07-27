// Deliberately does no caching -- this app's content (posts/ideas/analytics) changes constantly,
// and a stale cache would be worse than no offline support at all. It exists solely so browsers
// that still require a registered service worker as an installability signal see one.
self.addEventListener("install", function () {
  self.skipWaiting();
});
self.addEventListener("activate", function (event) {
  event.waitUntil(self.clients.claim());
});
