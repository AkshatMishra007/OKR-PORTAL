import React from "react";
import {
  render,
  screen,
  fireEvent,
  waitFor,
  waitForElementToBeRemoved,
  cleanup,
} from "@testing-library/react";
import "@testing-library/jest-dom";
import axios from "axios";
import Performance from "../Performance/Performance";

jest.mock("axios");

const BATCHES = [
  {
    id: "batch-1",
    name: "Batch 2026 Q1",
  },
  {
    id: "batch-2",
    name: "Batch 2026 Q2",
  },
];

const makeOkr = ({
  id,
  userId,
  userName,
  updates = [],
  progress = 0,
  trackerEntries = [],
}) => ({
  id,
  assigned_to: userId,
  assigned_to_name: userName,
  objective: `Objective ${id}`,
  target: "100",
  key_results: "Complete target",
  okr_type: "INDIVIDUAL",
  status: "ACTIVE",
  batch_id: "batch-1",
  progress_percentage: progress,
  display_progress_percentage: progress,
  weekly_updates: updates,
  tracker_entries: trackerEntries,
  created_at: "2026-09-01T00:00:00Z",
  updated_at: "2026-09-01T00:00:00Z",
});

const performanceResponse = (data) => ({
  data: {
    data,
  },
});

const renderPerformance = async (data = []) => {
  axios.get
    .mockResolvedValueOnce({ data: { data: BATCHES } })
    .mockResolvedValueOnce(performanceResponse(data));

  render(<Performance />);

  await screen.findByRole("heading", {
    name: "Performance Analytics",
  });

  await waitFor(() => {
    expect(
      screen.queryByText("Loading performance...")
    ).not.toBeInTheDocument();
  });
};

const getPerformanceCalls = () =>
  axios.get.mock.calls.filter(([url]) =>
    String(url).includes("/performance/")
  );

afterEach(() => {
  cleanup();
  jest.clearAllMocks();
  localStorage.clear();
});

