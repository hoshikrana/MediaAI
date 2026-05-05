import { Page } from "@playwright/test"

export async function uploadXrayAndSubmit(page: Page, imagePath: string, symptoms: string) {
    await page.goto("/upload")
    
    // Upload image
    const fileInput = page.locator('input[type="file"]')
    await fileInput.setInputFiles(imagePath)
    
    // Wait for preview
    await page.waitForSelector('[data-testid="image-preview"]', { timeout: 5000 })
    
    // Enter symptoms
    if (symptoms) {
        await page.fill('textarea', symptoms)
    }
    
    // Click analyze
    await page.click('[data-testid="analyze-button"]')
}
