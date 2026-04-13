/**
 * Simple token estimator: characters / 4.
 * Consistent with the backend's _estimate_tokens() function.
 */
export function estimateTokens(text: string): number {
  return Math.max(1, Math.floor(text.length / 4))
}
