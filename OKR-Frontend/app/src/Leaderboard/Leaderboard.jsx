import React, { useEffect, useMemo, useState } from "react";
import "./Leaderboard.css";
import { API_URL } from "../Config/ApiEndpoint";

const AWARDS = [
  { key: "gladiator", label: "Gladiator" },
  { key: "platinum", label: "Platinum" },
  { key: "gold", label: "Gold" },
  { key: "bronze", label: "Bronze" },
];

const getAwardIcon = (award) => {
  switch (award) {
    case "Gladiator":
      return "🏆";
    case "Platinum":
      return "💎";
    case "Gold":
      return "🥇";
    case "Bronze":
      return "🥉";
    default:
      return "🏅";
  }
};

const getInitials = (name = "") =>
  name
    .split(" ")
    .filter(Boolean)
    .map((part) => part[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

const getAuthToken = () => {
  return (
    localStorage.getItem("token") ||
    localStorage.getItem("access_token") ||
    localStorage.getItem("accessToken") ||
    localStorage.getItem("authToken")
  );
};

const Leaderboard = () => {
  const [leaderboardData, setLeaderboardData] = useState([]);
  const [myRank, setMyRank] = useState({
    rank: null,
    score: null,
    award: null,
  });
  const [awardDistribution, setAwardDistribution] = useState({
    gladiator: 0,
    platinum: 0,
    gold: 0,
    bronze: 0,
  });

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchLeaderboard = async () => {
      try {
        setLoading(true);
        setError("");

        const token = getAuthToken();

        const headers = {
          "Content-Type": "application/json",
        };

        if (token) {
          headers.Authorization = `Bearer ${token}`;
        }

        let response = await fetch(`${API_URL}/api/leaderboard/`, {
          method: "GET",
          headers,
        });

        if (!response.ok && response.status === 404) {
          response = await fetch(`${API_URL}/api/leaderboard/`, {
            method: "GET",
            headers,
          });
        }

        if (!response.ok) {
          throw new Error(
            `Failed to fetch leaderboard (${response.status})`
          );
        }

        const data = await response.json();

        setLeaderboardData(data.items || []);

        setMyRank(
          data.my_rank || {
            rank: null,
            score: null,
            award: null,
          }
        );

        setAwardDistribution(
          data.award_distribution || {
            gladiator: 0,
            platinum: 0,
            gold: 0,
            bronze: 0,
          }
        );
      } catch (err) {
        console.error("Leaderboard API error:", err);
        setError(
          err.message || "Unable to load leaderboard."
        );
      } finally {
        setLoading(false);
      }
    };

    fetchLeaderboard();
  }, []);

  const totalAwards = useMemo(
    () =>
      Object.values(awardDistribution).reduce(
        (total, count) => total + Number(count || 0),
        0
      ),
    [awardDistribution]
  );

  const donutStyle = useMemo(() => {
    if (!totalAwards) {
      return {
        background: "conic-gradient(#e5e7eb 0deg 360deg)",
      };
    }

    let currentDegree = 0;

    const colors = {
      gladiator: "#4778ed",
      platinum: "#aebbd0",
      gold: "#ffd166",
      bronze: "#f2556c",
    };

    const segments = [];

    AWARDS.forEach(({ key }) => {
      const count = Number(awardDistribution[key] || 0);

      if (!count) return;

      const degree = (count / totalAwards) * 360;
      const endDegree = currentDegree + degree;

      segments.push(
        `${colors[key]} ${currentDegree}deg ${endDegree}deg`
      );

      currentDegree = endDegree;
    });

    return {
      background: `conic-gradient(${segments.join(", ")})`,
    };
  }, [awardDistribution, totalAwards]);

  if (loading) {
    return (
      <div className="leaderboard-page">
        <div className="leaderboard-empty">
          <div className="leaderboard-empty-icon">⏳</div>
          <h3>Loading leaderboard...</h3>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="leaderboard-page">
        <div className="leaderboard-empty">
          <div className="leaderboard-empty-icon">⚠️</div>
          <h3>Unable to load leaderboard</h3>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="leaderboard-page">
      <div className="leaderboard-header">
        <div>
          <h1>Leaderboard</h1>
          <p>
            View performance rankings, scores and awards.
          </p>
        </div>

        <select className="leaderboard-period" defaultValue="current">
          <option value="current">Current Period</option>
          <option value="quarter">Quarter</option>
          <option value="year">Year</option>
        </select>
      </div>

      <div className="leaderboard-layout">
        <section className="leaderboard-card">
          <div className="leaderboard-card-header">
            <h2>Performance Ranking</h2>
          </div>

          {leaderboardData.length === 0 ? (
            <div className="leaderboard-empty">
              <div className="leaderboard-empty-icon">🏆</div>
              <h3>No leaderboard data</h3>
              <p>
                There are no leaderboard records available
                for your organization.
              </p>
            </div>
          ) : (
            <div className="leaderboard-list">
              {leaderboardData.map((item) => {
                const isCurrentUser =
                  item.rank === myRank.rank;

                return (
                  <div
                    className={`leaderboard-row ${
                      isCurrentUser
                        ? "current-user-row"
                        : ""
                    }`}
                    key={item.user_id}
                  >
                    <div className="rank-number">
                      #{item.rank}
                    </div>

                    <div className="leaderboard-avatar">
                      {getInitials(item.name)}
                    </div>

                    <div className="leaderboard-user">
                      <div className="leaderboard-name">
                        {item.name}
                        {isCurrentUser && (
                          <span
                            className="you-badge"
                            style={{
                              marginLeft: "8px",
                              fontSize: "10px",
                              padding: "2px 6px",
                              borderRadius: "4px",
                              background: "rgba(71, 120, 237, 0.15)",
                              color: "var(--accent)",
                            }}
                          >
                            You
                          </span>
                        )}
                      </div>
                      <div className="leaderboard-team">
                        {item.team || "General"}
                      </div>
                    </div>

                    <div className="leaderboard-score">
                      <span>{item.score}%</span>
                      <span
                        className="award-icon"
                        title={item.award}
                      >
                        {getAwardIcon(item.award)}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </section>

        <aside className="leaderboard-side">
          <section className="award-card">
            <div className="side-card-header">
              <h2>Award Distribution</h2>
            </div>

            <div className="award-chart-container">
              <div
                className="award-donut"
                style={donutStyle}
              >
                <div className="award-donut-center">
                  <strong>{totalAwards}</strong>
                  <span>Total</span>
                </div>
              </div>
            </div>

            <div className="award-legend">
              {AWARDS.map(({ key, label }) => (
                <div className="award-legend-row" key={key}>
                  <div className="award-label">
                    <span
                      className={`award-dot ${key}`}
                    />
                    <span>{label}</span>
                  </div>

                  <strong>
                    {awardDistribution[key] || 0}
                  </strong>
                </div>
              ))}
            </div>
          </section>

          <section className="my-rank-card">
            <div className="side-card-header">
              <h2>My Rank</h2>
            </div>

            {myRank.rank ? (
              <div className="my-rank-content">
                <div className="my-rank-award">
                  {getAwardIcon(myRank.award)}
                </div>

                <div className="my-rank-number">
                  #{myRank.rank}
                </div>

                <div className="my-rank-name">
                  {myRank.award}
                </div>

                <div className="my-rank-score">
                  Overall Score: {myRank.score}%
                </div>

                <div className="rank-progress">
                  <div
                    className="rank-progress-fill"
                    style={{
                      width: `${Math.min(
                        100,
                        Math.max(0, myRank.score || 0)
                      )}%`,
                    }}
                  />
                </div>

                <div className="rank-progress-label">
                  <span>
                    {myRank.score}% Target Progress
                  </span>
                </div>
              </div>
            ) : (
              <div className="my-rank-empty">
                <p>Your rank is not available yet.</p>
              </div>
            )}
          </section>
        </aside>
      </div>
    </div>
  );
};

export default Leaderboard;