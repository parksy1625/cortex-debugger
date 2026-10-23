import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
 testDir: './tests',
 timeout: 30_000,
 retries: process.env.CI ? 1 : 0,
 reporter: process.env.CI ? [['list'],['html',{open:'never'}]] : [['list']],
 use: { baseURL: 'http://127.0.0.1:5173', trace: 'retain-on-failure' },
 projects: [{name:'chromium',use:{...devices['Desktop Chrome'],...(process.env.CI?{channel:'chrome' as const}:{})}}],
 webServer: {
   command: 'npm run dev',
   url: 'http://127.0.0.1:5173',
   reuseExistingServer: !process.env.CI,
   timeout: 30_000,
 },
});
