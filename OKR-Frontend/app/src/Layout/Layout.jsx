import { useState } from "react";
import { Outlet } from "react-router-dom";
import { PanelLeftOpen } from "lucide-react";

import Sidebar from "./Sidebar/Sidebar";
import Header from "./Header/Header";
import "./Layout.css";

function Layout() {
  // Desktop/laptop starts open; mobile starts closed.
  const [sidebarOpen, setSidebarOpen] = useState(
    () => window.innerWidth > 768
  );

  const toggleSidebar = () => {
    setSidebarOpen((previous) => !previous);
  };

  return (
    <div className={`app-layout ${sidebarOpen ? "sidebar-open-layout" : "sidebar-closed-layout"}`}>
      <Sidebar
        isOpen={sidebarOpen}
        onMenuToggle={toggleSidebar}
      />

      <div className="main-area">
        <div className="topbar-wrapper">
          {!sidebarOpen && (
            <button
              className="sidebar-open-btn"
              onClick={toggleSidebar}
              aria-label="Open sidebar"
              title="Open sidebar"
            >
              <PanelLeftOpen size={18} strokeWidth={2} aria-hidden="true" />
            </button>
          )}

          <Header />
        </div>

        <main className="page-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

export default Layout;
