import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = { title: "Mengo — Mandarin for real life", description: "A privacy-aware Mandarin conversation practice MVP." };
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) { return <html lang="en"><body>{children}</body></html>; }
