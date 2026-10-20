import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import Login from "../Login/Login";
import { API_URL } from "../Config/ApiEndpoint";

describe("Authentication - Login Suite", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();

    global.fetch = jest.fn();
    global.alert = jest.fn();
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  const renderLoginWithRoutes = () => {
    return render(
      <MemoryRouter initialEntries={["/"]}>
        <Routes>
          <Route path="/" element={<Login />} />
          <Route
            path="/my-okr"
            element={<div data-testid="my-okr-page">My OKR Dashboard</div>}
          />
        </Routes>
      </MemoryRouter>
    );
  };

  /*
  |--------------------------------------------------------------------------
  | UI & Form Elements Rendering
  |--------------------------------------------------------------------------
  */

  test("AUTH-001: renders login page UI elements correctly", () => {
    renderLoginWithRoutes();

    expect(screen.getByText("OKR")).toBeInTheDocument();
    expect(screen.getByText("Portal")).toBeInTheDocument();
    expect(
      screen.getByText("Objectives & Key Results Platform")
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Username/Email")).toBeInTheDocument();
    expect(screen.getByLabelText("Password")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Sign In" })
    ).toBeInTheDocument();
    expect(screen.getByText("Reset here")).toBeInTheDocument();
  });

  test("AUTH-002: password input field uses type='password'", () => {
    renderLoginWithRoutes();

    const passwordInput = screen.getByLabelText("Password");
    expect(passwordInput).toHaveAttribute("type", "password");
  });

  test("AUTH-003: accepts username/email input", () => {
    renderLoginWithRoutes();

    const usernameInput = screen.getByLabelText("Username/Email");
    fireEvent.change(usernameInput, {
      target: { value: "employee@test.com" },
    });

    expect(usernameInput).toHaveValue("employee@test.com");
  });

  test("AUTH-004: accepts password input", () => {
    renderLoginWithRoutes();

    const passwordInput = screen.getByLabelText("Password");
    fireEvent.change(passwordInput, {
      target: { value: "Password@123" },
    });

    expect(passwordInput).toHaveValue("Password@123");
  });

  test("AUTH-005: username/email field is required", () => {
    renderLoginWithRoutes();

    const usernameInput = screen.getByLabelText("Username/Email");
    fireEvent.change(screen.getByLabelText("Password"), {
      target: { value: "Password@123" },
    });

    expect(usernameInput).toBeInvalid();
  });

  test("AUTH-006: password field is required", () => {
    renderLoginWithRoutes();

    const passwordInput = screen.getByLabelText("Password");
    fireEvent.change(screen.getByLabelText("Username/Email"), {
      target: { value: "employee@test.com" },
    });

    expect(passwordInput).toBeInvalid();
  });

  /*
  |--------------------------------------------------------------------------
  | API Payload & Submission Behavior
  |--------------------------------------------------------------------------
  */

  test("AUTH-007: sends correct credentials to login API", async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({
        access_token: "mock-access-token",
        refresh_token: "mock-refresh-token",
      }),
    });

    renderLoginWithRoutes();

    fireEvent.change(screen.getByLabelText("Username/Email"), {
      target: { value: "employee@test.com" },
    });

    fireEvent.change(screen.getByLabelText("Password"), {
      target: { value: "Password@123" },
    });

    fireEvent.click(screen.getByRole("button", { name: "Sign In" }));

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        `${API_URL}/api/auth/login`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Accept: "application/json",
          },
          body: JSON.stringify({
            username_or_email: "employee@test.com",
            password: "Password@123",
          }),
        }
      );
    });
  });

  test("AUTH-008: form submission triggers exactly one API request", async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({
        access_token: "mock-access-token",
        refresh_token: "mock-refresh-token",
      }),
    });

    renderLoginWithRoutes();

    fireEvent.change(screen.getByLabelText("Username/Email"), {
      target: { value: "employee@test.com" },
    });

    fireEvent.change(screen.getByLabelText("Password"), {
      target: { value: "Password@123" },
    });

    fireEvent.click(screen.getByRole("button", { name: "Sign In" }));

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledTimes(1);
    });
  });

  /*
  |--------------------------------------------------------------------------
  | Successful Authentication & Navigation
  |--------------------------------------------------------------------------
  */

  test("AUTH-009: stores access token after successful login", async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({
        access_token: "valid-access-token",
        refresh_token: "valid-refresh-token",
      }),
    });

    renderLoginWithRoutes();

    fireEvent.change(screen.getByLabelText("Username/Email"), {
      target: { value: "employee@test.com" },
    });

    fireEvent.change(screen.getByLabelText("Password"), {
      target: { value: "Password@123" },
    });

    fireEvent.click(screen.getByRole("button", { name: "Sign In" }));

    await waitFor(() => {
      expect(localStorage.getItem("token")).toBe("valid-access-token");
    });
  });

  test("AUTH-010: stores refresh token after successful login", async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({
        access_token: "valid-access-token",
        refresh_token: "valid-refresh-token",
      }),
    });

    renderLoginWithRoutes();

    fireEvent.change(screen.getByLabelText("Username/Email"), {
      target: { value: "employee@test.com" },
    });

    fireEvent.change(screen.getByLabelText("Password"), {
      target: { value: "Password@123" },
    });

    fireEvent.click(screen.getByRole("button", { name: "Sign In" }));

    await waitFor(() => {
      expect(localStorage.getItem("refresh_token")).toBe(
        "valid-refresh-token"
      );
    });
  });

  test("AUTH-011: replaces pre-existing tokens with new tokens on login", async () => {
    localStorage.setItem("token", "old-access-token");
    localStorage.setItem("refresh_token", "old-refresh-token");

    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({
        access_token: "new-access-token",
        refresh_token: "new-refresh-token",
      }),
    });

    renderLoginWithRoutes();

    fireEvent.change(screen.getByLabelText("Username/Email"), {
      target: { value: "employee@test.com" },
    });

    fireEvent.change(screen.getByLabelText("Password"), {
      target: { value: "Password@123" },
    });

    fireEvent.click(screen.getByRole("button", { name: "Sign In" }));

    await waitFor(() => {
      expect(localStorage.getItem("token")).toBe("new-access-token");
      expect(localStorage.getItem("refresh_token")).toBe("new-refresh-token");
    });
  });

  test("AUTH-012: navigates to /my-okr route on successful login", async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({
        access_token: "valid-access-token",
        refresh_token: "valid-refresh-token",
      }),
    });

    renderLoginWithRoutes();

    fireEvent.change(screen.getByLabelText("Username/Email"), {
      target: { value: "employee@test.com" },
    });

    fireEvent.change(screen.getByLabelText("Password"), {
      target: { value: "Password@123" },
    });

    fireEvent.click(screen.getByRole("button", { name: "Sign In" }));

    await waitFor(() => {
      expect(screen.getByTestId("my-okr-page")).toBeInTheDocument();
    });
  });

  test("AUTH-013: does not display alert message on successful login", async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({
        access_token: "valid-access-token",
        refresh_token: "valid-refresh-token",
      }),
    });

    renderLoginWithRoutes();

    fireEvent.change(screen.getByLabelText("Username/Email"), {
      target: { value: "employee@test.com" },
    });

    fireEvent.change(screen.getByLabelText("Password"), {
      target: { value: "Password@123" },
    });

    fireEvent.click(screen.getByRole("button", { name: "Sign In" }));

    await waitFor(() => {
      expect(screen.getByTestId("my-okr-page")).toBeInTheDocument();
    });

    expect(global.alert).not.toHaveBeenCalled();
  });

  /*
  |--------------------------------------------------------------------------
  | Error Handling & Failed Authentication
  |--------------------------------------------------------------------------
  */

  test("AUTH-014: displays error alert on 401 unauthorized response", async () => {
    global.fetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
      json: async () => ({ detail: "Invalid credentials" }),
    });

    renderLoginWithRoutes();

    fireEvent.change(screen.getByLabelText("Username/Email"), {
      target: { value: "wrong@test.com" },
    });

    fireEvent.change(screen.getByLabelText("Password"), {
      target: { value: "WrongPassword" },
    });

    fireEvent.click(screen.getByRole("button", { name: "Sign In" }));

    await waitFor(() => {
      expect(global.alert).toHaveBeenCalledWith(
        "Invalid email or password"
      );
    });
  });

  test("AUTH-015: displays error alert on 400 bad request response", async () => {
    global.fetch.mockResolvedValueOnce({
      ok: false,
      status: 400,
      json: async () => ({ detail: "Bad request payload" }),
    });

    renderLoginWithRoutes();

    fireEvent.change(screen.getByLabelText("Username/Email"), {
      target: { value: "badrequest@test.com" },
    });

    fireEvent.change(screen.getByLabelText("Password"), {
      target: { value: "Password@123" },
    });

    fireEvent.click(screen.getByRole("button", { name: "Sign In" }));

    await waitFor(() => {
      expect(global.alert).toHaveBeenCalledWith(
        "Invalid email or password"
      );
    });
  });

  test("AUTH-016: displays error alert on 500 server error response", async () => {
    global.fetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: async () => ({ detail: "Internal server error" }),
    });

    renderLoginWithRoutes();

    fireEvent.change(screen.getByLabelText("Username/Email"), {
      target: { value: "employee@test.com" },
    });

    fireEvent.change(screen.getByLabelText("Password"), {
      target: { value: "Password@123" },
    });

    fireEvent.click(screen.getByRole("button", { name: "Sign In" }));

    await waitFor(() => {
      expect(global.alert).toHaveBeenCalledWith(
        "Invalid email or password"
      );
    });
  });

  test("AUTH-017: displays error alert when response is missing access_token", async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ message: "Login successful without token" }),
    });

    renderLoginWithRoutes();

    fireEvent.change(screen.getByLabelText("Username/Email"), {
      target: { value: "employee@test.com" },
    });

    fireEvent.change(screen.getByLabelText("Password"), {
      target: { value: "Password@123" },
    });

    fireEvent.click(screen.getByRole("button", { name: "Sign In" }));

    await waitFor(() => {
      expect(global.alert).toHaveBeenCalledWith(
        "Invalid email or password"
      );
    });
  });

  test("AUTH-018: handles network failure during login attempt", async () => {
    global.fetch.mockRejectedValueOnce(new Error("Network connection error"));

    renderLoginWithRoutes();

    fireEvent.change(screen.getByLabelText("Username/Email"), {
      target: { value: "employee@test.com" },
    });

    fireEvent.change(screen.getByLabelText("Password"), {
      target: { value: "Password@123" },
    });

    fireEvent.click(screen.getByRole("button", { name: "Sign In" }));

    await waitFor(() => {
      expect(global.alert).toHaveBeenCalledWith(
        "Something went wrong while logging in"
      );
    });
  });

  test("AUTH-019: failed login does not store tokens or navigate", async () => {
    global.fetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
      json: async () => ({ detail: "Invalid credentials" }),
    });

    renderLoginWithRoutes();

    fireEvent.change(screen.getByLabelText("Username/Email"), {
      target: { value: "wrong@test.com" },
    });

    fireEvent.change(screen.getByLabelText("Password"), {
      target: { value: "WrongPassword" },
    });

    fireEvent.click(screen.getByRole("button", { name: "Sign In" }));

    await waitFor(() => {
      expect(global.alert).toHaveBeenCalled();
    });

    expect(localStorage.getItem("token")).toBeNull();
    expect(localStorage.getItem("refresh_token")).toBeNull();
    expect(screen.queryByTestId("my-okr-page")).not.toBeInTheDocument();
  });

  test("AUTH-020: handles successful response missing refresh_token safely", async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ access_token: "only-access-token" }),
    });

    renderLoginWithRoutes();

    fireEvent.change(screen.getByLabelText("Username/Email"), {
      target: { value: "employee@test.com" },
    });

    fireEvent.change(screen.getByLabelText("Password"), {
      target: { value: "Password@123" },
    });

    fireEvent.click(screen.getByRole("button", { name: "Sign In" }));

    await waitFor(() => {
      expect(localStorage.getItem("token")).toBe("only-access-token");
      expect(screen.getByTestId("my-okr-page")).toBeInTheDocument();
    });
  });

  test("AUTH-021: treats empty access_token in response as invalid login", async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ access_token: "" }),
    });

    renderLoginWithRoutes();

    fireEvent.change(screen.getByLabelText("Username/Email"), {
      target: { value: "employee@test.com" },
    });

    fireEvent.change(screen.getByLabelText("Password"), {
      target: { value: "Password@123" },
    });

    fireEvent.click(screen.getByRole("button", { name: "Sign In" }));

    await waitFor(() => {
      expect(global.alert).toHaveBeenCalledWith("Invalid email or password");
    });

    expect(screen.queryByTestId("my-okr-page")).not.toBeInTheDocument();
  });

  test("AUTH-022: handles malformed non-JSON backend response gracefully", async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => {
        throw new Error("Unexpected token < in JSON at position 0");
      },
    });

    renderLoginWithRoutes();

    fireEvent.change(screen.getByLabelText("Username/Email"), {
      target: { value: "employee@test.com" },
    });

    fireEvent.change(screen.getByLabelText("Password"), {
      target: { value: "Password@123" },
    });

    fireEvent.click(screen.getByRole("button", { name: "Sign In" }));

    await waitFor(() => {
      expect(global.alert).toHaveBeenCalledWith(
        "Something went wrong while logging in"
      );
    });
  });

  test("AUTH-023: existing valid tokens remain unchanged after a failed login attempt", async () => {
    localStorage.setItem("token", "existing-valid-access-token");
    localStorage.setItem("refresh_token", "existing-valid-refresh-token");

    global.fetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
      json: async () => ({ detail: "Invalid credentials" }),
    });

    renderLoginWithRoutes();

    fireEvent.change(screen.getByLabelText("Username/Email"), {
      target: { value: "wrong@test.com" },
    });

    fireEvent.change(screen.getByLabelText("Password"), {
      target: { value: "WrongPassword" },
    });

    fireEvent.click(screen.getByRole("button", { name: "Sign In" }));

    await waitFor(() => {
      expect(global.alert).toHaveBeenCalledWith("Invalid email or password");
    });

    expect(localStorage.getItem("token")).toBe("existing-valid-access-token");
    expect(localStorage.getItem("refresh_token")).toBe(
      "existing-valid-refresh-token"
    );
  });
});
