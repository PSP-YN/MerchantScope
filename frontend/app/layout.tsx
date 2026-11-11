import type { Metadata } from "next";
import "./globals.css";
import "@xyflow/react/dist/style.css";
export const metadata: Metadata = { title: "TRACE | Merchant Risk Intelligence", description: "Explainable merchant behaviour intelligence for payment ecosystems." };
export default function RootLayout({children}:{children:React.ReactNode}) {
 return <html lang="en"><body>{children}</body></html>;
}
