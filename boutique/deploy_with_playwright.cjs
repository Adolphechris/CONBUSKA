const { chromium } = require('playwright');
const { exec } = require('child_process');
const { promisify } = require('util');

const execAsync = promisify(exec);

async function deploy() {
  console.log('🚀 Déploiement automatique avec Playwright MCP...\n');
  
  try {
    // Se connecter au Chrome distant
    console.log('📱 Connexion à Chrome sur le port 9222...');
    const browser = await chromium.connectOverCDP('http://localhost:9222');
    const context = browser.contexts()[0];
    const page = context?.pages()[0] || await context.newPage();
    
    // Aller sur la page de login Firebase
    console.log('🔐 Navigation vers Firebase...\n');
    await page.goto('https://accounts.google.com/o/oauth2/auth?client_id=GMMP6CJ7xKGxqPqX2mQkKqk&redirect_uri=http://localhost&response_type=code&scope=email%20profile%20https://www.googleapis.com/auth/firebase');
    
    // Remplir le formulaire de connexion
    console.log('📧 Remplissage du formulaire...\n');
    
    // Attendre que la page soit chargée
    await page.waitForLoadState('networkidle');
    
    // Remplir l'email
    console.log('   → Saisie de l\'email...');
    await page.fill('input[type="email"]', 'adolphechristopher@gmail.com');
    await page.click('button:has-text("Suivant")');
    
    // Attendre le champ mot de passe
    await page.waitForSelector('input[type="password"]', { timeout: 10000 });
    console.log('   → Saisie du mot de passe...');
    await page.fill('input[type="password"]', 'Ekodi1990@');
    
    // Cliquer sur Suivant
    console.log('   → Connexion...\n');
    await page.click('button:has-text("Suivant")');
    
    // Attendre la redirection
    console.log('⏳ Attente de la connexion...');
    await page.waitForURL('http://localhost/**', { timeout: 30000 });
    
    console.log('✅ Connexion Firebase réussie !\n');
    
    // Attendre que le token soit sauvegardé
    await page.waitForTimeout(3000);
    
    await browser.close();
    
    // Maintenant, déployer avec Firebase CLI
    console.log('📦 Déploiement du site...\n');
    const { stdout, stderr } = await execAsync('cd /home/adolphe/CONBUSCA/boutique && npx firebase deploy --only hosting', {
      maxBuffer: 10 * 1024 * 1024,
      timeout: 120000
    });
    
    console.log(stdout);
    if (stderr) console.error(stderr);
    
    console.log('\n✅ DÉPLOIEMENT TERMINÉ !');
    console.log('🌐 Site en ligne : https://boutique.etslumiere.cd');
    
  } catch (error) {
    console.error('\n❌ Erreur:', error.message);
    console.log('\n💡 Vérifiez que :');
    console.log('   1. Chrome est bien lancé avec --remote-debugging-port=9222');
    console.log('   2. Vous êtes connecté à internet\n');
    process.exit(1);
  }
}

deploy();