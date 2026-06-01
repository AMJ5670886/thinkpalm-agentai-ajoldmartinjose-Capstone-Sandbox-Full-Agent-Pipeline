import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "IoT Dashboard Generator",
  description: "AI agent pipeline for IoT dashboard UI",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
