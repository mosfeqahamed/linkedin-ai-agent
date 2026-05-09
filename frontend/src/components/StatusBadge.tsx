import clsx from "clsx";
import type { PostStatus } from "@/lib/types";

const styles: Record<PostStatus, string> = {
  draft: "bg-gray-100 text-gray-700",
  scheduled: "bg-blue-100 text-blue-700",
  publishing: "bg-yellow-100 text-yellow-700",
  published: "bg-green-100 text-green-700",
  failed: "bg-red-100 text-red-700",
  cancelled: "bg-gray-100 text-gray-500",
};

export function StatusBadge({ status }: { status: PostStatus }) {
  return (
    <span
      className={clsx(
        "inline-block rounded px-2 py-0.5 text-xs font-medium uppercase tracking-wide",
        styles[status],
      )}
    >
      {status}
    </span>
  );
}
