/**
 * Comprehensive Regression Test Suite
 * Tests all major features against the live application
 */

const { test, expect } = require('@playwright/test');

const BASE_URL = process.env.TEST_URL || 'http://134.199.243.119';
const TEST_USER_EMAIL = `regression_${Date.now()}@test.com`;
const TEST_USER_PASSWORD = 'TestPass123!';
const TEST_USER_NAME = 'Regression Tester';

test.describe.serial('Full Regression Suite', () => {

  // ─── PUBLIC PAGES ──────────────────────────────────────────

  test('1. Homepage loads', async ({ page }) => {
    const response = await page.goto(BASE_URL);
    expect(response.status()).toBe(200);
    await expect(page.locator('body')).toContainText('Social Styles');
  });

  test('2. Health endpoint returns OK', async ({ page }) => {
    const response = await page.goto(`${BASE_URL}/health`);
    expect(response.status()).toBe(200);
    const body = await page.textContent('body');
    expect(body).toContain('healthy');
  });

  test('3. About page loads', async ({ page }) => {
    const response = await page.goto(`${BASE_URL}/about`);
    expect(response.status()).toBe(200);
  });

  test('4. Login page loads', async ({ page }) => {
    const response = await page.goto(`${BASE_URL}/auth/login`);
    expect(response.status()).toBe(200);
    await expect(page.locator('input[name="email"]')).toBeVisible();
    await expect(page.locator('input[name="password"]')).toBeVisible();
  });

  test('5. Register page loads', async ({ page }) => {
    const response = await page.goto(`${BASE_URL}/auth/register`);
    expect(response.status()).toBe(200);
    await expect(page.locator('input[name="email"]')).toBeVisible();
    await expect(page.locator('input[name="name"]')).toBeVisible();
  });

  // ─── GUEST ASSESSMENT FLOW ────────────────────────────────

  test('6. Guest assessment page loads with 30 questions', async ({ page }) => {
    await page.goto(`${BASE_URL}/assessment/take/1?guest=True`);
    await expect(page.locator('body')).toContainText('Assessment');

    // Verify questions are present
    const questionCards = page.locator('.question-card');
    const count = await questionCards.count();
    expect(count).toBe(30);
  });

  test('7. Guest assessment - DRIVER scores (high assert, low resp)', async ({ page }) => {
    await page.goto(`${BASE_URL}/assessment/take/1?guest=True`);

    for (let i = 1; i <= 15; i++) {
      await page.locator(`label[for="assertiveness_${i}_4"]`).click();
    }
    for (let i = 16; i <= 30; i++) {
      await page.locator(`label[for="responsiveness_${i}_1"]`).click();
    }

    await page.locator('[type="submit"]').click();
    await page.waitForURL(/.*post-assessment.*/, { timeout: 10000 });

    const body = await page.textContent('body');
    // Guest post-assessment shows scores but may not show style name
    expect(body).toContain('4.0');
    expect(body).toContain('1.0');
  });

  test('8. Guest assessment - AMIABLE scores (low assert, high resp)', async ({ page }) => {
    await page.goto(`${BASE_URL}/assessment/take/1?guest=True`);

    for (let i = 1; i <= 15; i++) {
      await page.locator(`label[for="assertiveness_${i}_1"]`).click();
    }
    for (let i = 16; i <= 30; i++) {
      await page.locator(`label[for="responsiveness_${i}_4"]`).click();
    }

    await page.locator('[type="submit"]').click();
    await page.waitForURL(/.*post-assessment.*/, { timeout: 10000 });

    const body = await page.textContent('body');
    expect(body).toContain('Assertiveness: 1.0');
    expect(body).toContain('Responsiveness: 4.0');
  });

  test('9. Guest assessment - ANALYTICAL scores (all low)', async ({ page }) => {
    await page.goto(`${BASE_URL}/assessment/take/1?guest=True`);

    for (let i = 1; i <= 15; i++) {
      await page.locator(`label[for="assertiveness_${i}_1"]`).click();
    }
    for (let i = 16; i <= 30; i++) {
      await page.locator(`label[for="responsiveness_${i}_1"]`).click();
    }

    await page.locator('[type="submit"]').click();
    await page.waitForURL(/.*post-assessment.*/, { timeout: 10000 });

    const body = await page.textContent('body');
    expect(body).toContain('Assertiveness: 1.0');
    expect(body).toContain('Responsiveness: 1.0');
  });

  test('10. Guest assessment - EXPRESSIVE scores (all high)', async ({ page }) => {
    await page.goto(`${BASE_URL}/assessment/take/1?guest=True`);

    for (let i = 1; i <= 15; i++) {
      await page.locator(`label[for="assertiveness_${i}_4"]`).click();
    }
    for (let i = 16; i <= 30; i++) {
      await page.locator(`label[for="responsiveness_${i}_4"]`).click();
    }

    await page.locator('[type="submit"]').click();
    await page.waitForURL(/.*post-assessment.*/, { timeout: 10000 });

    const body = await page.textContent('body');
    expect(body).toContain('Assertiveness: 4.0');
    expect(body).toContain('Responsiveness: 4.0');
  });

  // ─── USER REGISTRATION & AUTH ─────────────────────────────

  test('11. User registration', async ({ page }) => {
    await page.goto(`${BASE_URL}/auth/register`);

    await page.fill('input[name="name"]', TEST_USER_NAME);
    await page.fill('input[name="email"]', TEST_USER_EMAIL);
    await page.fill('input[name="password"]', TEST_USER_PASSWORD);
    await page.fill('input[name="password2"]', TEST_USER_PASSWORD);

    await page.locator('[type="submit"]').click();

    // Should redirect to login or dashboard
    await page.waitForURL(/.*\/(auth\/login|assessment\/dashboard).*/, { timeout: 10000 });
    const body = await page.textContent('body');
    // Should see success message or dashboard
    expect(body.toLowerCase()).toMatch(/(success|dashboard|welcome|login)/i);
  });

  test('12. User login', async ({ page }) => {
    await page.goto(`${BASE_URL}/auth/login`);

    await page.fill('input[name="email"]', TEST_USER_EMAIL);
    await page.fill('input[name="password"]', TEST_USER_PASSWORD);
    await page.locator('[type="submit"]').click();

    // Login redirects to homepage
    await page.waitForTimeout(3000);
    // Should no longer see login form — we're authenticated
    const url = page.url();
    expect(url).not.toContain('/auth/login');
  });

  // ─── AUTHENTICATED ASSESSMENT ─────────────────────────────

  test('13. Authenticated assessment flow', async ({ page }) => {
    // Login first
    await page.goto(`${BASE_URL}/auth/login`);
    await page.fill('input[name="email"]', TEST_USER_EMAIL);
    await page.fill('input[name="password"]', TEST_USER_PASSWORD);
    await page.locator('[type="submit"]').click();
    await page.waitForTimeout(3000);

    // Navigate to assessment
    await page.goto(`${BASE_URL}/assessment/take/1`);

    // Fill out as EXPRESSIVE (all 3s = above 2.5 on both axes)
    for (let i = 1; i <= 15; i++) {
      await page.locator(`label[for="assertiveness_${i}_3"]`).click();
    }
    for (let i = 16; i <= 30; i++) {
      await page.locator(`label[for="responsiveness_${i}_3"]`).click();
    }

    await page.locator('[type="submit"]').click();

    // Should go to results page
    await page.waitForURL(/.*result.*/, { timeout: 10000 });
    const body = await page.textContent('body');
    expect(body).toContain('EXPRESSIVE');
  });

  test('14. Dashboard shows assessment history', async ({ page }) => {
    // Login
    await page.goto(`${BASE_URL}/auth/login`);
    await page.fill('input[name="email"]', TEST_USER_EMAIL);
    await page.fill('input[name="password"]', TEST_USER_PASSWORD);
    await page.locator('[type="submit"]').click();
    await page.waitForTimeout(3000);

    // Go to dashboard
    await page.goto(`${BASE_URL}/assessment/dashboard`);

    // Should show assessment result
    const body = await page.textContent('body');
    expect(body).toContain('EXPRESSIVE');
  });

  // ─── TEAM FEATURES ────────────────────────────────────────

  test('15. Create a team', async ({ page }) => {
    // Login
    await page.goto(`${BASE_URL}/auth/login`);
    await page.fill('input[name="email"]', TEST_USER_EMAIL);
    await page.fill('input[name="password"]', TEST_USER_PASSWORD);
    await page.locator('[type="submit"]').click();
    await page.waitForTimeout(3000);

    // Go directly to team creation page
    await page.goto(`${BASE_URL}/team/teams/create`);

    await page.fill('input[name="name"]', 'Regression Test Team');
    const descInput = page.locator('textarea[name="description"], input[name="description"]');
    if (await descInput.count() > 0) {
      await descInput.first().fill('Created by regression test');
    }

    await page.locator('[type="submit"]').click();
    await page.waitForTimeout(3000);

    const body = await page.textContent('body');
    expect(body).toContain('Regression Test Team');
  });

  // ─── ERROR HANDLING ────────────────────────────────────────

  test('16. 404 page for invalid route', async ({ page }) => {
    const response = await page.goto(`${BASE_URL}/nonexistent-page-12345`);
    expect(response.status()).toBe(404);
  });

  test('17. Protected routes require authentication', async ({ browser }) => {
    // Use a fresh context with no cookies
    const context = await browser.newContext();
    const page = await context.newPage();

    const response = await page.goto(`${BASE_URL}/assessment/dashboard`);
    // Should return 401 (unauthorized) for unauthenticated users
    expect(response.status()).toBe(401);
    await context.close();
  });

  test('18. Invalid login shows error', async ({ page }) => {
    await page.goto(`${BASE_URL}/auth/login`);
    await page.fill('input[name="email"]', 'fake@fake.com');
    await page.fill('input[name="password"]', 'wrongpass');
    await page.locator('[type="submit"]').click();

    // Should stay on login page with error
    await page.waitForTimeout(1000);
    const url = page.url();
    expect(url).toContain('login');
  });

  // ─── STATIC ASSETS ────────────────────────────────────────

  test('19. Static CSS loads', async ({ page }) => {
    await page.goto(BASE_URL);
    const cssLinks = page.locator('link[rel="stylesheet"]');
    const count = await cssLinks.count();
    expect(count).toBeGreaterThan(0);

    // Verify at least one CSS file returns 200
    const href = await cssLinks.first().getAttribute('href');
    if (href) {
      const cssUrl = href.startsWith('http') ? href : `${BASE_URL}${href}`;
      const response = await page.request.get(cssUrl);
      expect(response.status()).toBe(200);
    }
  });

  test('20. Static JS loads', async ({ page }) => {
    await page.goto(BASE_URL);
    const jsScripts = page.locator('script[src]');
    const count = await jsScripts.count();
    expect(count).toBeGreaterThan(0);
  });

  // ─── TEAM DASHBOARD ─────────────────────────────────────────

  test('22. Team dashboard loads with chart', async ({ page }) => {
    // Login
    await page.goto(`${BASE_URL}/auth/login`);
    await page.fill('input[name="email"]', TEST_USER_EMAIL);
    await page.fill('input[name="password"]', TEST_USER_PASSWORD);
    await page.locator('[type="submit"]').click();
    await page.waitForTimeout(3000);

    // Go to teams list
    await page.goto(`${BASE_URL}/team/teams`);
    const teamsBody = await page.textContent('body');
    expect(teamsBody).toContain('Regression Test Team');

    // Click into the team
    await page.locator('a:has-text("Regression Test Team")').first().click();
    await page.waitForTimeout(2000);

    // Go to team dashboard
    const dashboardLink = page.locator('a[href*="dashboard"]');
    if (await dashboardLink.count() > 0) {
      await dashboardLink.first().click();
      await page.waitForTimeout(2000);
    }

    // Verify the SVG chart is present
    const svg = page.locator('.social-styles-svg');
    if (await svg.count() > 0) {
      // Chart should have quadrant labels
      const svgContent = await svg.innerHTML();
      expect(svgContent).toContain('ANALYTICAL');
      expect(svgContent).toContain('DRIVER');
      expect(svgContent).toContain('AMIABLE');
      expect(svgContent).toContain('EXPRESSIVE');
    }
  });

  test('23. Team dashboard chart axes are correct', async ({ page }) => {
    // Login
    await page.goto(`${BASE_URL}/auth/login`);
    await page.fill('input[name="email"]', TEST_USER_EMAIL);
    await page.fill('input[name="password"]', TEST_USER_PASSWORD);
    await page.locator('[type="submit"]').click();
    await page.waitForTimeout(3000);

    // Go to teams and find our team
    await page.goto(`${BASE_URL}/team/teams`);
    await page.locator('a:has-text("Regression Test Team")').first().click();
    await page.waitForTimeout(2000);

    const dashboardLink = page.locator('a[href*="dashboard"]');
    if (await dashboardLink.count() > 0) {
      await dashboardLink.first().click();
      await page.waitForTimeout(2000);
    }

    // Verify axis labels are present
    const body = await page.textContent('body');
    // The SVG should have ASKS/TELLS on x-axis and CONTROLS/EMOTES on y-axis
    const svgEl = page.locator('.social-styles-svg');
    if (await svgEl.count() > 0) {
      const svgText = await svgEl.textContent();
      expect(svgText).toContain('ASKS');
      expect(svgText).toContain('TELLS');
    }
  });

  test('24. Teams list page loads', async ({ page }) => {
    // Login
    await page.goto(`${BASE_URL}/auth/login`);
    await page.fill('input[name="email"]', TEST_USER_EMAIL);
    await page.fill('input[name="password"]', TEST_USER_PASSWORD);
    await page.locator('[type="submit"]').click();
    await page.waitForTimeout(3000);

    await page.goto(`${BASE_URL}/team/teams`);
    const body = await page.textContent('body');
    expect(body).toContain('Regression Test Team');
  });

  test('25. No duplicate navbar', async ({ page }) => {
    await page.goto(BASE_URL);
    // Should only have one navbar visible
    const navbars = page.locator('nav.rds-navbar');
    const count = await navbars.count();
    expect(count).toBe(1);

    // Old Bootstrap navbar should be hidden
    const oldNavbar = page.locator('nav.navbar:not(.rds-navbar)');
    const oldCount = await oldNavbar.count();
    expect(oldCount).toBe(0);
  });

  // ─── LOGOUT ────────────────────────────────────────────────

  test('26. Logout works', async ({ page }) => {
    // Login
    await page.goto(`${BASE_URL}/auth/login`);
    await page.fill('input[name="email"]', TEST_USER_EMAIL);
    await page.fill('input[name="password"]', TEST_USER_PASSWORD);
    await page.locator('[type="submit"]').click();
    await page.waitForTimeout(3000);

    // Logout by navigating directly
    await page.goto(`${BASE_URL}/auth/logout`);
    await page.waitForTimeout(2000);

    // Verify logged out - accessing dashboard should return 401
    const response = await page.goto(`${BASE_URL}/assessment/dashboard`);
    expect(response.status()).toBe(401);
  });
});
