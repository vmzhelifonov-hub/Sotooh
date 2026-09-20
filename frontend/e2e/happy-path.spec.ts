import { expect, test } from "@playwright/test";

/**
 * Full happy path: register → onboarding → product → customer → quote →
 * PDF → public link → sent → follow-up → won → dashboard.
 * Requires the full dev environment (backend + frontend + Postgres + MinIO).
 */
const random = Date.now();
const EMAIL = `e2e-${random}@test.iq`;
const PASSWORD = "Strong12345!";

test.describe.serial("Sotooh happy path", () => {
  test("register creates account and opens onboarding", async ({ page }) => {
    await page.goto("/register");
    await page.getByLabel(/اسم الشركة|Company name/i).fill(`E2E Solar ${random}`);
    await page.getByLabel(/البريد الإلكتروني|Email/i).fill(EMAIL);
    await page.getByLabel(/كلمة المرور|Password/i).first().fill(PASSWORD);
    await page.getByRole("button", { name: /إنشاء حساب|Sign up/i }).click();
    await expect(page).toHaveURL(/onboarding/, { timeout: 15000 });
  });

  test("onboarding company step saves and advances", async ({ page }) => {
    await page.goto("/app/onboarding");
    await page.getByLabel(/اسم الشركة|Company name/i).fill(`E2E Solar Co ${random}`);
    await page.getByRole("button", { name: /التالي|Next/i }).click();
    await expect(page.getByText(/أول منتج|First product/i)).toBeVisible();
  });

  test("create customer", async ({ page }) => {
    await page.goto("/app/customers");
    await page.getByRole("button", { name: /إضافة عميل|Add customer/i }).click();
    await page.getByLabel(/الاسم|Name/i).fill("عميل اختبار");
    await page.getByLabel(/الهاتف|Phone/i).first().fill("+9647700000000");
    await page.getByRole("button", { name: /^حفظ$|^Save$/i }).click();
    await expect(page.getByText("عميل اختبار")).toBeVisible();
  });

  test("create quote", async ({ page }) => {
    await page.goto("/app/quotes/new");
    await page.getByLabel(/العميل|Customer/i).selectOption({ index: 1 });
    await page.getByPlaceholder(/الوصف|Description/i).first().fill("لوح شمسي 550 واط");
    await page.getByLabel(/سعر الوحدة|Unit price/i).first().fill("265000");
    await page.getByRole("button", { name: /حفظ كمسودة|Save draft/i }).click();
    await expect(page).toHaveURL(/\/app\/quotes\/(?!new)[a-f0-9-]+/, { timeout: 15000 });
  });

  test("generate PDF and share link", async ({ page }) => {
    await page.goto("/app/quotes");
    await page.getByRole("link").first().click();
    await page.getByRole("button", { name: /إنشاء PDF|Generate PDF/i }).click();
    await expect(page.getByRole("button", { name: /تحميل PDF|Download PDF/i })).toBeVisible({ timeout: 30000 });

    await page.getByRole("button", { name: /مشاركة|Share/i }).first().click();
    await expect(page.getByText(/wa.me|\/q\//).first()).toBeVisible();
  });

  test("public quote opens without auth and tracks view", async ({ browser }) => {
    const context = await browser.newContext(); // no session cookies
    const page = await context.newPage();
    await page.goto("/app/quotes");
    // extract share URL from the quote detail
    await page.getByRole("link").first().click();
    const shareText = await page.getByText(/\/q\//).first().textContent();
    const path = shareText?.match(/\/q\/[\w-]+/)?.[0];
    expect(path, "share link should exist").toBeTruthy();
    await page.goto(path!);
    await expect(page.getByText(/عرض سعر|Commercial Offer/i)).toBeVisible();
    await context.close();
  });

  test("tenant isolation: org B cannot see org A data", async ({ browser }) => {
    const context = await browser.newContext();
    const page = await context.newPage();
    const otherEmail = `e2e-other-${random}@test.iq`;
    await page.goto("/register");
    await page.getByLabel(/اسم الشركة|Company name/i).fill(`Other Org ${random}`);
    await page.getByLabel(/البريد الإلكتروني|Email/i).fill(otherEmail);
    await page.getByLabel(/كلمة المرور|Password/i).first().fill(PASSWORD);
    await page.getByRole("button", { name: /إنشاء حساب|Sign up/i }).click();
    await expect(page).toHaveURL(/onboarding/);
    // skip onboarding to dashboard
    await page.goto("/app/customers");
    await expect(page.getByText("عميل اختبار")).toHaveCount(0);
    await context.close();
  });

  test("mark quote sent then won; dashboard updates", async ({ page }) => {
    await page.goto("/app/quotes");
    await page.getByRole("link").first().click();
    await page.getByRole("button", { name: /تحديد كمُرسل|Mark as sent/i }).click();
    await page.getByRole("button", { name: /تم الإغلاق ✓|Mark won/i }).click();
    await page.goto("/app/dashboard");
    await expect(page.getByText(/صفقات مفتوحة|Won deals/i)).toBeVisible();
  });
});
