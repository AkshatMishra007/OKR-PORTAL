import React from "react";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import Sidebar from "../Layout/Sidebar/Sidebar";

describe("Authorization - Session and Logout Suite", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();

    global.fetch = jest.fn();
    global.alert = jest.fn();
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  const renderSidebarWithRoutes = (initialEntries = ["/dashboard"]) => {
    return render(
      <MemoryRouter initialEntries={initialEntries}>
        <Routes>
          <Route path="/dashboard" element={<Sidebar />} />
          <Route
            path="/login"
            element={<div data-testid="login-page">Login Page</div>}
          />
          <Route
            path="/"
            element={<div data-testid="home-page">Home Landing Page</div>}
          />
        </Routes>
      </MemoryRouter>
    );
  };

  /*
  |--------------------------------------------------------------------------
  | Session Verification & Unauthenticated Redirects
  |--------------------------------------------------------------------------
  */

  test("AUTHZ-001: alerts and navigates to /login when token is missing", async () => {
    renderSidebarWithRoutes();

    await waitFor(() => {
      expect(global.alert).toHaveBeenCalledWith(
        "Your session has expired. Please log in again."
      );
    });

    expect(screen.getByTestId("login-page")).toBeInTheDocument();
    expect(global.fetch).not.toHaveBeenCalled();
  });

  test("AUTHZ-002: verifies authenticated user using /api/users/me endpoint", async () => {
    localStorage.setItem("token", "valid-access-token");

    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({
        id: "user-1",
        first_name: "John",
        last_name: "Doe",
        email: "john.doe@test.com",
      }),
    });

    renderSidebarWithRoutes();

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        "http://127.0.0.1:8000/api/users/me",
        {
          method: "GET",
          headers: {
            Accept: "application/json",
            Authorization: "Bearer valid-access-token",
          },
        }
      );
    });
  });

  test("AUTHZ-003: includes Bearer token in Authorization header", async () => {
    localStorage.setItem("token", "my-secret-bearer-token");

    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({
        id: "user-1",
        first_name: "Alice",
        last_name: "Smith",
      }),
    });

    renderSidebarWithRoutes();

    await waitFor(() => {
      const fetchCall = global.fetch.mock.calls[0];
      expect(fetchCall[1].headers.Authorization).toBe(
        "Bearer my-secret-bearer-token"
      );
    });
  });

  test("AUTHZ-004: displays user name and initials after successful session verification", async () => {
    localStorage.setItem("token", "valid-access-token");

    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({
        id: "user-100",
        first_name: "Jane",
        last_name: "Doe",
        email: "jane.doe@test.com",
      }),
    });

    renderSidebarWithRoutes();

    await waitFor(() => {
      expect(screen.getByText("Jane Doe")).toBeInTheDocument();
      expect(screen.getByText("JD")).toBeInTheDocument();
    });
  });

  /*
  |--------------------------------------------------------------------------
  | Unauthorized & Backend Error Handling
  |--------------------------------------------------------------------------
  */

  test("AUTHZ-005: removes token from localStorage when /users/me returns 401", async () => {
    localStorage.setItem("token", "expired-token");

    global.fetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
      json: async () => ({ detail: "Token expired" }),
    });

    renderSidebarWithRoutes();

    await waitFor(() => {
      expect(localStorage.getItem("token")).toBeNull();
    });

    expect(global.alert).toHaveBeenCalledWith(
      "Your session has expired. Please log in again."
    );
  });

  test("AUTHZ-006: navigates to /login when /users/me returns 401 status", async () => {
    localStorage.setItem("token", "expired-token");

    global.fetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
      json: async () => ({ detail: "Unauthorized" }),
    });

    renderSidebarWithRoutes();

    await waitFor(() => {
      expect(screen.getByTestId("login-page")).toBeInTheDocument();
    });
  });

  test("AUTHZ-007: handles 403 forbidden status by alerting and navigating to /login", async () => {
    localStorage.setItem("token", "forbidden-token");

    global.fetch.mockResolvedValueOnce({
      ok: false,
      status: 403,
      json: async () => ({ detail: "Forbidden resource" }),
    });

    renderSidebarWithRoutes();

    await waitFor(() => {
      expect(global.alert).toHaveBeenCalledWith(
        "Unable to verify your session."
      );
      expect(screen.getByTestId("login-page")).toBeInTheDocument();
    });
  });

  test("AUTHZ-008: handles 500 server error by alerting and navigating to /login", async () => {
    localStorage.setItem("token", "server-error-token");

    global.fetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: async () => ({ detail: "Internal Server Error" }),
    });

    renderSidebarWithRoutes();

    await waitFor(() => {
      expect(global.alert).toHaveBeenCalledWith(
        "Unable to verify your session."
      );
      expect(screen.getByTestId("login-page")).toBeInTheDocument();
    });
  });

  test("AUTHZ-009: handles network failure during session verification", async () => {
    localStorage.setItem("token", "valid-token");

    global.fetch.mockRejectedValueOnce(new Error("Network disconnect"));

    renderSidebarWithRoutes();

    await waitFor(() => {
      expect(global.alert).toHaveBeenCalledWith(
        "Unable to verify your session."
      );
      expect(screen.getByTestId("login-page")).toBeInTheDocument();
    });
  });

  /*
  |--------------------------------------------------------------------------
  | Logout Functionality
  |--------------------------------------------------------------------------
  */

  test("AUTHZ-010: renders Logout button for authenticated session", async () => {
    localStorage.setItem("token", "active-token");

    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({
        id: "user-1",
        first_name: "Active",
        last_name: "User",
      }),
    });

    renderSidebarWithRoutes();

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /logout/i })
      ).toBeInTheDocument();
    });
  });

  test("AUTHZ-011: logout removes access token from localStorage", async () => {
    localStorage.setItem("token", "access-token-123");
    localStorage.setItem("refresh_token", "refresh-token-456");

    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ id: "user-1", first_name: "User" }),
    });

    renderSidebarWithRoutes();

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /logout/i })
      ).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: /logout/i }));

    expect(localStorage.getItem("token")).toBeNull();
  });

  test("AUTHZ-012: logout removes refresh token from localStorage", async () => {
    localStorage.setItem("token", "access-token-123");
    localStorage.setItem("refresh_token", "refresh-token-456");

    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ id: "user-1", first_name: "User" }),
    });

    renderSidebarWithRoutes();

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /logout/i })
      ).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: /logout/i }));

    expect(localStorage.getItem("refresh_token")).toBeNull();
  });

  test("AUTHZ-013: logout removes both access and refresh tokens simultaneously", async () => {
    localStorage.setItem("token", "access-token-123");
    localStorage.setItem("refresh_token", "refresh-token-456");

    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ id: "user-1", first_name: "User" }),
    });

    renderSidebarWithRoutes();

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /logout/i })
      ).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: /logout/i }));

    expect(localStorage.getItem("token")).toBeNull();
    expect(localStorage.getItem("refresh_token")).toBeNull();
  });

  test("AUTHZ-014: logout navigates to / route and renders Home target", async () => {
    localStorage.setItem("token", "access-token-123");

    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ id: "user-1", first_name: "User" }),
    });

    renderSidebarWithRoutes();

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /logout/i })
      ).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: /logout/i }));

    expect(screen.getByTestId("home-page")).toBeInTheDocument();
  });

  test("AUTHZ-015: logout does not trigger any additional backend API calls", async () => {
    localStorage.setItem("token", "access-token-123");

    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ id: "user-1", first_name: "User" }),
    });

    renderSidebarWithRoutes();

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledTimes(1);
    });

    fireEvent.click(screen.getByRole("button", { name: /logout/i }));

    expect(global.fetch).toHaveBeenCalledTimes(1);
  });

  test("AUTHZ-016: logout succeeds when only one token exists in localStorage", async () => {
    localStorage.setItem("token", "single-access-token");

    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ id: "user-1", first_name: "User" }),
    });

    renderSidebarWithRoutes();

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /logout/i })
      ).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: /logout/i }));

    expect(localStorage.getItem("token")).toBeNull();
    expect(localStorage.getItem("refresh_token")).toBeNull();
    expect(screen.getByTestId("home-page")).toBeInTheDocument();
  });

  test("AUTHZ-017: handles 404 status from /users/me by alerting and navigating to /login", async () => {
    localStorage.setItem("token", "not-found-token");

    global.fetch.mockResolvedValueOnce({
      ok: false,
      status: 404,
      json: async () => ({ detail: "User not found" }),
    });

    renderSidebarWithRoutes();

    await waitFor(() => {
      expect(global.alert).toHaveBeenCalledWith(
        "Unable to verify your session."
      );
      expect(screen.getByTestId("login-page")).toBeInTheDocument();
    });
  });

  test("AUTHZ-018: handles malformed non-JSON response from /users/me gracefully", async () => {
    localStorage.setItem("token", "valid-token");

    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => {
        throw new Error("Invalid JSON body");
      },
    });

    renderSidebarWithRoutes();

    await waitFor(() => {
      expect(global.alert).toHaveBeenCalledWith(
        "Unable to verify your session."
      );
      expect(screen.getByTestId("login-page")).toBeInTheDocument();
    });
  });

  test("AUTHZ-019: redirects to /login when refresh_token exists but access_token is missing", async () => {
    localStorage.setItem("refresh_token", "only-refresh-token");

    renderSidebarWithRoutes();

    await waitFor(() => {
      expect(global.alert).toHaveBeenCalledWith(
        "Your session has expired. Please log in again."
      );
      expect(screen.getByTestId("login-page")).toBeInTheDocument();
    });

    expect(global.fetch).not.toHaveBeenCalled();
  });

  test("AUTHZ-020: renders profile safely when user object is missing first_name or last_name", async () => {
    localStorage.setItem("token", "valid-token");

    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({
        id: "user-101",
        email: "no.name@test.com",
      }),
    });

    renderSidebarWithRoutes();

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledTimes(1);
    });

    // getUserInitials() should return "" safely when first_name & last_name are missing
    // Sidebar should render without crashing
    expect(screen.getByRole("button", { name: /logout/i })).toBeInTheDocument();
  });
});
