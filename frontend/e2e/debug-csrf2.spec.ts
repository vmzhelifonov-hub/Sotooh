import { test, expect } from "@playwright/test";

test("debug2: repeat happy-path test 3 exactly", async ({ page }) => {
  const random = Date.now();
  await page.goto("/register");
  await page.getByLabel(/اسم الشركة|Company name/i).fill(`Dbg2 ${random}`);
  await page.getByLabel(/البريد الإلكتروني|Email/i).fill(`dbg2-${random}@test.iq`);
  await page.getByLabel(/كلمة المرور|Password/i).first().fill("Strong12345!");
  await page.getByRole("button", { name: /إنشاء حساب|Sign up/i }).click();
  await page.waitForURL(/onboarding/, { timeout: 10000 });
  await page.getByLabel(/اسم الشركة|Company name/i).fill(`Dbg2 Co ${random}`);
  await page.getByLabel(/المدينة|City/i).fill("Baghdad");
  await page.getByLabel(/الهاتف|Phone/i).fill("+9647701234567");
  const reqHeaders: Record<string, string> = {};
  page.on("request", (r) => {
    if (r.url().includes("/organization/") && r.method() === "PATCH") {
      reqHeaders["csrf"] = (r.headers()["x-csrftoken"] ?? "MISSING").slice(0, 20);
    }
  });
  const [patchResponse] = await Promise.all([
    page.waitForResponse((r) => r.url().includes("/organization/")),
    page.getByRole("button", { name: /التالي|Next/i }).click(),
  ]);
  console.log("csrf header sent:", JSON.stringify(reqHeaders));
  console.log("PATCH status:", patchResponse.status());
  console.log("PATCH body:", (await patchResponse.text()).slice(0, 150));
  await page.waitForTimeout(2000);
  console.log("step2 visible after 2s:", await page.getByText(/أول منتج|First product/i).isVisible());
  console.log("step label:", await page.locator(".onboarding__step-label").textContent());
  await page.screenshot({ path: "/app/dbg-after-patch.png", fullPage: true });
  const html = await page.evaluate(() => document.querySelector(".onboarding")?.innerHTML.slice(0, 400));
  console.log("onboarding html:", html);
  console.log("toast count:", await page.locator(".toast").count());
  console.log("toast text:", await page.locator(".toast").first().textContent().catch(() => "none"));
});
