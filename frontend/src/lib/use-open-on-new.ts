"use client";

import { useEffect } from "react";

/**
 * Opens a dialog when the URL carries ``?new=1`` (used by the command palette
 * quick actions). Reads ``window.location`` in an effect so it does not require
 * a Suspense boundary the way ``useSearchParams`` does during prerender.
 */
export function useOpenOnNew(setOpen: (open: boolean) => void) {
  useEffect(() => {
    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);
      if (params.get("new") === "1") setOpen(true);
    }
  }, [setOpen]);
}
