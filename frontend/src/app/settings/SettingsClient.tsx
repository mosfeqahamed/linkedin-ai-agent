"use client";

import { useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { auth } from "@/lib/auth";

export default function SettingsClient() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const qc = useQueryClient();

  useEffect(() => {
    if (!auth.get()) router.replace("/");
  }, [router]);

  const me = useQuery({ queryKey: ["me"], queryFn: api.me });

  const connect = useMutation({
    mutationFn: api.linkedinAuthorizeUrl,
    onSuccess: ({ url }) => {
      window.location.href = url;
    },
  });

  const disconnect = useMutation({
    mutationFn: api.linkedinDisconnect,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["me"] }),
  });

  const callbackStatus = searchParams.get("linkedin");
  const callbackError = searchParams.get("linkedin_error");

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Settings</h1>

      {callbackStatus === "connected" && (
        <div className="rounded border border-green-200 bg-green-50 p-3 text-sm text-green-800">
          LinkedIn connected successfully.
        </div>
      )}
      {callbackError && (
        <div className="rounded border border-red-200 bg-red-50 p-3 text-sm text-red-800">
          LinkedIn connection failed: {callbackError}
        </div>
      )}

      <section className="rounded-lg border border-gray-200 bg-white p-6">
        <h2 className="mb-3 font-medium">Account</h2>
        {me.isLoading && <p className="text-sm text-gray-500">Loading…</p>}
        {me.data && (
          <dl className="space-y-1 text-sm">
            <div className="flex gap-2">
              <dt className="w-24 text-gray-500">Email</dt>
              <dd>{me.data.email}</dd>
            </div>
            <div className="flex gap-2">
              <dt className="w-24 text-gray-500">Name</dt>
              <dd>{me.data.name || "—"}</dd>
            </div>
            <div className="flex gap-2">
              <dt className="w-24 text-gray-500">Timezone</dt>
              <dd>{me.data.timezone}</dd>
            </div>
          </dl>
        )}
      </section>

      <section className="rounded-lg border border-gray-200 bg-white p-6">
        <h2 className="mb-3 font-medium">LinkedIn</h2>

        {me.isLoading ? (
          <p className="text-sm text-gray-500">Loading…</p>
        ) : me.data?.linkedin_connected ? (
          <div className="space-y-3">
            <p className="text-sm text-green-700">
              Connected — scheduled posts will publish automatically.
            </p>
            <button
              onClick={() => disconnect.mutate()}
              disabled={disconnect.isPending}
              className="rounded border border-red-300 px-3 py-1.5 text-sm text-red-700 hover:bg-red-50 disabled:opacity-50"
            >
              {disconnect.isPending
                ? "Disconnecting…"
                : "Disconnect LinkedIn"}
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            <p className="text-sm text-gray-700">
              Not connected. Scheduled posts will fail at publish time.
            </p>
            <button
              onClick={() => connect.mutate()}
              disabled={connect.isPending}
              className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {connect.isPending ? "Loading…" : "Connect LinkedIn"}
            </button>
            {connect.error && (
              <p className="text-sm text-red-600">
                {(connect.error as Error).message}
              </p>
            )}
          </div>
        )}
      </section>
    </div>
  );
}
