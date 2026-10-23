import { defineConfig, devices } from '@playwright/test';

/** M8: test the *extracted release ZIP*, not the Vite development server. */
export default defineConfig({
  testDir: './tests',
  timeout: 240_000,
  retries: 0,
  reporter: [['list']],
  use: {baseURL:'http://127.0.0.1:8000',trace:'retain-on-failure'},
  projects: [{
    name:'release-chromium',
    use:{...devices['Desktop Chrome'],channel:'chrome'},
  }],
});
