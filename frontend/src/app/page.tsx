"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { auth } from "@/lib/auth";
import { Field } from "@/components/Field";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  useEffect(() => {
    if (auth.get()) router.replace("/dashboard");
  }, [router]);

  const login = useMutation({
    mutationFn: () => api.login(email, password),
    onSuccess: ({ access_token }) => {
      auth.set(access_token);
      router.push("/compose");
    },
  });

  const errorMessage = login.error ? (login.error as Error).message : null;
  const needsVerification = errorMessage?.toLowerCase().includes("verify");

  return (
    <div className="mx-auto max-w-sm pt-10">
      <h1 className="mb-2 text-3xl font-semibold">LinkedIn AI Agent</h1>
      <p className="mb-6 text-sm text-gray-600">Sign in to your account.</p>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          login.mutate();
        }}
        className="space-y-4"
      >
        <Field
          label="Email"
          id="email"
          type="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="you@example.com"
        />

        <Field
          label="Password"
          id="password"
          type="password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="••••••••"
        />

        {errorMessage && (
          <div className="space-y-1 text-sm text-red-600">
            <p>{errorMessage}</p>
            {needsVerification && (
              <button
                type="button"
                onClick={() => {
                  sessionStorage.setItem("pending_email", email);
                  router.push("/verify-email");
                }}
                className="font-medium text-blue-600 hover:underline"
              >
                Verify your email →
              </button>
            )}
          </div>
        )}

        <button
          type="submit"
          disabled={!email || !password || login.isPending}
          className="w-full rounded bg-blue-600 py-2 font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {login.isPending ? "Signing in…" : "Log in"}
        </button>
      </form>

      <div className="mt-4 flex justify-between text-sm">
        <Link href="/register" className="text-blue-600 hover:underline">
          Create an account
        </Link>
        <Link href="/forgot-password" className="text-blue-600 hover:underline">
          Forgot password?
        </Link>
      </div>
    </div>
  );
}
