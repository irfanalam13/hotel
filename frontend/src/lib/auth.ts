import type { TokenPair } from "@/types";

const ACCESS_KEY = "hms.access";
const REFRESH_KEY = "hms.refresh";
const ORG_KEY = "hms.org";

const isBrowser = typeof window !== "undefined";

export const auth = {
  getAccess(): string | null {
    return isBrowser ? localStorage.getItem(ACCESS_KEY) : null;
  },
  getRefresh(): string | null {
    return isBrowser ? localStorage.getItem(REFRESH_KEY) : null;
  },
  setTokens(tokens: TokenPair) {
    if (!isBrowser) return;
    localStorage.setItem(ACCESS_KEY, tokens.access);
    localStorage.setItem(REFRESH_KEY, tokens.refresh);
  },
  clear() {
    if (!isBrowser) return;
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
  },
  getOrgSlug(): string | null {
    return isBrowser ? localStorage.getItem(ORG_KEY) : null;
  },
  setOrgSlug(slug: string) {
    if (isBrowser) localStorage.setItem(ORG_KEY, slug);
  },
  isAuthenticated(): boolean {
    return Boolean(this.getAccess());
  },
};
