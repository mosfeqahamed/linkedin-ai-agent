"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { auth } from "@/lib/auth";
import { PostCard } from "@/components/PostCard";

export default function DashboardPage() {
  const router = useRouter();

  useEffect(() => {
    if (!auth.get()) router.replace("/");
  }, [router]);

  const { data, isLoading, error } = useQuery({
    queryKey: ["posts"],
    queryFn: api.listPosts,
    refetchInterval: 30_000,
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Your posts</h1>
        <Link
          href="/compose"
          className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          + New post
        </Link>
      </div>

      {isLoading && <p className="text-sm text-gray-500">Loading…</p>}
      {error && (
        <div className="rounded border border-red-200 bg-red-50 p-3 text-sm text-red-800">
          {(error as Error).message}
        </div>
      )}

      {data && data.length === 0 && (
        <div className="rounded-lg border border-dashed border-gray-300 bg-white p-10 text-center">
          <p className="text-sm text-gray-500">
            No posts yet. Compose your first one.
          </p>
        </div>
      )}

      <div className="grid gap-4">
        {data?.map((post) => (
          <PostCard key={post.id} post={post} />
        ))}
      </div>
    </div>
  );
}
