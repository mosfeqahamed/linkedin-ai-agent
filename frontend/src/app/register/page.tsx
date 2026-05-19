"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { auth } from "@/lib/auth";
import { Field } from "@/components/Field";

export default function RegisterPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");

  useEffect(() => {
    if (auth.get()) router.replace("/dashboard");
  }, [router]);

  const register = useMutation({
    mutationFn: () => api.register(email, password, name || undefined),
    onSuccess: () => {
      sessionStorage.setItem("pending_email", email);
      router.push("/verify-email");
    },
  });

  const mismatch = confirm.length > 0 && password !== confirm;
  const tooShort = password.length > 0 && password.length < 8;

  return (
    <div className="mx-auto max-w-sm pt-10">
      <h1 className="mb-2 text-3xl font-semibold">Create your account</h1>
      <p className="mb-6 text-sm text-gray-600">
        We&apos;ll email you a 6-digit code to verify your address.
      </p>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (!mismatch && !tooShort) register.mutate();
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
          label="Name (optional)"
          id="name"
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Your name"
        />

        <Field
          label="Password"
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
          label="Confirm password"
          id="confirm"
          type="password"
          required
          value={confirm}
          onChange={(e) => setConfirm(e.target.value)}
          placeholder="Re-enter your password"
        />
        {mismatch && (
          <p className="text-sm text-red-600">Passwords do not match.</p>
        )}

        {register.error && (
          <p className="text-sm text-red-600">
            {(register.error as Error).message}
          </p>
        )}

        <button
          type="submit"
          disabled={
            !email ||
            !password ||
            !confirm ||
            mismatch ||
            tooShort ||
            register.isPending
          }
          className="w-full rounded bg-blue-600 py-2 font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {register.isPending ? "Creating account…" : "Create account"}
        </button>
      </form>

      <p className="mt-4 text-sm text-gray-600">
        Already have an account?{" "}
        <Link href="/" className="text-blue-600 hover:underline">
          Log in
        </Link>
      </p>
    </div>
  );
}
