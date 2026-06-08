import { notFound } from "next/navigation";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "https://ai-agency-platform.onrender.com";

interface PageProps {
  params: { slug: string };
}

export default async function BusinessPage({ params }: PageProps) {
  const { slug } = params;

  // Skip internal Next.js routes
  const reserved = ["leads", "websites", "outreach", "editor", "tools", "growth", "analytics", "creatives", "api", "_next", "favicon.ico"];
  if (reserved.includes(slug)) {
    notFound();
  }

  try {
    const res = await fetch(`${API_URL}/api/preview/by-slug/${slug}`, {
      cache: "no-store",
    });

    if (!res.ok) {
      notFound();
    }

    const html = await res.text();

    return (
      <div dangerouslySetInnerHTML={{ __html: html }} />
    );
  } catch {
    notFound();
  }
}

export async function generateMetadata({ params }: PageProps) {
  const { slug } = params;
  const title = slug
    .replace(/-/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());

  return {
    title: `${title} | City Maps`,
    description: `Visit ${title} - powered by City Maps`,
  };
}
