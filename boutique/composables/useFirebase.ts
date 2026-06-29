import { initializeApp, getApps } from 'firebase/app'
import { getFirestore } from 'firebase/firestore'
import { getStorage } from 'firebase/storage'

/**
 * Hook Firebase sécurisé - ne plante pas si Firebase n'est pas configuré.
 * Retourne { app, db, storage, isConfigured }
 */
export const useFirebase = () => {
  const config = useRuntimeConfig()
  const apiKey = config.public?.firebaseApiKey

  // Vérifier que les clés Firebase sont configurées
  if (!apiKey || apiKey === 'your-api-key' || apiKey === '') {
    return { app: null, db: null, storage: null, isConfigured: false }
  }

  try {
    const firebaseConfig = {
      apiKey,
      authDomain: config.public.firebaseAuthDomain,
      projectId: config.public.firebaseProjectId,
      storageBucket: config.public.firebaseStorageBucket,
      messagingSenderId: config.public.firebaseMessagingSenderId,
      appId: config.public.firebaseAppId
    }

    // Éviter les initialisations multiples
    const app = getApps().length === 0 ? initializeApp(firebaseConfig) : getApps()[0]
    const db = getFirestore(app)
    const storage = getStorage(app)

    return { app, db, storage, isConfigured: true }
  } catch (e) {
    console.warn('[Firebase] Erreur d\'initialisation:', e)
    return { app: null, db: null, storage: null, isConfigured: false }
  }
}