"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useRequireAdmin } from "@/lib/useRequireAdmin";
import { formatDateTime } from "@/lib/format";
import { StatusBadge } from "@/components/StatusBadge";
import type { AdminPost } from "@/lib/types";

export default function AdminPostsPage() {
  const { isAdmin } = useRequireAdmin();

  const posts = useQuery({
    queryKey: ["admin-posts"],
    queryFn: api.adminListPosts,
    enabled: isAdmin,
    refetchInterval: 30_000,
  });

  if (!isAdmin) {
    return <p className="text-sm text-gray-500">Checking access…</p>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">All posts</h1>
        <Link
          href="/admin"
          className="rounded border border-gray-300 px-3 py-1.5 text-sm hover:bg-gray-50"
        >
          ← Admin
        </Link>
      </div>

      {posts.isLoading && <p className="text-sm text-gray-500">Loading…</p>}
      {posts.error && (
        <div className="rounded border border-red-200 bg-red-50 p-3 text-sm text-red-800">
          {(posts.error as Error).message}
        </div>
      )}

      {posts.data && (
        <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white">
          <table className="w-full text-sm">
            <thead className="border-b border-gray-200 bg-gray-50 text-left text-gray-600">
              <tr>
                <th className="p-3">Topic</th>
                <th className="p-3">User</th>
                <th className="p-3">Status</th>
                <th className="p-3">Scheduled</th>
              </tr>
            </thead>
            <tbody>
              {posts.data.posts.map((p: AdminPost) => (
                <tr key={p.id} className="border-b border-gray-100 last:border-0">
                  <td className="p-3">
                    <div className="font-medium">{p.topic}</div>
                    {p.error_message && (
                      <div className="text-xs text-red-600">{p.error_message}</div>
                    )}
                  </td>
                  <td className="p-3 text-gray-600">{p.user_email ?? "—"}</td>
                  <td className="p-3">
                    <StatusBadge status={p.status} />
                  </td>
                  <td className="p-3 text-gray-600">
                    {formatDateTime(p.scheduled_at)}
                  </td>
                </tr>
              ))}
              {posts.data.posts.length === 0 && (
                <tr>
                  <td colSpan={4} className="p-6 text-center text-gray-500">
                    No posts yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
      {posts.data && (
        <p className="text-xs text-gray-500">
          Showing {posts.data.posts.length} of {posts.data.total} post(s).
        </p>
      )}
    </div>
  );
}
