/**
 * End-to-End Assessment Test using Playwright
 * Tests the complete assessment flow from UI to result display
 */

const { test, expect } = require('@playwright/test');

// Test data for each social style
const TEST_SCENARIOS = [
  {
    name: 'ANALYTICAL - All strongly disagree',
    style: 'ANALYTICAL',
    assertiveness: Array(15).fill(1), // Questions 1-15: all 1s
    responsiveness: Array(15).fill(1), // Questions 16-30: all 1s
    expectedAssertScore: '1.0',
    expectedRespScore: '1.0'
  },
  {
    name: 'DRIVER - High assertiveness, low responsiveness',
    style: 'DRIVER',
    assertiveness: Array(15).fill(4), // All strongly agree
    responsiveness: Array(15).fill(1), // All strongly disagree
    expectedAssertScore: '4.0',
    expectedRespScore: '1.0'
  },
  {
    name: 'AMIABLE - Low assertiveness, high responsiveness',
    style: 'AMIABLE',
    assertiveness: Array(15).fill(1), // All strongly disagree
    responsiveness: Array(15).fill(4), // All strongly agree
    expectedAssertScore: '1.0',
    expectedRespScore: '4.0'
  },
  {
    name: 'EXPRESSIVE - All strongly agree',
    style: 'EXPRESSIVE',
    assertiveness: Array(15).fill(4), // All strongly agree
    responsiveness: Array(15).fill(4), // All strongly agree
    expectedAssertScore: '4.0',
    expectedRespScore: '4.0'
  },
  {
    name: 'Borderline EXPRESSIVE',
    style: 'EXPRESSIVE',
    assertiveness: [3,3,3,3,2,2,2,2,3,3,2,2,3,2,3], // avg = 2.53
    responsiveness: [3,3,2,2,3,3,2,2,3,3,2,2,3,2,3], // avg = 2.53
    expectedAssertScore: '2.5', // Will display as 2.5
    expectedRespScore: '2.5'
  }
];

test.describe('Social Styles Assessment E2E Tests', () => {

  TEST_SCENARIOS.forEach((scenario) => {
    test(`${scenario.name} should result in ${scenario.style}`, async ({ page }) => {
      // Navigate to assessment as guest
      await page.goto('http://localhost:5001/assessment/take/1?guest=True');

      // Wait for page to load
      await expect(page.locator('h1')).toContainText('Social Styles Assessment');

      // Fill out assertiveness questions (1-15)
      for (let i = 1; i <= 15; i++) {
        const value = scenario.assertiveness[i - 1];
        await page.click(`input[name="assertiveness_${i}"][value="${value}"]`);
      }

      // Fill out responsiveness questions (16-30)
      for (let i = 16; i <= 30; i++) {
        const value = scenario.responsiveness[i - 16];
        await page.click(`input[name="responsiveness_${i}"][value="${value}"]`);
      }

      // Submit the assessment
      await page.click('button[type="submit"]');

      // Wait for results page
      await page.waitForURL(/.*post-assessment.*/);

      // Verify the social style result is displayed (adjust selector based on your actual page)
      const resultText = await page.textContent('body');

      // Check if the expected style appears in the result
      // Note: This is a basic check - you may need to adjust based on actual page structure
      expect(resultText).toContain(scenario.style);

      console.log(`✓ Test passed: ${scenario.name} → ${scenario.style}`);
    });
  });

  test('Should display all 30 questions in Likert format', async ({ page }) => {
    await page.goto('http://localhost:5001/assessment/take/1?guest=True');

    // Check for first assertiveness question
    await expect(page.locator('.question-card').first()).toContainText('I typically take charge in group situations');

    // Count total questions
    const questionCount = await page.locator('.question-card').count();
    expect(questionCount).toBe(30);

    // Verify Likert scale options exist (1-4 for each question)
    const firstQuestion = page.locator('.question-card').first();
    for (let i = 1; i <= 4; i++) {
      await expect(firstQuestion.locator(`input[value="${i}"]`)).toBeVisible();
      await expect(firstQuestion.locator(`label[for*="_${i}"]`)).toBeVisible();
    }

    console.log('✓ All questions display correctly in Likert format');
  });

  test('Should require all questions to be answered', async ({ page }) => {
    await page.goto('http://localhost:5001/assessment/take/1?guest=True');

    // Try to submit without answering
    await page.click('button[type="submit"]');

    // Should still be on the same page (form validation prevents submit)
    await expect(page).toHaveURL(/.*take.*/);

    console.log('✓ Form validation prevents incomplete submission');
  });

  test('Boundary test: 2.5 cutoff correctly determines style', async ({ page }) => {
    // Test case: Assert 2.53 (≥2.5), Resp 2.27 (<2.5) = DRIVER
    await page.goto('http://localhost:5001/assessment/take/1?guest=True');

    // Assertiveness: [3,3,2,2,3,2,3,2,3,2,3,2,3,2,3] = avg 2.53
    const assertResponses = [3,3,2,2,3,2,3,2,3,2,3,2,3,2,3];
    for (let i = 1; i <= 15; i++) {
      await page.click(`input[name="assertiveness_${i}"][value="${assertResponses[i-1]}"]`);
    }

    // Responsiveness: [2,2,2,2,3,2,2,3,2,2,3,2,2,3,2] = avg 2.27
    const respResponses = [2,2,2,2,3,2,2,3,2,2,3,2,2,3,2];
    for (let i = 16; i <= 30; i++) {
      await page.click(`input[name="responsiveness_${i}"][value="${respResponses[i-16]}"]`);
    }

    await page.click('button[type="submit"]');
    await page.waitForURL(/.*post-assessment.*/);

    const resultText = await page.textContent('body');
    expect(resultText).toContain('DRIVER');

    console.log('✓ Boundary test passed: Correctly identified as DRIVER');
  });
});

test.describe('Assessment Scoring Display Tests', () => {

  test('Scores should display with correct scale (x/4.0)', async ({ page }) => {
    // Take a simple test
    await page.goto('http://localhost:5001/assessment/take/1?guest=True');

    // Fill with known values
    for (let i = 1; i <= 15; i++) {
      await page.click(`input[name="assertiveness_${i}"][value="3"]`);
    }
    for (let i = 16; i <= 30; i++) {
      await page.click(`input[name="responsiveness_${i}"][value="3"]`);
    }

    await page.click('button[type="submit"]');
    await page.waitForURL(/.*post-assessment.*/);

    // Check that scores are displayed (should be 3.0 for both)
    const resultText = await page.textContent('body');
    expect(resultText).toMatch(/3\.0/); // Should show score of 3.0

    console.log('✓ Scores display correctly');
  });
});

// Run configuration
test.use({
  baseURL: 'http://localhost:5001',
  screenshot: 'only-on-failure',
  video: 'retain-on-failure'
});
