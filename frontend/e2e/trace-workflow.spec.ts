import {test,expect} from "@playwright/test";

test("command center, merchant investigation and scenario pipeline work end to end",async({page})=>{
  await page.goto("/");
  await expect(page.getByText("MERCHANTS MONITORED")).toBeVisible({timeout:120000});
  await expect(page.getByText("TRANSACTIONS MONITORED")).toBeVisible();
  await expect(page.getByText("SYNTHETIC DATA ENVIRONMENT")).toBeVisible();

  await page.getByRole("button",{name:"Merchant Intelligence"}).click();
  await expect(page.getByText("Merchant-specific baseline comparison")).toBeVisible();
  await page.getByRole("button",{name:/Open investigation/}).click();
  await expect(page.getByText("Investigation workbench")).toBeVisible();

  await page.getByRole("button",{name:"Scenario Simulator"}).click();
  await page.getByRole("button",{name:"Run scenario through TRACE"}).click();
  await expect(page.getByText(/Scenario executed/)).toBeVisible({timeout:30000});
});
