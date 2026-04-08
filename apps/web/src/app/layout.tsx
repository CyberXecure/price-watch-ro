import type { Metadata } from "next";
import Link from "next/link";
import { HeaderNav } from "@/components/ui/HeaderNav";
import "./globals.css";

export const metadata: Metadata = {
  title: "Chilipir",
  description: "Liste și alerte de preț pentru Freshful",
  applicationName: "Chilipir",
};

function LogoMark() {
  return (
    <span className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl border border-blue-400/20 bg-blue-600/15 shadow-[0_0_30px_rgba(37,99,235,0.18)] md:h-11 md:w-11">
      <svg
        width="22"
        height="22"
        viewBox="0 0 24 24"
        fill="none"
        aria-hidden="true"
      >
        <path
          d="M6 7.5C6 6.67157 6.67157 6 7.5 6H12.879C13.2768 6 13.6584 6.15804 13.9393 6.43934L17.5607 10.0607C17.842 10.3416 18 10.7232 18 11.121V16.5C18 17.3284 17.3284 18 16.5 18H7.5C6.67157 18 6 17.3284 6 16.5V7.5Z"
          stroke="#DCEBFF"
          strokeWidth="1.8"
        />
        <circle cx="9" cy="9" r="1.2" fill="#DCEBFF" />
        <path
          d="M10 13.2L11.8 15L15 11.8"
          stroke="#DCEBFF"
          strokeWidth="1.8"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    </span>
  );
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ro">
      <body>
        <div className="min-h-screen">
          <header className="sticky top-0 z-50 border-b border-white/5 bg-[#081120]/80 backdrop-blur-xl">
            <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-4 py-3 md:px-6 md:py-4">
              <Link href="/" className="flex min-w-0 items-center gap-3 md:gap-4">
                <LogoMark />
                <div className="min-w-0">
                  <div className="truncate text-xl font-bold tracking-tight text-white md:text-2xl">
                    Chilipir
                  </div>
                  <div className="hidden text-sm text-slate-400 md:block">
                    Liste și alerte de preț pentru Freshful
                  </div>
                </div>
              </Link>

              <HeaderNav />
            </div>
          </header>

          {children}
        </div>
      </body>
    </html>
  );
}