import { expect, test, type Page } from '@playwright/test';

const ID = '0123456789abcdef0123456789abcdef';
const stored = {id:ID,status:'completed',created_at:'2026-10-24T00:00:00Z',
  configuration:{device:'cpu',layer:5,token_index:2,revision:null}};
const summary={schema_version:1,kind:'cortex-redacted-summary',redacted:true,
  warning:'Aggregate results may be sensitive',
  model:{id:'openai-community/gpt2',revision:'a'.repeat(40),device:'cpu'},
  scores:{clean_margin:1,corrupted_margin:-1,patched_margin:.8,recovery:.9,identity_control_delta:0},
  patch:{layer:5,token_index:2},
  note:'This redacted summary cannot be used for exact experiment replay.'};
async function mockedHistory(page:Page){
 let deleted=false;
 await page.route('**/api/v1/**',async route=>{
  const url=new URL(route.request().url()).pathname;
  const request=route.request();
  const respond=(data:unknown, status=200)=>route.fulfill({
   status,contentType:'application/json',body:JSON.stringify(data)
  });
  if(url.endsWith('/health'))return respond({status:'ok',stage:'M7'});
  if(url==='/api/v1/experiments'&&request.method()==='GET')return respond({items:deleted?[]:[stored]});
  if(url.endsWith('/shareable'))return respond(summary);
  if(url.endsWith('/'+ID)&&request.method()==='DELETE'){
   deleted=true;return route.fulfill({status:204,body:''});
  }
  if(url.endsWith('/'+ID))return respond({...stored,result:{...summary,status:'pass'},error:null});
  return respond({detail:'not found'},404);
 });
}
test('history deletion asks confirmation and removes local record',async({page})=>{
 await mockedHistory(page);await page.goto('/');
 await page.getByRole('button',{name:'History'}).click();
 await expect(page.getByText(ID.slice(0,8))).toBeVisible();
 page.once('dialog',dialog=>dialog.accept());
 await page.getByRole('button',{name:'Delete experiment '+ID.slice(0,8)}).click();
 await expect(page.getByText('No local experiments yet.')).toBeVisible();
});
test('history deleting cancelled dialog preserves entry',async({page})=>{
 await mockedHistory(page);await page.goto('/');
 await page.getByRole('button',{name:'History'}).click();
 page.once('dialog',dialog=>dialog.dismiss());
 await page.getByRole('button',{name:'Delete experiment '+ID.slice(0,8)}).click();
 await expect(page.getByText(ID.slice(0,8))).toBeVisible();
});
