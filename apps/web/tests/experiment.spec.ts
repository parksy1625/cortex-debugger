import { expect, test, type Page } from '@playwright/test';
import { readFile } from 'node:fs/promises';

const ID='0123456789abcdef0123456789abcdef';
const SHA='607a30d783dfa663caf39e06633721c8d4cfcd7e';
const CLEAN_SHA='e6d806101d9d984fe5eff71ca254aad3072386fd0b202d571a600d204d6489ba';
const CORRUPTED_SHA='f0309b487361809e69f54fe863a4d1f096b6f2f3df22046e496f4448ddaa53ca';
const delta=Array.from({length:12},(_,layer)=>Array.from({length:4},(_,token)=>layer===5&&token===2?2.5:.2));
const evidence=(cleanHash=CLEAN_SHA)=>({
 schema_version:1,status:'pass',
 model:{id:'openai-community/gpt2',revision:SHA,device:'cpu'},
 input:{clean_sha256:cleanHash,corrupted_sha256:CORRUPTED_SHA},
 patch:{site:'blocks.5.hook_out',layer:5,token_index:2},
 scores:{clean:.8115386963,corrupted:-.3125610352,patched:.850479126,recovery:1.0346414367},
 control:{max_abs_logit_delta:0,tolerance:.0001},
 activation_rms_delta:delta,runtime_seconds:.338
});
async function mockApi(page:Page, result=evidence()){
 await page.route('**/api/v1/**',async route=>{
  const url=new URL(route.request().url());
  const path=url.pathname;
  const json=(data:unknown,status=200)=>route.fulfill({status,contentType:'application/json',body:JSON.stringify(data)});
  if(path.endsWith('/health'))return json({status:'ok',stage:'M4',version:'0.5.0.dev0'});
  if(path.endsWith('/models'))return json({models:[]});
  if(path==='/api/v1/experiments' && route.request().method()==='POST')
   return json({id:ID,status:'queued',created_at:'2026-10-24T00:00:00Z'},202);
  if(path==='/api/v1/experiments' && route.request().method()==='GET')
   return json({items:[{id:ID,status:'completed',created_at:'2026-10-24T00:00:00Z',configuration:{device:'cpu',layer:5,token_index:2,revision:SHA}}]});
  if(path===`/api/v1/experiments/${ID}`)
   return json({id:ID,status:'completed',created_at:'2026-10-24T00:00:00Z',configuration:{device:'cpu',layer:5,token_index:2,revision:SHA},result,error:null});
  return json({detail:'Unexpected test API path '+path},404);
 });
}
test('experiment to hash-verified regression manifest with reviewed thresholds',async({page})=>{
 await mockApi(page);
 await page.goto('/');
 await expect(page.getByText('Local API connected')).toBeVisible();
 await page.getByRole('button',{name:/Run experiment/}).click();
 await expect(page.getByText('103.5%')).toBeVisible({timeout:10000});
 await expect(page.getByRole('button',{name:/Layer 5, token 2, RMS/})).toBeVisible();
 await page.getByRole('button',{name:'Prepare regression test'}).click();
 await expect(page.getByText('Contains raw prompts.')).toBeVisible();
 await expect(page.getByLabel('MIN RECOVERY')).toBeVisible();
 await page.getByLabel('MIN RECOVERY').fill('0.7');
 const downloading=page.waitForEvent('download');
 await page.getByRole('button',{name:'Download regression JSON'}).click();
 const file=await downloading;
 expect(file.suggestedFilename()).toMatch(/^cortex-regression-/);
 const manifest=JSON.parse(await readFile(await file.path(),'utf8'));
 expect(manifest.schema_version).toBe(1);
 expect(manifest.model.revision).toBe(SHA);
 expect(manifest.experiment.clean).toBe('The dog runs');
 expect(manifest.experiment.token_index).toBe(2);
 expect(manifest.assertions.recovery_min).toBe(.7);
});

test('wrong evidence fingerprint blocks raw-prompt manifest',async({page})=>{
 await mockApi(page,evidence('a'.repeat(64)));
 await page.goto('/');
 await page.getByRole('button',{name:/Run experiment/}).click();
 await expect(page.getByText('103.5%')).toBeVisible({timeout:10000});
 await page.getByRole('button',{name:'Prepare regression test'}).click();
 await expect(page.getByRole('alert')).toContainText('Prompt hashes do not match');
 await expect(page.getByRole('button',{name:'Download regression JSON'})).toHaveCount(0);
});

test('historical experiments never reconstruct raw prompts',async({page})=>{
 await mockApi(page);
 await page.goto('/');
 await page.getByRole('button',{name:'History'}).click();
 await expect(page.getByText(ID.slice(0,8))).toBeVisible();
 await page.getByRole('button',{name:new RegExp('^'+ID.slice(0,8))}).click();
 await expect(page.getByText('Saved history alone cannot reconstruct prompts.')).toBeVisible();
 await expect(page.getByRole('button',{name:'Prepare regression test'})).toHaveCount(0);
});
