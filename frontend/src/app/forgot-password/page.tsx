"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Field } from "@/components/Field";

export default function ForgotPasswordPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");

  const forgot = useMutation({
    mutationFn: () => api.forgotPassword(email),
    onSuccess: () => {
      sessionStorage.setItem("pending_email", email);
    },
  });

  return (
    <div className="mx-auto max-w-sm pt-10">
      <h1 className="mb-2 text-3xl font-semibold">Forgot password</h1>
      <p className="mb-6 text-sm text-gray-600">
        Enter your email and we&apos;ll send you a reset code.
      </p>

      {forgot.isSuccess ? (
        <div className="space-y-4">
          <div className="rounded border border-green-200 bg-green-50 p-3 text-sm text-green-800">
            {forgot.data.message}
          </div>
          <button
            onClick={() => router.push("/reset-password")}
            className="w-full rounded bg-blue-600 py-2 font-medium text-white hover:bg-blue-700"
          >
            Enter reset code
          </button>
        </div>
      ) : (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            forgot.mutate();
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

          {forgot.error && (
            <p className="text-sm text-red-600">
              {(forgot.error as Error).message}
            </p>
          )}

          <button
            type="submit"
            disabled={!email || forgot.isPending}
            className="w-full rounded bg-blue-600 py-2 font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {forgot.isPending ? "Sending…" : "Send reset code"}
          </button>
        </form>
      )}

      <p className="mt-4 text-sm text-gray-600">
        <Link href="/" className="text-blue-600 hover:underline">
          Back to login
        </Link>
      </p>
    </div>
  );
}
