self.addEventListener('install', (e) => {
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(self.clients.claim());
});

// Skrip latar belakang untuk mendengarkan perintah dari VPS secara terus-menerus
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SYNC_DATA') {
    // Proses sinkronisasi otomatis berjalan di latar belakang sistem
    console.log('Background sync active via Cloudflare channel...');
  }
});
