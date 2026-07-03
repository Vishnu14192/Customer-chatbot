// Import Metadata type from Next.js for type-safe metadata configuration
import type { Metadata } from "next";
// Import global stylesheet
import "./globals.css";

// Define metadata for the application including title and description
export const metadata: Metadata = {
  title: "Flipkart Customer Care Chatbot",
  description: "AI-powered customer support chatbot for Flipkart orders and policies",
};

// Root layout component that wraps all pages in the application
export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    // HTML root element with antialiasing and full height styling
    <html lang="en" className="h-full antialiased">
      {/* Body element with flexbox layout to fill minimum height */}
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
