"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { auth } from "@/lib/auth";
import { Field } from "@/components/Field";

export default function ResetPasswordPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [otp, setOtp] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");

  useEffect(() => {
    const pending = sessionStorage.getItem("pending_email");
    if (pending) setEmail(pending);
  }, []);

  const reset = useMutation({
    mutationFn: () => api.resetPassword(email, otp, password),
    onSuccess: ({ access_token }) => {
      auth.set(access_token);
      sessionStorage.removeItem("pending_email");
      router.push("/compose");
    },
  });

  const mismatch = confirm.length > 0 && password !== confirm;
  const tooShort = password.length > 0 && password.length < 8;

  return (
    <div className="mx-auto max-w-sm pt-10">
      <h1 className="mb-2 text-3xl font-semibold">Reset password</h1>
      <p className="mb-6 text-sm text-gray-600">
        Enter the code we emailed you and choose a new password.
      </p>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (!mismatch && !tooShort) reset.mutate();
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
          label="Reset code"
          id="otp"
          type="text"
          inputMode="numeric"
          autoComplete="one-time-code"
          required
          maxLength={6}
          value={otp}
          onChange={(e) => setOtp(e.target.value.replace(/\D/g, ""))}
          placeholder="123456"
        />

        <Field
          label="New password"
          id="password"
          type="password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="At least 8 characters"
        />
        {tooShort && (
          <p className="text-sm text-red-600">
            Password must be at least 8 characters.
          </p>
        )}

        <Field
          label="Confirm new password"
          id="confirm"
          type="password"
          required
          value={confirm}
          onChange={(e) => setConfirm(e.target.value)}
          placeholder="Re-enter your new password"
        />
        {mismatch && (
          <p className="text-sm text-red-600">Passwords do not match.</p>
        )}

        {reset.error && (
          <p className="text-sm text-red-600">
            {(reset.error as Error).message}
          </p>
        )}

        <button
          type="submit"
          disabled={
            !email ||
            otp.length < 4 ||
            !password ||
            !confirm ||
            mismatch ||
            tooShort ||
            reset.isPending
          }
          className="w-full rounded bg-blue-600 py-2 font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {reset.isPending ? "Resetting…" : "Reset password"}
        </button>
      </form>

      <p className="mt-4 text-sm text-gray-600">
        <Link href="/" className="text-blue-600 hover:underline">
          Back to login
        </Link>
      </p>
    </div>
  );
}
