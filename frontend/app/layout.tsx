import type { Metadata } from "next";
import { DM_Sans, Geist_Mono } from "next/font/google";
import { Providers } from "./providers";
import { Toaster } from "@/components/ui/sonner";
import "./globals.css";

const dmSans = DM_Sans({
  variable: "--font-sans",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "RecruitTech | AI-Powered Talent Platform",
  description: "Intelligent candidate matching, copilot dashboards, and multi-persona workflows for modern recruitment",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={`${dmSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-background text-foreground">
        <a href="#main-content" className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-primary focus:text-primary-foreground focus:rounded-md focus:shadow-lg focus:outline-none">
          Skip to content
        </a>
        <Providers>
          <div id="main-content">{children}</div>
          <Toaster />
        </Providers>
      </body>
    </html>
  );
}
