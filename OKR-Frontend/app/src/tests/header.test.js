import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import Header from "../Layout/Header/Header";

describe("Header component", () => {
  const renderHeader = (initialEntry = "/dashboard") => {
    return render(
      <MemoryRouter initialEntries={[initialEntry]}>
        <Routes>
          <Route path="/" element={<div>Home Page</div>} />
          <Route path="/dashboard" element={<Header />} />
          <Route path="*" element={<Header />} />
        </Routes>
      </MemoryRouter>
    );
  };

  beforeEach(() => {
    localStorage.clear();
    document.documentElement.removeAttribute("data-theme");
  });

  test("HEADER-001: Header renders successfully", () => {
    renderHeader();

    expect(screen.getByText("OKR PORTAL")).toBeInTheDocument();
    expect(screen.getByText("Dashboard")).toBeInTheDocument();
  });

  test("HEADER-002: Header title and cycle information are rendered correctly", () => {
    renderHeader();

    expect(screen.getByText("OKR PORTAL")).toBeInTheDocument();
    expect(screen.getByText("SSDN Technologies — AMJ 2026")).toBeInTheDocument();
    expect(screen.getByText("›")).toBeInTheDocument();
  });

  test("HEADER-003: Theme toggle renders and persists the selected theme", async () => {
    localStorage.setItem("theme", "light");

    renderHeader();

    expect(document.documentElement).toHaveAttribute("data-theme", "light");

    const toggleButton = screen.getByTitle("Toggle Theme");
    fireEvent.click(toggleButton);

    await waitFor(() => {
      expect(localStorage.getItem("theme")).toBe("dark");
      expect(document.documentElement).not.toHaveAttribute("data-theme");
    });
  });

  test("HEADER-004: Toggle button exists and is the implemented theme control", () => {
    renderHeader();

    expect(screen.getByTitle("Toggle Theme")).toBeInTheDocument();
    expect(document.querySelectorAll(".topbar-btn").length).toBeGreaterThanOrEqual(2);
  });
});
