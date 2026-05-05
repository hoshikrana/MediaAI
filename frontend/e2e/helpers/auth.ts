import { Page } from "@playwright/test"

export async function loginAs(page: Page, email: string, password: string) {
    await page.goto("/login")
    await page.fill('[placeholder*="email" i]', email)
    await page.fill('[placeholder*="password" i]', password)
    await page.click('button[type="submit"]')
    await page.waitForURL("/upload", { timeout: 10000 })
}

export async function registerTestUser(page: Page) {
    const email = `test_${Date.now()}@medsight.ai`
    const password = "TestPass123!"
    
    await page.goto("/register")
    await page.fill('[name="full_name"]', "E2E Test User")
    await page.fill('[name="email"]', email)
    await page.fill('[name="password"]', password)
    await page.click('button[type="submit"]')
    
    return { email, password }
}
