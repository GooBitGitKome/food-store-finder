import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Food Store Finder - 自前Webサイトなし飲食店検索＆連絡先収集",
  description: "指定エリア・Pin半径から自社Webサイトを持たない飲食店を抽出し、メール・連絡先を一覧化・CSV出力するツール",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ja">
      <body className="bg-slate-50 text-slate-900 min-h-screen antialiased">
        {children}
      </body>
    </html>
  );
}
