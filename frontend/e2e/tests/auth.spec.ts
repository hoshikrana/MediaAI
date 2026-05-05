import { test, expect } from "@playwright/test"
import { loginAs } from "../helpers/auth"

test.describe("Authentication Flow", () => {
    
    test("landing page loads and shows CTA", async ({ page }) => {
        await page.goto("/")
        await expect(page.locator("h1")).toContainText("MedSight")
        await expect(page.locator('a[href="/upload"]')).toBeVisible()
    })
    
    test("login with valid credentials redirects to upload", async ({ page }) => {
        // Assumes a test user is seeded in the test database
        await loginAs(page, "test@medsight.ai", "TestPass123!")
        await expect(page).toHaveURL("/upload")
        await expect(page.locator('[data-testid="navbar-user"]')).toBeVisible()
    })
    
    test("login with wrong password shows error", async ({ page }) => {
        await page.goto("/login")
        await page.fill('[name="email"]', "test@medsight.ai")
        await page.fill('[name="password"]', "WrongPassword!")
        await page.click('button[type="submit"]')
        
        // Wait for error alert to appear
        const alert = page.locator('[role="alert"]').first()
        await expect(alert).toBeVisible({ timeout: 5000 })
        await expect(alert).toContainText("Invalid")
    })
    
    test("protected page redirects to login if not authenticated", async ({ page }) => {
        await page.goto("/upload")
        await expect(page).toHaveURL(/.*login.*/)
    })
    
    test("logout clears session and redirects to login", async ({ page }) => {
        await loginAs(page, "test@medsight.ai", "TestPass123!")
        
        // Open user menu and click logout
        await page.click('[data-testid="user-menu"]')
        await page.click('[data-testid="logout-button"]')
        
        await expect(page).toHaveURL("/login")
        
        // Verify protected page now redirects back to login
        await page.goto("/upload")
        await expect(page).toHaveURL(/.*login.*/)
    })
})
