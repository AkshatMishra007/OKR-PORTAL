import React from "react";
import {
    render,
    screen,
    fireEvent,
    waitFor,
} from "@testing-library/react";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import MyOkr from "../MyOkr/MyOkr";

describe("My OKR Module Unit Tests", () => {
    const mockUser = {
        id: 1,
        first_name: "John",
        last_name: "Doe",
        email: "john@example.com",
    };

    const mockOKRs = {
        data: [
            {
                id: 101,
                objective: "Increase Market Share",
                key_results: "Expand sales by 15%",
                target: "100",
                okr_type: "Professional",
                expected_time_progress_percentage: 50,
                batch: {
                    id: 10,
                    name: "Batch 2026 Q1",
                    start_date: "2026-01-01",
                    end_date: "2026-03-31",
                },
            },
            {
                id: 102,
                objective: "Improve Product Quality",
                key_results: "Reduce URGENT bugs",
                target: "50",
                okr_type: "Personal",
                expected_time_progress_percentage: 60,
                batch: {
                    id: 20,
                    name: "Batch 2026 Q2",
                    start_date: "2026-04-01",
                    end_date: "2026-06-30",
                },
            },
        ],
        pagination: {
            page: 1,
            size: 10,
            total: 2,
        },
    };

    const mockWeeklyUpdates = {
        101: [
            {
                id: 1,
                week_number: 1,
                progress: 40,
                remarks: "Good progress",
                created_at: "2026-01-10T10:00:00Z",
            },
            {
                id: 2,
                week_number: 1,
                progress: 60,
                remarks: "Improved this week",
                created_at: "2026-01-15T10:00:00Z",
            },
            {
                id: 3,
                week_number: 2,
                progress: 70,
                remarks: "On track",
                created_at: "2026-01-22T10:00:00Z",
            },
        ],
        102: [],
    };

    const mockFogsHistory = {
        data: [
            {
                id: 1,
                fogs_hurdles: "Dependency on sales team",
                action_points: "Coordinate with sales team",
                created_at: "2026-01-15T10:00:00Z",
            },
        ],
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
                    <Route path="/my-okr" element={<MyOkr />} />
                </Routes>
            </MemoryRouter>
        );
    };

    const setupDefaultMocks = () => {
        global.fetch.mockImplementation((url) => {
            if (url.includes("/api/users/me")) {
                return Promise.resolve({
                    ok: true,
                    json: () => Promise.resolve(mockUser),
                });
            }

            if (url.includes("/api/okrs/user/1")) {
                return Promise.resolve({
                    ok: true,
                    json: () => Promise.resolve(mockOKRs),
                });
            }

            if (url.includes("/okrs/101/weekly-updates")) {
                return Promise.resolve({
                    ok: true,
                    json: () => Promise.resolve({
                        data: mockWeeklyUpdates[101],
                    }),
                });
            }

            if (url.includes("/okrs/102/weekly-updates")) {
                return Promise.resolve({
                    ok: true,
                    json: () => Promise.resolve({
                        data: mockWeeklyUpdates[102],
                    }),
                });
            }

            if (url.includes("/fogs-hurdles")) {
                return Promise.resolve({
                    ok: true,
                    json: () => Promise.resolve(mockFogsHistory),
                });
            }

            return Promise.resolve({
                ok: true,
                json: () => Promise.resolve({ data: [] }),
            });
        });
    };

    /*
    |--------------------------------------------------------------------------
    | PAGE RENDERING & INITIAL LOAD
    |--------------------------------------------------------------------------
    */

    test("MYOKR-001: My OKR page renders successfully", async () => {
        setupDefaultMocks();

        renderMyOkrComponent();

        await waitFor(() => {
            expect(screen.getByText("My OKRs")).toBeInTheDocument();
        });
    });

    test("MYOKR-002: Current user API is called with authorization token", async () => {
        setupDefaultMocks();

        renderMyOkrComponent();

        await waitFor(() => {
            expect(global.fetch).toHaveBeenCalledWith(
                "http://127.0.0.1:8000/api/users/me",
                expect.objectContaining({
                    headers: expect.objectContaining({
                        Authorization: "Bearer mock-token-123",
                    }),
                })
            );
        });
    });

    test("MYOKR-003: User OKRs API is called after user is fetched", async () => {
        setupDefaultMocks();

        renderMyOkrComponent();

        await waitFor(() => {
            expect(global.fetch).toHaveBeenCalledWith(
                "http://127.0.0.1:8000/api/okrs/user/1?page=1&size=10",
                expect.objectContaining({
                    method: "GET",
                    headers: expect.objectContaining({
                        Authorization: "Bearer mock-token-123",
                    }),
                })
            );
        });
    });

    test("MYOKR-004: OKRs returned by API are displayed", async () => {
        setupDefaultMocks();

        renderMyOkrComponent();

        expect(
            await screen.findByText("Increase Market Share")
        ).toBeInTheDocument();

        expect(
            screen.getByText("Improve Product Quality")
        ).toBeInTheDocument();
    });

    test("MYOKR-005: Weekly updates are fetched for returned OKRs", async () => {
        setupDefaultMocks();

        renderMyOkrComponent();

        await waitFor(() => {
            expect(global.fetch).toHaveBeenCalledWith(
                "http://127.0.0.1:8000/api/okrs/101/weekly-updates",
                expect.objectContaining({
                    headers: expect.objectContaining({
                        Authorization: "Bearer mock-token-123",
                    }),
                })
            );

            expect(global.fetch).toHaveBeenCalledWith(
                "http://127.0.0.1:8000/api/okrs/102/weekly-updates",
                expect.objectContaining({
                    headers: expect.objectContaining({
                        Authorization: "Bearer mock-token-123",
                    }),
                })
            );
        });
    });

    /*
    |--------------------------------------------------------------------------
    | SEARCH
    |--------------------------------------------------------------------------
    */

    test("MYOKR-006: Search filters OKRs by objective", async () => {
        setupDefaultMocks();

        renderMyOkrComponent();

        await screen.findByText("Increase Market Share");

        const searchInput = screen.getByPlaceholderText("Search OKRs...");

        fireEvent.change(searchInput, {
            target: { value: "market" },
        });

        expect(
            screen.getByText("Increase Market Share")
        ).toBeInTheDocument();

        expect(
            screen.queryByText("Improve Product Quality")
        ).not.toBeInTheDocument();
    });

    test("MYOKR-007: Search is case insensitive", async () => {
        setupDefaultMocks();

        renderMyOkrComponent();

        await screen.findByText("Increase Market Share");

        const searchInput = screen.getByPlaceholderText("Search OKRs...");

        fireEvent.change(searchInput, {
            target: { value: "MARKET" },
        });

        expect(
            screen.getByText("Increase Market Share")
        ).toBeInTheDocument();
    });

    test("MYOKR-008: Clearing search restores all OKRs", async () => {
        setupDefaultMocks();

        renderMyOkrComponent();

        await screen.findByText("Increase Market Share");

        const searchInput = screen.getByPlaceholderText("Search OKRs...");

        fireEvent.change(searchInput, {
            target: { value: "market" },
        });

        expect(
            screen.queryByText("Improve Product Quality")
        ).not.toBeInTheDocument();

        fireEvent.change(searchInput, {
            target: { value: "" },
        });

        expect(
            screen.getByText("Increase Market Share")
        ).toBeInTheDocument();

        expect(
            screen.getByText("Improve Product Quality")
        ).toBeInTheDocument();
    });

    /*
    |--------------------------------------------------------------------------
    | OKR DETAILS MODAL
    |--------------------------------------------------------------------------
    */

    test("MYOKR-009: Clicking an OKR opens OKR details modal", async () => {
        setupDefaultMocks();

        renderMyOkrComponent();

        const objective = await screen.findByText("Increase Market Share");

        fireEvent.click(objective.closest("tr"));

        expect(
            screen.getByRole("heading", { name: "OKR Details" })
        ).toBeInTheDocument();
    });

    test("MYOKR-010: OKR details are displayed correctly", async () => {
        setupDefaultMocks();

        renderMyOkrComponent();

        const objective = await screen.findByText("Increase Market Share");

        fireEvent.click(objective.closest("tr"));

        const modal = document.querySelector(".show-okr-modal-card");

        expect(modal).toHaveTextContent("Increase Market Share");
        expect(modal).toHaveTextContent("Expand sales by 15%");
        expect(modal).toHaveTextContent("100");
        expect(modal).toHaveTextContent("Professional");
    });

    test("MYOKR-011: Weekly progress history is displayed", async () => {
        setupDefaultMocks();

        renderMyOkrComponent();

        const objective = await screen.findByText("Increase Market Share");

        fireEvent.click(objective.closest("tr"));

        expect(
            await screen.findByText(/Week 1/i)
        ).toBeInTheDocument();

        expect(screen.getByText("60 / 100")).toBeInTheDocument();
        expect(screen.getByText("Improved this week")).toBeInTheDocument();
    });

    test("MYOKR-012: Weekly history can be expanded and collapsed", async () => {
        setupDefaultMocks();

        renderMyOkrComponent();

        const objective = await screen.findByText("Increase Market Share");

        fireEvent.click(objective.closest("tr"));

        const showHistoryButtons = await screen.findAllByRole("button", {
            name: "Show History",
        });

        expect(showHistoryButtons).toHaveLength(2);

        // Expand Week 1
        fireEvent.click(showHistoryButtons[0]);

        expect(
            screen.getByRole("button", { name: "Hide History" })
        ).toBeInTheDocument();

        expect(
            screen.getByText("Good progress")
        ).toBeInTheDocument();

        expect(
            screen.getByText("40 / 100")
        ).toBeInTheDocument();

        // Collapse Week 1
        fireEvent.click(
            screen.getByRole("button", { name: "Hide History" })
        );

        expect(
            screen.queryByText("Good progress")
        ).not.toBeInTheDocument();
    });

    test("MYOKR-013: OKR with no weekly updates shows empty state", async () => {
        setupDefaultMocks();

        renderMyOkrComponent();

        const objective = await screen.findByText("Improve Product Quality");

        fireEvent.click(objective.closest("tr"));

        expect(
            screen.getByText("No weekly updates available.")
        ).toBeInTheDocument();
    });

    test("MYOKR-014: OKR details modal can be closed", async () => {
        setupDefaultMocks();

        renderMyOkrComponent();

        const objective = await screen.findByText("Increase Market Share");

        fireEvent.click(objective.closest("tr"));

        expect(
            screen.getByRole("heading", { name: "OKR Details" })
        ).toBeInTheDocument();

        const modal = screen.getByRole("heading", {
            name: "OKR Details",
        }).closest(".show-okr-modal-card");

        fireEvent.click(
            modal.querySelector(".progress-close-btn")
        );

        expect(
            screen.queryByRole("heading", { name: "OKR Details" })
        ).not.toBeInTheDocument();
    });

    /*
    |--------------------------------------------------------------------------
    | UPDATE PROGRESS MODAL
    |--------------------------------------------------------------------------
    */

    test("MYOKR-015: Update Progress modal opens", async () => {
        setupDefaultMocks();

        renderMyOkrComponent();

        await screen.findByText("Increase Market Share");

        const buttons = screen.getAllByTitle("Update OKR Status");

        fireEvent.click(buttons[0]);

        expect(
            screen.getByRole("heading", { name: "Update Progress" })
        ).toBeInTheDocument();
    });

    test("MYOKR-016: Progress modal displays given target value", async () => {
        setupDefaultMocks();

        renderMyOkrComponent();

        await screen.findByText("Increase Market Share");

        fireEvent.click(
            screen.getAllByTitle("Update OKR Status")[0]
        );

        const targetInput = screen.getByDisplayValue("100");

        expect(targetInput).toBeInTheDocument();
        expect(targetInput).toHaveAttribute("readonly");
    });

    test("MYOKR-017: Target achieved input accepts value", async () => {
        setupDefaultMocks();

        renderMyOkrComponent();

        await screen.findByText("Increase Market Share");

        fireEvent.click(
            screen.getAllByTitle("Update OKR Status")[0]
        );

        const inputs = screen.getAllByPlaceholderText("Enter achieved value");

        const achievedInput = inputs[1];

        fireEvent.change(achievedInput, {
            target: { value: "75" },
        });

        expect(achievedInput).toHaveValue(75);
    });

    test("MYOKR-018: Save Progress requires week selection", async () => {
        setupDefaultMocks();

        renderMyOkrComponent();

        await screen.findByText("Increase Market Share");

        fireEvent.click(
            screen.getAllByTitle("Update OKR Status")[0]
        );

        fireEvent.click(
            screen.getByRole("button", { name: "Save Progress" })
        );

        expect(global.alert).toHaveBeenCalledWith(
            "Please select a week."
        );
    });

    test("MYOKR-019: Progress modal can be cancelled", async () => {
        setupDefaultMocks();

        renderMyOkrComponent();

        await screen.findByText("Increase Market Share");

        fireEvent.click(
            screen.getAllByTitle("Update OKR Status")[0]
        );

        expect(
            screen.getByRole("heading", { name: "Update Progress" })
        ).toBeInTheDocument();

        fireEvent.click(
            screen.getByRole("button", { name: "Cancel" })
        );

        expect(
            screen.queryByRole("heading", { name: "Update Progress" })
        ).not.toBeInTheDocument();
    });

    /*
    |--------------------------------------------------------------------------
    | UPDATE FOGS / HURDLES
    |--------------------------------------------------------------------------
    */

    test("MYOKR-020: Update FOGS/Hurdles modal opens", async () => {
        setupDefaultMocks();

        renderMyOkrComponent();

        await screen.findByText("Increase Market Share");

        fireEvent.click(
            screen.getAllByTitle("Update FOGS / Action Points")[0]
        );

        expect(
            screen.getByRole("heading", {
                name: "Update FOGS / Hurdles",
            })
        ).toBeInTheDocument();
    });

    test("MYOKR-021: FOGS and Action Points fields accept input", async () => {
        setupDefaultMocks();

        renderMyOkrComponent();

        await screen.findByText("Increase Market Share");

        fireEvent.click(
            screen.getAllByTitle("Update FOGS / Action Points")[0]
        );

        const fogsInput = screen.getByPlaceholderText("Enter FOGS...");
        const actionInput = screen.getByPlaceholderText(
            "Enter action points..."
        );

        fireEvent.change(fogsInput, {
            target: { value: "Waiting for approval" },
        });

        fireEvent.change(actionInput, {
            target: { value: "Follow up with manager" },
        });

        expect(fogsInput).toHaveValue("Waiting for approval");
        expect(actionInput).toHaveValue("Follow up with manager");
    });

    test("MYOKR-022: Save FOGS requires FOGS value", async () => {
        setupDefaultMocks();

        renderMyOkrComponent();

        await screen.findByText("Increase Market Share");

        fireEvent.click(
            screen.getAllByTitle("Update FOGS / Action Points")[0]
        );

        fireEvent.change(
            screen.getByPlaceholderText("Enter action points..."),
            { target: { value: "Follow up" } }
        );

        fireEvent.click(
            screen.getByRole("button", { name: "Save Changes" })
        );

        expect(global.alert).toHaveBeenCalledWith(
            "Please enter FOGS."
        );
    });

    test("MYOKR-023: Save FOGS requires Action Points value", async () => {
        setupDefaultMocks();

        renderMyOkrComponent();

        await screen.findByText("Increase Market Share");

        fireEvent.click(
            screen.getAllByTitle("Update FOGS / Action Points")[0]
        );

        fireEvent.change(
            screen.getByPlaceholderText("Enter FOGS..."),
            { target: { value: "Blocked by dependency" } }
        );

        fireEvent.click(
            screen.getByRole("button", { name: "Save Changes" })
        );

        expect(global.alert).toHaveBeenCalledWith(
            "Please enter action points."
        );
    });

    test("MYOKR-024: FOGS modal can be cancelled", async () => {
        setupDefaultMocks();

        renderMyOkrComponent();

        await screen.findByText("Increase Market Share");

        fireEvent.click(
            screen.getAllByTitle("Update FOGS / Action Points")[0]
        );

        expect(
            screen.getByRole("heading", {
                name: "Update FOGS / Hurdles",
            })
        ).toBeInTheDocument();

        fireEvent.click(
            screen.getByRole("button", { name: "Cancel" })
        );

        expect(
            screen.queryByRole("heading", {
                name: "Update FOGS / Hurdles",
            })
        ).not.toBeInTheDocument();
    });

    /*
    |--------------------------------------------------------------------------
    | PAGINATION
    |--------------------------------------------------------------------------
    */

    test("MYOKR-025: Page size selector is rendered", async () => {
        setupDefaultMocks();

        renderMyOkrComponent();

        await screen.findByText("Increase Market Share");

        expect(
            screen.getByDisplayValue("10")
        ).toBeInTheDocument();
    });

    test("MYOKR-026: Page size selector contains expected options", async () => {
        setupDefaultMocks();

        renderMyOkrComponent();

        await screen.findByText("Increase Market Share");

        const selector = screen.getByDisplayValue("10");

        expect(selector).toHaveValue("10");

        expect(
            screen.getByRole("option", { name: "10" })
        ).toBeInTheDocument();

        expect(
            screen.getByRole("option", { name: "20" })
        ).toBeInTheDocument();

        expect(
            screen.getByRole("option", { name: "30" })
        ).toBeInTheDocument();

        expect(
            screen.getByRole("option", { name: "50" })
        ).toBeInTheDocument();
    });

    test("MYOKR-027: Pagination displays current page", async () => {
        setupDefaultMocks();

        renderMyOkrComponent();

        await screen.findByText("Increase Market Share");

        expect(screen.getByText("Page 1 of 1")).toBeInTheDocument();
    });

    test("MYOKR-028: Previous button is disabled on first page", async () => {
        setupDefaultMocks();

        renderMyOkrComponent();

        await screen.findByText("Increase Market Share");

        const previousButton = screen.getByRole("button", {
            name: /previous/i,
        });

        expect(previousButton).toBeDisabled();
    });

    test("MYOKR-029: Next button is disabled on last page", async () => {
        setupDefaultMocks();

        renderMyOkrComponent();

        await screen.findByText("Increase Market Share");

        const nextButton = screen.getByRole("button", {
            name: /next/i,
        });

        expect(nextButton).toBeDisabled();
    });
});
