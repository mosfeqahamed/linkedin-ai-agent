"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { formatDateTime, relativeTime } from "@/lib/format";
import type { Post } from "@/lib/types";
import { StatusBadge } from "./StatusBadge";

const editableStatuses: Post["status"][] = ["draft", "scheduled", "failed"];

export function PostCard({ post }: { post: Post }) {
  const qc = useQueryClient();

  const del = useMutation({
    mutationFn: () => api.deletePost(post.id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["posts"] }),
  });

  const regen = useMutation({
    mutationFn: () => api.regeneratePost(post.id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["posts"] }),
  });

  const isEditable = editableStatuses.includes(post.status);

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4">
      <div className="mb-2 flex items-start justify-between gap-3">
        <h3 className="font-medium">{post.topic}</h3>
        <StatusBadge status={post.status} />
      </div>

      <p className="mb-3 line-clamp-6 whitespace-pre-wrap text-sm text-gray-700">
        {post.generated_text}
      </p>

      <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-gray-500">
        <span title={post.scheduled_at}>
          Scheduled: {formatDateTime(post.scheduled_at)} ({relativeTime(post.scheduled_at)})
        </span>
        {post.error_message && (
          <span className="text-red-600">⚠ {post.error_message}</span>
        )}
      </div>

      {(isEditable || regen.isError) && (
        <div className="mt-3 flex gap-3 text-xs">
          {isEditable && (
            <>
              <button
                onClick={() => regen.mutate()}
                disabled={regen.isPending}
                className="text-blue-600 hover:underline disabled:opacity-50"
              >
                {regen.isPending ? "Regenerating…" : "Regenerate text"}
              </button>
              <button
                onClick={() => del.mutate()}
                disabled={del.isPending}
                className="text-red-600 hover:underline disabled:opacity-50"
              >
                {del.isPending ? "Cancelling…" : "Cancel"}
              </button>
            </>
          )}
        </div>
      )}

      {post.linkedin_post_urn && (
        <p className="mt-2 text-xs text-gray-500">
          URN: <span className="font-mono">{post.linkedin_post_urn}</span>
        </p>
      )}
    </div>
  );
}
