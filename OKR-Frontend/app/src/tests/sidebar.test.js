import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import Sidebar from "../Layout/Sidebar/Sidebar";

const renderSidebar = (initialEntry = "/dashboard") => {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <Routes>
        <Route path="/" element={<div>Home Page</div>} />
        <Route path="/login" element={<div>Login Page</div>} />
        <Route path="/dashboard" element={<><Sidebar /><div>Dashboard Page</div></>} />
        <Route path="/my-okr" element={<><Sidebar /><div>My OKR Page</div></>} />
        <Route path="/team-okr" element={<><Sidebar /><div>Team OKR Page</div></>} />
        <Route path="/performance" element={<><Sidebar /><div>Performance Page</div></>} />
        <Route path="/leaderboard" element={<><Sidebar /><div>Leaderboard Page</div></>} />
        <Route path="/raise-query" element={<><Sidebar /><div>Raise Query Page</div></>} />
        <Route path="/organizations" element={<><Sidebar /><div>Organizations Page</div></>} />
        <Route path="/users" element={<><Sidebar /><div>Users Page</div></>} />
        <Route path="/roles" element={<><Sidebar /><div>Roles Page</div></>} />
        <Route path="/batches" element={<><Sidebar /><div>Batches Page</div></>} />
        <Route path="/manage-okr" element={<><Sidebar /><div>Manage OKR Page</div></>} />
        <Route path="*" element={<><Sidebar /><div>Fallback Page</div></>} />
      </Routes>
    </MemoryRouter>
  );
};

const mockUserProfile = (overrides = {}) => ({
  ok: true,
  status: 200,
  json: () => Promise.resolve({
    first_name: "John",
    last_name: "Doe",
    email: "john.doe@example.com",
    ...overrides,
  }),
});

const setValidSession = (overrides = {}) => {
  localStorage.setItem("token", "mock-token-456");
  global.fetch.mockResolvedValueOnce(mockUserProfile(overrides));
};

