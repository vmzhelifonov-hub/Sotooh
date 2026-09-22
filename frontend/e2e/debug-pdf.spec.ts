import { test, expect } from "@playwright/test";

test("debug3: quote detail with pdf in db shows download button", async ({ page }) => {
  const random = Date.now();
  // register + full skip onboarding
  await page.goto("/register");
  await page.getByLabel(/اسم الشركة|Company name/i).fill(`Dbg3 ${random}`);
  await page.getByLabel(/البريد الإلكتروني|Email/i).fill(`dbg3-${random}@test.iq`);
  await page.getByLabel(/كلمة المرور|Password/i).first().fill("Strong12345!");
  await page.getByRole("button", { name: /إنشاء حساب|Sign up/i }).click();
  await page.waitForURL(/onboarding/, { timeout: 15000 });
  await page.getByLabel(/اسم الشركة|Company name/i).fill(`Dbg3 Co ${random}`);
  await page.getByRole("button", { name: /التالي|Next/i }).click();
  for (let i = 0; i < 3; i++) {
    await page.getByRole("button", { name: /تخطي|Skip/i }).first().click();
    await page.waitForTimeout(400);
  }
  await page.waitForURL(/dashboard|onboarding/, { timeout: 15000 }).catch(() => undefined);

  // create customer via API from browser context (has session)
  const customer = await page.evaluate(async () => {
    const csrf = document.cookie.match(/csrftoken=([^;]+)/)?.[1];
    const r = await fetch("/api/v1/customers/", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrf ?? "" },
      body: JSON.stringify({ name: "Dbg3 Cust", phone: "+9647707777777" }),
    });
    return r.json();
  });
  console.log("customer:", customer.id);

  // create quote via UI
  await page.goto("/app/quotes/new");
  await page.getByLabel(/العميل|Customer/i).selectOption({ index: 1 });
  await page.getByPlaceholder(/الوصف|Description/i).first().fill("لوح شمسي тест");
  await page.getByLabel(/سعر الوحدة|Unit price/i).first().fill("100000");
  await page.getByRole("button", { name: /حفظ كمسودة|Save draft/i }).click();
  await page.waitForURL(/\/app\/quotes\/[a-f0-9-]+/, { timeout: 15000 });
  console.log("quote page url:", page.url());

  // generate PDF and watch state
  const [pdfResp] = await Promise.all([
    page.waitForResponse((r) => r.url().includes("/pdf/"), { timeout: 20000 }),
    page.getByRole("button", { name: /إنشاء PDF|Generate PDF/i }).click(),
  ]);
  console.log("pdf api status:", pdfResp.status());
  console.log("pdf api body:", (await pdfResp.text()).slice(0, 200));
  await page.waitForTimeout(2500);
  const genBtn = page.getByRole("button", { name: /إنشاء PDF|Generate PDF/i });
  console.log("generate still visible:", await genBtn.isVisible().catch(() => false));
  console.log("download visible:", await page.getByRole("button", { name: /تحميل PDF|Download PDF/i }).isVisible().catch(() => false));
  await page.screenshot({ path: "/app/dbg3.png", fullPage: true });
});
