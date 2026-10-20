import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import "./Header.css";
import {
  Sun,
  Moon,
} from "lucide-react";
import "../../App.css";
function Header() {
  const navigate = useNavigate();

  const [theme, setTheme] = useState("dark");

  useEffect(() => {
    const savedTheme = localStorage.getItem("theme") || "dark";
   console.log("Saved theme from localStorage:", savedTheme);
    setTheme(savedTheme);

    if (savedTheme === "light") {
      console.log("Setting theme to light");
      document.documentElement.setAttribute("data-theme", "light");
    } else {
      console.log("Setting theme to dark");
      document.documentElement.removeAttribute("data-theme");
    }
  }, []);

  const toggleTheme = () => {
    console.log("button clicked");
    if (theme === "dark") {
      console.log("Switching to light theme");
      setTheme("light");
      document.documentElement.setAttribute("data-theme", "light");
      localStorage.setItem("theme", "light");
    } else {
      console.log("Switching to dark theme");
      setTheme("dark");
      document.documentElement.removeAttribute("data-theme");
      localStorage.setItem("theme", "dark");
    }
  };

  const handleLogout = () => {
    navigate("/");
  };

  return (
    <header className="topbar">
      <div className="topbar-left">
        <div className="page-title">
          OKR PORTAL
        </div>

        <div className="breadcrumb">
         
          <span>›</span>
          <span>Dashboard</span>
        </div>
      </div>

      <div className="topbar-right">
      
        <button
          className="topbar-btn"
          onClick={toggleTheme}
          title="Toggle Theme"
        >
{theme === "dark" ? (
    <Sun size={19} strokeWidth={2} />
  ) : (
    <Moon size={19} strokeWidth={2} />
  )}
        </button>

      
              </div>
    </header>
  );
}

export default Header;