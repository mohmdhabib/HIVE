import { Outlet } from "react-router-dom";
import { Sidebar } from "./sidebar";
import { Topbar } from "./topbar";

export function Shell() {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="mx-auto w-full max-w-[1500px] px-10">
        <Topbar />
        <div className="py-6">
          <Outlet />
        </div>
        <footer className="pb-6 font-mono text-[8px] tracking-[1.1px] text-gray-600">
          HIVE <span className="mx-1.5 text-hive">·</span> AUTONOMOUS MEDIA NETWORK{" "}
          <span className="mx-1.5 text-hive">·</span> BUILD 0.1.0
        </footer>
      </main>
    </div>
  );
}
