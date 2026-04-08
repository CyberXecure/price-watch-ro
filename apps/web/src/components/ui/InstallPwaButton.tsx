"use client";

import { useEffect, useState } from "react";

type BeforeInstallPromptEvent = Event & {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed"; platform: string }>;
};

export function InstallPwaButton() {
  const [deferredPrompt, setDeferredPrompt] =
    useState<BeforeInstallPromptEvent | null>(null);
  const [isInstalled, setIsInstalled] = useState(false);

  useEffect(() => {
    const onBeforeInstallPrompt = (event: Event) => {
      event.preventDefault();
      setDeferredPrompt(event as BeforeInstallPromptEvent);
    };

    const onAppInstalled = () => {
      setIsInstalled(true);
      setDeferredPrompt(null);
    };

    const standalone =
      window.matchMedia("(display-mode: standalone)").matches ||
      (window.navigator as Navigator & { standalone?: boolean }).standalone ===
        true;

    if (standalone) {
      setIsInstalled(true);
    }

    window.addEventListener("beforeinstallprompt", onBeforeInstallPrompt);
    window.addEventListener("appinstalled", onAppInstalled);

    return () => {
      window.removeEventListener("beforeinstallprompt", onBeforeInstallPrompt);
      window.removeEventListener("appinstalled", onAppInstalled);
    };
  }, []);

  async function handleInstall() {
    if (!deferredPrompt) return;

    await deferredPrompt.prompt();
    await deferredPrompt.userChoice;
    setDeferredPrompt(null);
  }

  if (isInstalled) {
    return (
      <span className="inline-flex h-11 items-center justify-center rounded-2xl border border-emerald-400/20 bg-emerald-500/10 px-4 text-sm font-medium text-emerald-200 shadow-sm">
        Installed
      </span>
    );
  }

  if (!deferredPrompt) {
    return null;
  }

  return (
    <button
      type="button"
      onClick={handleInstall}
      className="inline-flex h-11 items-center justify-center rounded-2xl border border-blue-400/20 bg-blue-500/15 px-4 text-sm font-medium text-blue-100 shadow-sm transition hover:bg-blue-500/20"
    >
      Install
    </button>
  );
}