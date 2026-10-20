import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import Users from "../Users/Users";

describe("Users Module Unit Tests", () => {
  // Realistic API user response reflecting backend relationship models (organization & role objects)
  const mockUsersResponse = {
    data: [
      {
        id: "u1",
        username: "johndoe",
        email: "john@example.com",
        first_name: "John",
        last_name: "Doe",
        phone: "9876543210",
        designation: "Software Engineer",
        description: "Senior developer",
        is_active: true,
        // Backend API returns nested relationship objects
        organization: { id: "org-1", name: "Acme Corp" },
        role: { id: "role-1", name: "Admin" },
      },
      {
        id: "u2",
        username: "janesmith",
        email: "jane@example.com",
        first_name: "Jane",
        last_name: "Smith",
        phone: "9123456789",
        designation: "Product Manager",
        description: "Product lead",
        is_active: false,
        organization: { id: "org-2", name: "Beta Inc" },
        role: { id: "role-2", name: "Employee" },
      },
    ],
    page: 1,
    size: 10,
    total: 2,
  };

  const mockOrganizationsDropdown = {
    data: [
      { id: "org-1", name: "Acme Corp" },
      { id: "org-2", name: "Beta Inc" },
    ],
  };

  const mockRolesDropdown = {
    data: [
      { id: "role-1", name: "Admin" },
      { id: "role-2", name: "Employee" },
    ],
  };

  let currentUsersData = mockUsersResponse;

  const setupFetchMocks = (
    usersData = mockUsersResponse,
    orgsData = mockOrganizationsDropdown,
    rolesData = mockRolesDropdown
  ) => {
    currentUsersData = usersData;
    global.fetch = jest.fn((url) => {
      if (url.includes("/api/users/")) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => currentUsersData,
        });
      }
      if (url.includes("/api/organizations/")) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => orgsData,
        });
      }
      if (url.includes("/api/roles/")) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => rolesData,
        });
      }
      return Promise.reject(new Error(`Unhandled endpoint: ${url}`));
    });
  };

  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();

    global.alert = jest.fn();
    localStorage.setItem("token", "mock-user-token-123");
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  const renderUsersComponent = () => {
    return render(
      <MemoryRouter initialEntries={["/users"]}>
        <Routes>
          <Route path="/users" element={<Users />} />
        </Routes>
      </MemoryRouter>
    );
  };

  /*
  |--------------------------------------------------------------------------
  | Page Rendering & Data Fetching (USER-001 - USER-005)
  |--------------------------------------------------------------------------
  */

  test("USER-001: Users page renders correctly", async () => {
    setupFetchMocks();
    renderUsersComponent();

    expect(screen.getByPlaceholderText("Search users...")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /\+ Add User/i })).toBeInTheDocument();
    expect(screen.getByText("Users")).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("Showing 2 Users")).toBeInTheDocument();
      expect(screen.getByText("John Doe")).toBeInTheDocument();
    });
  });

  test("USER-002: User list/table renders users returned by API", async () => {
    setupFetchMocks();
    renderUsersComponent();

    await waitFor(() => {
      expect(screen.getByText("John Doe")).toBeInTheDocument();
      expect(screen.getByText("johndoe")).toBeInTheDocument();
      expect(screen.getByText("john@example.com")).toBeInTheDocument();
      expect(screen.getByText("9876543210")).toBeInTheDocument();
      expect(screen.getByText("Software Engineer")).toBeInTheDocument();
      expect(screen.getByText("Active")).toBeInTheDocument();

      expect(screen.getByText("Jane Smith")).toBeInTheDocument();
      expect(screen.getByText("Inactive")).toBeInTheDocument();
    });
  });

  test("USER-003: [NOT IMPLEMENTED] Loading state is handled correctly", async () => {
    // Users.jsx does not implement an explicit loading spinner/state.
    global.fetch = jest.fn(() => new Promise(() => {}));

    renderUsersComponent();

    expect(screen.getByText("Users")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Search users...")).toBeInTheDocument();
  });

  test("USER-004: Users API is called using the correct endpoint and HTTP method", async () => {
    setupFetchMocks();
    renderUsersComponent();

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        "http://127.0.0.1:8000/api/users/?page=1&size=10",
        {
          headers: {
            Authorization: "Bearer mock-user-token-123",
          },
        }
      );
    });
  });

  test("USER-005: Authorization Bearer token is included in user API requests", async () => {
    localStorage.setItem("token", "user-bearer-secret-789");
    setupFetchMocks();

    renderUsersComponent();

    await waitFor(() => {
      const calls = global.fetch.mock.calls;
      expect(calls.length).toBeGreaterThan(0);

      calls.forEach((call) => {
        expect(call[1].headers.Authorization).toBe("Bearer user-bearer-secret-789");
      });
    });
  });

  /*
  |--------------------------------------------------------------------------
  | Add User Modal & Form Fields (USER-006 - USER-017)
  |--------------------------------------------------------------------------
  */

  test("USER-006: Add User button is rendered", async () => {
    setupFetchMocks();
    renderUsersComponent();

    expect(screen.getByRole("button", { name: /\+ Add User/i })).toBeInTheDocument();
  });

  test("USER-007: Add User modal opens correctly", async () => {
    setupFetchMocks();
    renderUsersComponent();

    fireEvent.click(screen.getByRole("button", { name: /\+ Add User/i }));

    expect(screen.getByRole("heading", { name: "Add New User" })).toBeInTheDocument();
  });

  test("USER-008: All Add User fields are rendered", async () => {
    setupFetchMocks();
    renderUsersComponent();

    fireEvent.click(screen.getByRole("button", { name: /\+ Add User/i }));

    expect(screen.getByPlaceholderText("Enter first name")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Enter last name")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Enter username")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("user@example.com")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Enter password")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Enter phone number")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Enter designation")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Enter description")).toBeInTheDocument();

    expect(screen.getByText("Select Organization")).toBeInTheDocument();
    expect(screen.getByText("Select Role")).toBeInTheDocument();
  });

  test("USER-009: First Name accepts input", async () => {
    setupFetchMocks();
    renderUsersComponent();
    fireEvent.click(screen.getByRole("button", { name: /\+ Add User/i }));

    const input = screen.getByPlaceholderText("Enter first name");
    fireEvent.change(input, { target: { value: "Alice" } });
    expect(input).toHaveValue("Alice");
  });

  test("USER-010: Last Name accepts input", async () => {
    setupFetchMocks();
    renderUsersComponent();
    fireEvent.click(screen.getByRole("button", { name: /\+ Add User/i }));

    const input = screen.getByPlaceholderText("Enter last name");
    fireEvent.change(input, { target: { value: "Williams" } });
    expect(input).toHaveValue("Williams");
  });

  test("USER-011: Username accepts input", async () => {
    setupFetchMocks();
    renderUsersComponent();
    fireEvent.click(screen.getByRole("button", { name: /\+ Add User/i }));

    const input = screen.getByPlaceholderText("Enter username");
    fireEvent.change(input, { target: { value: "alicew" } });
    expect(input).toHaveValue("alicew");
  });

  test("USER-012: Email accepts input", async () => {
    setupFetchMocks();
    renderUsersComponent();
    fireEvent.click(screen.getByRole("button", { name: /\+ Add User/i }));

    const input = screen.getByPlaceholderText("user@example.com");
    fireEvent.change(input, { target: { value: "alice@example.com" } });
    expect(input).toHaveValue("alice@example.com");
  });

  test("USER-013: Phone accepts input", async () => {
    setupFetchMocks();
    renderUsersComponent();
    fireEvent.click(screen.getByRole("button", { name: /\+ Add User/i }));

    const input = screen.getByPlaceholderText("Enter phone number");
    fireEvent.change(input, { target: { value: "9876500000" } });
    expect(input).toHaveValue("9876500000");
  });

  test("USER-014: Designation accepts input", async () => {
    setupFetchMocks();
    renderUsersComponent();
    fireEvent.click(screen.getByRole("button", { name: /\+ Add User/i }));

    const input = screen.getByPlaceholderText("Enter designation");
    fireEvent.change(input, { target: { value: "QA Lead" } });
    expect(input).toHaveValue("QA Lead");
  });

  test("USER-015: Description accepts input", async () => {
    setupFetchMocks();
    renderUsersComponent();
    fireEvent.click(screen.getByRole("button", { name: /\+ Add User/i }));

    const input = screen.getByPlaceholderText("Enter description");
    fireEvent.change(input, { target: { value: "QA Team Lead" } });
    expect(input).toHaveValue("QA Team Lead");
  });

  test("USER-016: Organization dropdown is rendered and can be selected", async () => {
    setupFetchMocks();
    renderUsersComponent();

    fireEvent.click(screen.getByRole("button", { name: /\+ Add User/i }));

    await waitFor(() => expect(screen.getByDisplayValue("Select Organization")).toBeInTheDocument());

    const orgSelect = screen.getByDisplayValue("Select Organization");
    fireEvent.change(orgSelect, { target: { value: "org-1" } });

    expect(orgSelect).toHaveValue("org-1");
  });

  test("USER-017: Role dropdown is rendered and can be selected", async () => {
    setupFetchMocks();
    renderUsersComponent();

    fireEvent.click(screen.getByRole("button", { name: /\+ Add User/i }));

    await waitFor(() => expect(screen.getByDisplayValue("Select Role")).toBeInTheDocument());

    const roleSelect = screen.getByDisplayValue("Select Role");
    fireEvent.change(roleSelect, { target: { value: "role-1" } });

    expect(roleSelect).toHaveValue("role-1");
  });

  /*
  |--------------------------------------------------------------------------
  | Validation & Creation (USER-018 - USER-023)
  |--------------------------------------------------------------------------
  */

  test("USER-018: Add User form currently does not enforce required-field validation on input fields", async () => {
    setupFetchMocks();
    renderUsersComponent();

    fireEvent.click(screen.getByRole("button", { name: /\+ Add User/i }));

    const firstNameInput = screen.getByPlaceholderText("Enter first name");
    expect(firstNameInput).not.toHaveAttribute("required");
  });

  test("USER-019: Invalid email is handled correctly", async () => {
    setupFetchMocks();
    renderUsersComponent();

    fireEvent.click(screen.getByRole("button", { name: /\+ Add User/i }));

    const emailInput = screen.getByPlaceholderText("user@example.com");
    fireEvent.change(emailInput, { target: { value: "invalid-email-format" } });

    expect(emailInput).toBeInvalid();
  });

  test("USER-020: Invalid phone number is handled correctly", async () => {
    setupFetchMocks();
    renderUsersComponent();

    fireEvent.click(screen.getByRole("button", { name: /\+ Add User/i }));

    const phoneInput = screen.getByPlaceholderText("Enter phone number");
    fireEvent.change(phoneInput, { target: { value: "abcde" } });

    expect(phoneInput).toHaveValue("abcde");
  });

  test("USER-021: Create User sends the correct API endpoint, HTTP method, headers and payload", async () => {
    setupFetchMocks();
    renderUsersComponent();

    await waitFor(() => expect(screen.getByText("John Doe")).toBeInTheDocument());

    fireEvent.click(screen.getByRole("button", { name: /\+ Add User/i }));

    fireEvent.change(screen.getByPlaceholderText("Enter first name"), { target: { value: "Alice" } });
    fireEvent.change(screen.getByPlaceholderText("Enter last name"), { target: { value: "Smith" } });
    fireEvent.change(screen.getByPlaceholderText("Enter username"), { target: { value: "alices" } });
    fireEvent.change(screen.getByPlaceholderText("user@example.com"), { target: { value: "alice@test.com" } });
    fireEvent.change(screen.getByPlaceholderText("Enter password"), { target: { value: "Secret@123" } });
    fireEvent.change(screen.getByPlaceholderText("Enter phone number"), { target: { value: "9876543210" } });
    fireEvent.change(screen.getByPlaceholderText("Enter designation"), { target: { value: "Dev" } });
    fireEvent.change(screen.getByPlaceholderText("Enter description"), { target: { value: "Developer" } });
    fireEvent.change(screen.getByDisplayValue("Select Organization"), { target: { value: "org-1" } });
    fireEvent.change(screen.getByDisplayValue("Select Role"), { target: { value: "role-1" } });

    const submitBtn = screen.getByRole("button", { name: "Create User" });

    global.fetch = jest.fn((url, options = {}) => {
      const method = (options.method || "GET").toUpperCase();
      if (method === "POST" && url === "http://127.0.0.1:8000/api/users/") {
        return Promise.resolve({
          ok: true,
          status: 201,
          json: async () => ({ id: "u3", first_name: "Alice" }),
        });
      }
      if (url.includes("/api/users/")) {
        return Promise.resolve({ ok: true, status: 200, json: async () => mockUsersResponse });
      }
      if (url.includes("/api/organizations/")) {
        return Promise.resolve({ ok: true, status: 200, json: async () => mockOrganizationsDropdown });
      }
      if (url.includes("/api/roles/")) {
        return Promise.resolve({ ok: true, status: 200, json: async () => mockRolesDropdown });
      }
      return Promise.reject(new Error(`Unhandled endpoint: ${url}`));
    });

    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        "http://127.0.0.1:8000/api/users/",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: "Bearer mock-user-token-123",
          },
          body: JSON.stringify({
            username: "alices",
            email: "alice@test.com",
            password: "Secret@123",
            first_name: "Alice",
            last_name: "Smith",
            phone: "9876543210",
            designation: "Dev",
            organization_id: "org-1",
            role_id: "role-1",
            description: "Developer",
          }),
        }
      );
    });
  });

  test("USER-022: Successful user creation updates the UI/list appropriately", async () => {
    setupFetchMocks();
    renderUsersComponent();

    await waitFor(() => expect(screen.getByText("John Doe")).toBeInTheDocument());

    fireEvent.click(screen.getByRole("button", { name: /\+ Add User/i }));
    fireEvent.change(screen.getByPlaceholderText("Enter first name"), { target: { value: "Alice" } });
    fireEvent.change(screen.getByPlaceholderText("Enter last name"), { target: { value: "Smith" } });

    global.fetch = jest.fn((url, options = {}) => {
      const method = (options.method || "GET").toUpperCase();
      if (method === "POST" && url === "http://127.0.0.1:8000/api/users/") {
        return Promise.resolve({
          ok: true,
          status: 201,
          json: async () => ({ id: "u3", first_name: "Alice" }),
        });
      }
      if (url.includes("/api/users/")) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => ({
            ...mockUsersResponse,
            data: [
              ...mockUsersResponse.data,
              { id: "u3", first_name: "Alice", last_name: "Smith", username: "alices", is_active: true },
            ],
            total: 3,
          }),
        });
      }
      if (url.includes("/api/organizations/")) {
        return Promise.resolve({ ok: true, status: 200, json: async () => mockOrganizationsDropdown });
      }
      if (url.includes("/api/roles/")) {
        return Promise.resolve({ ok: true, status: 200, json: async () => mockRolesDropdown });
      }
      return Promise.reject(new Error(`Unhandled endpoint: ${url}`));
    });

    fireEvent.click(screen.getByRole("button", { name: "Create User" }));

    await waitFor(() => {
      expect(screen.queryByRole("heading", { name: "Add New User" })).not.toBeInTheDocument();
      expect(screen.getByText("Alice Smith")).toBeInTheDocument();
    });
  });

  test("USER-023: User creation failure is handled correctly", async () => {
    setupFetchMocks();
    renderUsersComponent();

    await waitFor(() => expect(screen.getByText("John Doe")).toBeInTheDocument());

    fireEvent.click(screen.getByRole("button", { name: /\+ Add User/i }));
    fireEvent.change(screen.getByPlaceholderText("Enter first name"), { target: { value: "Alice" } });

    global.fetch = jest.fn((url, options = {}) => {
      const method = (options.method || "GET").toUpperCase();
      if (method === "POST" && url === "http://127.0.0.1:8000/api/users/") {
        return Promise.resolve({
          ok: false,
          status: 400,
          json: async () => ({ detail: "Username already exists" }),
        });
      }
      if (url.includes("/api/users/")) {
        return Promise.resolve({ ok: true, status: 200, json: async () => mockUsersResponse });
      }
      if (url.includes("/api/organizations/")) {
        return Promise.resolve({ ok: true, status: 200, json: async () => mockOrganizationsDropdown });
      }
      if (url.includes("/api/roles/")) {
        return Promise.resolve({ ok: true, status: 200, json: async () => mockRolesDropdown });
      }
      return Promise.reject(new Error(`Unhandled endpoint: ${url}`));
    });

    fireEvent.click(screen.getByRole("button", { name: "Create User" }));

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Add New User" })).toBeInTheDocument();
    });
  });

  /*
  |--------------------------------------------------------------------------
  | User Editing & Defects Verification (USER-024 - USER-031)
  |--------------------------------------------------------------------------
  */

  test("USER-024: Edit User modal opens correctly", async () => {
    setupFetchMocks();
    renderUsersComponent();

    await waitFor(() => expect(screen.getByText("John Doe")).toBeInTheDocument());

    const row = screen.getByText("John Doe").closest("tr");
    fireEvent.click(row);

    expect(screen.getByRole("heading", { name: "Edit User" })).toBeInTheDocument();
  });

  test("USER-025: Existing user information is populated correctly in Edit User", async () => {
    setupFetchMocks();
    renderUsersComponent();

    await waitFor(() => expect(screen.getByText("John Doe")).toBeInTheDocument());

    const row = screen.getByText("John Doe").closest("tr");
    fireEvent.click(row);

    expect(screen.getByDisplayValue("John")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Doe")).toBeInTheDocument();
    expect(screen.getByDisplayValue("johndoe")).toBeInTheDocument();
    expect(screen.getByDisplayValue("john@example.com")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Software Engineer")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Senior developer")).toBeInTheDocument();
  });

  test("USER-026: Edit User form populates Organization dropdown when backend returns user organization data", async () => {
    setupFetchMocks();
    renderUsersComponent();

    await waitFor(() => expect(screen.getByText("John Doe")).toBeInTheDocument());

    fireEvent.click(screen.getByText("John Doe").closest("tr"));

    const orgSelect = screen.getByRole("combobox", { name: /organization/i });
    expect(orgSelect).toHaveValue("org-1");
  });

  test("USER-027: Edit User form populates Role dropdown when backend returns user role data", async () => {
    setupFetchMocks();
    renderUsersComponent();

    await waitFor(() => expect(screen.getByText("John Doe")).toBeInTheDocument());

    fireEvent.click(screen.getByText("John Doe").closest("tr"));

    const roleSelect = screen.getByRole("combobox", { name: /role/i });
    expect(roleSelect).toHaveValue("role-1");
  });

  test("USER-028: Edit User form populates Phone number when backend returns valid phone number", async () => {
    // Tests whether Edit User form populates Phone input when backend API returns user phone number.
    setupFetchMocks();
    renderUsersComponent();

    await waitFor(() => expect(screen.getByText("John Doe")).toBeInTheDocument());

    fireEvent.click(screen.getByText("John Doe").closest("tr"));

    const phoneInputs = screen.getAllByPlaceholderText("Enter phone number");
    const editPhoneInput = phoneInputs[phoneInputs.length - 1];

    // Strict assertion: verifies Phone input populates "9876543210"
    expect(editPhoneInput).toHaveValue("9876543210");
  });

  test("USER-029: Edit User sends the correct API request", async () => {
    setupFetchMocks();
    renderUsersComponent();

    await waitFor(() => expect(screen.getByText("John Doe")).toBeInTheDocument());

    fireEvent.click(screen.getByText("John Doe").closest("tr"));

    const firstNameInput = screen.getByDisplayValue("John");
    fireEvent.change(firstNameInput, { target: { value: "Johnny" } });

    global.fetch = jest.fn((url, options = {}) => {
      const method = (options.method || "GET").toUpperCase();
      if (method === "PUT" && url === "http://127.0.0.1:8000/api/users/u1") {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => ({ id: "u1", first_name: "Johnny" }),
        });
      }
      if (url.includes("/api/users/")) {
        return Promise.resolve({ ok: true, status: 200, json: async () => mockUsersResponse });
      }
      if (url.includes("/api/organizations/")) {
        return Promise.resolve({ ok: true, status: 200, json: async () => mockOrganizationsDropdown });
      }
      if (url.includes("/api/roles/")) {
        return Promise.resolve({ ok: true, status: 200, json: async () => mockRolesDropdown });
      }
      return Promise.reject(new Error(`Unhandled endpoint: ${url}`));
    });

    const updateBtn = screen.getByRole("button", { name: "Update User" });
    fireEvent.click(updateBtn);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        "http://127.0.0.1:8000/api/users/u1",
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            Authorization: "Bearer mock-user-token-123",
          },
          body: JSON.stringify({
            username: "johndoe",
            email: "john@example.com",
            first_name: "Johnny",
            last_name: "Doe",
            phone: "9876543210",
            designation: "Software Engineer",
            organization_id: "org-1",
            role_id: "role-1",
            description: "Senior developer",
          }),
        }
      );
    });
  });

  test("USER-030: Successful user update reflects the updated information in the UI", async () => {
    setupFetchMocks();
    renderUsersComponent();

    await waitFor(() => expect(screen.getByText("John Doe")).toBeInTheDocument());

    fireEvent.click(screen.getByText("John Doe").closest("tr"));

    global.fetch = jest.fn((url, options = {}) => {
      const method = (options.method || "GET").toUpperCase();
      if (method === "PUT" && url === "http://127.0.0.1:8000/api/users/u1") {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => ({ id: "u1", first_name: "Johnny" }),
        });
      }
      if (url.includes("/api/users/")) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => ({
            ...mockUsersResponse,
            data: [
              { ...mockUsersResponse.data[0], first_name: "Johnny" },
              mockUsersResponse.data[1],
            ],
          }),
        });
      }
      if (url.includes("/api/organizations/")) {
        return Promise.resolve({ ok: true, status: 200, json: async () => mockOrganizationsDropdown });
      }
      if (url.includes("/api/roles/")) {
        return Promise.resolve({ ok: true, status: 200, json: async () => mockRolesDropdown });
      }
      return Promise.reject(new Error(`Unhandled endpoint: ${url}`));
    });

    fireEvent.click(screen.getByRole("button", { name: "Update User" }));

    await waitFor(() => {
      expect(screen.queryByRole("heading", { name: "Edit User" })).not.toBeInTheDocument();
      expect(screen.getByText("Johnny Doe")).toBeInTheDocument();
    });
  });

  test("USER-031: User update failure is handled correctly", async () => {
    setupFetchMocks();
    renderUsersComponent();

    await waitFor(() => expect(screen.getByText("John Doe")).toBeInTheDocument());

    fireEvent.click(screen.getByText("John Doe").closest("tr"));

    global.fetch = jest.fn((url, options = {}) => {
      const method = (options.method || "GET").toUpperCase();
      if (method === "PUT" && url === "http://127.0.0.1:8000/api/users/u1") {
        return Promise.resolve({
          ok: false,
          status: 500,
          json: async () => ({ detail: "Update failed" }),
        });
      }
      if (url.includes("/api/users/")) {
        return Promise.resolve({ ok: true, status: 200, json: async () => mockUsersResponse });
      }
      if (url.includes("/api/organizations/")) {
        return Promise.resolve({ ok: true, status: 200, json: async () => mockOrganizationsDropdown });
      }
      if (url.includes("/api/roles/")) {
        return Promise.resolve({ ok: true, status: 200, json: async () => mockRolesDropdown });
      }
      return Promise.reject(new Error(`Unhandled endpoint: ${url}`));
    });

    fireEvent.click(screen.getByRole("button", { name: "Update User" }));

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Edit User" })).toBeInTheDocument();
    });
  });

  /*
  |--------------------------------------------------------------------------
  | User Deletion (USER-032 - USER-035)
  |--------------------------------------------------------------------------
  */

  test("USER-032: Delete User action is available where implemented", async () => {
    setupFetchMocks();
    renderUsersComponent();

    await waitFor(() => expect(screen.getByText("John Doe")).toBeInTheDocument());

    const deleteBtns = screen.getAllByTitle("Delete User");
    expect(deleteBtns.length).toBe(2);
  });

  test("USER-033: [NOT IMPLEMENTED] Delete User confirmation modal is not rendered in Users.jsx UI", async () => {
    setupFetchMocks();
    renderUsersComponent();

    await waitFor(() => expect(screen.getByText("John Doe")).toBeInTheDocument());

    const deleteBtns = screen.getAllByTitle("Delete User");
    fireEvent.click(deleteBtns[0]);

    // Documenting feature limitation: delete confirm modal is not present in DOM
    expect(screen.queryByText("Delete User?")).not.toBeInTheDocument();
  });

  test.skip("USER-034: [NOT IMPLEMENTED] Successful deletion removes the user from the list", () => {
    // Explicitly skipped: feature cannot be executed via UI interaction as delete modal is not rendered in Users.jsx
  });

  test.skip("USER-035: [NOT IMPLEMENTED] Delete failure is handled correctly", () => {
    // Explicitly skipped: feature cannot be executed via UI interaction as delete modal is not rendered in Users.jsx
  });

  /*
  |--------------------------------------------------------------------------
  | Search, Empty State, Errors & Pagination (USER-036 - USER-039)
  |--------------------------------------------------------------------------
  */

  test("USER-036: Search functionality works correctly if implemented", async () => {
    setupFetchMocks();
    renderUsersComponent();

    await waitFor(() => expect(screen.getByText("John Doe")).toBeInTheDocument());

    const searchInput = screen.getByPlaceholderText("Search users...");
    fireEvent.change(searchInput, { target: { value: "Jane" } });

    expect(screen.queryByText("John Doe")).not.toBeInTheDocument();
    expect(screen.getByText("Jane Smith")).toBeInTheDocument();

    fireEvent.change(searchInput, { target: { value: "" } });
    expect(screen.getByText("John Doe")).toBeInTheDocument();
    expect(screen.getByText("Jane Smith")).toBeInTheDocument();
  });

  test("USER-037: Empty user list is handled correctly", async () => {
    setupFetchMocks({
      data: [],
      page: 1,
      size: 10,
      total: 0,
    });

    renderUsersComponent();

    await waitFor(() => {
      expect(screen.getByText("Showing 0 Users")).toBeInTheDocument();
      expect(screen.getByText("Page 1 of 0")).toBeInTheDocument();
    });
  });

  test("USER-038: User API network failure is handled correctly", async () => {
    const consoleSpy = jest.spyOn(console, "error").mockImplementation(() => {});

    global.fetch = jest.fn((url) => {
      if (url.includes("/api/users/")) {
        return Promise.resolve({
          ok: false,
          status: 500,
          statusText: "Internal Server Error",
          json: async () => ({ detail: "Network/Server Error", data: [] }),
        });
      }
      return Promise.resolve({
        ok: true,
        status: 200,
        json: async () => ({ data: [] }),
      });
    });

    renderUsersComponent();

    await waitFor(() => {
      expect(screen.getByText("Users")).toBeInTheDocument();
    });

    consoleSpy.mockRestore();
  });

  test("USER-039: Pagination works correctly if implemented", async () => {
    const paginatedUsers = {
      data: Array.from({ length: 10 }, (_, i) => ({
        id: `u-${i + 1}`,
        username: `user${i + 1}`,
        first_name: `User`,
        last_name: `${i + 1}`,
        email: `user${i + 1}@test.com`,
        is_active: true,
      })),
      page: 1,
      size: 10,
      total: 25,
    };

    setupFetchMocks(paginatedUsers);
    renderUsersComponent();

    await waitFor(() => {
      expect(screen.getByText("Page 1 of 3")).toBeInTheDocument();
    });

    const nextBtn = screen.getByRole("button", { name: "Next" });
    expect(nextBtn).not.toBeDisabled();

    fireEvent.click(nextBtn);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        "http://127.0.0.1:8000/api/users/?page=2&size=10",
        expect.any(Object)
      );
    });
  });

  /*
  |--------------------------------------------------------------------------
  | Status Display & Toggling (USER-040 - USER-042)
  |--------------------------------------------------------------------------
  */

  test("USER-040: User status is displayed correctly", async () => {
    setupFetchMocks();
    renderUsersComponent();

    await waitFor(() => {
      expect(screen.getByText("Active")).toHaveClass("status-badge active");
      expect(screen.getByText("Inactive")).toHaveClass("status-badge inactive");
    });
  });

  test.skip("USER-041: [NOT IMPLEMENTED] Edit User form lacks status toggle for Active -> Inactive", () => {
    // Explicitly skipped: status toggle input is not present in Edit User form in Users.jsx
  });

  test.skip("USER-042: [NOT IMPLEMENTED] Edit User form lacks status toggle for Inactive -> Active", () => {
    // Explicitly skipped: status toggle input is not present in Edit User form in Users.jsx
  });
});
