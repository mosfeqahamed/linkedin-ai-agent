"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { auth } from "@/lib/auth";
import { Field } from "@/components/Field";

export default function VerifyEmailPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [otp, setOtp] = useState("");

  useEffect(() => {
    if (auth.get()) router.replace("/dashboard");
    const pending = sessionStorage.getItem("pending_email");
    if (pending) setEmail(pending);
  }, [router]);

  const verify = useMutation({
    mutationFn: () => api.verifyEmail(email, otp),
    onSuccess: ({ access_token }) => {
      auth.set(access_token);
      sessionStorage.removeItem("pending_email");
      router.push("/compose");
    },
  });

  const resend = useMutation({
    mutationFn: () => api.resendOtp(email),
  });

  return (
    <div className="mx-auto max-w-sm pt-10">
      <h1 className="mb-2 text-3xl font-semibold">Verify your email</h1>
      <p className="mb-6 text-sm text-gray-600">
        Enter the 6-digit code we sent to your email address.
      </p>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          verify.mutate();
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
          label="Verification code"
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

        {verify.error && (
          <p className="text-sm text-red-600">
            {(verify.error as Error).message}
          </p>
        )}

        <button
          type="submit"
          disabled={!email || otp.length < 4 || verify.isPending}
          className="w-full rounded bg-blue-600 py-2 font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {verify.isPending ? "Verifying…" : "Verify email"}
        </button>
      </form>

      <div className="mt-4 space-y-2 text-sm">
        <button
          type="button"
          onClick={() => resend.mutate()}
          disabled={!email || resend.isPending}
          className="text-blue-600 hover:underline disabled:opacity-50"
        >
          {resend.isPending ? "Sending…" : "Resend code"}
        </button>
        {resend.data && (
          <p className="text-green-600">{resend.data.message}</p>
        )}
        {resend.error && (
          <p className="text-red-600">{(resend.error as Error).message}</p>
        )}
        <p className="text-gray-600">
          <Link href="/" className="text-blue-600 hover:underline">
            Back to login
          </Link>
        </p>
      </div>
    </div>
  );
}
