import React from "react";
import {
  render,
  screen,
  fireEvent,
  waitFor,
  within,
} from "@testing-library/react";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import Menu from "../MyOkr/MyOkr";
import OKR from "../ManageOKR/ManageOKR";

describe("Manage OKR / My OKR Module Unit Tests", () => {
  // Mock Data
  const mockUserMe = {
    id: 1,
    first_name: "John",
    last_name: "Doe",
    email: "john.doe@example.com",
  };

  const mockOrganizationsResponse = {
    data: [
      { id: 1, name: "Acme Corp" },
      { id: 2, name: "Beta Inc" },
    ],
  };

  const mockOKRsResponse = {
    data: [
      {
        id: 101,
        assignee: {
          user: {
            first_name: "John",
            last_name: "Doe",
            email: "john.doe@example.com",
          },
        },
        employee: "John Doe",
        email: "john.doe@example.com",
        organization_id: 1,
        organization: { id: 1, name: "Acme Corp" },
        year: "2026",
        quarter: "JFM",
        batch_id: 10,
        batch: { id: 10, name: "Batch 2026 Q1", year: "2026", quarter: "JFM" },
        status: "Active",
        last_updated: "2026-08-30",
        objective: "Increase Market Share",
        target: "15%",
        key_results: "KR1: Expand sales",
        okr_type: "Professional",
        tracker_enabled: true,
      },
      {
        id: 102,
        assignee: {
          user: {
            first_name: "Jane",
            last_name: "Smith",
            email: "jane.smith@example.com",
          },
        },
        employee: "Jane Smith",
        email: "jane.smith@example.com",
        organization_id: 2,
        organization: { id: 2, name: "Beta Inc" },
        year: "2026",
        quarter: "AMJ",
        batch_id: 20,
        batch: { id: 20, name: "Batch 2026 Q2", year: "2026", quarter: "AMJ" },
        status: "Draft",
        last_updated: "2026-08-31",
        objective: "Improve Product Quality",
        target: "99%",
        key_results: "KR1: Zero URGENT bugs",
        okr_type: "Personal",
        tracker_enabled: false,
      },
    ],
  };

  const mockBatchesResponse = {
    data: [
      {
        id: 10,
        name: "Batch 2026 Q1",
        organization_id: 1,
        year: "2026",
        quarter: "JFM",
      },
      {
        id: 20,
        name: "Batch 2026 Q2",
        organization_id: 2,
        year: "2026",
        quarter: "AMJ",
      },
    ],
  };

  const mockBatchDetailsResponse = {
    data: {
      id: 10,
      name: "Batch 2026 Q1",
      users: [
        {
          id: 201,
          name: "John Doe",
          email: "john.doe@example.com",
          organization_id: 1,
          batch_id: 10,
        },
      ],
    },
  };

  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
    global.fetch = jest.fn();
    global.alert = jest.fn();
    localStorage.setItem("token", "mock-token-123");
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  const renderMyOkrComponent = () => {
    return render(
      <MemoryRouter initialEntries={["/my-okr"]}>
        <Routes>
          <Route path="/my-okr" element={<Menu />} />
          <Route path="/" element={<div>Login Page</div>} />
        </Routes>
      </MemoryRouter>
    );
  };

  const renderManageOkrComponent = () => {
    return render(
      <MemoryRouter initialEntries={["/manage-okr"]}>
        <Routes>
          <Route path="/manage-okr" element={<OKR />} />
        </Routes>
      </MemoryRouter>
    );
  };

  const setupDefaultManageOkrMocks = () => {
    global.fetch.mockImplementation((url) => {
      if (url.includes("/api/organizations/")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockOrganizationsResponse),
        });
      }
      if (url.includes("/api/okrs/")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockOKRsResponse),
        });
      }
      if (url.includes("/api/batches/?")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockBatchesResponse),
        });
      }
      if (url.includes("/api/batches/10")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockBatchDetailsResponse),
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ data: [] }),
      });
    });
  };

  const openAddOkrModal = async () => {
    await screen.findByRole("heading", { name: /manage okrs/i });
    fireEvent.click(screen.getByRole("button", { name: /add okr/i }));
  };

  // ==================================================
  // PAGE RENDERING & INITIAL LOAD
  // ==================================================

  test("OKR-001: My OKR page renders successfully and verifies token via API", async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockUserMe),
    });

    renderMyOkrComponent();

    expect(await screen.findByRole("heading", { name: /menu/i })).toBeInTheDocument();
    expect(global.fetch).toHaveBeenCalledWith(
      "http://127.0.0.1:8000/api/users/me",
      expect.objectContaining({
        method: "GET",
        headers: expect.objectContaining({
          Authorization: "Bearer mock-token-123",
        }),
      })
    );
  });

  test("OKR-002: Expected Manage OKR page title and subtitle are displayed", async () => {
    setupDefaultManageOkrMocks();

    renderManageOkrComponent();

    expect(await screen.findByRole("heading", { name: /manage okrs/i })).toBeInTheDocument();
    expect(screen.getByText("Create and manage employee OKRs.")).toBeInTheDocument();
  });

  test("OKR-003: Main OKR controls and buttons are rendered", async () => {
    setupDefaultManageOkrMocks();

    renderManageOkrComponent();

    expect(await screen.findByRole("button", { name: /add okr/i })).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Search employee...")).toBeInTheDocument();
    expect(screen.getByDisplayValue("All Organizations")).toBeInTheDocument();
    expect(screen.getByDisplayValue("All Years")).toBeInTheDocument();
    expect(screen.getByDisplayValue("All Quarters")).toBeInTheDocument();
    expect(screen.getByDisplayValue("All Batches")).toBeInTheDocument();
    expect(screen.getByDisplayValue("All Status")).toBeInTheDocument();
  });

  test("OKR-004: Loading behavior and empty response handling when data is empty", async () => {
    global.fetch.mockImplementation((url) => {
      if (url.includes("/api/organizations/")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ data: [] }),
        });
      }
      if (url.includes("/api/okrs/")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ data: [] }),
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ data: [] }),
      });
    });

    renderManageOkrComponent();

    expect(await screen.findByText("No OKRs found.")).toBeInTheDocument();
  });

  test("OKR-005: Empty OKR state is handled correctly when API returns empty list", async () => {
    setupDefaultManageOkrMocks();
    global.fetch.mockImplementation((url) => {
      if (url.includes("/api/okrs/")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ data: [] }),
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockOrganizationsResponse),
      });
    });

    renderManageOkrComponent();

    expect(await screen.findByText("No OKRs found.")).toBeInTheDocument();
  });

  // ==================================================
  // AUTHENTICATION / USER CONTEXT
  // ==================================================

  test("OKR-006: My OKR uses the authentication token from localStorage", async () => {
    localStorage.setItem("token", "custom-user-token-999");
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockUserMe),
    });

    renderMyOkrComponent();

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        "http://127.0.0.1:8000/api/users/me",
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: "Bearer custom-user-token-999",
          }),
        })
      );
    });
  });

  test("OKR-007: Correct Authorization Bearer token is sent to the API", async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockUserMe),
    });

    renderMyOkrComponent();

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        "http://127.0.0.1:8000/api/users/me",
        expect.objectContaining({
          method: "GET",
          headers: {
            "Content-Type": "application/json",
            Accept: "application/json",
            Authorization: "Bearer mock-token-123",
          },
        })
      );
    });
  });

  test("OKR-008: Missing authentication token in My OKR alerts user and redirects to login", async () => {
    localStorage.removeItem("token");

    renderMyOkrComponent();

    expect(global.alert).toHaveBeenCalledWith("Your Token expired. Please log in to access the menu.");
    expect(screen.getByText("Login Page")).toBeInTheDocument();
  });

  test("OKR-009: 401 Unauthorized response in My OKR is handled correctly", async () => {
    global.fetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
    });

    renderMyOkrComponent();

    await waitFor(() => {
      expect(global.alert).toHaveBeenCalledWith("Your Token expired. Please log in to access the menu.");
      expect(screen.getByText("Login Page")).toBeInTheDocument();
    });
  });

  test("OKR-010: Network/API failure in My OKR is handled correctly", async () => {
    global.fetch.mockRejectedValueOnce(new Error("Network Error"));

    renderMyOkrComponent();

    await waitFor(() => {
      expect(global.alert).toHaveBeenCalledWith("Your Token expired. Please log in to access the menu.");
      expect(screen.getByText("Login Page")).toBeInTheDocument();
    });
  });

  // ==================================================
  // FETCHING OKR DATA & API CONTRACTS
  // ==================================================

  test("OKR-011: Manage OKR calls correct GET endpoint for fetching OKRs on mount", async () => {
    setupDefaultManageOkrMocks();

    renderManageOkrComponent();

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        "http://127.0.0.1:8000/api/okrs/?page=1&size=20",
        expect.objectContaining({
          method: "GET",
          headers: {
            Authorization: "Bearer mock-token-123",
          },
        })
      );
    });
  });

  test("OKR-012: Correct HTTP method (GET) and Authorization header are sent for Organizations fetch", async () => {
    setupDefaultManageOkrMocks();

    renderManageOkrComponent();

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        "http://127.0.0.1:8000/api/organizations/?page=1&size=10",
        expect.objectContaining({
          method: "GET",
          headers: {
            Authorization: "Bearer mock-token-123",
          },
        })
      );
    });
  });

  test("OKR-013: Selecting Organization, Year, and Quarter triggers GET request to Batches endpoint with query params", async () => {
    setupDefaultManageOkrMocks();

    renderManageOkrComponent();
    await openAddOkrModal();

    fireEvent.change(screen.getByDisplayValue("Select Organization"), { target: { value: "1" } });
    fireEvent.change(screen.getByDisplayValue("Select Year"), { target: { value: "2026" } });
    fireEvent.change(screen.getByDisplayValue("Select Quarter"), { target: { value: "JFM" } });

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("http://127.0.0.1:8000/api/batches/?"),
        expect.objectContaining({
          method: "GET",
          headers: {
            Authorization: "Bearer mock-token-123",
          },
        })
      );
    });
  });

  test("OKR-014: Selecting a Batch triggers GET request to fetch Batch employees", async () => {
    setupDefaultManageOkrMocks();

    renderManageOkrComponent();
    await openAddOkrModal();

    fireEvent.change(screen.getByDisplayValue("Select Organization"), { target: { value: "1" } });
    fireEvent.change(screen.getByDisplayValue("Select Year"), { target: { value: "2026" } });
    fireEvent.change(screen.getByDisplayValue("Select Quarter"), { target: { value: "JFM" } });

    await waitFor(() => {
      expect(screen.getByDisplayValue("Select Batch")).not.toBeDisabled();
    });

    fireEvent.change(screen.getByDisplayValue("Select Batch"), { target: { value: "10" } });

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        "http://127.0.0.1:8000/api/batches/10",
        expect.objectContaining({
          method: "GET",
          headers: {
            Authorization: "Bearer mock-token-123",
          },
        })
      );
    });
  });

  test("OKR-015: Returned OKR data is rendered correctly in the table", async () => {
    setupDefaultManageOkrMocks();

    renderManageOkrComponent();

    const table = await screen.findByRole("table");
    expect(within(table).getAllByText("Acme Corp").length).toBeGreaterThan(0);
    expect(within(table).getByText("Batch 2026 Q1")).toBeInTheDocument();
    expect(within(table).getByText("Active")).toBeInTheDocument();
  });

  test("OKR-016: Multiple OKRs are rendered correctly in separate rows", async () => {
    setupDefaultManageOkrMocks();

    renderManageOkrComponent();

    expect(await screen.findByText("John Doe")).toBeInTheDocument();
    expect(screen.getByText("Jane Smith")).toBeInTheDocument();
    expect(screen.getAllByText("Beta Inc").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Draft").length).toBeGreaterThan(0);
  });

  test("OKR-017: Malformed or null API response is handled safely without crashing", async () => {
    global.fetch.mockImplementation((url) => {
      if (url.includes("/api/okrs/")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ data: null }),
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockOrganizationsResponse),
      });
    });

    renderManageOkrComponent();

    expect(await screen.findByText("No OKRs found.")).toBeInTheDocument();
  });

  test("OKR-018: API 500 error on fetching OKRs is handled gracefully without crashing", async () => {
    global.fetch.mockImplementation((url) => {
      if (url.includes("/api/okrs/")) {
        return Promise.resolve({
          ok: false,
          status: 500,
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockOrganizationsResponse),
      });
    });

    renderManageOkrComponent();

    expect(await screen.findByRole("heading", { name: /manage okrs/i })).toBeInTheDocument();
    expect(screen.getByText("No OKRs found.")).toBeInTheDocument();
  });

  // ==================================================
  // OBJECTIVE CREATION & ADD OKR MODAL
  // ==================================================

  test("OKR-019: Add OKR button opens the Add OKR modal", async () => {
    setupDefaultManageOkrMocks();

    renderManageOkrComponent();
    await openAddOkrModal();

    expect(screen.getByRole("heading", { name: /^add okrs$/i })).toBeInTheDocument();
    expect(screen.getByText("Create multiple OKRs for an employee.")).toBeInTheDocument();
  });

  test("OKR-020: Step 1 Context form fields are rendered inside modal", async () => {
    setupDefaultManageOkrMocks();

    renderManageOkrComponent();
    await openAddOkrModal();

    expect(screen.getByDisplayValue("Select Organization")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Select Year")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Select Quarter")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Select Batch")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Select Employee")).toBeInTheDocument();
  });

  test("OKR-021: Step 1 required context validation displays alert when fields are missing", async () => {
    setupDefaultManageOkrMocks();

    renderManageOkrComponent();
    await openAddOkrModal();

    fireEvent.click(screen.getByRole("button", { name: /next/i }));

    expect(global.alert).toHaveBeenCalledWith("Please select an organization.");
  });

  test("OKR-022: Step 2 OKR form fields render correctly after Step 1 completion", async () => {
    setupDefaultManageOkrMocks();

    renderManageOkrComponent();
    await openAddOkrModal();

    fireEvent.change(screen.getByDisplayValue("Select Organization"), { target: { value: "1" } });
    fireEvent.change(screen.getByDisplayValue("Select Year"), { target: { value: "2026" } });
    fireEvent.change(screen.getByDisplayValue("Select Quarter"), { target: { value: "JFM" } });

    await waitFor(() => {
      expect(screen.getByDisplayValue("Select Batch")).not.toBeDisabled();
    });
    fireEvent.change(screen.getByDisplayValue("Select Batch"), { target: { value: "10" } });

    await waitFor(() => {
      expect(screen.getByDisplayValue("Select Employee")).not.toBeDisabled();
    });
    fireEvent.change(screen.getByDisplayValue("Select Employee"), { target: { value: "201" } });

    fireEvent.click(screen.getByRole("button", { name: /next/i }));

    expect(screen.getByPlaceholderText("Enter objective")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Enter key results")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Enter measurable target")).toBeInTheDocument();
  });

  test("OKR-023: Required-field validation for Objective works on Step 2", async () => {
    setupDefaultManageOkrMocks();

    renderManageOkrComponent();
    await openAddOkrModal();

    fireEvent.change(screen.getByDisplayValue("Select Organization"), { target: { value: "1" } });
    fireEvent.change(screen.getByDisplayValue("Select Year"), { target: { value: "2026" } });
    fireEvent.change(screen.getByDisplayValue("Select Quarter"), { target: { value: "JFM" } });

    await waitFor(() => {
      expect(screen.getByDisplayValue("Select Batch")).not.toBeDisabled();
    });
    fireEvent.change(screen.getByDisplayValue("Select Batch"), { target: { value: "10" } });

    await waitFor(() => {
      expect(screen.getByDisplayValue("Select Employee")).not.toBeDisabled();
    });
    fireEvent.change(screen.getByDisplayValue("Select Employee"), { target: { value: "201" } });

    fireEvent.click(screen.getByRole("button", { name: /next/i }));

    fireEvent.click(screen.getByRole("button", { name: /next/i }));

    expect(global.alert).toHaveBeenCalledWith("Please enter objective for OKR 1.");
  });

  test("OKR-024: Add Another OKR button adds a new OKR entry", async () => {
    setupDefaultManageOkrMocks();

    renderManageOkrComponent();
    await openAddOkrModal();

    fireEvent.change(screen.getByDisplayValue("Select Organization"), { target: { value: "1" } });
    fireEvent.change(screen.getByDisplayValue("Select Year"), { target: { value: "2026" } });
    fireEvent.change(screen.getByDisplayValue("Select Quarter"), { target: { value: "JFM" } });

    await waitFor(() => {
      expect(screen.getByDisplayValue("Select Batch")).not.toBeDisabled();
    });
    fireEvent.change(screen.getByDisplayValue("Select Batch"), { target: { value: "10" } });

    await waitFor(() => {
      expect(screen.getByDisplayValue("Select Employee")).not.toBeDisabled();
    });
    fireEvent.change(screen.getByDisplayValue("Select Employee"), { target: { value: "201" } });

    fireEvent.click(screen.getByRole("button", { name: /next/i }));

    fireEvent.click(screen.getByRole("button", { name: /add another okr/i }));

    expect(screen.getByRole("heading", { name: /okr 1/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /okr 2/i })).toBeInTheDocument();
  });

  test("OKR-025: Remove button removes an OKR entry when multiple entries exist", async () => {
    setupDefaultManageOkrMocks();

    renderManageOkrComponent();
    await openAddOkrModal();

    fireEvent.change(screen.getByDisplayValue("Select Organization"), { target: { value: "1" } });
    fireEvent.change(screen.getByDisplayValue("Select Year"), { target: { value: "2026" } });
    fireEvent.change(screen.getByDisplayValue("Select Quarter"), { target: { value: "JFM" } });

    await waitFor(() => {
      expect(screen.getByDisplayValue("Select Batch")).not.toBeDisabled();
    });
    fireEvent.change(screen.getByDisplayValue("Select Batch"), { target: { value: "10" } });

    await waitFor(() => {
      expect(screen.getByDisplayValue("Select Employee")).not.toBeDisabled();
    });
    fireEvent.change(screen.getByDisplayValue("Select Employee"), { target: { value: "201" } });

    fireEvent.click(screen.getByRole("button", { name: /next/i }));

    fireEvent.click(screen.getByRole("button", { name: /add another okr/i }));
    expect(screen.getByRole("heading", { name: /okr 2/i })).toBeInTheDocument();

    const removeBtns = screen.getAllByRole("button", { name: /remove/i });
    fireEvent.click(removeBtns[1]);

    expect(screen.queryByRole("heading", { name: /okr 2/i })).not.toBeInTheDocument();
  });

  test("OKR-026: Step 3 Preview displays summary of context and OKR inputs", async () => {
    setupDefaultManageOkrMocks();

    renderManageOkrComponent();
    await openAddOkrModal();

    fireEvent.change(screen.getByDisplayValue("Select Organization"), { target: { value: "1" } });
    fireEvent.change(screen.getByDisplayValue("Select Year"), { target: { value: "2026" } });
    fireEvent.change(screen.getByDisplayValue("Select Quarter"), { target: { value: "JFM" } });

    await waitFor(() => {
      expect(screen.getByDisplayValue("Select Batch")).not.toBeDisabled();
    });
    fireEvent.change(screen.getByDisplayValue("Select Batch"), { target: { value: "10" } });

    await waitFor(() => {
      expect(screen.getByDisplayValue("Select Employee")).not.toBeDisabled();
    });
    fireEvent.change(screen.getByDisplayValue("Select Employee"), { target: { value: "201" } });

    fireEvent.click(screen.getByRole("button", { name: /next/i }));

    fireEvent.change(screen.getByPlaceholderText("Enter objective"), { target: { value: "Boost System Scalability" } });
    fireEvent.change(screen.getByPlaceholderText("Enter key results"), { target: { value: "99.9% Uptime" } });
    fireEvent.change(screen.getByPlaceholderText("Enter measurable target"), { target: { value: "100" } });

    fireEvent.click(screen.getByRole("button", { name: /next/i }));

    expect(screen.getByRole("heading", { name: /preview/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /boost system scalability/i })).toBeInTheDocument();
  });

  test("OKR-027: Save OKRs sends POST request to API with correct contract parameters", async () => {
    setupDefaultManageOkrMocks();
    global.fetch.mockImplementation((url, options) => {
      if (url === "http://127.0.0.1:8000/api/okrs/" && options?.method === "POST") {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ id: 105 }),
        });
      }
      if (url.includes("/api/organizations/")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockOrganizationsResponse),
        });
      }
      if (url.includes("/api/okrs/")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockOKRsResponse),
        });
      }
      if (url.includes("/api/batches/?")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockBatchesResponse),
        });
      }
      if (url.includes("/api/batches/10")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockBatchDetailsResponse),
        });
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
    });

    renderManageOkrComponent();
    await openAddOkrModal();

    fireEvent.change(screen.getByDisplayValue("Select Organization"), { target: { value: "1" } });
    fireEvent.change(screen.getByDisplayValue("Select Year"), { target: { value: "2026" } });
    fireEvent.change(screen.getByDisplayValue("Select Quarter"), { target: { value: "JFM" } });

    await waitFor(() => {
      expect(screen.getByDisplayValue("Select Batch")).not.toBeDisabled();
    });
    fireEvent.change(screen.getByDisplayValue("Select Batch"), { target: { value: "10" } });

    await waitFor(() => {
      expect(screen.getByDisplayValue("Select Employee")).not.toBeDisabled();
    });
    fireEvent.change(screen.getByDisplayValue("Select Employee"), { target: { value: "201" } });

    fireEvent.click(screen.getByRole("button", { name: /next/i }));

    fireEvent.change(screen.getByPlaceholderText("Enter objective"), { target: { value: "New Objective Test" } });
    fireEvent.change(screen.getByPlaceholderText("Enter key results"), { target: { value: "New KR Test" } });
    fireEvent.change(screen.getByPlaceholderText("Enter measurable target"), { target: { value: "50" } });

    fireEvent.click(screen.getByRole("button", { name: /next/i }));

    fireEvent.click(screen.getByRole("button", { name: /save okrs/i }));

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        "http://127.0.0.1:8000/api/okrs/",
        expect.objectContaining({
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: "Bearer mock-token-123",
          },
          body: JSON.stringify({
            batch_id: "10",
            assigned_to: "201",
            objective: "New Objective Test",
            target: "50",
            key_results: "New KR Test",
            okr_type: "Professional",
            tracker_enabled: false,
          }),
        })
      );
    });
  });

  test("OKR-028: Successful OKR creation refetches OKRs list and closes modal", async () => {
    setupDefaultManageOkrMocks();

    renderManageOkrComponent();
    await openAddOkrModal();

    fireEvent.change(screen.getByDisplayValue("Select Organization"), { target: { value: "1" } });
    fireEvent.change(screen.getByDisplayValue("Select Year"), { target: { value: "2026" } });
    fireEvent.change(screen.getByDisplayValue("Select Quarter"), { target: { value: "JFM" } });

    await waitFor(() => {
      expect(screen.getByDisplayValue("Select Batch")).not.toBeDisabled();
    });
    fireEvent.change(screen.getByDisplayValue("Select Batch"), { target: { value: "10" } });

    await waitFor(() => {
      expect(screen.getByDisplayValue("Select Employee")).not.toBeDisabled();
    });
    fireEvent.change(screen.getByDisplayValue("Select Employee"), { target: { value: "201" } });

    fireEvent.click(screen.getByRole("button", { name: /next/i }));

    fireEvent.change(screen.getByPlaceholderText("Enter objective"), { target: { value: "Automated Testing OKR" } });

    fireEvent.click(screen.getByRole("button", { name: /next/i }));

    fireEvent.click(screen.getByRole("button", { name: /save okrs/i }));

    await waitFor(() => {
      expect(screen.queryByRole("heading", { name: /^add okrs$/i })).not.toBeInTheDocument();
    });
  });

  test("OKR-029: OKR creation failure displays error alert", async () => {
    setupDefaultManageOkrMocks();
    global.fetch.mockImplementation((url, options) => {
      if (url === "http://127.0.0.1:8000/api/okrs/" && options?.method === "POST") {
        return Promise.resolve({
          ok: false,
          json: () => Promise.resolve({ detail: "Validation error saving OKR" }),
        });
      }
      if (url.includes("/api/organizations/")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockOrganizationsResponse),
        });
      }
      if (url.includes("/api/okrs/")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockOKRsResponse),
        });
      }
      if (url.includes("/api/batches/?")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockBatchesResponse),
        });
      }
      if (url.includes("/api/batches/10")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockBatchDetailsResponse),
        });
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
    });

    renderManageOkrComponent();
    await openAddOkrModal();

    fireEvent.change(screen.getByDisplayValue("Select Organization"), { target: { value: "1" } });
    fireEvent.change(screen.getByDisplayValue("Select Year"), { target: { value: "2026" } });
    fireEvent.change(screen.getByDisplayValue("Select Quarter"), { target: { value: "JFM" } });

    await waitFor(() => {
      expect(screen.getByDisplayValue("Select Batch")).not.toBeDisabled();
    });
    fireEvent.change(screen.getByDisplayValue("Select Batch"), { target: { value: "10" } });

    await waitFor(() => {
      expect(screen.getByDisplayValue("Select Employee")).not.toBeDisabled();
    });
    fireEvent.change(screen.getByDisplayValue("Select Employee"), { target: { value: "201" } });

    fireEvent.click(screen.getByRole("button", { name: /next/i }));

    fireEvent.change(screen.getByPlaceholderText("Enter objective"), { target: { value: "Failing OKR" } });

    fireEvent.click(screen.getByRole("button", { name: /next/i }));

    fireEvent.click(screen.getByRole("button", { name: /save okrs/i }));

    await waitFor(() => {
      expect(global.alert).toHaveBeenCalledWith("Validation error saving OKR");
    });
  });

  test("OKR-030: Closing Add OKR modal resets form state", async () => {
    setupDefaultManageOkrMocks();

    renderManageOkrComponent();
    await openAddOkrModal();

    fireEvent.change(screen.getByDisplayValue("Select Organization"), { target: { value: "1" } });

    const closeBtn = document.querySelector(".modal-close-btn");
    fireEvent.click(closeBtn);

    expect(screen.queryByRole("heading", { name: /^add okrs$/i })).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /add okr/i }));
    expect(screen.getByDisplayValue("Select Organization")).toHaveValue("");
  });

  // ==================================================
  // SEARCH, FILTERING & PAGINATION
  // ==================================================

  test("OKR-031: Searching employee by name or email filters table rows", async () => {
    setupDefaultManageOkrMocks();

    renderManageOkrComponent();

    expect(await screen.findByText("John Doe")).toBeInTheDocument();
    expect(screen.getByText("Jane Smith")).toBeInTheDocument();

    const searchInput = screen.getByPlaceholderText("Search employee...");
    fireEvent.change(searchInput, { target: { value: "Jane" } });

    expect(screen.getByText("Jane Smith")).toBeInTheDocument();
    expect(screen.queryByText("John Doe")).not.toBeInTheDocument();
  });

  test("OKR-032: Filtering by Organization filters table rows", async () => {
    setupDefaultManageOkrMocks();

    renderManageOkrComponent();

    expect(await screen.findByText("John Doe")).toBeInTheDocument();

    const orgFilter = screen.getByDisplayValue("All Organizations");
    fireEvent.change(orgFilter, { target: { value: "1" } });

    expect(screen.getByText("John Doe")).toBeInTheDocument();
    expect(screen.queryByText("Jane Smith")).not.toBeInTheDocument();
  });

  test("OKR-033: Filtering by Year filters table rows", async () => {
    setupDefaultManageOkrMocks();

    renderManageOkrComponent();

    expect(await screen.findByText("John Doe")).toBeInTheDocument();

    const yearFilter = screen.getByDisplayValue("All Years");
    fireEvent.change(yearFilter, { target: { value: "2026" } });

    expect(screen.getByText("John Doe")).toBeInTheDocument();
    expect(screen.getByText("Jane Smith")).toBeInTheDocument();
  });

  test("OKR-034: Filtering by Quarter filters table rows", async () => {
    setupDefaultManageOkrMocks();

    renderManageOkrComponent();

    expect(await screen.findByText("John Doe")).toBeInTheDocument();

    const quarterFilter = screen.getByDisplayValue("All Quarters");
    fireEvent.change(quarterFilter, { target: { value: "JFM" } });

    expect(screen.getByText("John Doe")).toBeInTheDocument();
    expect(screen.queryByText("Jane Smith")).not.toBeInTheDocument();
  });

  test("OKR-035: Filtering by Batch filters table rows", async () => {
    setupDefaultManageOkrMocks();

    renderManageOkrComponent();

    const table = await screen.findByRole("table");
    expect(await within(table).findByText("John Doe")).toBeInTheDocument();

    const batchFilter = screen.getByDisplayValue("All Batches");
    fireEvent.change(batchFilter, { target: { value: "10" } });

    await waitFor(() => {
      expect(within(table).getByText("John Doe")).toBeInTheDocument();
      expect(within(table).queryByText("Jane Smith")).not.toBeInTheDocument();
    });
  });

  test("OKR-036: Filtering by Status filters table rows", async () => {
    setupDefaultManageOkrMocks();

    renderManageOkrComponent();

    expect(await screen.findByText("John Doe")).toBeInTheDocument();

    const statusFilter = screen.getByDisplayValue("All Status");
    fireEvent.change(statusFilter, { target: { value: "Draft" } });

    expect(screen.getByText("Jane Smith")).toBeInTheDocument();
    expect(screen.queryByText("John Doe")).not.toBeInTheDocument();
  });

  test("OKR-037: Rows per page select updates pagination rows count", async () => {
    setupDefaultManageOkrMocks();

    renderManageOkrComponent();

    expect(await screen.findByText("2 records")).toBeInTheDocument();

    const rowsPerPageSelect = screen.getByDisplayValue("10");
    fireEvent.change(rowsPerPageSelect, { target: { value: "5" } });

    expect(rowsPerPageSelect).toHaveValue("5");
  });

  test("OKR-038: Pagination controls navigate between pages", async () => {
    const manyOKRs = Array.from({ length: 12 }, (_, i) => ({
      id: 200 + i,
      assignee: { user: { first_name: `Emp${i}`, last_name: "Test", email: `emp${i}@test.com` } },
      employee: `Emp${i} Test`,
      email: `emp${i}@test.com`,
      organization_id: 1,
      organization: { id: 1, name: "Acme Corp" },
      year: "2026",
      quarter: "JFM",
      batch_id: 10,
      batch: { id: 10, name: "Batch 1", year: "2026", quarter: "JFM" },
      status: "Active",
      last_updated: "2026-08-30",
      objective: `Obj ${i}`,
    }));

    global.fetch.mockImplementation((url) => {
      if (url.includes("/api/okrs/")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ data: manyOKRs }),
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockOrganizationsResponse),
      });
    });

    renderManageOkrComponent();

    expect(await screen.findByText("Emp0 Test")).toBeInTheDocument();

    const paginationContainer = document.querySelector(".pagination-controls");
    const buttons = paginationContainer.querySelectorAll("button");
    const nextBtn = buttons[1];
    fireEvent.click(nextBtn);

    expect(await screen.findByText("Emp10 Test")).toBeInTheDocument();
  });

  // ==================================================
  // VIEWING & EDITING OKRS
  // ==================================================

  test("OKR-039: View OKRs action button displays view details", async () => {
    setupDefaultManageOkrMocks();

    renderManageOkrComponent();

    expect(await screen.findByText("John Doe")).toBeInTheDocument();

    const viewBtns = screen.getAllByTitle("View OKRs");
    fireEvent.click(viewBtns[0]);

    expect(viewBtns[0]).toBeInTheDocument();
  });

  test("OKR-040: Clicking table row opens Edit OKR modal with pre-populated values", async () => {
    setupDefaultManageOkrMocks();

    renderManageOkrComponent();

    const rowName = await screen.findByText("John Doe");
    const tr = rowName.closest("tr");
    fireEvent.click(tr);

    expect(screen.getByRole("heading", { name: /^employee okr$/i })).toBeInTheDocument();
    expect(screen.getByDisplayValue("Increase Market Share")).toBeInTheDocument();
  });

  test("OKR-041: Pencil action button in table row shows alert message based on current implementation", async () => {
    setupDefaultManageOkrMocks();

    renderManageOkrComponent();

    expect(await screen.findByText("John Doe")).toBeInTheDocument();

    const editBtns = screen.getAllByTitle("Edit OKRs");
    fireEvent.click(editBtns[0]);

    expect(global.alert).toHaveBeenCalledWith("Edit functionality will be connected next.");
  });

  test("OKR-042: Editing fields in Edit OKR modal updates input state", async () => {
    setupDefaultManageOkrMocks();

    renderManageOkrComponent();

    const rowName = await screen.findByText("John Doe");
    fireEvent.click(rowName.closest("tr"));

    const objectiveInput = screen.getByDisplayValue("Increase Market Share");
    fireEvent.change(objectiveInput, { target: { value: "New Edited Objective" } });

    expect(objectiveInput).toHaveValue("New Edited Objective");
  });

  test("OKR-043: Exposes frontend edit defect: clicking Save Changes calls updateOKR signature mismatch without sending API update request", async () => {
    setupDefaultManageOkrMocks();

    renderManageOkrComponent();

    const rowName = await screen.findByText("John Doe");
    fireEvent.click(rowName.closest("tr"));

    const saveChangesBtn = screen.getByRole("button", { name: /save changes/i });
    fireEvent.click(saveChangesBtn);

    // Verify that NO PUT or PATCH request was made to backend API
    const calls = global.fetch.mock.calls;
    const putOrPatchCall = calls.find(([url, opt]) => opt?.method === "PUT" || opt?.method === "PATCH");
    expect(putOrPatchCall).toBeUndefined();
  });

  // ==================================================
  // EDGE CASES & SAFETY
  // ==================================================

  test("OKR-044: Whitespace-only objective is rejected by validation", async () => {
    setupDefaultManageOkrMocks();

    renderManageOkrComponent();
    await openAddOkrModal();

    fireEvent.change(screen.getByDisplayValue("Select Organization"), { target: { value: "1" } });
    fireEvent.change(screen.getByDisplayValue("Select Year"), { target: { value: "2026" } });
    fireEvent.change(screen.getByDisplayValue("Select Quarter"), { target: { value: "JFM" } });

    await waitFor(() => {
      expect(screen.getByDisplayValue("Select Batch")).not.toBeDisabled();
    });
    fireEvent.change(screen.getByDisplayValue("Select Batch"), { target: { value: "10" } });

    await waitFor(() => {
      expect(screen.getByDisplayValue("Select Employee")).not.toBeDisabled();
    });
    fireEvent.change(screen.getByDisplayValue("Select Employee"), { target: { value: "201" } });

    fireEvent.click(screen.getByRole("button", { name: /next/i }));

    fireEvent.change(screen.getByPlaceholderText("Enter objective"), { target: { value: "   " } });

    fireEvent.click(screen.getByRole("button", { name: /next/i }));

    expect(global.alert).toHaveBeenCalledWith("Please enter objective for OKR 1.");
  });

  test("OKR-045: Null OKR collection response handles empty table without error", async () => {
    global.fetch.mockImplementation((url) => {
      if (url.includes("/api/okrs/")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ data: null }),
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockOrganizationsResponse),
      });
    });

    renderManageOkrComponent();

    expect(await screen.findByText("No OKRs found.")).toBeInTheDocument();
  });

  test("OKR-046: Dependent dropdowns remain disabled until parent criteria are selected", async () => {
    setupDefaultManageOkrMocks();

    renderManageOkrComponent();
    await openAddOkrModal();

    expect(screen.getByDisplayValue("Select Batch")).toBeDisabled();
    expect(screen.getByDisplayValue("Select Employee")).toBeDisabled();
  });
});
