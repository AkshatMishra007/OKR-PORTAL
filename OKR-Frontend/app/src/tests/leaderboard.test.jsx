import React from "react";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Leaderboard from "../Leaderboard/Leaderboard";

const mockLeaderboardResponse = {
  items: [
    {
      rank: 1,
      user_id: "user-1",
      name: "Akash Sharma",
      team: "Demo Technology Pvt Ltd",
      score: 95.0,
      award: "Gladiator",
    },
    {
      rank: 2,
      user_id: "user-2",
      name: "Rohan Gupta",
      team: "Demo Technology Pvt Ltd",
      score: 85.0,
      award: "Platinum",
    },
    {
      rank: 3,
      user_id: "user-3",
      name: "Ananya Verma",
      team: "Demo Technology Pvt Ltd",
      score: 75.0,
      award: "Gold",
    },
    {
      rank: 4,
      user_id: "user-4",
      name: "Vikram Singh",
      team: "Demo Technology Pvt Ltd",
      score: 55.0,
      award: "Bronze",
    },
  ],
  my_rank: {
    rank: 2,
    score: 85.0,
    award: "Platinum",
  },
  award_distribution: {
    gladiator: 1,
    platinum: 1,
    gold: 1,
    bronze: 1,
  },
};

describe("Leaderboard Module Unit & Integration Tests", () => {
  beforeEach(() => {
    localStorage.clear();
    localStorage.setItem("token", "fake-test-token");
    jest.restoreAllMocks();
  });

  const renderLeaderboard = () => {
    return render(
      <MemoryRouter>
        <Leaderboard />
      </MemoryRouter>
    );
  };

  test("LDB-001: Displays loading state while fetching leaderboard data", async () => {
    jest.spyOn(global, "fetch").mockImplementation(
      () => new Promise(() => {}) // Never resolves to keep loading state
    );

    renderLeaderboard();

    expect(screen.getByText("Loading leaderboard...")).toBeInTheDocument();
  });

  test("LDB-002: Displays error message when API call fails", async () => {
    jest.spyOn(global, "fetch").mockResolvedValue({
      ok: false,
      status: 500,
    });

    renderLeaderboard();

    await waitFor(() => {
      expect(screen.getByText("Unable to load leaderboard")).toBeInTheDocument();
      expect(
        screen.getByText("Failed to fetch leaderboard (500)")
      ).toBeInTheDocument();
    });
  });

  test("LDB-003: Renders empty state message when no leaderboard data is available", async () => {
    jest.spyOn(global, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({
        items: [],
        my_rank: { rank: null, score: null, award: null },
        award_distribution: { gladiator: 0, platinum: 0, gold: 0, bronze: 0 },
      }),
    });

    renderLeaderboard();

    await waitFor(() => {
      expect(screen.getByText("No leaderboard data")).toBeInTheDocument();
      expect(
        screen.getByText(
          "There are no leaderboard records available for your organization."
        )
      ).toBeInTheDocument();
    });
  });

  test("LDB-004: Renders performance ranking rows, scores, and award icons successfully", async () => {
    jest.spyOn(global, "fetch").mockResolvedValue({
      ok: true,
      json: async () => mockLeaderboardResponse,
    });

    renderLeaderboard();

    await waitFor(() => {
      expect(screen.getByText("Akash Sharma")).toBeInTheDocument();
      expect(screen.getByText("Rohan Gupta")).toBeInTheDocument();
      expect(screen.getByText("Ananya Verma")).toBeInTheDocument();
      expect(screen.getByText("Vikram Singh")).toBeInTheDocument();
      expect(screen.getByText("95%")).toBeInTheDocument();
      expect(screen.getByText("85%")).toBeInTheDocument();
    });
  });

  test("LDB-005: Highlights logged-in user row with 'You' badge when user rank matches my_rank", async () => {
    jest.spyOn(global, "fetch").mockResolvedValue({
      ok: true,
      json: async () => mockLeaderboardResponse,
    });

    renderLeaderboard();

    await waitFor(() => {
      const youBadge = screen.getByText("You");
      expect(youBadge).toBeInTheDocument();
      expect(youBadge.closest(".leaderboard-row")).toHaveClass(
        "current-user-row"
      );
    });
  });

  test("LDB-006: Renders Award Distribution card with total count and category counts", async () => {
    jest.spyOn(global, "fetch").mockResolvedValue({
      ok: true,
      json: async () => mockLeaderboardResponse,
    });

    const { container } = renderLeaderboard();

    await waitFor(() => {
      const awardCard = container.querySelector(".award-card");
      expect(awardCard).toBeInTheDocument();
      expect(awardCard).toHaveTextContent("Award Distribution");
      expect(awardCard).toHaveTextContent("4"); // Total awards
      expect(awardCard).toHaveTextContent("Gladiator");
      expect(awardCard).toHaveTextContent("Platinum");
      expect(awardCard).toHaveTextContent("Gold");
      expect(awardCard).toHaveTextContent("Bronze");
    });
  });

  test("LDB-007: Renders My Rank card with rank number, score, and target progress", async () => {
    jest.spyOn(global, "fetch").mockResolvedValue({
      ok: true,
      json: async () => mockLeaderboardResponse,
    });

    const { container } = renderLeaderboard();

    await waitFor(() => {
      expect(screen.getByText("My Rank")).toBeInTheDocument();
      const myRankNumber = container.querySelector(".my-rank-number");
      expect(myRankNumber).toHaveTextContent("#2");
      expect(screen.getByText("Overall Score: 85%")).toBeInTheDocument();
      expect(screen.getByText("85% Target Progress")).toBeInTheDocument();
    });
  });

  test("LDB-008: Falls back to /leaderboard/ endpoint if /api/leaderboard/ returns 404", async () => {
    const fetchSpy = jest.spyOn(global, "fetch").mockImplementation((url) => {
      if (typeof url === "string" && url.endsWith("/api/leaderboard/")) {
        return Promise.resolve({ ok: false, status: 404 });
      }
      return Promise.resolve({
        ok: true,
        json: async () => mockLeaderboardResponse,
      });
    });

    renderLeaderboard();

    await waitFor(() => {
      expect(fetchSpy).toHaveBeenCalledTimes(2);
      expect(screen.getByText("Akash Sharma")).toBeInTheDocument();
    });
  });

  test("LDB-009: Period filter select option changes cleanly", async () => {
    jest.spyOn(global, "fetch").mockResolvedValue({
      ok: true,
      json: async () => mockLeaderboardResponse,
    });

    renderLeaderboard();

    await waitFor(() => {
      const periodSelect = screen.getByRole("combobox");
      expect(periodSelect).toHaveValue("current");

      fireEvent.change(periodSelect, { target: { value: "quarter" } });
      expect(periodSelect).toHaveValue("quarter");

      fireEvent.change(periodSelect, { target: { value: "year" } });
      expect(periodSelect).toHaveValue("year");
    });
  });

  test("LDB-010: Handles missing token in localStorage gracefully", async () => {
    localStorage.clear();

    const fetchSpy = jest.spyOn(global, "fetch").mockResolvedValue({
      ok: true,
      json: async () => mockLeaderboardResponse,
    });

    renderLeaderboard();

    await waitFor(() => {
      expect(fetchSpy).toHaveBeenCalled();
      const headers = fetchSpy.mock.calls[0][1].headers;
      expect(headers.Authorization).toBeUndefined();
    });
  });

  test("LDB-011: Handles missing my_rank safely without UI crash", async () => {
    jest.spyOn(global, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({
        items: mockLeaderboardResponse.items,
      }),
    });

    renderLeaderboard();

    await waitFor(() => {
      expect(screen.getByText("Your rank is not available yet.")).toBeInTheDocument();
    });
  });

  test("LDB-012: Calculates single-word name initials correctly", async () => {
    jest.spyOn(global, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({
        items: [
          { rank: 1, user_id: "u1", name: "Akash", team: "Tech", score: 90.0, award: "Gladiator" },
        ],
        my_rank: {},
        award_distribution: { gladiator: 1, platinum: 0, gold: 0, bronze: 0 },
      }),
    });

    renderLeaderboard();

    await waitFor(() => {
      expect(screen.getByText("A")).toBeInTheDocument();
      expect(screen.getByText("Akash")).toBeInTheDocument();
    });
  });

  test("LDB-013: Renders network failure / exception gracefully", async () => {
    jest.spyOn(global, "fetch").mockRejectedValue(new TypeError("Network error"));

    renderLeaderboard();

    await waitFor(() => {
      expect(screen.getByText("Unable to load leaderboard")).toBeInTheDocument();
      expect(screen.getByText("Network error")).toBeInTheDocument();
    });
  });

  test("LDB-014: Renders 0% score and Bronze tier correctly", async () => {
    jest.spyOn(global, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({
        items: [
          { rank: 1, user_id: "u0", name: "Zero User", team: "QA", score: 0.0, award: "Bronze" },
        ],
        my_rank: { rank: 1, score: 0.0, award: "Bronze" },
        award_distribution: { gladiator: 0, platinum: 0, gold: 0, bronze: 1 },
      }),
    });

    const { container } = renderLeaderboard();

    await waitFor(() => {
      expect(screen.getByText("Zero User")).toBeInTheDocument();
      expect(screen.getByText("0% Target Progress")).toBeInTheDocument();
      expect(container.querySelector(".my-rank-award")).toHaveTextContent("🥉");
    });
  });
});
