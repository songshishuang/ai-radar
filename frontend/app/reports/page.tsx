import type { Metadata } from "next";
import ReportsBrowser from "@/components/ReportsBrowser";
import { getReports } from "@/lib/content";

export const metadata: Metadata = {
  title: "报告归档",
};

export default function ReportsPage() {
  return <ReportsBrowser reports={getReports()} />;
}
