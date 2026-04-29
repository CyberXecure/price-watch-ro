export const APP_MODE = process.env.NEXT_PUBLIC_APP_MODE ?? "dev";
export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:18400";

export function isDesktopMode(): boolean {
  return APP_MODE === "desktop";
}


