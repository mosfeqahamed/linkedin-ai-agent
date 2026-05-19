"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { api } from "./api";
import { auth } from "./auth";

/**
 * Guards an admin page: redirects to "/" when unauthenticated and to
 * "/dashboard" when the signed-in user is not an admin.
 */
export function useRequireAdmin() {
  const router = useRouter();

  const { data: me, isLoading, isError } = useQuery({
    queryKey: ["me"],
    queryFn: api.me,
    retry: false,
  });

  useEffect(() => {
    if (!auth.get()) router.replace("/");
  }, [router]);

  useEffect(() => {
    if (isError) {
      router.replace("/");
    } else if (me && me.role !== "admin") {
      router.replace("/dashboard");
    }
  }, [me, isError, router]);

  return { isAdmin: me?.role === "admin", isLoading };
}
