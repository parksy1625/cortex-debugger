import { expect, test } from '@playwright/test';

test('real GPT-2 browser-to-API experiment and manifest export', async ({ page }) => {
  test.skip(process.env.CORTEX_LIVE_MODEL !== '1', 'Live model test runs only in opted-in CI');
  await page.goto('/');
  await expect(page.getByText('Local API connected')).toBeVisible();
  await expect(page.getByText('GPT-2 Small')).toBeVisible();
  await page.getByRole('button', { name: /Run experiment/ }).click();
  await expect(page.getByText('Experiment results')).toBeVisible();

  await expect(page.getByText(/103\.5%|103\.4%|103\.6%/)).toBeVisible({timeout:180000});
  await expect(page.getByRole('button', {name: /Layer 5, token 2, RMS/})).toBeVisible();

  const info = await page.request.get('/api/v1/models');
  expect(info.ok()).toBeTruthy();
  const models = await info.json();
  expect(models.models[0].loaded).toBe(true);
  expect(models.models[0].revision).toBe('607a30d783dfa663caf39e06633721c8d4cfcd7e');
  await page.getByRole('button', {name:'Prepare regression test'}).click();
  await expect(page.getByText('Contains raw prompts.')).toBeVisible();
  const dl = page.waitForEvent('download');
  await page.getByRole('button', {name:'Download regression JSON'}).click();
  const artifact = await dl;
  expect(artifact.suggestedFilename()).toMatch(/^cortex-regression-/);
});
