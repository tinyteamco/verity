/**
 * Helper to wrap When steps with automatic hydration.
 * Call this in step definitions instead of raw When.
 *
 * Usage:
 *   When('I click {string}', async ({ page, fixtures }, text) => {
 *     // Hydration automatically applied before this runs
 *     await page.click(`button:has-text("${text}")`)
 *   })
 */
export function createWhenWithHydration(WhenRaw: any) {
  return (pattern: string | RegExp, handler: any) => {
    // Extract parameter names from handler
    const handlerStr = handler.toString()
    const match = handlerStr.match(/\{\s*([^}]+)\s*\}/)
    const params = match ? match[1].split(',').map((p: string) => p.trim()) : []

    // Create wrapper that preserves destructuring pattern
    const wrapper = new Function(
      'handler',
      'fixtures',
      `return async ({ ${params.join(', ')} }, ...args) => {
        if (fixtures) await fixtures.applyHydration()
        return handler({ ${params.join(', ')} }, ...args)
      }`
    )(handler, undefined)

    // Register with playwright-bdd
    WhenRaw(pattern, async ({ fixtures, ...context }: any, ...args: any[]) => {
      if (fixtures) await fixtures.applyHydration()
      return handler({ fixtures, ...context }, ...args)
    })
  }
}
