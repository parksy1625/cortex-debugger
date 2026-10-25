import { expect, test } from '@playwright/test';

test('M11 one-time pairing unlocks the API without persisting code',async({page})=>{
 let authorized=false;
 await page.route('**/api/v1/**',async route=>{
  const path=new URL(route.request().url()).pathname;
  const method=route.request().method();
  const json=(data:unknown,status=200)=>route.fulfill({
   status,contentType:'application/json',body:JSON.stringify(data)
  });
  if(path==='/api/v1/health')return json({status:'ok',stage:'M11'});
  if(path==='/api/v1/setup')return json({
    python:'3.11.9',python_supported:true,os:'Linux',architecture:'x86_64',
    torch_installed:true,transformerlens_installed:true,free_disk_gb:45,
    model_download_required_first_use:true
  });
  if(path==='/api/v1/auth/status')return json({enabled:true,authenticated:false});
  if(path==='/api/v1/auth/pair'&&method==='POST'){
   const post=route.request().postDataJSON();
   if(post.code==='123456789')return json({token:'m11-session-example-token'});
   return json({detail:'Invalid code'},403);
  }
  if(path==='/api/v1/experiments'){
   authorized=route.request().headers()['authorization']==='Bearer m11-session-example-token';
   return authorized?json({items:[]}):json({detail:'Pairing required'},401);
  }
  return json({detail:'Not found'},404);
 });
 await page.goto('/');
 await expect(page.getByRole('heading',{name:'Connect to your local Cortex'})).toBeVisible();
 await expect(page.getByRole('button',{name:'Unlock local studio'})).toBeDisabled();
 await page.getByRole('textbox',{name:'Pairing code'}).fill('123456789');
 await page.getByRole('button',{name:'Unlock local studio'}).click();
 await expect(page.getByRole('heading',{name:'Experiment studio'})).toBeVisible();
 await expect(page.getByRole('region',{name:'Local runtime readiness'})).toBeVisible();
 expect(authorized).toBe(true);
 const saved=await page.evaluate(()=>sessionStorage.getItem('cortex-pair-token'));
 expect(saved).toBe('m11-session-example-token');
 expect(await page.evaluate(()=>localStorage.length)).toBe(0);
});
