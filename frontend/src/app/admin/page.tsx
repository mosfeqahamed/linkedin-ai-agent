"use client";

import { useState } from "react";
import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useRequireAdmin } from "@/lib/useRequireAdmin";
import type { AdminUser } from "@/lib/types";

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4">
      <p className="text-sm text-gray-500">{label}</p>
      <p className="mt-1 text-2xl font-semibold">{value}</p>
    </div>
  );
}

export default function AdminPage() {
  const { isAdmin } = useRequireAdmin();
  const qc = useQueryClient();
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");

  const stats = useQuery({
    queryKey: ["admin-stats"],
    queryFn: api.adminStats,
    enabled: isAdmin,
  });

  const users = useQuery({
    queryKey: ["admin-users", search],
    queryFn: () => api.adminListUsers(search || undefined),
    enabled: isAdmin,
  });

  const updateUser = useMutation({
    mutationFn: (vars: {
      id: string;
      data: { role?: "user" | "admin"; is_active?: boolean };
    }) => api.adminUpdateUser(vars.id, vars.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin-users"] });
      qc.invalidateQueries({ queryKey: ["admin-stats"] });
    },
  });

  const deleteUser = useMutation({
    mutationFn: (id: string) => api.adminDeleteUser(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin-users"] });
      qc.invalidateQueries({ queryKey: ["admin-stats"] });
    },
  });

  const actionError =
    (updateUser.error as Error | null)?.message ||
    (deleteUser.error as Error | null)?.message;

  if (!isAdmin) {
    return <p className="text-sm text-gray-500">Checking access…</p>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Admin</h1>
        <Link
          href="/admin/posts"
          className="rounded border border-gray-300 px-3 py-1.5 text-sm hover:bg-gray-50"
        >
          All posts →
        </Link>
      </div>

      {/* Stats */}
      {stats.data && (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
          <StatCard label="Users" value={stats.data.total_users} />
          <StatCard label="Verified" value={stats.data.verified_users} />
          <StatCard label="Admins" value={stats.data.admins} />
          <StatCard label="LinkedIn linked" value={stats.data.linkedin_connected} />
          <StatCard label="Posts" value={stats.data.total_posts} />
        </div>
      )}

      {/* Search */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          setSearch(searchInput.trim());
        }}
        className="flex gap-2"
      >
        <input
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          placeholder="Search by email…"
          className="w-64 rounded border border-gray-300 p-2 text-sm focus:border-blue-500 focus:outline-none"
        />
        <button
          type="submit"
          className="rounded bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          Search
        </button>
        {search && (
          <button
            type="button"
            onClick={() => {
              setSearchInput("");
              setSearch("");
            }}
            className="rounded border border-gray-300 px-3 py-2 text-sm hover:bg-gray-50"
          >
            Clear
          </button>
        )}
      </form>

      {actionError && (
        <div className="rounded border border-red-200 bg-red-50 p-3 text-sm text-red-800">
          {actionError}
        </div>
      )}

      {/* Users table */}
      {users.isLoading && <p className="text-sm text-gray-500">Loading…</p>}
      {users.error && (
        <div className="rounded border border-red-200 bg-red-50 p-3 text-sm text-red-800">
          {(users.error as Error).message}
        </div>
      )}

      {users.data && (
        <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white">
          <table className="w-full text-sm">
            <thead className="border-b border-gray-200 bg-gray-50 text-left text-gray-600">
              <tr>
                <th className="p-3">Email</th>
                <th className="p-3">Role</th>
                <th className="p-3">Status</th>
                <th className="p-3">LinkedIn</th>
                <th className="p-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.data.users.map((u: AdminUser) => (
                <tr key={u.id} className="border-b border-gray-100 last:border-0">
                  <td className="p-3">
                    <div className="font-medium">{u.email}</div>
                    {u.name && <div className="text-gray-500">{u.name}</div>}
                  </td>
                  <td className="p-3">
                    <span
                      className={
                        u.role === "admin"
                          ? "font-medium text-blue-600"
                          : "text-gray-600"
                      }
                    >
                      {u.role}
                    </span>
                  </td>
                  <td className="p-3">
                    <div className="flex flex-col gap-0.5">
                      <span className={u.is_active ? "text-green-600" : "text-red-600"}>
                        {u.is_active ? "active" : "disabled"}
                      </span>
                      {!u.is_verified && (
                        <span className="text-xs text-amber-600">unverified</span>
                      )}
                    </div>
                  </td>
                  <td className="p-3 text-gray-600">
                    {u.linkedin_connected ? "linked" : "—"}
                  </td>
                  <td className="p-3">
                    <div className="flex justify-end gap-2">
                      <button
                        onClick={() =>
                          updateUser.mutate({
                            id: u.id,
                            data: {
                              role: u.role === "admin" ? "user" : "admin",
                            },
                          })
                        }
                        disabled={updateUser.isPending}
                        className="rounded border border-gray-300 px-2 py-1 text-xs hover:bg-gray-50 disabled:opacity-50"
                      >
                        {u.role === "admin" ? "Demote" : "Promote"}
                      </button>
                      <button
                        onClick={() =>
                          updateUser.mutate({
                            id: u.id,
                            data: { is_active: !u.is_active },
                          })
                        }
                        disabled={updateUser.isPending}
                        className="rounded border border-gray-300 px-2 py-1 text-xs hover:bg-gray-50 disabled:opacity-50"
                      >
                        {u.is_active ? "Disable" : "Enable"}
                      </button>
                      <button
                        onClick={() => {
                          if (
                            window.confirm(
                              `Permanently delete ${u.email} and all their posts? This cannot be undone.`,
                            )
                          ) {
                            deleteUser.mutate(u.id);
                          }
                        }}
                        disabled={deleteUser.isPending}
                        className="rounded border border-red-300 px-2 py-1 text-xs text-red-700 hover:bg-red-50 disabled:opacity-50"
                      >
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {users.data.users.length === 0 && (
                <tr>
                  <td colSpan={5} className="p-6 text-center text-gray-500">
                    No users found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
      {users.data && (
        <p className="text-xs text-gray-500">
          Showing {users.data.users.length} of {users.data.total} user(s).
        </p>
      )}
    </div>
  );
}
