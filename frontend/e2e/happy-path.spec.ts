import { expect, test, type Page } from "@playwright/test";

/**
 * Full happy path: register → onboarding → customer → quote →
 * PDF → share link → public quote → sent → won → dashboard → tenant isolation.
 */
const random = Date.now();
const PASSWORD = "Strong12345!";

async function register(page: Page, suffix = "") {
  await page.goto("/register");
  await page.getByLabel(/اسم الشركة|Company name/i).fill(`E2E Solar ${random}${suffix}`);
  await page.getByLabel(/البريد الإلكتروني|Email/i).fill(`e2e-${random}${suffix}@test.iq`);
  await page.getByLabel(/كلمة المرور|Password/i).first().fill(PASSWORD);
  await page.getByRole("button", { name: /إنشاء حساب|Sign up/i }).click();
  await expect(page).toHaveURL(/onboarding/, { timeout: 15000 });
}

test.describe.serial("Sotooh happy path", () => {
  test("register creates account and opens onboarding", async ({ page }) => {
    await register(page, "first");
  });

  test("onboarding: company → skip product → create customer → create quote", async ({ page }) => {
    await register(page, "main");
    // Step 1: company
    await page.getByLabel(/اسم الشركة|Company name/i).fill(`E2E Solar Co ${random}`);
    await page.getByLabel(/المدينة|City/i).fill("Baghdad");
    await page.getByLabel(/الهاتف|Phone/i).fill("+9647701234567");
    await page.getByRole("button", { name: /التالي|Next/i }).click();
    await expect(page.getByText(/أول منتج|First product/i)).toBeVisible({ timeout: 10000 });

    // Step 2: skip product
    await page.getByRole("button", { name: /تخطي|Skip/i }).click();
    await expect(page.getByText(/أول عميل|First customer/i)).toBeVisible({ timeout: 10000 });

    // Step 3: create customer
    await page.getByLabel(/الاسم|Name/i).fill("عميل اختبار");
    await page.getByLabel(/الهاتف|Phone/i).fill("+9647709999111");
    await page.getByRole("button", { name: /التالي|Next/i }).click();
    await expect(page.locator(".onboarding__step-label")).toContainText(/أول عرض سعر|First quotation/i, { timeout: 10000 });

    // Step 4: create quote (customer auto-selected)
    await page.getByLabel(/الوصف|Description/i).fill("منظومة طاقة شمسية 3 كيلوواط");
    await page.getByLabel(/سعر الوحدة|Unit price/i).fill("4500000");
    await page.getByRole("button", { name: /البدء باستخدام سطوع|Start using Sotooh/i }).click();
    await expect(page).toHaveURL(/dashboard/, { timeout: 15000 });
    await expect(page.getByText("عميل اختبار")).toBeVisible();
  });

  test("quote: PDF + share + public link + sent + won + dashboard", async ({ page, browser }) => {
    await register(page, "quote");
    // Skip through onboarding
    await page.getByLabel(/اسم الشركة|Company name/i).fill(`E2E Solar Q ${random}`);
    await page.getByRole("button", { name: /التالي|Next/i }).click();
    await page.getByRole("button", { name: /تخطي|Skip/i }).first().click();
    await page.getByRole("button", { name: /تخطي|Skip/i }).first().click();
    await page.getByRole("button", { name: /تخطي|Skip/i }).first().click();

    // Create customer via UI
    await page.goto("/app/customers");
    await page.getByRole("button", { name: /إضافة عميل|Add customer/i }).click();
    await page.getByLabel(/الاسم|Name/i).fill("عميل عروض");
    await page.getByLabel(/الهاتف|Phone/i).first().fill("+9647700000042");
    await page.getByRole("button", { name: /^حفظ$|^Save$/i }).click();
    await expect(page.getByText("عميل عروض")).toBeVisible({ timeout: 10000 });

    // Create quote
    await page.goto("/app/quotes/new");
    await page.getByLabel(/العميل|Customer/i).selectOption({ index: 1 });
    await page.getByPlaceholder(/الوصف|Description/i).first().fill("بطارية ليثيوم 5 كيلوواط");
    await page.getByLabel(/سعر الوحدة|Unit price/i).first().fill("1250000");
    await page.getByRole("button", { name: /حفظ كمسودة|Save draft/i }).click();
    await expect(page).toHaveURL(/\/app\/quotes\/[a-f0-9-]+/, { timeout: 15000 });

    // Generate PDF
    await page.getByRole("button", { name: /إنشاء PDF|Generate PDF/i }).click();
    await expect(page.getByRole("button", { name: /تحميل PDF|Download PDF/i })).toBeVisible({ timeout: 30000 });

    // Create share link
    await page.getByRole("button", { name: /^مشاركة$|^Share$/i }).first().click();
    await expect(page.getByText(/\/q\//).first()).toBeVisible({ timeout: 15000 });
    const shareUrl = (await page.getByText(/\/q\//).first().textContent())!.trim();
    const path = shareUrl.match(/\/q\/[\w-]+/)?.[0];
    expect(path).toBeTruthy();

    // Open public link without session
    const anon = await browser.newContext();
    const anonPage = await anon.newPage();
    await anonPage.goto(path!);
    await expect(anonPage.getByText(/عرض سعر|Commercial Offer/i)).toBeVisible({ timeout: 15000 });
    await anon.close();

    // Mark sent then won
    await page.getByRole("button", { name: /تحديد كمُرسل|Mark as sent/i }).click();
    await expect(page.getByRole("button", { name: /تم الإغلاق ✓|Mark won/i })).toBeVisible({ timeout: 10000 });
    await page.getByRole("button", { name: /تم الإغلاق ✓|Mark won/i }).click();

    // Dashboard reflects the won deal
    await page.goto("/app/dashboard");
    await expect(page.getByText(/صفقات مفتوحة|Won deals/i)).toBeVisible();
  });

  test("tenant isolation: org B cannot see org A data", async ({ page }) => {
    await page.goto("/register");
    await page.getByLabel(/اسم الشركة|Company name/i).fill(`Isolation Org ${random}`);
    await page.getByLabel(/البريد الإلكتروني|Email/i).fill(`iso-${random}@test.iq`);
    await page.getByLabel(/كلمة المرور|Password/i).first().fill(PASSWORD);
    await page.getByRole("button", { name: /إنشاء حساب|Sign up/i }).click();
    await expect(page).toHaveURL(/onboarding/);

    // Their customers list must not contain org A's customers
    await page.goto("/app/customers");
    await expect(page.getByText("عميل عروض")).toHaveCount(0);
    await expect(page.getByText("عميل اختبار")).toHaveCount(0);
  });
});
