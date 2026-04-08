"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { InstallPwaButton } from "@/components/ui/InstallPwaButton";

const navButtonBase =
  "inline-flex h-10 items-center justify-center rounded-2xl border px-3 text-sm font-medium shadow-sm transition md:h-11 md:px-4";

const navButtonInactive =
  "border-white/10 bg-white/5 text-white/75 hover:bg-white/10 hover:text-white";

const navButtonActive =
  "border-blue-400/20 bg-blue-500/15 text-blue-100 shadow-sm";

export function HeaderNav() {
  const pathname = usePathname();

  const isHome = pathname === "/";
  const isLists = pathname === "/lists" || pathname.startsWith("/lists/");

  return (
    <nav className="flex flex-wrap items-center justify-end gap-2 text-sm md:gap-3">
      <InstallPwaButton />

      <Link
        href="/"
        className={`${navButtonBase} ${
          isHome ? navButtonActive : navButtonInactive
        }`}
      >
        Acasă
      </Link>

      <Link
        href="/lists"
        className={`${navButtonBase} ${
          isLists ? navButtonActive : navButtonInactive
        }`}
      >
        Liste
      </Link>
    </nav>
  );
}