import { test, expect } from "@playwright/test"
import { loginAs } from "../helpers/auth"

test.describe("Analysis Upload Flow", () => {
    
    test.beforeEach(async ({ page }) => {
        // Assumes test user is seeded
        await loginAs(page, "test@medsight.ai", "TestPass123!")
    })
    
    test("upload page has required elements", async ({ page }) => {
        await page.goto("/upload")
        
        // Use generic selectors if testids aren't present on dropzone yet
        await expect(page.locator('input[type="file"]')).toBeAttached()
        await expect(page.locator('textarea')).toBeVisible()
        await expect(page.locator('[data-testid="analyze-button"]')).toBeDisabled()
    })
    
    test("analyze button enables after image upload", async ({ page }) => {
        await page.goto("/upload")
        
        const fileInput = page.locator('input[type="file"]')
        // Ensure this fixture exists or path is correct
        await fileInput.setInputFiles("../backend/tests/fixtures/sample_xray.png") 
        
        await expect(page.locator('[data-testid="image-preview"]')).toBeVisible()
        await expect(page.locator('[data-testid="analyze-button"]')).toBeEnabled()
    })
    
    test("wrong file type shows error", async ({ page }) => {
        await page.goto("/upload")
        const fileInput = page.locator('input[type="file"]')
        
        // Provide a dummy PDF path
        await fileInput.setInputFiles("../backend/tests/fixtures/sample.pdf")
        await expect(page.locator('[data-testid="file-error"]')).toBeVisible()
    })
    
    test("full analysis flow completes successfully", async ({ page }) => {
        test.setTimeout(90000) // Increase test timeout for ML processing
        
        await page.goto("/upload")
        
        const fileInput = page.locator('input[type="file"]')
        await fileInput.setInputFiles("../backend/tests/fixtures/sample_xray.png")
        await page.fill('textarea', "chest pain and shortness of breath")
        
        await page.click('[data-testid="analyze-button"]')
        
        // Wait for progress tracking UI
        await expect(page.locator('[data-testid="progress-tracker"]')).toBeVisible()
        
        // Wait for redirect to results (polling takes time)
        await page.waitForURL(/.*results.*/, { timeout: 80000 })
        
        // Verify results page loaded
        await expect(page.locator('[data-testid="risk-banner"]')).toBeVisible()
        await expect(page.locator('[data-testid="heatmap-viewer"]')).toBeVisible()
        await expect(page.locator('[data-testid="ai-report"]')).toBeVisible()
    })
})
