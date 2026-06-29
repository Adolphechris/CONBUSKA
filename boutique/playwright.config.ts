import { defineConfig, devices } from '@playwright/test';

/**
 * Configuration Playwright pour les tests E2E de la boutique.
 *
 * Tests couverts:
 * - Navigation pages (accueil, catégories, produit)
 * - Panier (ajout, modification, suppression)
 * - Checkout et commande
 * - Confirmation
 */
export default defineConfig({
  testDir: './tests',
  testMatch: 'e2e.spec.ts',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: [
    ['html', { outputFolder: 'test-results/reports' }],
    ['list']
  ],
  timeout: 30000,
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
  },
});
