import { redirect } from "next/navigation";

export default function Home() {
  // The dashboard layout guards auth client-side and bounces to /login.
  redirect("/dashboard");
}
