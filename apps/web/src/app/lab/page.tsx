import { notFound } from "next/navigation";
import { connection } from "next/server";
import { isLabEnabled } from "@/server/lab";
import { LabClient } from "./lab-client";

export const metadata = { title: "Lab · GrahRekha" };

export default async function LabPage() {
  await connection(); // decide per request, not at build time
  if (!isLabEnabled()) notFound();
  return <LabClient />;
}
