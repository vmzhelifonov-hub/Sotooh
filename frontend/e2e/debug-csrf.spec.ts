import { test, expect } from "@playwright/test";

test("debug: csrf cookie visibility after register", async ({ page }) => {
  const random = Date.now();
  await page.goto("/register");
  await page.getByLabel(/اسم الشركة|Company name/i).fill(`Debug Org ${random}`);
  await page.getByLabel(/البريد الإلكتروني|Email/i).fill(`dbg-${random}@test.iq`);
  await page.getByLabel(/كلمة المرور|Password/i).first().fill("Strong12345!");
  const [response] = await Promise.all([
    page.waitForResponse((r) => r.url().includes("/auth/register/")),
    page.getByRole("button", { name: /إنشاء حساب|Sign up/i }).click(),
  ]);
  console.log("register status:", response.status());
  const cookies = await page.context().cookies();
  console.log("cookies:", cookies.map((c) => `${c.name}=${c.value.slice(0, 12)} httpOnly=${c.httpOnly}`));
  const docCookie = await page.evaluate(() => document.cookie);
  console.log("document.cookie:", docCookie.slice(0, 120));
  await page.waitForURL(/onboarding/, { timeout: 10000 });
  // Now try saving company step
  await page.getByLabel(/اسم الشركة|Company name/i).fill(`Debug Org ${random}`);
  const [patchResponse] = await Promise.all([
    page.waitForResponse((r) => r.url().includes("/organization/")),
    page.getByRole("button", { name: /التالي|Next/i }).click(),
  ]);
  console.log("PATCH org status:", patchResponse.status());
  console.log("PATCH body:", (await patchResponse.text()).slice(0, 200));
});
