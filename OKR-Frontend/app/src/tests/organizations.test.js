import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import Organization from "../Organizations/Organizations";

describe("Organizations Module Unit Tests", () => {
  const mockOrganizationsResponse = {
    data: [
      {
        id: "org-1",
        name: "Acme Corp",
        description: "Technology Solutions",
        email: "contact@acme.com",
        phone: "9876543210",
        website: "https://acme.com",
        logo: "https://acme.com/logo.png",
        address: "123 Tech Park, City",
        is_active: true,
      },
      {
        id: "org-2",
        name: "Beta Inc",
        description: "Financial Services",
        email: "info@beta.com",
        phone: "08012345678",
        website: "https://beta.com",
        logo: "https://beta.com/logo.png",
        address: "456 Finance Tower, City",
        is_active: false,
      },
    ],
    pagination: {
      page: 1,
      size: 10,
      total: 2,
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

  const renderOrganizationComponent = () => {
    return render(
      <MemoryRouter initialEntries={["/organizations"]}>
        <Routes>
          <Route path="/organizations" element={<Organization />} />
        </Routes>
      </MemoryRouter>
    );
  };

  /*
  |--------------------------------------------------------------------------
  | Page Rendering & Data Fetching (ORG-001 - ORG-005)
  |--------------------------------------------------------------------------
  */

  test("ORG-001: Organization page renders correctly", async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => mockOrganizationsResponse,
    });

    renderOrganizationComponent();

    expect(screen.getByPlaceholderText("Search organizations...")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /\+ Add Organization/i })).toBeInTheDocument();
    expect(screen.getByText("Organization")).toBeInTheDocument();
    expect(screen.getByText("Description")).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("Acme Corp")).toBeInTheDocument();
    });
  });

  test("ORG-002: Organization list/table renders organization data returned by API", async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => mockOrganizationsResponse,
    });

    renderOrganizationComponent();

    await waitFor(() => {
      expect(screen.getByText("Acme Corp")).toBeInTheDocument();
      expect(screen.getByText("Technology Solutions")).toBeInTheDocument();
      expect(screen.getByText("contact@acme.com")).toBeInTheDocument();
      expect(screen.getByText("9876543210")).toBeInTheDocument();
      expect(screen.getByText("https://acme.com")).toBeInTheDocument();
      expect(screen.getByText("123 Tech Park, City")).toBeInTheDocument();
      expect(screen.getByText("Active")).toBeInTheDocument();

      expect(screen.getByText("Beta Inc")).toBeInTheDocument();
      expect(screen.getByText("Inactive")).toBeInTheDocument();
    });
  });

  test("ORG-003: [NOT IMPLEMENTED] Organization loading state is handled correctly", async () => {
    // Organizations.jsx does not implement an explicit loading spinner/state.
    global.fetch.mockImplementationOnce(() => new Promise(() => {}));

    renderOrganizationComponent();

    expect(screen.getByText("Organizations")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Search organizations...")).toBeInTheDocument();
  });

  test("ORG-004: Organization API is called with the correct endpoint and HTTP method", async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => mockOrganizationsResponse,
    });

    renderOrganizationComponent();

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        "http://127.0.0.1:8000/api/organizations/?page=1&size=10",
        {
          method: "get",
          headers: {
            "Content-Type": "application/json",
            Authorization: "Bearer mock-token-123",
          },
        }
      );
    });
  });

  test("ORG-005: Authorization Bearer token is included in organization API requests", async () => {
    localStorage.setItem("token", "secret-bearer-token-456");

    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => mockOrganizationsResponse,
    });

    renderOrganizationComponent();

    await waitFor(() => {
      const callHeaders = global.fetch.mock.calls[0][1].headers;
      expect(callHeaders.Authorization).toBe("Bearer secret-bearer-token-456");
    });
  });

  /*
  |--------------------------------------------------------------------------
  | Add Organization Modal & Form Fields (ORG-006 - ORG-015)
  |--------------------------------------------------------------------------
  */

  test("ORG-006: Add Organization button is rendered", async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => mockOrganizationsResponse,
    });

    renderOrganizationComponent();

    expect(screen.getByRole("button", { name: /\+ Add Organization/i })).toBeInTheDocument();
  });

  test("ORG-007: Add Organization modal opens correctly", async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => mockOrganizationsResponse,
    });

    renderOrganizationComponent();

    const addBtn = screen.getByRole("button", { name: /\+ Add Organization/i });
    fireEvent.click(addBtn);

    expect(screen.getByRole("heading", { name: "Add Organization" })).toBeInTheDocument();
    expect(screen.getByText("Create a new organization")).toBeInTheDocument();
  });

  test("ORG-008: All Add Organization fields are rendered", async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => mockOrganizationsResponse,
    });

    renderOrganizationComponent();

    fireEvent.click(screen.getByRole("button", { name: /\+ Add Organization/i }));

    expect(screen.getByPlaceholderText("Enter organization name")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("contact@example.com")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("https://example.com")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Enter logo")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Enter organization address")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Enter organization description")).toBeInTheDocument();
  });

  test("ORG-009: Organization name accepts input", async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => mockOrganizationsResponse,
    });

    renderOrganizationComponent();
    fireEvent.click(screen.getByRole("button", { name: /\+ Add Organization/i }));

    const nameInput = screen.getByPlaceholderText("Enter organization name");
    fireEvent.change(nameInput, { target: { value: "Gamma LLC" } });

    expect(nameInput).toHaveValue("Gamma LLC");
  });

  test("ORG-010: Email accepts input", async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => mockOrganizationsResponse,
    });

    renderOrganizationComponent();
    fireEvent.click(screen.getByRole("button", { name: /\+ Add Organization/i }));

    const emailInput = screen.getByPlaceholderText("contact@example.com");
    fireEvent.change(emailInput, { target: { value: "gamma@example.com" } });

    expect(emailInput).toHaveValue("gamma@example.com");
  });

  test("ORG-011: Phone accepts input", async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => mockOrganizationsResponse,
    });

    renderOrganizationComponent();
    fireEvent.click(screen.getByRole("button", { name: /\+ Add Organization/i }));

    const phoneInput = document.querySelector('input[type="tel"]');
    fireEvent.change(phoneInput, { target: { value: "9876543210" } });

    expect(phoneInput).toHaveValue("9876543210");
  });

  test("ORG-012: Website accepts input", async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => mockOrganizationsResponse,
    });

    renderOrganizationComponent();
    fireEvent.click(screen.getByRole("button", { name: /\+ Add Organization/i }));

    const websiteInput = screen.getByPlaceholderText("https://example.com");
    fireEvent.change(websiteInput, { target: { value: "https://gamma.com" } });

    expect(websiteInput).toHaveValue("https://gamma.com");
  });

  test("ORG-013: Status field works correctly", async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => mockOrganizationsResponse,
    });

    renderOrganizationComponent();
    fireEvent.click(screen.getByRole("button", { name: /\+ Add Organization/i }));

    const statusSelect = document.querySelector('select[name="is_active"]');
    expect(statusSelect).toBeInTheDocument();

    fireEvent.change(statusSelect, { target: { value: "false" } });
    expect(statusSelect).toHaveValue("false");
  });

  test("ORG-014: Address accepts input", async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => mockOrganizationsResponse,
    });

    renderOrganizationComponent();
    fireEvent.click(screen.getByRole("button", { name: /\+ Add Organization/i }));

    const addressInput = screen.getByPlaceholderText("Enter organization address");
    fireEvent.change(addressInput, { target: { value: "789 Gamma Road" } });

    expect(addressInput).toHaveValue("789 Gamma Road");
  });

  test("ORG-015: Description accepts input", async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => mockOrganizationsResponse,
    });

    renderOrganizationComponent();
    fireEvent.click(screen.getByRole("button", { name: /\+ Add Organization/i }));

    const descInput = screen.getByPlaceholderText("Enter organization description");
    fireEvent.change(descInput, { target: { value: "Gamma description" } });

    expect(descInput).toHaveValue("Gamma description");
  });

  /*
  |--------------------------------------------------------------------------
  | Validation & Input Edge Cases (ORG-016 - ORG-019)
  |--------------------------------------------------------------------------
  */

  test("ORG-016: Required-field validation works correctly", async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => mockOrganizationsResponse,
    });

    renderOrganizationComponent();
    fireEvent.click(screen.getByRole("button", { name: /\+ Add Organization/i }));

    const nameInput = screen.getByPlaceholderText("Enter organization name");
    const emailInput = screen.getByPlaceholderText("contact@example.com");

    expect(nameInput).toHaveAttribute("required");
    expect(emailInput).toHaveAttribute("required");
  });

  test("ORG-017: Invalid email is handled correctly according to the current implementation", async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => mockOrganizationsResponse,
    });

    renderOrganizationComponent();
    fireEvent.click(screen.getByRole("button", { name: /\+ Add Organization/i }));

    const emailInput = screen.getByPlaceholderText("contact@example.com");
    fireEvent.change(emailInput, { target: { value: "invalid-email" } });

    expect(emailInput).toBeInvalid();
  });

  test("ORG-018: Invalid phone number is handled correctly according to the current implementation", async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => mockOrganizationsResponse,
    });

    renderOrganizationComponent();
    fireEvent.click(screen.getByRole("button", { name: /\+ Add Organization/i }));

    const phoneInput = document.querySelector('input[type="tel"]');
    fireEvent.change(phoneInput, { target: { value: "12345" } });

    expect(screen.getByText("Enter a valid Indian mobile or landline number.")).toBeInTheDocument();
    expect(phoneInput).toHaveClass("input-error");
  });

  test("ORG-019: [KNOWN DEFECT] Website input type='url' rejects domain values missing http:// or https:// (e.g. www.frigoglass.com)", async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => mockOrganizationsResponse,
    });

    renderOrganizationComponent();
    fireEvent.click(screen.getByRole("button", { name: /\+ Add Organization/i }));

    const websiteInput = screen.getByPlaceholderText("https://example.com");
    fireEvent.change(websiteInput, { target: { value: "www.frigoglass.com" } });

    // Known defect test: native type="url" rejects www.frigoglass.com because of missing protocol scheme
    expect(websiteInput).toBeInvalid();
  });

  /*
  |--------------------------------------------------------------------------
  | Organization Creation (ORG-020 - ORG-022)
  |--------------------------------------------------------------------------
  */

  test("ORG-020: Create Organization sends the correct API request, including method, endpoint, headers and payload", async () => {
    global.fetch
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockOrganizationsResponse,
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 201,
        json: async () => ({ id: "org-3", name: "New Corp" }),
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockOrganizationsResponse,
      });

    renderOrganizationComponent();

    await waitFor(() => expect(screen.getByText("Acme Corp")).toBeInTheDocument());

    fireEvent.click(screen.getByRole("button", { name: /\+ Add Organization/i }));

    fireEvent.change(screen.getByPlaceholderText("Enter organization name"), { target: { value: "New Corp" } });
    fireEvent.change(screen.getByPlaceholderText("contact@example.com"), { target: { value: "new@corp.com" } });
    fireEvent.change(document.querySelector('input[type="tel"]'), { target: { value: "9876543210" } });
    fireEvent.change(screen.getByPlaceholderText("https://example.com"), { target: { value: "https://newcorp.com" } });
    fireEvent.change(screen.getByPlaceholderText("Enter logo"), { target: { value: "https://newcorp.com/logo.png" } });
    fireEvent.change(screen.getByPlaceholderText("Enter organization address"), { target: { value: "New Street" } });
    fireEvent.change(screen.getByPlaceholderText("Enter organization description"), { target: { value: "New Desc" } });

    const submitBtn = screen.getByRole("button", { name: "Create Organization" });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        "http://127.0.0.1:8000/api/organizations/",
        {
          method: "POST",
          headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
            Authorization: "Bearer mock-token-123",
          },
          body: JSON.stringify({
            name: "New Corp",
            description: "New Desc",
            logo: "https://newcorp.com/logo.png",
            website: "https://newcorp.com",
            email: "new@corp.com",
            phone: "9876543210",
            address: "New Street",
          }),
        }
      );
    });
  });

  test("ORG-021: Successful organization creation updates the UI/list appropriately", async () => {
    global.fetch
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockOrganizationsResponse,
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 201,
        json: async () => ({ id: "org-3", name: "New Corp" }),
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          ...mockOrganizationsResponse,
          data: [
            ...mockOrganizationsResponse.data,
            { id: "org-3", name: "New Corp", is_active: true },
          ],
        }),
      });

    renderOrganizationComponent();

    await waitFor(() => expect(screen.getByText("Acme Corp")).toBeInTheDocument());

    fireEvent.click(screen.getByRole("button", { name: /\+ Add Organization/i }));
    fireEvent.change(screen.getByPlaceholderText("Enter organization name"), { target: { value: "New Corp" } });
    fireEvent.change(screen.getByPlaceholderText("contact@example.com"), { target: { value: "new@corp.com" } });

    fireEvent.click(screen.getByRole("button", { name: "Create Organization" }));

    await waitFor(() => {
      expect(screen.queryByRole("heading", { name: "Add Organization" })).not.toBeInTheDocument();
      expect(screen.getByText("New Corp")).toBeInTheDocument();
    });
  });

  test("ORG-022: Organization creation failure displays the application's actual error behavior", async () => {
    const consoleSpy = jest.spyOn(console, "error").mockImplementation(() => {});

    global.fetch
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockOrganizationsResponse,
      })
      .mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({ detail: "Organization name already exists" }),
      });

    renderOrganizationComponent();
    await waitFor(() => expect(screen.getByText("Acme Corp")).toBeInTheDocument());

    fireEvent.click(screen.getByRole("button", { name: /\+ Add Organization/i }));
    fireEvent.change(screen.getByPlaceholderText("Enter organization name"), { target: { value: "Duplicate Org" } });
    fireEvent.change(screen.getByPlaceholderText("contact@example.com"), { target: { value: "dup@corp.com" } });

    fireEvent.click(screen.getByRole("button", { name: "Create Organization" }));

    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith("Create Organization Error:", { detail: "Organization name already exists" });
    });

    expect(screen.getByRole("heading", { name: "Add Organization" })).toBeInTheDocument();
    consoleSpy.mockRestore();
  });

  /*
  |--------------------------------------------------------------------------
  | Organization Editing (ORG-023 - ORG-026)
  |--------------------------------------------------------------------------
  */

  test("ORG-023: Edit Organization modal opens with existing organization data populated", async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => mockOrganizationsResponse,
    });

    renderOrganizationComponent();

    await waitFor(() => expect(screen.getByText("Acme Corp")).toBeInTheDocument());

    const row = screen.getByText("Acme Corp").closest("tr");
    fireEvent.click(row);

    expect(screen.getByRole("heading", { name: "Edit Organization" })).toBeInTheDocument();
    expect(screen.getByDisplayValue("Acme Corp")).toBeInTheDocument();
    expect(screen.getByDisplayValue("contact@acme.com")).toBeInTheDocument();
    expect(screen.getByDisplayValue("9876543210")).toBeInTheDocument();
    expect(screen.getByDisplayValue("https://acme.com")).toBeInTheDocument();
    expect(screen.getByDisplayValue("https://acme.com/logo.png")).toBeInTheDocument();
    expect(screen.getByDisplayValue("123 Tech Park, City")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Technology Solutions")).toBeInTheDocument();
  });

  test("ORG-024: Edit Organization sends the correct API request", async () => {
    global.fetch
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockOrganizationsResponse,
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ id: "org-1", name: "Acme Corp Updated" }),
      });

    renderOrganizationComponent();
    await waitFor(() => expect(screen.getByText("Acme Corp")).toBeInTheDocument());

    const row = screen.getByText("Acme Corp").closest("tr");
    fireEvent.click(row);

    const nameInput = screen.getByDisplayValue("Acme Corp");
    fireEvent.change(nameInput, { target: { value: "Acme Corp Updated" } });

    const updateBtn = screen.getByRole("button", { name: "Update Organization" });
    fireEvent.click(updateBtn);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        "http://127.0.0.1:8000/api/organizations/org-1",
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            Authorization: "Bearer mock-token-123",
          },
          body: JSON.stringify({
            name: "Acme Corp Updated",
            email: "contact@acme.com",
            phone: "9876543210",
            website: "https://acme.com",
            logo: "https://acme.com/logo.png",
            address: "123 Tech Park, City",
            description: "Technology Solutions",
            is_active: true,
          }),
        }
      );
    });
  });

  test("ORG-025: Successful organization update reflects the updated data in the UI", async () => {
    // Tests whether updated organization name appears in UI table after update.
    // Exposes defect in Organizations.jsx: updateOrganization does NOT refetch or update state, so UI fails to reflect updated data.
    global.fetch
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockOrganizationsResponse,
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ id: "org-1", name: "Acme Corp Updated" }),
      });

    renderOrganizationComponent();
    await waitFor(() => expect(screen.getByText("Acme Corp")).toBeInTheDocument());

    const row = screen.getByText("Acme Corp").closest("tr");
    fireEvent.click(row);

    const nameInput = screen.getByDisplayValue("Acme Corp");
    fireEvent.change(nameInput, { target: { value: "Acme Corp Updated" } });

    fireEvent.click(screen.getByRole("button", { name: "Update Organization" }));

    await waitFor(() => {
      expect(screen.queryByRole("heading", { name: "Edit Organization" })).not.toBeInTheDocument();
      // Assertion verifies updated data appears in UI list
      expect(screen.getByText("Acme Corp Updated")).toBeInTheDocument();
    });
  });

  test("ORG-026: Organization update failure is handled correctly", async () => {
    const consoleSpy = jest.spyOn(console, "error").mockImplementation(() => {});

    global.fetch
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockOrganizationsResponse,
      })
      .mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({ detail: "Server error" }),
      });

    renderOrganizationComponent();
    await waitFor(() => expect(screen.getByText("Acme Corp")).toBeInTheDocument());

    const row = screen.getByText("Acme Corp").closest("tr");
    fireEvent.click(row);

    fireEvent.click(screen.getByRole("button", { name: "Update Organization" }));

    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalled();
    });

    consoleSpy.mockRestore();
  });

  /*
  |--------------------------------------------------------------------------
  | Organization Deletion (ORG-027 - ORG-030)
  |--------------------------------------------------------------------------
  */

  test("ORG-027: Delete Organization action is available where implemented", async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => mockOrganizationsResponse,
    });

    renderOrganizationComponent();

    await waitFor(() => expect(screen.getByText("Acme Corp")).toBeInTheDocument());

    const deleteBtns = screen.getAllByTitle("Delete Organization");
    expect(deleteBtns.length).toBe(2);

    fireEvent.click(deleteBtns[0]);

    expect(screen.getByText("Delete Organization?")).toBeInTheDocument();
    expect(screen.getByText("This action cannot be undone.")).toBeInTheDocument();
  });

  test("ORG-028: Delete Organization sends the correct API request where implemented", async () => {
    global.fetch
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockOrganizationsResponse,
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ message: "Deleted successfully" }),
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          data: [mockOrganizationsResponse.data[1]],
          pagination: { page: 1, size: 10, total: 1 },
        }),
      });

    renderOrganizationComponent();
    await waitFor(() => expect(screen.getByText("Acme Corp")).toBeInTheDocument());

    const deleteBtns = screen.getAllByTitle("Delete Organization");
    fireEvent.click(deleteBtns[0]);

    const confirmBtn = screen.getByRole("button", { name: "Yes, Delete" });
    fireEvent.click(confirmBtn);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        "http://127.0.0.1:8000/api/organizations/org-1",
        {
          method: "DELETE",
          headers: {
            "Content-Type": "application/json",
            Authorization: "Bearer mock-token-123",
          },
        }
      );
    });
  });

  test("ORG-029: Successful deletion removes the organization from the UI/list", async () => {
    global.fetch
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockOrganizationsResponse,
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ message: "Deleted successfully" }),
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          data: [mockOrganizationsResponse.data[1]],
          pagination: { page: 1, size: 10, total: 1 },
        }),
      });

    renderOrganizationComponent();
    await waitFor(() => expect(screen.getByText("Acme Corp")).toBeInTheDocument());

    const deleteBtns = screen.getAllByTitle("Delete Organization");
    fireEvent.click(deleteBtns[0]);

    fireEvent.click(screen.getByRole("button", { name: "Yes, Delete" }));

    await waitFor(() => {
      expect(screen.queryByText("Acme Corp")).not.toBeInTheDocument();
      expect(screen.getByText("Beta Inc")).toBeInTheDocument();
    });
  });

  test("ORG-030: Delete failure is handled correctly", async () => {
    const consoleSpy = jest.spyOn(console, "error").mockImplementation(() => {});

    global.fetch
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockOrganizationsResponse,
      })
      .mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({ detail: "Cannot delete organization with active users" }),
      });

    renderOrganizationComponent();
    await waitFor(() => expect(screen.getByText("Acme Corp")).toBeInTheDocument());

    const deleteBtns = screen.getAllByTitle("Delete Organization");
    fireEvent.click(deleteBtns[0]);

    fireEvent.click(screen.getByRole("button", { name: "Yes, Delete" }));

    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalled();
    });

    consoleSpy.mockRestore();
  });

  /*
  |--------------------------------------------------------------------------
  | Search, Empty State, Errors & Pagination (ORG-031 - ORG-034)
  |--------------------------------------------------------------------------
  */

  test("ORG-031: Search/filter functionality works correctly if implemented", async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => mockOrganizationsResponse,
    });

    renderOrganizationComponent();
    await waitFor(() => expect(screen.getByText("Acme Corp")).toBeInTheDocument());

    const searchInput = screen.getByPlaceholderText("Search organizations...");
    fireEvent.change(searchInput, { target: { value: "Beta" } });

    expect(screen.queryByText("Acme Corp")).not.toBeInTheDocument();
    expect(screen.getByText("Beta Inc")).toBeInTheDocument();

    fireEvent.change(searchInput, { target: { value: "" } });
    expect(screen.getByText("Acme Corp")).toBeInTheDocument();
    expect(screen.getByText("Beta Inc")).toBeInTheDocument();
  });

  test("ORG-032: Empty organization list is handled correctly", async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({
        data: [],
        pagination: { page: 1, size: 10, total: 0 },
      }),
    });

    renderOrganizationComponent();

    await waitFor(() => {
      expect(screen.getByText("Organizations")).toBeInTheDocument();
    });

    const rows = document.querySelectorAll("tbody tr");
    expect(rows.length).toBe(0);
    expect(screen.getByText("Page 1 of 0")).toBeInTheDocument();
  });

  test("ORG-033: Organization API network failure is handled correctly", async () => {
    const consoleSpy = jest.spyOn(console, "error").mockImplementation(() => {});

    global.fetch.mockRejectedValueOnce(new Error("Network Failure"));

    renderOrganizationComponent();

    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith("Error fetching organizations:", expect.any(Error));
    });

    expect(screen.getByText("Organizations")).toBeInTheDocument();
    consoleSpy.mockRestore();
  });

  test("ORG-034: Pagination works correctly if implemented", async () => {
    global.fetch
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          data: Array.from({ length: 10 }, (_, i) => ({
            id: `org-${i + 1}`,
            name: `Org ${i + 1}`,
            is_active: true,
          })),
          pagination: { page: 1, size: 10, total: 25 },
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          data: Array.from({ length: 10 }, (_, i) => ({
            id: `org-${i + 11}`,
            name: `Org ${i + 11}`,
            is_active: true,
          })),
          pagination: { page: 2, size: 10, total: 25 },
        }),
      });

    renderOrganizationComponent();

    await waitFor(() => {
      expect(screen.getByText("Page 1 of 3")).toBeInTheDocument();
    });

    const nextBtn = screen.getByRole("button", { name: "Next" });
    expect(nextBtn).not.toBeDisabled();

    fireEvent.click(nextBtn);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenLastCalledWith(
        "http://127.0.0.1:8000/api/organizations/?page=2&size=10",
        expect.any(Object)
      );
    });
  });
});