describe("Sidebar component", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
    global.alert = jest.fn();
    global.fetch = jest.fn();
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  test("SIDEBAR-001: Sidebar renders successfully", async () => {
    setValidSession();
    renderSidebar();

    expect(await screen.findByText("John Doe")).toBeInTheDocument();
    expect(screen.getByRole("navigation")).toBeInTheDocument();
    expect(screen.getByAltText("Logo")).toBeInTheDocument();
  });

  test("SIDEBAR-002: Navigation items render with the correct labels", async () => {
    setValidSession();
    renderSidebar();

    await screen.findByText("John Doe");

    [
      "Dashboard",
      "My OKR",
      "Team OKR",
      "Performance",
      "Leaderboard",
      "Raise Query",
      "Organizations",
      "Users",
      "Roles",
      "Batches",
      "Manage OKR",
    ].forEach((label) => {
      expect(screen.getByRole("link", { name: new RegExp(label, "i") })).toBeInTheDocument();
    });
  });

  test("SIDEBAR-003: Navigation links point to the correct routes", async () => {
    setValidSession();
    renderSidebar();

    await screen.findByText("John Doe");

    const expectedRoutes = {
      Dashboard: "/dashboard",
      "My OKR": "/my-okr",
      "Team OKR": "/team-okr",
      Performance: "/performance",
      Leaderboard: "/leaderboard",
      "Raise Query": "/raise-query",
      Organizations: "/organizations",
      Users: "/users",
      Roles: "/roles",
      Batches: "/batches",
      "Manage OKR": "/manage-okr",
    };

    Object.entries(expectedRoutes).forEach(([label, route]) => {
      expect(screen.getByRole("link", { name: new RegExp(label, "i") })).toHaveAttribute("href", route);
    });
  });

  test("SIDEBAR-004: Active navigation state works correctly", async () => {
    setValidSession();
    renderSidebar("/my-okr");

    await screen.findByText("My OKR Page");
    const activeLink = screen.getByRole("link", { name: /my okr/i });
    expect(activeLink).toHaveAttribute("aria-current", "page");
  });

  test("SIDEBAR-005: Sidebar navigation works using MemoryRouter", async () => {
    setValidSession();
    renderSidebar("/dashboard");

    await screen.findByText("John Doe");
    fireEvent.click(screen.getByRole("link", { name: /users/i }));

    expect(await screen.findByText("Users Page")).toBeInTheDocument();
  });

  test("SIDEBAR-006: User/profile section renders correctly", async () => {
    localStorage.setItem("token", "mock-token-456");
    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () => Promise.resolve({
        first_name: "John",
        last_name: "Doe",
        email: "john.doe@example.com",
        phone: "9876543210",
        designation: "Senior Engineer",
        description: "Product delivery lead",
      }),
    });

    renderSidebar();

    expect(await screen.findByText("John Doe")).toBeInTheDocument();
    expect(screen.getByText("SSDN Technologies")).toBeInTheDocument();
    expect(screen.getByText("JD")).toBeInTheDocument();
  });

  test("SIDEBAR-007: Current user/session API request is made on component mount", async () => {
    localStorage.setItem("token", "mock-token-456");
    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ first_name: "John", last_name: "Doe" }),
    });

    renderSidebar();

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        "http://127.0.0.1:8000/api/users/me",
        expect.objectContaining({
          method: "GET",
          headers: expect.objectContaining({
            Accept: "application/json",
            Authorization: "Bearer mock-token-456",
          }),
        })
      );
    });
  });

  test("SIDEBAR-008: Missing token behavior alerts and redirects to login", async () => {
    renderSidebar();

    await waitFor(() => {
      expect(global.alert).toHaveBeenCalledWith("Your session has expired. Please log in again.");
    });

    expect(await screen.findByText("Login Page")).toBeInTheDocument();
  });

  test("SIDEBAR-009: 401 response removes the token and redirects to login", async () => {
    localStorage.setItem("token", "expired-token");
    global.fetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
    });

    renderSidebar();

    await waitFor(() => {
      expect(localStorage.getItem("token")).toBeNull();
      expect(global.alert).toHaveBeenCalledWith("Your session has expired. Please log in again.");
    });

    expect(await screen.findByText("Login Page")).toBeInTheDocument();
  });

  test("SIDEBAR-010: Non-401 API errors are handled according to the current implementation", async () => {
    localStorage.setItem("token", "mock-token-500");
    global.fetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
    });

    renderSidebar();

    await waitFor(() => {
      expect(global.alert).toHaveBeenCalledWith("Unable to verify your session.");
    });

    expect(await screen.findByText("Login Page")).toBeInTheDocument();
  });

  test("SIDEBAR-011: Network failure is handled correctly", async () => {
    localStorage.setItem("token", "network-token");
    global.fetch.mockRejectedValueOnce(new Error("Network Error"));

    renderSidebar();

    await waitFor(() => {
      expect(global.alert).toHaveBeenCalledWith("Unable to verify your session.");
    });

    expect(await screen.findByText("Login Page")).toBeInTheDocument();
  });

  test("SIDEBAR-012: Profile dropdown menu opens when its control is clicked", async () => {
    localStorage.setItem("token", "mock-token-456");
    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () => Promise.resolve({
        first_name: "John",
        last_name: "Doe",
        email: "john.doe@example.com",
      }),
    });

    renderSidebar();

    expect(await screen.findByText("John Doe")).toBeInTheDocument();

    fireEvent.click(screen.getByText("John Doe"));

    expect(screen.getByText(/📞/i)).toBeInTheDocument();
    expect(screen.getByText(/✉️/i)).toBeInTheDocument();
  });

  test("SIDEBAR-013: Profile dropdown menu closes when appropriate and outside-click closes it", async () => {
    localStorage.setItem("token", "mock-token-456");
    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () => Promise.resolve({
        first_name: "John",
        last_name: "Doe",
        email: "john.doe@example.com",
        phone: "9876543210",
      }),
    });

    renderSidebar();

    fireEvent.click(await screen.findByText("John Doe"));
    expect(screen.getByText(/📞/i)).toBeInTheDocument();

    fireEvent.mouseDown(document.body);

    await waitFor(() => {
      expect(screen.queryByText(/📞/i)).not.toBeInTheDocument();
    });
  });

  test("SIDEBAR-014: Logout button is rendered and clears session data", async () => {
    localStorage.setItem("token", "mock-token-456");
    localStorage.setItem("refresh_token", "refresh-123");
    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ first_name: "John", last_name: "Doe" }),
    });

    renderSidebar();

    expect(await screen.findByRole("button", { name: /logout/i })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /logout/i }));

    expect(localStorage.getItem("token")).toBeNull();
    expect(localStorage.getItem("refresh_token")).toBeNull();
    expect(await screen.findByText("Home Page")).toBeInTheDocument();
  });

  test("SIDEBAR-015: Logout does not trigger an unnecessary backend request", async () => {
    localStorage.setItem("token", "mock-token-456");
    localStorage.setItem("refresh_token", "refresh-123");
    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ first_name: "John", last_name: "Doe" }),
    });

    renderSidebar();

    await waitFor(() => expect(global.fetch).toHaveBeenCalledTimes(1));

    fireEvent.click(screen.getByRole("button", { name: /logout/i }));

    expect(global.fetch).toHaveBeenCalledTimes(1);
  });

  test("SIDEBAR-016: Important sidebar UI text and controls are present", async () => {
    setValidSession();
    renderSidebar();

    expect(await screen.findByText("John Doe")).toBeInTheDocument();
    expect(screen.getByText("OKR Portal · Enterprise")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /logout/i })).toBeInTheDocument();
  });
});
