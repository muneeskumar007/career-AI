import { Outlet } from "react-router-dom";
import Navbar from "@/components/layout/Navbar";

export default function DashboardLayout() {
  return (
    <div className="min-h-screen bg-ink">
      <Navbar />
      <main className="mx-auto max-w-6xl px-6 py-8">
        <Outlet />
      </main>
    </div>
  );
}
