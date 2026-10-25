import { expect, test } from '@playwright/test';

test('M10 first-run runtime check shows actionable local readiness', async ({page})=>{
 await page.route('**/api/v1/**',async route=>{
  const path=new URL(route.request().url()).pathname;
  let body:unknown={detail:'Not found'};
  let status=404;
  if(path.endsWith('/health')){body={status:'ok',stage:'M10'};status=200;}
  if(path.endsWith('/setup')){
   body={python:'3.11.9',python_supported:true,os:'Darwin',
    architecture:'arm64',torch_installed:true,
    transformerlens_installed:false,free_disk_gb:48.2,
    model_download_required_first_use:true};
   status=200;
  }
  if(path==='/api/v1/experiments'){body={items:[]};status=200;}
  await route.fulfill({status,contentType:'application/json',body:JSON.stringify(body)});
 });
 await page.goto('/');
 await expect(page.getByRole('region',{name:'Local runtime readiness'})).toBeVisible();
 await expect(page.getByText('Darwin · arm64 · Python 3.11.9')).toBeVisible();
 await expect(page.getByText('PyTorch installed')).toBeVisible();
 await expect(page.getByText('TransformerLens missing')).toBeVisible();
 await expect(page.getByText('Free disk 48.2 GB')).toBeVisible();
 await expect(page.getByText(/GPT-2 weights download on first use/)).toBeVisible();
 await page.getByRole('button',{name:'Check again'}).click();
 await expect(page.getByText('PyTorch installed')).toBeVisible();
});
