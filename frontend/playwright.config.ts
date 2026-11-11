import {defineConfig,devices} from "@playwright/test";
export default defineConfig({
  testDir:"./e2e",
  fullyParallel:false,
  forbidOnly:!!process.env.CI,
  retries:process.env.CI?1:0,
  workers:process.env.CI?1:undefined,
  reporter:"list",
  use:{baseURL:"http://127.0.0.1:3000",trace:"retain-on-failure",...devices["Desktop Chrome"]},
  webServer:[
    {command:"cd ../backend && uvicorn app.main:app --host 127.0.0.1 --port 8000",url:"http://127.0.0.1:8000/health",reuseExistingServer:!process.env.CI,timeout:180000,env:{APP_ENV:"demo",DATABASE_URL:"sqlite:///./trace_e2e.db"}},
    {command:"npm run dev",url:"http://127.0.0.1:3000",reuseExistingServer:!process.env.CI,timeout:120000,env:{NEXT_PUBLIC_API_URL:"http://127.0.0.1:8000"}}
  ]
});
