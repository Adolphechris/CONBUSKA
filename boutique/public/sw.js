/**
 * Service Worker Conbuska PWA
 * Gestion du cache, mode offline, synchronisation
 */

const CACHE_NAME = 'conbuska-v1';
const STATIC_CACHE = 'conbuska-static-v1';
const DYNAMIC_CACHE = 'conbuska-dynamic-v1';

// Ressources statiques à mettre en cache
const STATIC_ASSETS = [
  '/',
  '/_nuxt/',
];

// Ressources à ne jamais mettre en cache
const NO_CACHE_PATTERNS = [
  /\/api\//,
  /\/media\//,
];

// Install event - cache des ressources statiques
self.addEventListener('install', (event) => {
  console.log('[SW] Install');
  
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then((cache) => {
        console.log('[SW] Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => {
        console.log('[SW] Static assets cached');
        return self.skipWaiting();
      })
      .catch((error) => {
        console.error('[SW] Install failed:', error);
      })
  );
});

// Activate event - nettoyage des anciens caches
self.addEventListener('activate', (event) => {
  console.log('[SW] Activate');
  
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames
            .filter((name) => {
              return name !== STATIC_CACHE && name !== DYNAMIC_CACHE;
            })
            .map((name) => {
              console.log('[SW] Deleting old cache:', name);
              return caches.delete(name);
            })
        );
      })
      .then(() => {
        console.log('[SW] Claiming clients');
        return self.clients.claim();
      })
  );
});

// Fetch event - stratégie de cache
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Ignorer les requêtes non-GET
  if (request.method !== 'GET') {
    return;
  }

  // Ignorer les patterns à ne pas cacher
  if (NO_CACHE_PATTERNS.some(pattern => pattern.test(url.pathname))) {
    return;
  }

  // Stratégie pour les assets statiques (images, CSS, JS)
  if (request.destination === 'image' || 
      request.destination === 'style' || 
      request.destination === 'script') {
    event.respondWith(cacheFirst(request));
    return;
  }

  // Stratégie pour les pages HTML - Network First
  if (request.mode === 'navigate') {
    event.respondWith(networkFirst(request));
    return;
  }

  // Stratégie par défaut - Stale While Revalidate
  event.respondWith(staleWhileRevalidate(request));
});

// Stratégie: Cache First
async function cacheFirst(request) {
  try {
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      const cache = await caches.open(DYNAMIC_CACHE);
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  } catch (error) {
    console.error('[SW] Cache first failed:', error);
    return new Response('Offline', { status: 503 });
  }
}

// Stratégie: Network First
async function networkFirst(request) {
  try {
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      const cache = await caches.open(DYNAMIC_CACHE);
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  } catch (error) {
    console.log('[SW] Network failed, trying cache');
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // Fallback page pour offline
    return caches.match('/offline.html') || new Response('Offline', {
      status: 503,
      headers: { 'Content-Type': 'text/html' }
    });
  }
}

// Stratégie: Stale While Revalidate
async function staleWhileRevalidate(request) {
  try {
    const cachedResponse = await caches.match(request);
    
    const fetchPromise = fetch(request)
      .then((networkResponse) => {
        if (networkResponse.ok) {
          const cache = caches.open(DYNAMIC_CACHE);
          cache.then(c => c.put(request, networkResponse.clone()));
        }
        return networkResponse;
      })
      .catch((error) => {
        console.error('[SW] Fetch failed:', error);
        return cachedResponse || new Response('Offline', { status: 503 });
      });
    
    return cachedResponse || await fetchPromise;
  } catch (error) {
    console.error('[SW] Stale while revalidate failed:', error);
    return new Response('Offline', { status: 503 });
  }
}

// Background Sync pour les actions hors-ligne
self.addEventListener('sync', (event) => {
  console.log('[SW] Background sync:', event.tag);
  
  if (event.tag === 'sync-actions') {
    event.waitUntil(syncOfflineActions());
  }
});

// Synchroniser les actions hors-ligne
async function syncOfflineActions() {
  try {
    // Récupérer les actions en attente depuis IndexedDB
    const actions = await getOfflineActions();
    
    for (const action of actions) {
      try {
        await fetch(action.url, {
          method: action.method,
          headers: action.headers,
          body: JSON.stringify(action.body),
        });
        
        // Supprimer l'action synchronisée
        await removeOfflineAction(action.id);
      } catch (error) {
        console.error('[SW] Sync action failed:', action, error);
      }
    }
  } catch (error) {
    console.error('[SW] Sync failed:', error);
  }
}

// IndexedDB pour stocker les actions hors-ligne
function openDatabase() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('ConbuskaOfflineDB', 1);
    
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
    
    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      if (!db.objectStoreNames.contains('actions')) {
        db.createObjectStore('actions', { keyPath: 'id', autoIncrement: true });
      }
    };
  });
}

async function getOfflineActions() {
  const db = await openDatabase();
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(['actions'], 'readonly');
    const store = transaction.objectStore('actions');
    const request = store.getAll();
    
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

async function removeOfflineAction(id) {
  const db = await openDatabase();
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(['actions'], 'readwrite');
    const store = transaction.objectStore('actions');
    const request = store.delete(id);
    
    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error);
  });
}

// Push notifications (pour futures fonctionnalités)
self.addEventListener('push', (event) => {
  if (!event.data) {
    return;
  }

  const data = event.data.json();
  const options = {
    body: data.body || 'Nouvelle notification',
    icon: '/icons/icon-192x192.png',
    badge: '/icons/badge-72x72.png',
    vibrate: [100, 50, 100],
    data: data.data || {},
    actions: data.actions || [],
  };

  event.waitUntil(
    self.registration.showNotification(data.title || 'Conbuska', options)
  );
});

// Gestion des clics sur les notifications
self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  if (event.action) {
    // Action spécifique
    event.waitUntil(
      clients.openWindow(event.action)
    );
  } else {
    // Ouvrir l'application
    event.waitUntil(
      clients.matchAll({ type: 'window' })
        .then((clientList) => {
          // Si une fenêtre est déjà ouverte, la focus
          for (const client of clientList) {
            if (client.url === '/' && 'focus' in client) {
              return client.focus();
            }
          }
          // Sinon ouvrir une nouvelle fenêtre
          if (clients.openWindow) {
            return clients.openWindow('/');
          }
        })
    );
  }
});

// Message handling depuis le client
self.addEventListener('message', (event) => {
  const { type, payload } = event.data;
  
  switch (type) {
    case 'SKIP_WAITING':
      self.skipWaiting();
      break;
      
    case 'GET_VERSION':
      event.ports[0].postMessage({ version: CACHE_NAME });
      break;
      
    case 'CACHE_URLS':
      event.waitUntil(
        caches.open(DYNAMIC_CACHE)
          .then((cache) => cache.addAll(payload.urls))
      );
      break;
      
    case 'CLEAR_CACHE':
      event.waitUntil(
        caches.delete(payload.cacheName || DYNAMIC_CACHE)
      );
      break;
      
    default:
      console.log('[SW] Unknown message type:', type);
  }
});

console.log('[SW] Service Worker loaded');