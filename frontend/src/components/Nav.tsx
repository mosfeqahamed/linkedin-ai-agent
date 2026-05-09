"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import clsx from "clsx";
import { auth } from "@/lib/auth";

const tabs = [
  { href: "/compose", label: "Compose" },
  { href: "/dashboard", label: "Dashboard" },
  { href: "/settings", label: "Settings" },
];

export function Nav() {
  const router = useRouter();
  const pathname = usePathname();
  const [authed, setAuthed] = useState(false);

  useEffect(() => {
    setAuthed(!!auth.get());
  }, [pathname]);

  if (!authed || pathname === "/") return null;

  const logout = () => {
    auth.clear();
    router.push("/");
  };

  return (
    <nav className="border-b border-gray-200 bg-white">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-3">
        <Link href="/dashboard" className="font-semibold">
          LinkedIn AI Agent
        </Link>
        <div className="flex items-center gap-4 text-sm">
          {tabs.map((t) => (
            <Link
              key={t.href}
              href={t.href}
              className={clsx(
                pathname === t.href
                  ? "font-medium text-blue-600"
                  : "text-gray-600 hover:text-gray-900",
              )}
            >
              {t.label}
            </Link>
          ))}
          <button
            onClick={logout}
            className="text-gray-600 hover:text-gray-900"
          >
            Log out
          </button>
        </div>
      </div>
    </nav>
  );
}
