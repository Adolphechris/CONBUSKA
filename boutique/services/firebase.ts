import { initializeApp } from 'firebase/app'
import { getFirestore } from 'firebase/firestore'
import { getStorage } from 'firebase/storage'

const firebaseConfig = {
  apiKey: useRuntimeConfig().public.firebaseApiKey,
  authDomain: useRuntimeConfig().public.firebaseAuthDomain,
  projectId: useRuntimeConfig().public.firebaseProjectId,
  storageBucket: useRuntimeConfig().public.firebaseStorageBucket,
  messagingSenderId: useRuntimeConfig().public.firebaseMessagingSenderId,
  appId: useRuntimeConfig().public.firebaseAppId
}

// Initialize Firebase
const app = initializeApp(firebaseConfig)
export const db = getFirestore(app)
export const storage = getStorage(app)

export default app