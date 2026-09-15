const { test, expect } = require('@playwright/test');

test('smoke: add expense, close group, suggested settlement', async ({ page }) => {
  await page.goto('http://127.0.0.1:8080');

  // ensure page loaded
  await expect(page.locator('text=CloseTab MVP')).toBeVisible();

  // add a new member Charlie to have 3 members
  await page.fill('#member-name', 'Charlie');
  await page.click('#add-member-btn');
  await expect(page.locator('.member', { hasText: 'Charlie' })).toBeVisible();

  // Add expense: Rent $3000 paid by Alice for Alice and Bob
  await page.fill('#expense-desc', 'Rent');
  await page.fill('#expense-amt', '3000');
  // pick today date
  const today = new Date().toISOString().slice(0,10);
  await page.fill('#expense-date', today);
  // switch to Selected Members and pick Alice and Bob only
  await page.click('input[name=mode][value=selected]');
  // uncheck all then check Alice and Bob
  const checks = await page.$$('#participant-list input[type=checkbox]');
  for(const c of checks) await c.evaluate(n=>n.checked=false);
  await page.check('#participant-list input[type=checkbox] >> nth=0'); // Alice
  await page.check('#participant-list input[type=checkbox] >> nth=1'); // Bob
  // set payer to Alice
  await page.selectOption('#expense-payer', { label: 'Alice' });
  await page.click('button:has-text("Add Expense")');

  // expect expense to appear
  await expect(page.locator('.expense', { hasText: 'Rent' })).toBeVisible();

  // balances should show Alice positive, Bob negative
  await expect(page.locator('#balances', { hasText: 'Alice' })).toBeVisible();
  await expect(page.locator('#balances', { hasText: 'Bob' })).toBeVisible();

  // suggested settlement should show Bob → Alice: $1500.00
  await expect(page.locator('#balances')).toContainText('Bob → Alice');

  // ensure record settlement disabled while open
  await expect(page.locator('#record-settlement-btn')).toBeDisabled();

  // close group, then record settlement
  await page.click('#close-group-btn');
  await expect(page.locator('#record-settlement-btn')).toBeEnabled();

});
