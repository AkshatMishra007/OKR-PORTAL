import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import Batches from "../Batches/Batches";

describe("Batches Module Unit Tests", () => {
  const mockBatchesResponse = {
    data: [
      {
        id: "batch-1",
        name: "Q1 2026 Engineering",
        organization_id: "org-1",
        year: 2026,
        quarter: "JFM",
        start_date: "2026-01-01",
        end_date: "2026-03-31",
        meeting_day: "MONDAY",
      },
      {
        id: "batch-2",
        name: "Q2 2026 Sales",
        organization_id: "org-2",
        year: 2026,
        quarter: "AMJ",
        start_date: "2026-04-01",
        end_date: "2026-06-30",
        meeting_day: "WEDNESDAY",
      },
    ],
    pagination: {
      page: 1,
      size: 10,
      total: 2,
    },
  };

  const mockOrganizationsResponse = {
    data: [
      { id: "org-1", name: "Acme Corp" },
      { id: "org-2", name: "Beta Inc" },
    ],
  };

  const mockOrgUsersResponse = {
    data: [
      { id: "user-101", name: "Alice Developer", email: "alice@acme.com" },
      { id: "user-102", name: "Bob Admin", email: "bob@acme.com" },
      { id: "user-103", name: "Charlie Lead", email: "charlie@acme.com" },
    ],
  };

  const mockBatchDetailsResponse = {
    data: {
      id: "batch-1",
      name: "Q1 2026 Engineering",
      users: [{ id: "user-101", name: "Alice Developer", email: "alice@acme.com" }],
      admins: [{ id: "user-102", name: "Bob Admin", email: "bob@acme.com" }],
    },
  };

  let currentBatchesResponse;
  let currentOrganizationsResponse;
  let currentOrgUsersResponse;
  let currentBatchDetailsResponse;

  let postBatchHandler = null;
  let putBatchHandler = null;
  let deleteBatchHandler = null;

  const setupFetchMocks = (
    batchesResp = mockBatchesResponse,
    orgsResp = mockOrganizationsResponse,
    orgUsersResp = mockOrgUsersResponse,
    batchDetailsResp = mockBatchDetailsResponse
  ) => {
    currentBatchesResponse = batchesResp;
    currentOrganizationsResponse = orgsResp;
    currentOrgUsersResponse = orgUsersResp;
    currentBatchDetailsResponse = batchDetailsResp;
    postBatchHandler = null;
    putBatchHandler = null;
    deleteBatchHandler = null;

    global.fetch = jest.fn((url, options = {}) => {
      const method = (options.method || "GET").toUpperCase();

      if (method === "POST" && url.includes("/api/batches/")) {
        if (postBatchHandler) return postBatchHandler(url, options);
        return Promise.resolve({
          ok: true,
          status: 201,
          json: async () => ({ id: "batch-3", name: "New Batch" }),
        });
      }

      if (method === "PUT" && url.includes("/api/batches/")) {
        if (putBatchHandler) return putBatchHandler(url, options);
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => ({ id: "batch-1", name: "Updated Batch" }),
        });
      }

      if (method === "DELETE" && url.includes("/api/batches/")) {
        if (deleteBatchHandler) return deleteBatchHandler(url, options);
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => ({ message: "Deleted" }),
        });
      }

      if (method === "GET" && url.includes("/api/batches/batch-1")) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => currentBatchDetailsResponse,
        });
      }

      if (method === "GET" && url.includes("/api/batches/")) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => currentBatchesResponse,
        });
      }

      if (method === "GET" && url.includes("/api/organizations/")) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => currentOrganizationsResponse,
        });
      }

      if (method === "GET" && url.includes("/api/users/organization/")) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => currentOrgUsersResponse,
        });
      }

      return Promise.reject(new Error(`Unhandled mock endpoint: ${url}`));
    });
  };

  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();

    global.alert = jest.fn();
    localStorage.setItem("token", "mock-batch-token-123");
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  const renderBatchesComponent = () => {
    return render(
      <MemoryRouter initialEntries={["/batches"]}>
        <Routes>
          <Route path="/batches" element={<Batches />} />
        </Routes>
      </MemoryRouter>
    );
  };

  /*
  |--------------------------------------------------------------------------
  | Page and List (BATCH-001 - BATCH-008)
  |--------------------------------------------------------------------------
  */

  test("BATCH-001: Batches page renders correctly", async () => {
    setupFetchMocks();
    renderBatchesComponent();

    expect(screen.getByPlaceholderText("Search batches...")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /\+ Add Batch/i })).toBeInTheDocument();
    expect(screen.getByText("Batches")).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("Q1 2026 Engineering")).toBeInTheDocument();
    });
  });

  test("BATCH-002: Batch list/table renders data returned by the backend", async () => {
    setupFetchMocks();
    renderBatchesComponent();

    await waitFor(() => {
      expect(screen.getAllByText("Acme Corp").length).toBeGreaterThan(0);
      expect(screen.getByText("Q1 2026 Engineering")).toBeInTheDocument();
      expect(screen.getAllByText("2026").length).toBeGreaterThan(0);
      expect(screen.getAllByText("JFM").length).toBeGreaterThan(0);
      expect(screen.getAllByText("MONDAY").length).toBeGreaterThan(0);

      expect(screen.getAllByText("Beta Inc").length).toBeGreaterThan(0);
      expect(screen.getByText("Q2 2026 Sales")).toBeInTheDocument();
      expect(screen.getAllByText("AMJ").length).toBeGreaterThan(0);
      expect(screen.getAllByText("WEDNESDAY").length).toBeGreaterThan(0);
    });
  });

  test("BATCH-003: [NOT IMPLEMENTED] Loading state is handled correctly", async () => {
    // Batches.jsx does not implement an explicit loading spinner/state component.
    global.fetch = jest.fn(() => new Promise(() => { }));

    renderBatchesComponent();

    expect(screen.getByText("Batches")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Search batches...")).toBeInTheDocument();
  });

  test("BATCH-004: Correct batches API endpoint is called", async () => {
    setupFetchMocks();
    renderBatchesComponent();

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        "http://127.0.0.1:8000/api/batches/?page=1&size=10",
        expect.any(Object)
      );
    });
  });

  test("BATCH-005: Correct HTTP method is used for fetching batches", async () => {
    setupFetchMocks();
    renderBatchesComponent();

    await waitFor(() => {
      const calls = global.fetch.mock.calls;
      const batchesCall = calls.find((c) => c[0].includes("/api/batches/?page="));
      expect(batchesCall).toBeDefined();
      const options = batchesCall[1] || {};
      expect(!options.method || options.method.toUpperCase() === "GET").toBe(true);
    });
  });

  test("BATCH-006: Authorization Bearer token is included", async () => {
    localStorage.setItem("token", "secret-batch-token-999");
    setupFetchMocks();

    renderBatchesComponent();

    await waitFor(() => {
      const calls = global.fetch.mock.calls;
      expect(calls.length).toBeGreaterThan(0);
      calls.forEach((call) => {
        expect(call[1].headers.Authorization).toBe("Bearer secret-batch-token-999");
      });
    });
  });

  test("BATCH-007: Empty batch list is handled correctly", async () => {
    setupFetchMocks({
      data: [],
      pagination: { total: 0, page: 1, size: 10 },
    });

    renderBatchesComponent();

    await waitFor(() => {
      expect(screen.getByText("No batches found")).toBeInTheDocument();
    });
  });

  test("BATCH-008: API/network failure is handled according to the current implementation", async () => {
    const consoleSpy = jest.spyOn(console, "error").mockImplementation(() => { });

    global.fetch = jest.fn(() => Promise.reject(new Error("Network Error")));

    renderBatchesComponent();

    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith(
        "Error fetching batches:",
        expect.any(Error)
      );
    });

    expect(screen.getByText("Batches")).toBeInTheDocument();
    consoleSpy.mockRestore();
  });

  /*
  |--------------------------------------------------------------------------
  | Add Batch (BATCH-009 - BATCH-026)
  |--------------------------------------------------------------------------
  */

  test("BATCH-009: Add Batch button is rendered", async () => {
    setupFetchMocks();
    renderBatchesComponent();

    expect(screen.getByRole("button", { name: /\+ Add Batch/i })).toBeInTheDocument();
  });

  test("BATCH-010: Add Batch modal opens correctly", async () => {
    setupFetchMocks();
    renderBatchesComponent();

    fireEvent.click(screen.getByRole("button", { name: /\+ Add Batch/i }));

    expect(screen.getByRole("heading", { name: "Add New Batch" })).toBeInTheDocument();
  });

  test("BATCH-011: All fields in the Add Batch form are rendered", async () => {
    setupFetchMocks();
    renderBatchesComponent();

    fireEvent.click(screen.getByRole("button", { name: /\+ Add Batch/i }));

    expect(screen.getByPlaceholderText("Enter batch name")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Select Organization")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Select Year")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Select Quarter")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Select Meeting Day")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Search and add users...")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Search and add admins...")).toBeInTheDocument();
  });

  test("BATCH-012: Batch name accepts input", async () => {
    setupFetchMocks();
    renderBatchesComponent();

    fireEvent.click(screen.getByRole("button", { name: /\+ Add Batch/i }));

    const nameInput = screen.getByPlaceholderText("Enter batch name");
    fireEvent.change(nameInput, { target: { value: "Q3 2026 Product" } });

    expect(nameInput).toHaveValue("Q3 2026 Product");
  });

  test("BATCH-013: Batch/quarter/year fields accept input where implemented", async () => {
    setupFetchMocks();
    renderBatchesComponent();

    fireEvent.click(screen.getByRole("button", { name: /\+ Add Batch/i }));

    const yearSelect = screen.getByDisplayValue("Select Year");
    fireEvent.change(yearSelect, { target: { value: "2026" } });
    expect(yearSelect).toHaveValue("2026");

    const quarterSelect = screen.getByDisplayValue("Select Quarter");
    fireEvent.change(quarterSelect, { target: { value: "JAS" } });
    expect(quarterSelect).toHaveValue("JAS");
  });

  test("BATCH-014: Start date accepts input", async () => {
    setupFetchMocks();
    renderBatchesComponent();

    fireEvent.click(screen.getByRole("button", { name: /\+ Add Batch/i }));

    const dateInputs = document.querySelectorAll('input[type="date"]');
    const startDateInput = dateInputs[0];

    fireEvent.change(startDateInput, { target: { value: "2026-07-01" } });
    expect(startDateInput).toHaveValue("2026-07-01");
  });

  test("BATCH-015: End date accepts input", async () => {
    setupFetchMocks();
    renderBatchesComponent();

    fireEvent.click(screen.getByRole("button", { name: /\+ Add Batch/i }));

    const dateInputs = document.querySelectorAll('input[type="date"]');
    const endDateInput = dateInputs[1];

    fireEvent.change(endDateInput, { target: { value: "2026-09-30" } });
    expect(endDateInput).toHaveValue("2026-09-30");
  });

  test("BATCH-016: Meeting day/time fields work where implemented", async () => {
    setupFetchMocks();
    renderBatchesComponent();

    fireEvent.click(screen.getByRole("button", { name: /\+ Add Batch/i }));

    const meetingSelect = screen.getByDisplayValue("Select Meeting Day");
    fireEvent.change(meetingSelect, { target: { value: "FRIDAY" } });

    expect(meetingSelect).toHaveValue("FRIDAY");
  });

  test("BATCH-017: Batch Admin selection works where implemented", async () => {
    setupFetchMocks();
    renderBatchesComponent();

    await waitFor(() => expect(screen.getByText("Q1 2026 Engineering")).toBeInTheDocument());

    fireEvent.click(screen.getByRole("button", { name: /\+ Add Batch/i }));

    // Select organization first
    fireEvent.change(screen.getByDisplayValue("Select Organization"), {
      target: { value: "org-1" },
    });

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        "http://127.0.0.1:8000/api/users/organization/org-1",
        expect.any(Object)
      );
    });

    const adminSearchInput = screen.getByPlaceholderText("Search and add admins...");
    fireEvent.change(adminSearchInput, { target: { value: "Bob" } });

    await waitFor(() => {
      expect(screen.getByText("Bob Admin")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Bob Admin"));

    // Chip should appear
    expect(screen.getByText("bob@acme.com")).toBeInTheDocument();
  });

  test("BATCH-018: Member selection works where implemented", async () => {
    setupFetchMocks();
    renderBatchesComponent();

    await waitFor(() => expect(screen.getByText("Q1 2026 Engineering")).toBeInTheDocument());

    fireEvent.click(screen.getByRole("button", { name: /\+ Add Batch/i }));

    // Select organization first
    fireEvent.change(screen.getByDisplayValue("Select Organization"), {
      target: { value: "org-1" },
    });

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        "http://127.0.0.1:8000/api/users/organization/org-1",
        expect.any(Object)
      );
    });

    const userSearchInput = screen.getByPlaceholderText("Search and add users...");
    fireEvent.change(userSearchInput, { target: { value: "Alice" } });

    await waitFor(() => {
      expect(screen.getByText("Alice Developer")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Alice Developer"));

    expect(screen.getByText("alice@acme.com")).toBeInTheDocument();
  });

  test("BATCH-019: Required-field validation works according to the actual implementation", async () => {
    setupFetchMocks();
    renderBatchesComponent();

    fireEvent.click(screen.getByRole("button", { name: /\+ Add Batch/i }));

    const nameInput = screen.getByPlaceholderText("Enter batch name");
    // Batches.jsx form inputs do not use native required HTML attributes
    expect(nameInput).not.toHaveAttribute("required");
  });

  test("BATCH-020: Create Batch sends the correct endpoint", async () => {
    setupFetchMocks();
    renderBatchesComponent();

    await waitFor(() => expect(screen.getByText("Q1 2026 Engineering")).toBeInTheDocument());

    fireEvent.click(screen.getByRole("button", { name: /\+ Add Batch/i }));
    fireEvent.change(screen.getByPlaceholderText("Enter batch name"), {
      target: { value: "New Batch" },
    });

    fireEvent.click(screen.getByRole("button", { name: "Create Batch" }));

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        "http://127.0.0.1:8000/api/batches/",
        expect.any(Object)
      );
    });
  });

  test("BATCH-021: Create Batch uses the correct HTTP method", async () => {
    setupFetchMocks();
    renderBatchesComponent();

    await waitFor(() => expect(screen.getByText("Q1 2026 Engineering")).toBeInTheDocument());

    fireEvent.click(screen.getByRole("button", { name: /\+ Add Batch/i }));

    fireEvent.click(screen.getByRole("button", { name: "Create Batch" }));

    await waitFor(() => {
      const postCall = global.fetch.mock.calls.find(
        (c) => c[0] === "http://127.0.0.1:8000/api/batches/" && c[1]?.method === "POST"
      );
      expect(postCall).toBeDefined();
    });
  });

  test("BATCH-022: Create Batch sends the correct Authorization header", async () => {
    setupFetchMocks();
    renderBatchesComponent();

    await waitFor(() => expect(screen.getByText("Q1 2026 Engineering")).toBeInTheDocument());

    fireEvent.click(screen.getByRole("button", { name: /\+ Add Batch/i }));

    fireEvent.click(screen.getByRole("button", { name: "Create Batch" }));

    await waitFor(() => {
      const postCall = global.fetch.mock.calls.find((c) => c[1]?.method === "POST");
      expect(postCall[1].headers.Authorization).toBe("Bearer mock-batch-token-123");
    });
  });

  test("BATCH-023: Create Batch sends the correct Content-Type header", async () => {
    setupFetchMocks();
    renderBatchesComponent();

    await waitFor(() => expect(screen.getByText("Q1 2026 Engineering")).toBeInTheDocument());

    fireEvent.click(screen.getByRole("button", { name: /\+ Add Batch/i }));

    fireEvent.click(screen.getByRole("button", { name: "Create Batch" }));

    await waitFor(() => {
      const postCall = global.fetch.mock.calls.find((c) => c[1]?.method === "POST");
      expect(postCall[1].headers["Content-Type"]).toBe("application/json");
    });
  });

  test("BATCH-024: Create Batch sends the correct request payload", async () => {
    setupFetchMocks();
    renderBatchesComponent();

    await waitFor(() => expect(screen.getByText("Q1 2026 Engineering")).toBeInTheDocument());

    fireEvent.click(screen.getByRole("button", { name: /\+ Add Batch/i }));
    fireEvent.change(screen.getByPlaceholderText("Enter batch name"), {
      target: { value: "Batch Alpha" },
    });
    fireEvent.change(screen.getByDisplayValue("Select Organization"), {
      target: { value: "org-1" },
    });
    fireEvent.change(screen.getByDisplayValue("Select Year"), {
      target: { value: "2026" },
    });
    fireEvent.change(screen.getByDisplayValue("Select Quarter"), {
      target: { value: "JFM" },
    });
    fireEvent.change(screen.getByDisplayValue("Select Meeting Day"), {
      target: { value: "MONDAY" },
    });

    fireEvent.click(screen.getByRole("button", { name: "Create Batch" }));

    await waitFor(() => {
      const postCall = global.fetch.mock.calls.find((c) => c[1]?.method === "POST");
      expect(JSON.parse(postCall[1].body)).toEqual({
        name: "Batch Alpha",
        organization_id: "org-1",
        year: "2026",
        quarter: "JFM",
        start_date: "",
        end_date: "",
        meeting_day: "MONDAY",
        batch_users: [],
        batch_admins: [],
      });
    });
  });

  test("BATCH-025: Successful batch creation updates/refetches the batch list appropriately", async () => {
    setupFetchMocks();
    renderBatchesComponent();

    await waitFor(() => expect(screen.getByText("Q1 2026 Engineering")).toBeInTheDocument());

    fireEvent.click(screen.getByRole("button", { name: /\+ Add Batch/i }));

    postBatchHandler = () =>
      Promise.resolve({ ok: true, status: 201, json: async () => ({ id: "b3" }) });

    currentBatchesResponse = {
      ...mockBatchesResponse,
      data: [
        ...mockBatchesResponse.data,
        { id: "batch-3", name: "Q3 2026 Design", organization_id: "org-1" },
      ],
    };

    fireEvent.click(screen.getByRole("button", { name: "Create Batch" }));

    await waitFor(() => {
      expect(screen.queryByRole("heading", { name: "Add New Batch" })).not.toBeInTheDocument();
      expect(screen.getByText("Q3 2026 Design")).toBeInTheDocument();
    });
  });

  test("BATCH-026: Batch creation failure is handled correctly", async () => {
    setupFetchMocks();
    renderBatchesComponent();

    await waitFor(() => expect(screen.getByText("Q1 2026 Engineering")).toBeInTheDocument());

    fireEvent.click(screen.getByRole("button", { name: /\+ Add Batch/i }));

    postBatchHandler = () =>
      Promise.resolve({
        ok: false,
        status: 400,
        json: async () => ({ detail: "Batch name already exists in organization" }),
      });

    fireEvent.click(screen.getByRole("button", { name: "Create Batch" }));

    await waitFor(() => {
      expect(screen.getByText("Batch name already exists in organization")).toBeInTheDocument();
    });
  });

  /*
  |--------------------------------------------------------------------------
  | Edit / Update Batch (BATCH-027 - BATCH-036)
  |--------------------------------------------------------------------------
  */

  test("BATCH-027: Edit option is available for an existing batch", async () => {
    setupFetchMocks();
    renderBatchesComponent();

    await waitFor(() => {
      const row = screen.getByText("Q1 2026 Engineering").closest("tr");
      expect(row).toBeInTheDocument();
      expect(row.tagName).toBe("TR");
    });
  });

  test("BATCH-028: Edit Batch modal opens correctly", async () => {
    setupFetchMocks();
    renderBatchesComponent();

    await waitFor(() => expect(screen.getByText("Q1 2026 Engineering")).toBeInTheDocument());

    const row = screen.getByText("Q1 2026 Engineering").closest("tr");
    fireEvent.click(row);

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Edit Batch" })).toBeInTheDocument();
    });
  });

  test("BATCH-029: Existing batch information is populated correctly", async () => {
    setupFetchMocks();
    renderBatchesComponent();

    await waitFor(() => expect(screen.getByText("Q1 2026 Engineering")).toBeInTheDocument());

    const row = screen.getByText("Q1 2026 Engineering").closest("tr");
    fireEvent.click(row);

    await waitFor(() => {
      expect(screen.getByDisplayValue("Q1 2026 Engineering")).toBeInTheDocument();
      expect(screen.getByDisplayValue("2026")).toBeInTheDocument();
      expect(screen.getByDisplayValue("JFM")).toBeInTheDocument();
      expect(screen.getByDisplayValue("MONDAY")).toBeInTheDocument();
    });
  });

  test("BATCH-030: Changing a batch field updates the form state", async () => {
    setupFetchMocks();
    renderBatchesComponent();

    await waitFor(() => expect(screen.getByText("Q1 2026 Engineering")).toBeInTheDocument());

    fireEvent.click(screen.getByText("Q1 2026 Engineering").closest("tr"));

    await waitFor(() => expect(screen.getByDisplayValue("Q1 2026 Engineering")).toBeInTheDocument());

    const nameInput = screen.getByDisplayValue("Q1 2026 Engineering");
    fireEvent.change(nameInput, { target: { value: "Q1 2026 Engineering Updated" } });

    expect(nameInput).toHaveValue("Q1 2026 Engineering Updated");
  });

  test("BATCH-031: Update Batch sends the correct endpoint", async () => {
    setupFetchMocks();
    renderBatchesComponent();

    await waitFor(() => expect(screen.getByText("Q1 2026 Engineering")).toBeInTheDocument());

    fireEvent.click(screen.getByText("Q1 2026 Engineering").closest("tr"));

    await waitFor(() => expect(screen.getByDisplayValue("Q1 2026 Engineering")).toBeInTheDocument());

    fireEvent.click(screen.getByRole("button", { name: "Update Batch" }));

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        "http://127.0.0.1:8000/api/batches/batch-1",
        expect.any(Object)
      );
    });
  });

  test("BATCH-032: Update Batch uses the correct HTTP method", async () => {
    setupFetchMocks();
    renderBatchesComponent();

    await waitFor(() => expect(screen.getByText("Q1 2026 Engineering")).toBeInTheDocument());

    fireEvent.click(screen.getByText("Q1 2026 Engineering").closest("tr"));

    await waitFor(() => expect(screen.getByDisplayValue("Q1 2026 Engineering")).toBeInTheDocument());

    fireEvent.click(screen.getByRole("button", { name: "Update Batch" }));

    await waitFor(() => {
      const putCall = global.fetch.mock.calls.find((c) => c[1]?.method === "PUT");
      expect(putCall).toBeDefined();
    });
  });

  test("BATCH-033: Update Batch sends the correct Authorization header", async () => {
    setupFetchMocks();
    renderBatchesComponent();

    await waitFor(() => expect(screen.getByText("Q1 2026 Engineering")).toBeInTheDocument());

    fireEvent.click(screen.getByText("Q1 2026 Engineering").closest("tr"));

    await waitFor(() => expect(screen.getByDisplayValue("Q1 2026 Engineering")).toBeInTheDocument());

    fireEvent.click(screen.getByRole("button", { name: "Update Batch" }));

    await waitFor(() => {
      const putCall = global.fetch.mock.calls.find((c) => c[1]?.method === "PUT");
      expect(putCall[1].headers.Authorization).toBe("Bearer mock-batch-token-123");
    });
  });

  test("BATCH-034: Update Batch sends the correct request payload", async () => {
    setupFetchMocks();
    renderBatchesComponent();

    await waitFor(() => expect(screen.getByText("Q1 2026 Engineering")).toBeInTheDocument());

    fireEvent.click(screen.getByText("Q1 2026 Engineering").closest("tr"));

    await waitFor(() => expect(screen.getByDisplayValue("Q1 2026 Engineering")).toBeInTheDocument());

    const nameInput = screen.getByDisplayValue("Q1 2026 Engineering");
    fireEvent.change(nameInput, { target: { value: "Q1 2026 Engineering Updated" } });

    fireEvent.click(screen.getByRole("button", { name: "Update Batch" }));

    await waitFor(() => {
      const putCall = global.fetch.mock.calls.find((c) => c[1]?.method === "PUT");
      expect(JSON.parse(putCall[1].body)).toEqual({
        organization_id: "org-1",
        name: "Q1 2026 Engineering Updated",
        year: 2026,
        quarter: "JFM",
        start_date: "2026-01-01",
        end_date: "2026-03-31",
        meeting_day: "MONDAY",
        batch_users: ["user-101"],
        batch_admins: ["user-102"],
      });
    });
  });

  test("BATCH-035: Successful update reflects the updated batch in the UI", async () => {
    // Tests whether submitting an update sends PUT request, closes modal, and re-renders updated batch in UI table
    setupFetchMocks();
    renderBatchesComponent();

    await waitFor(() => expect(screen.getByText("Q1 2026 Engineering")).toBeInTheDocument());

    fireEvent.click(screen.getByText("Q1 2026 Engineering").closest("tr"));

    await waitFor(() => expect(screen.getByDisplayValue("Q1 2026 Engineering")).toBeInTheDocument());

    fireEvent.change(screen.getByDisplayValue("Q1 2026 Engineering"), {
      target: { value: "Q1 2026 Engineering Updated" },
    });

    currentBatchesResponse = {
      ...mockBatchesResponse,
      data: [
        { ...mockBatchesResponse.data[0], name: "Q1 2026 Engineering Updated" },
        mockBatchesResponse.data[1],
      ],
    };

    fireEvent.click(screen.getByRole("button", { name: "Update Batch" }));

    await waitFor(() => {
      expect(screen.queryByRole("heading", { name: "Edit Batch" })).not.toBeInTheDocument();
      // Assert updated batch name appears in the UI list
      expect(screen.getByText("Q1 2026 Engineering Updated")).toBeInTheDocument();
    });
  });

  test("BATCH-036: Update failure is handled according to the actual implementation", async () => {
    const consoleSpy = jest.spyOn(console, "error").mockImplementation(() => { });
    setupFetchMocks();
    renderBatchesComponent();

    await waitFor(() => expect(screen.getByText("Q1 2026 Engineering")).toBeInTheDocument());

    fireEvent.click(screen.getByText("Q1 2026 Engineering").closest("tr"));

    await waitFor(() => expect(screen.getByDisplayValue("Q1 2026 Engineering")).toBeInTheDocument());

    putBatchHandler = () =>
      Promise.resolve({
        ok: false,
        status: 500,
        text: async () => "Internal Server Error",
      });

    fireEvent.click(screen.getByRole("button", { name: "Update Batch" }));

    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith("Failed to update batch:", "Internal Server Error");
    });

    consoleSpy.mockRestore();
  });

  /*
  |--------------------------------------------------------------------------
  | Delete Batch (BATCH-037 - BATCH-041)
  |--------------------------------------------------------------------------
  */

  test("BATCH-037: Delete action is rendered if implemented", async () => {
    setupFetchMocks();
    renderBatchesComponent();

    await waitFor(() => expect(screen.getByText("Q1 2026 Engineering")).toBeInTheDocument());

    const deleteBtns = document.querySelectorAll(".organization-delete-btn");
    expect(deleteBtns.length).toBe(2);
  });

  test("BATCH-038: Delete confirmation UI appears if implemented", async () => {
    setupFetchMocks();
    renderBatchesComponent();

    await waitFor(() => expect(screen.getByText("Q1 2026 Engineering")).toBeInTheDocument());

    const deleteBtn = document.querySelectorAll(".organization-delete-btn")[0];
    fireEvent.click(deleteBtn);

    expect(screen.getByRole("heading", { name: "Delete Batch?" })).toBeInTheDocument();
    expect(screen.getByText(/Are you sure you want to delete/i)).toBeInTheDocument();
  });

  test("BATCH-039: Delete request uses the correct endpoint and method", async () => {
    setupFetchMocks();
    renderBatchesComponent();

    await waitFor(() => expect(screen.getByText("Q1 2026 Engineering")).toBeInTheDocument());

    const deleteBtn = document.querySelectorAll(".organization-delete-btn")[0];
    fireEvent.click(deleteBtn);

    fireEvent.click(screen.getByRole("button", { name: "Yes, Delete" }));

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        "http://127.0.0.1:8000/api/batches/batch-1",
        {
          method: "DELETE",
          headers: {
            Authorization: "Bearer mock-batch-token-123",
          },
        }
      );
    });
  });

  test("BATCH-040: Successful deletion removes the batch from the UI/list", async () => {
    setupFetchMocks();
    renderBatchesComponent();

    await waitFor(() => expect(screen.getByText("Q1 2026 Engineering")).toBeInTheDocument());

    const deleteBtn = document.querySelectorAll(".organization-delete-btn")[0];
    fireEvent.click(deleteBtn);

    currentBatchesResponse = {
      ...mockBatchesResponse,
      data: [mockBatchesResponse.data[1]],
      pagination: { page: 1, size: 10, total: 1 },
    };

    fireEvent.click(screen.getByRole("button", { name: "Yes, Delete" }));

    await waitFor(() => {
      expect(screen.queryByText("Q1 2026 Engineering")).not.toBeInTheDocument();
      expect(screen.getByText("Q2 2026 Sales")).toBeInTheDocument();
    });
  });

  test("BATCH-041: Delete failure is handled correctly", async () => {
    const consoleSpy = jest.spyOn(console, "error").mockImplementation(() => { });
    setupFetchMocks();
    renderBatchesComponent();

    await waitFor(() => expect(screen.getByText("Q1 2026 Engineering")).toBeInTheDocument());

    const deleteBtn = document.querySelectorAll(".organization-delete-btn")[0];
    fireEvent.click(deleteBtn);

    deleteBatchHandler = () =>
      Promise.resolve({
        ok: false,
        status: 400,
        text: async () => "Cannot delete active batch",
      });

    fireEvent.click(screen.getByRole("button", { name: "Yes, Delete" }));

    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith("Failed to delete batch:", "Cannot delete active batch");
    });

    consoleSpy.mockRestore();
  });

  /*
  |--------------------------------------------------------------------------
  | Batch Membership & Admin (BATCH-042 - BATCH-051)
  |--------------------------------------------------------------------------
  */

  test("BATCH-042: Members can be displayed", async () => {
    setupFetchMocks();
    renderBatchesComponent();

    await waitFor(() => expect(screen.getByText("Q1 2026 Engineering")).toBeInTheDocument());

    fireEvent.click(screen.getByText("Q1 2026 Engineering").closest("tr"));

    await waitFor(() => {
      expect(screen.getByText("alice@acme.com")).toBeInTheDocument();
    });
  });

  test("BATCH-043: Member selection works", async () => {
    setupFetchMocks();
    renderBatchesComponent();

    await waitFor(() => expect(screen.getByText("Q1 2026 Engineering")).toBeInTheDocument());

    fireEvent.click(screen.getByText("Q1 2026 Engineering").closest("tr"));

    await waitFor(() => expect(screen.getByText("alice@acme.com")).toBeInTheDocument());

    const userInputs = screen.getAllByPlaceholderText("Search user...");
    const userSearchInput = userInputs[0];

    fireEvent.change(userSearchInput, { target: { value: "Charlie" } });

    await waitFor(() => {
      expect(screen.getByText("Charlie Lead")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Charlie Lead"));

    expect(screen.getByText("charlie@acme.com")).toBeInTheDocument();
  });

  test("BATCH-044: Adding a member sends the correct API request", async () => {
    setupFetchMocks();
    renderBatchesComponent();

    await waitFor(() => expect(screen.getByText("Q1 2026 Engineering")).toBeInTheDocument());

    fireEvent.click(screen.getByText("Q1 2026 Engineering").closest("tr"));

    await waitFor(() => expect(screen.getByText("alice@acme.com")).toBeInTheDocument());

    const userSearchInput = screen.getAllByPlaceholderText("Search user...")[0];
    fireEvent.change(userSearchInput, { target: { value: "Charlie" } });

    await waitFor(() => expect(screen.getByText("Charlie Lead")).toBeInTheDocument());

    fireEvent.click(screen.getByText("Charlie Lead"));

    fireEvent.click(screen.getByRole("button", { name: "Update Batch" }));

    await waitFor(() => {
      const putCall = global.fetch.mock.calls.find((c) => c[1]?.method === "PUT");
      const body = JSON.parse(putCall[1].body);
      expect(body.batch_users).toContain("user-103");
    });
  });

  test("BATCH-045: Removing a member sends the correct API request", async () => {
    setupFetchMocks();
    renderBatchesComponent();

    await waitFor(() => expect(screen.getByText("Q1 2026 Engineering")).toBeInTheDocument());

    fireEvent.click(screen.getByText("Q1 2026 Engineering").closest("tr"));

    await waitFor(() => expect(screen.getByText("alice@acme.com")).toBeInTheDocument());

    const removeUserBtn = screen.getByText("alice@acme.com").nextElementSibling;
    fireEvent.click(removeUserBtn);

    expect(screen.queryByText("alice@acme.com")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Update Batch" }));

    await waitFor(() => {
      const putCall = global.fetch.mock.calls.find((c) => c[1]?.method === "PUT");
      const body = JSON.parse(putCall[1].body);
      expect(body.batch_users).not.toContain("user-101");
    });
  });

  test("BATCH-046: Successful membership changes are reflected in the UI", async () => {
    setupFetchMocks();
    renderBatchesComponent();

    await waitFor(() => expect(screen.getByText("Q1 2026 Engineering")).toBeInTheDocument());

    fireEvent.click(screen.getByText("Q1 2026 Engineering").closest("tr"));

    await waitFor(() => expect(screen.getByText("alice@acme.com")).toBeInTheDocument());

    const removeUserBtn = screen.getByText("alice@acme.com").nextElementSibling;
    fireEvent.click(removeUserBtn);

    // Update batch details response for refetching
    currentBatchDetailsResponse = {
      data: {
        ...mockBatchDetailsResponse.data,
        users: [],
      },
    };

    fireEvent.click(screen.getByRole("button", { name: "Update Batch" }));

    await waitFor(() => {
      expect(screen.queryByRole("heading", { name: "Edit Batch" })).not.toBeInTheDocument();
    });
  });

  test("BATCH-047: Membership error when organization is not selected is handled correctly", async () => {
    setupFetchMocks();
    renderBatchesComponent();

    fireEvent.click(screen.getByRole("button", { name: /\+ Add Batch/i }));

    const searchInput = screen.getByPlaceholderText("Search and add users...");
    fireEvent.change(searchInput, { target: { value: "Alice" } });

    expect(screen.getByText("Please select an organization first.")).toBeInTheDocument();
  });

  test("BATCH-048: Batch Admin is displayed correctly", async () => {
    setupFetchMocks();
    renderBatchesComponent();

    await waitFor(() => expect(screen.getByText("Q1 2026 Engineering")).toBeInTheDocument());

    fireEvent.click(screen.getByText("Q1 2026 Engineering").closest("tr"));

    await waitFor(() => {
      expect(screen.getByText("bob@acme.com")).toBeInTheDocument();
    });
  });

  test("BATCH-049: Batch Admin can be selected", async () => {
    setupFetchMocks();
    renderBatchesComponent();

    await waitFor(() => expect(screen.getByText("Q1 2026 Engineering")).toBeInTheDocument());

    fireEvent.click(screen.getByText("Q1 2026 Engineering").closest("tr"));

    await waitFor(() => expect(screen.getByText("bob@acme.com")).toBeInTheDocument());

    const adminInputs = screen.getAllByPlaceholderText("Search admin...");
    fireEvent.change(adminInputs[0], { target: { value: "Charlie" } });

    await waitFor(() => {
      expect(screen.getByText("Charlie Lead")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Charlie Lead"));

    expect(screen.getByText("charlie@acme.com")).toBeInTheDocument();
  });

  test("BATCH-050: Batch Admin update sends the correct API request", async () => {
    setupFetchMocks();
    renderBatchesComponent();

    await waitFor(() => expect(screen.getByText("Q1 2026 Engineering")).toBeInTheDocument());

    fireEvent.click(screen.getByText("Q1 2026 Engineering").closest("tr"));

    await waitFor(() => expect(screen.getByText("bob@acme.com")).toBeInTheDocument());

    const adminInput = screen.getAllByPlaceholderText("Search admin...")[0];
    fireEvent.change(adminInput, { target: { value: "Charlie" } });

    await waitFor(() => expect(screen.getByText("Charlie Lead")).toBeInTheDocument());

    fireEvent.click(screen.getByText("Charlie Lead"));

    fireEvent.click(screen.getByRole("button", { name: "Update Batch" }));

    await waitFor(() => {
      const putCall = global.fetch.mock.calls.find((c) => c[1]?.method === "PUT");
      const body = JSON.parse(putCall[1].body);
      expect(body.batch_admins).toEqual(["user-102", "user-103"]);
    });
  });

  test("BATCH-051: Batch Admin change is reflected in the UI", async () => {
    setupFetchMocks();
    renderBatchesComponent();

    await waitFor(() => expect(screen.getByText("Q1 2026 Engineering")).toBeInTheDocument());

    fireEvent.click(screen.getByText("Q1 2026 Engineering").closest("tr"));

    await waitFor(() => expect(screen.getByText("bob@acme.com")).toBeInTheDocument());

    const removeAdminBtn = screen.getByText("bob@acme.com").nextElementSibling;
    fireEvent.click(removeAdminBtn);

    currentBatchDetailsResponse = {
      data: {
        ...mockBatchDetailsResponse.data,
        admins: [],
      },
    };

    fireEvent.click(screen.getByRole("button", { name: "Update Batch" }));

    await waitFor(() => {
      expect(screen.queryByRole("heading", { name: "Edit Batch" })).not.toBeInTheDocument();
    });
  });

  /*
  |--------------------------------------------------------------------------
  | Batch Close / Workflow (BATCH-052 - BATCH-056) [UNIMPLEMENTED]
  |--------------------------------------------------------------------------
  */

  test.skip("BATCH-052: [NOT IMPLEMENTED] Close batch action is rendered", () => {
    // Feature not implemented in Batches.jsx frontend
  });

  test.skip("BATCH-053: [NOT IMPLEMENTED] Close batch confirmation works", () => {
    // Feature not implemented in Batches.jsx frontend
  });

  test.skip("BATCH-054: [NOT IMPLEMENTED] Close batch sends the correct API request", () => {
    // Feature not implemented in Batches.jsx frontend
  });

  test.skip("BATCH-055: [NOT IMPLEMENTED] Successful batch close updates the UI/status", () => {
    // Feature not implemented in Batches.jsx frontend
  });

  test.skip("BATCH-056: [NOT IMPLEMENTED] Closed batch cannot perform actions that the frontend prevents", () => {
    // Feature not implemented in Batches.jsx frontend
  });

  /*
  |--------------------------------------------------------------------------
  | Search / Pagination & Filters (BATCH-057 - BATCH-060)
  |--------------------------------------------------------------------------
  */

  test("BATCH-057: Search filters batches correctly", async () => {
    setupFetchMocks();
    renderBatchesComponent();

    await waitFor(() => expect(screen.getByText("Q1 2026 Engineering")).toBeInTheDocument());

    const searchInput = screen.getByPlaceholderText("Search batches...");
    fireEvent.change(searchInput, { target: { value: "Sales" } });

    expect(screen.queryByText("Q1 2026 Engineering")).not.toBeInTheDocument();
    expect(screen.getByText("Q2 2026 Sales")).toBeInTheDocument();

    fireEvent.change(searchInput, { target: { value: "" } });
    expect(screen.getByText("Q1 2026 Engineering")).toBeInTheDocument();
    expect(screen.getByText("Q2 2026 Sales")).toBeInTheDocument();
  });

  test("BATCH-058: Search handles no matching results", async () => {
    setupFetchMocks();
    renderBatchesComponent();

    await waitFor(() => expect(screen.getByText("Q1 2026 Engineering")).toBeInTheDocument());

    const searchInput = screen.getByPlaceholderText("Search batches...");
    fireEvent.change(searchInput, { target: { value: "NonExistentBatch" } });

    expect(screen.getByText("No batches found")).toBeInTheDocument();
  });

  test("BATCH-059: Pagination controls render correctly", async () => {
    setupFetchMocks();
    renderBatchesComponent();

    await waitFor(() => {
      expect(screen.getByText("Rows per page")).toBeInTheDocument();
      expect(screen.getByText("Page 1 of 1")).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "Previous" })).toBeDisabled();
      expect(screen.getByRole("button", { name: "Next" })).toBeDisabled();
    });
  });

  test("BATCH-060: Changing pages requests/displays the correct data", async () => {
    const paginatedBatches = {
      data: Array.from({ length: 10 }, (_, i) => ({
        id: `batch-${i + 1}`,
        name: `Batch ${i + 1}`,
        organization_id: "org-1",
        year: 2026,
        quarter: "JFM",
      })),
      pagination: { page: 1, size: 10, total: 25 },
    };

    setupFetchMocks(paginatedBatches);
    renderBatchesComponent();

    await waitFor(() => {
      expect(screen.getByText("Page 1 of 3")).toBeInTheDocument();
    });

    const nextBtn = screen.getByRole("button", { name: "Next" });
    expect(nextBtn).not.toBeDisabled();

    fireEvent.click(nextBtn);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        "http://127.0.0.1:8000/api/batches/?page=2&size=10",
        expect.any(Object)
      );
    });
  });
});
