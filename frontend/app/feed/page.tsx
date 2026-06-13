import type { Metadata } from "next";
import FeedBrowser from "@/components/FeedBrowser";
import { getItems } from "@/lib/content";

export const metadata: Metadata = {
  title: "信息流",
};

export default function FeedPage() {
  return <FeedBrowser items={getItems()} />;
}
