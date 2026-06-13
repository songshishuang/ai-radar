import type { Metadata } from "next";
import SearchBrowser from "@/components/SearchBrowser";
import { getItems } from "@/lib/content";

export const metadata: Metadata = {
  title: "搜索",
};

export default function SearchPage() {
  return <SearchBrowser items={getItems()} />;
}
