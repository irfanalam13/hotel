import { QueryClient } from "@tanstack/react-query";

export function makeQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 30_000,
        retry: (failureCount, error: unknown) => {
          // Don't retry auth/permission errors.
          const status = (error as { status?: number })?.status;
          if (status && [400, 401, 403, 404, 409].includes(status)) return false;
          return failureCount < 2;
        },
        refetchOnWindowFocus: false,
      },
    },
  });
}
