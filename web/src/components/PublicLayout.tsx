import { Outlet } from "react-router-dom";
import { Navbar } from "./Navbar.tsx";
import { Footer } from "./Footer.tsx";

export function PublicLayout() {
  return (
    <div className="flex min-h-screen flex-col">
      <Navbar />
      <main className="flex-1">
        <Outlet />
      </main>
      <Footer />
    </div>
  );
}