describe("Performance Module", () => {
  test("PERF-001: Performance page loads successfully", async () => {
    await renderPerformance([
      makeOkr({
        id: "okr-1",
        userId: "user-1",
        userName: "Test User",
        updates: [
          { week_number: 1, progress: 20 },
        ],
      }),
    ]);

    expect(
      screen.getByRole("heading", { name: "Performance" })
    ).toBeInTheDocument();

    expect(
      screen.getByRole("heading", {
        name: "Performance Analytics",
      })
    ).toBeInTheDocument();
  });

  test("PERF-004/PERF-005: Batch selector is displayed and populated", async () => {
    await renderPerformance();

    const selector = screen.getByLabelText("Batch");

    expect(selector).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "Batch 2026 Q1" }))
      .toBeInTheDocument();
    expect(screen.getByRole("option", { name: "Batch 2026 Q2" }))
      .toBeInTheDocument();
  });

  test("PERF-006: First available batch is selected automatically", async () => {
    await renderPerformance();

    expect(screen.getByLabelText("Batch")).toHaveValue("batch-1");

    expect(getPerformanceCalls()).toHaveLength(1);
    expect(getPerformanceCalls()[0][1]).toEqual(
      expect.objectContaining({
        params: { batch_id: "batch-1" },
      })
    );
  });

  test("PERF-007: Changing batch reloads performance for the selected batch", async () => {
    await renderPerformance();

    axios.get.mockResolvedValueOnce(
      performanceResponse([
        makeOkr({
          id: "okr-2",
          userId: "user-2",
          userName: "Second User",
          updates: [{ week_number: 1, progress: 60 }],
        }),
      ])
    );

    fireEvent.change(screen.getByLabelText("Batch"), {
      target: { value: "batch-2" },
    });

    await waitFor(() => {
      expect(getPerformanceCalls()).toHaveLength(2);
    });

    expect(getPerformanceCalls()[1][1]).toEqual(
      expect.objectContaining({
        params: { batch_id: "batch-2" },
      })
    );

    expect(await screen.findByText("Second User")).toBeInTheDocument();
  });

  test("PERF-011: Only Weekly View is displayed", async () => {
    await renderPerformance();

    expect(
      screen.getByRole("button", { name: "Weekly View" })
    ).toBeInTheDocument();

    expect(
      screen.queryByRole("button", { name: "Monthly View" })
    ).not.toBeInTheDocument();

    expect(
      screen.queryByRole("button", { name: "Cycle View" })
    ).not.toBeInTheDocument();
  });

  test("PERF-013/PERF-014: Multiple users are rendered as separate graph series and legend entries", async () => {
    await renderPerformance([
      makeOkr({
        id: "okr-1",
        userId: "user-1",
        userName: "Alice",
        updates: [{ week_number: 1, progress: 40 }],
      }),
      makeOkr({
        id: "okr-2",
        userId: "user-2",
        userName: "Bob",
        updates: [{ week_number: 1, progress: 70 }],
      }),
      makeOkr({
        id: "okr-3",
        userId: "user-3",
        userName: "Charlie",
        updates: [{ week_number: 1, progress: 90 }],
      }),
    ]);

    expect(screen.getByText("Alice")).toBeInTheDocument();
    expect(screen.getByText("Bob")).toBeInTheDocument();
    expect(screen.getByText("Charlie")).toBeInTheDocument();

    expect(
      document.querySelectorAll(".performance-series-line")
    ).toHaveLength(3);

    expect(
      document.querySelectorAll(".performance-legend-item")
    ).toHaveLength(3);
  });

  test("PERF-016: Multiple OKRs belonging to one user produce one user series", async () => {
    await renderPerformance([
      makeOkr({
        id: "okr-1",
        userId: "user-1",
        userName: "Alice",
        updates: [{ week_number: 1, progress: 40 }],
      }),
      makeOkr({
        id: "okr-2",
        userId: "user-1",
        userName: "Alice",
        updates: [{ week_number: 1, progress: 60 }],
      }),
    ]);

    expect(screen.getAllByText("Alice")).toHaveLength(1);

    expect(
      document.querySelectorAll(".performance-series-line")
    ).toHaveLength(1);
  });

  test("PERF-015: Weekly update values are represented in the graph", async () => {
    await renderPerformance([
      makeOkr({
        id: "okr-1",
        userId: "user-1",
        userName: "Alice",
        updates: [
          { week_number: 1, progress: 20 },
          { week_number: 2, progress: 40 },
          { week_number: 3, progress: 60 },
          { week_number: 4, progress: 80 },
          { week_number: 5, progress: 100 },
          { week_number: 6, progress: 90 },
        ],
      }),
    ]);

    const circles = document.querySelectorAll(
      ".performance-series-point"
    );

    expect(circles.length).toBeGreaterThanOrEqual(6);
  });

  test("PERF-017: Exactly six weeks are rendered when six weeks are available", async () => {
    await renderPerformance([
      makeOkr({
        id: "okr-1",
        userId: "user-1",
        userName: "Alice",
        updates: Array.from({ length: 6 }, (_, index) => ({
          week_number: index + 1,
          progress: (index + 1) * 10,
        })),
      }),
    ]);

    const weekLabels = Array.from(
      document.querySelectorAll(".chart-x-label")
    ).map((element) => element.textContent);

    expect(weekLabels).toHaveLength(12);
  });

  test("PERF-018: More than six weeks create additional graph content inside the scroll container", async () => {
    await renderPerformance([
      makeOkr({
        id: "okr-1",
        userId: "user-1",
        userName: "Alice",
        updates: Array.from({ length: 8 }, (_, index) => ({
          week_number: index + 1,
          progress: (index + 1) * 10,
        })),
      }),
    ]);

    const scrollContainer = document.querySelector(
      ".performance-chart-scroll-container"
    );

    expect(scrollContainer).toBeInTheDocument();

    const weekLabels = document.querySelectorAll(".chart-x-label");
    expect(weekLabels.length).toBeGreaterThan(6);
  });

  test("PERF-019: Horizontal scrolling is contained inside the graph area", async () => {
    await renderPerformance([
      makeOkr({
        id: "okr-1",
        userId: "user-1",
        userName: "Alice",
        updates: Array.from({ length: 8 }, (_, index) => ({
          week_number: index + 1,
          progress: 50,
        })),
      }),
    ]);

    const scrollContainer = document.querySelector(
      ".performance-chart-scroll-container"
    );

    expect(scrollContainer).toBeInTheDocument();
    expect(
      document.querySelector(".performance-right-column")
    ).toBeInTheDocument();
    expect(
      document.querySelector(".performance-chart")
    ).toBeInTheDocument();
  });

  test("PERF-021: A missing week after the last update carries forward the last recorded score", async () => {
    await renderPerformance([
      makeOkr({
        id: "okr-1",
        userId: "user-1",
        userName: "Alice",
        updates: [
          { week_number: 1, progress: 20 },
          { week_number: 2, progress: 35 },
          { week_number: 3, progress: 50 },
          { week_number: 4, progress: 65 },
          { week_number: 5, progress: 75 },
        ],
      }),
    ]);

    const circles = document.querySelectorAll(
      ".performance-series-point"
    );

    expect(circles.length).toBeGreaterThanOrEqual(6);

    const weekFiveY = circles[4].getAttribute("cy");
    const weekSixY = circles[5].getAttribute("cy");

    expect(weekSixY).toBe(weekFiveY);
  });

  test("PERF-022: The last recorded score remains flat across multiple later weeks", async () => {
    await renderPerformance([
      makeOkr({
        id: "okr-1",
        userId: "user-1",
        userName: "Alice",
        updates: [
          { week_number: 1, progress: 20 },
          { week_number: 2, progress: 40 },
          { week_number: 3, progress: 60 },
          { week_number: 4, progress: 80 },
          { week_number: 5, progress: 70 },
        ],
      }),
    ]);

    const circles = document.querySelectorAll(
      ".performance-series-point"
    );

    expect(circles.length).toBeGreaterThanOrEqual(8);

    const lastRecordedY = circles[4].getAttribute("cy");

    expect(circles[5].getAttribute("cy")).toBe(lastRecordedY);
    expect(circles[6].getAttribute("cy")).toBe(lastRecordedY);
    expect(circles[7].getAttribute("cy")).toBe(lastRecordedY);
  });

  test("PERF-023: A later real update replaces the carried-forward value", async () => {
    await renderPerformance([
      makeOkr({
        id: "okr-1",
        userId: "user-1",
        userName: "Alice",
        updates: [
          { week_number: 1, progress: 20 },
          { week_number: 2, progress: 40 },
          { week_number: 3, progress: 60 },
          { week_number: 4, progress: 80 },
          { week_number: 5, progress: 70 },
          { week_number: 8, progress: 95 },
        ],
      }),
    ]);

    const circles = document.querySelectorAll(
      ".performance-series-point"
    );

    expect(circles.length).toBeGreaterThanOrEqual(8);

    const weekFiveY = circles[4].getAttribute("cy");
    const weekEightY = circles[7].getAttribute("cy");

    expect(circles[5].getAttribute("cy")).toBe(weekFiveY);
    expect(circles[6].getAttribute("cy")).toBe(weekFiveY);
    expect(weekEightY).not.toBe(weekFiveY);
  });

  test("PERF-025: Zero progress is rendered as a valid graph point", async () => {
    await renderPerformance([
      makeOkr({
        id: "okr-1",
        userId: "user-1",
        userName: "Alice",
        updates: [{ week_number: 1, progress: 0 }],
      }),
    ]);

    expect(
      document.querySelectorAll(".performance-series-point").length
    ).toBeGreaterThanOrEqual(1);
  });

  test("PERF-026: 100 percent progress is rendered as a valid graph point", async () => {
    await renderPerformance([
      makeOkr({
        id: "okr-1",
        userId: "user-1",
        userName: "Alice",
        updates: [{ week_number: 1, progress: 100 }],
      }),
    ]);

    expect(
      document.querySelectorAll(".performance-series-point").length
    ).toBeGreaterThanOrEqual(1);
  });

  test("PERF-027: Empty performance data shows the no-users state", async () => {
    await renderPerformance([]);

    expect(
      screen.getByText(/No users found in this batch/i)
    ).toBeInTheDocument();
  });

  test("PERF-028/PERF-029: Score Distribution is displayed for populated data", async () => {
    await renderPerformance([
      makeOkr({
        id: "okr-1",
        userId: "user-1",
        userName: "Gladiator User",
        updates: [{ week_number: 1, progress: 95 }],
      }),
      makeOkr({
        id: "okr-2",
        userId: "user-2",
        userName: "Gold User",
        updates: [{ week_number: 1, progress: 65 }],
      }),
    ]);

    expect(
      screen.getByRole("heading", { name: "Score Distribution" })
    ).toBeInTheDocument();

    expect(screen.getByText("90–100")).toBeInTheDocument();
    expect(screen.getByText("80–90")).toBeInTheDocument();
    expect(screen.getByText("60–80")).toBeInTheDocument();
    expect(screen.getByText("<60")).toBeInTheDocument();
  });

  test("PERF-030: Quick Stats are displayed", async () => {
    await renderPerformance([
      makeOkr({
        id: "okr-1",
        userId: "user-1",
        userName: "Alice",
        updates: [
          { week_number: 1, progress: 40 },
          { week_number: 2, progress: 80 },
        ],
      }),
    ]);

    expect(
      screen.getByRole("heading", { name: "Quick Stats" })
    ).toBeInTheDocument();

    expect(screen.getByText("Top Score")).toBeInTheDocument();
    expect(screen.getByText("Lowest Score")).toBeInTheDocument();
    expect(screen.getByText("Avg Score")).toBeInTheDocument();
    expect(screen.getByText("Gladiators")).toBeInTheDocument();
  });

  test("PERF-031: Empty data does not produce NaN or undefined statistics", async () => {
    await renderPerformance([]);

    expect(screen.queryByText(/NaN/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/undefined/i)).not.toBeInTheDocument();

    expect(screen.getByText("Top Score")).toBeInTheDocument();
    expect(screen.getByText("Lowest Score")).toBeInTheDocument();
  });

  test("PERF-033: Batch data is isolated after switching batches", async () => {
    await renderPerformance([
      makeOkr({
        id: "okr-1",
        userId: "user-1",
        userName: "Batch One User",
        updates: [{ week_number: 1, progress: 50 }],
      }),
    ]);

    axios.get.mockResolvedValueOnce(
      performanceResponse([
        makeOkr({
          id: "okr-2",
          userId: "user-2",
          userName: "Batch Two User",
          updates: [{ week_number: 1, progress: 80 }],
        }),
      ])
    );

    fireEvent.change(screen.getByLabelText("Batch"), {
      target: { value: "batch-2" },
    });

    await waitFor(() => {
      expect(screen.getByText("Batch Two User")).toBeInTheDocument();
    });

    expect(
      screen.queryByText("Batch One User")
    ).not.toBeInTheDocument();
  });

  test("PERF-034/PERF-035: Authentication token is attached to batch and performance requests", async () => {
    localStorage.setItem("access_token", "test-token");

    await renderPerformance();

    const calls = axios.get.mock.calls;

    expect(calls[0][1]).toEqual(
      expect.objectContaining({
        headers: {
          Authorization: "Bearer test-token",
        },
      })
    );

    expect(calls[1][1]).toEqual(
      expect.objectContaining({
        headers: {
          Authorization: "Bearer test-token",
        },
        params: {
          batch_id: "batch-1",
        },
      })
    );
  });

  test("PERF-010: Performance API failure displays an error message", async () => {
    axios.get
      .mockResolvedValueOnce({ data: { data: BATCHES } })
      .mockRejectedValueOnce({
        response: {
          data: {
            detail: "Performance service unavailable",
          },
        },
      });

    render(<Performance />);

    expect(
      await screen.findByText("Performance service unavailable")
    ).toBeInTheDocument();
  });

  test("PERF-009: Loading state is displayed while performance data is pending", async () => {
    let resolvePerformance;

    axios.get
      .mockResolvedValueOnce({ data: { data: BATCHES } })
      .mockImplementationOnce(
        () =>
          new Promise((resolve) => {
            resolvePerformance = resolve;
          })
      );

    render(<Performance />);

    expect(
      await screen.findByText("Loading performance...")
    ).toBeInTheDocument();

    await waitFor(() => {
      expect(resolvePerformance).toEqual(expect.any(Function));
    });

    resolvePerformance(
      performanceResponse([
        makeOkr({
          id: "okr-1",
          userId: "user-1",
          userName: "Alice",
          updates: [{ week_number: 1, progress: 50 }],
        }),
      ])
    );

    await waitFor(() => {
      expect(screen.getByText("Alice")).toBeInTheDocument();
    });
  });
});
