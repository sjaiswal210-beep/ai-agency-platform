"use client";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function DashboardIndex() {
  const router = useRouter();
  useEffect(() => {
    router.replace("/");
  }, [router]);
  return <div className="min-h-screen bg-[#020817] flex items-center justify-center"><p className="text-slate-400">Redirecting...</p></div>;
}
