const KEY = "linkedin_agent_token";

export const auth = {
  get(): string | null {
    if (typeof window === "undefined") return null;
    return window.localStorage.getItem(KEY);
  },
  set(token: string): void {
    window.localStorage.setItem(KEY, token);
  },
  clear(): void {
    window.localStorage.removeItem(KEY);
  },
};
