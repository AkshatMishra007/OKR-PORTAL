import React, {
  useEffect,
  useMemo,
  useState,
} from "react";
import axios from "axios";
import "./Performance.css";
import { API_URL } from "../Config/ApiEndpoint";

const SERIES_COLORS = [
  "#2563eb",
  "#16a34a",
  "#dc2626",
  "#9333ea",
  "#ea580c",
  "#0891b2",
  "#db2777",
  "#65a30d",
  "#7c3aed",
  "#0284c7",
  "#ca8a04",
  "#be123c",
];

const getAuthToken = () => {
  const keys = [
    "access_token",
    "token",
    "accessToken",
    "authToken",
  ];

  for (const key of keys) {
    const value = localStorage.getItem(key);

    if (value) {
      return value;
    }
  }

  return null;
};

const getApiConfig = () => {
  const token = getAuthToken();

  if (!token) {
    return {};
  }

  return {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  };
};

const getDisplayName = (item, index) => {
  const possibleNames = [
    item?.user_name,
    item?.employee_name,
    item?.assignee_name,
    item?.assigned_to_name,
    item?.user?.full_name,
    item?.user?.name,
    item?.assignee?.full_name,
    item?.assignee?.name,
    item?.assignee?.user?.full_name,
    item?.assignee?.user?.name,
  ];

  const name = possibleNames.find(
    (value) =>
      typeof value === "string" &&
      value.trim().length > 0
  );

  return name
    ? name.trim()
    : `User ${index + 1}`;
};

/*
 * Return the actual score recorded for a specific week.
 * Missing weeks return null; the user-series builder carries
 * the latest recorded value forward through Week 12.
 */
const getWeeklyScore = (okr, weekNumber) => {
  const updates = Array.isArray(okr?.weekly_updates)
    ? okr.weekly_updates
    : [];

  const matchingUpdates = updates.filter(
    (item) => Number(item?.week_number) === weekNumber
  );

  if (matchingUpdates.length > 0) {
    const latestUpdate = matchingUpdates[matchingUpdates.length - 1];
    const rawProgress =
      latestUpdate?.progress ??
      latestUpdate?.score ??
      latestUpdate?.progress_percentage ??
      latestUpdate?.display_progress_percentage ??
      latestUpdate?.value;

    const progress = Number(rawProgress);

    if (Number.isFinite(progress)) {
      return Math.max(0, Math.min(100, progress));
    }
  }

  const trackerEntries = Array.isArray(okr?.tracker_entries)
    ? okr.tracker_entries
    : [];

  if (trackerEntries.length >= weekNumber) {
    const entry = trackerEntries[weekNumber - 1];
    const received = Number(entry?.opportunities_received || 0);
    const completed = Number(entry?.opportunities_completed || 0);

    if (received > 0) {
      const trackerProgress = (completed / received) * 100;
      return Math.max(0, Math.min(100, trackerProgress));
    }
  }

  if (weekNumber === 1) {
    const okrProgress = Number(
      okr?.display_progress_percentage ??
      okr?.progress_percentage ??
      okr?.progress ??
      0
    );

    if (Number.isFinite(okrProgress) && okrProgress > 0) {
      return Math.max(0, Math.min(100, okrProgress));
    }
  }

  return null;
};

const getWeekLabel = (
  weekNumber,
  firstDate
) => {
  if (!firstDate) {
    return `Week ${weekNumber}`;
  }

  const date = new Date(firstDate);

  if (Number.isNaN(date.getTime())) {
    return `Week ${weekNumber}`;
  }

  date.setDate(
    date.getDate() +
    (weekNumber - 1) * 7
  );

  return `Week ${weekNumber} (${date.toLocaleDateString(
    "en-GB",
    {
      day: "2-digit",
      month: "short",
    }
  )})`;
};

const getBatchId = (batch) =>
  batch?.id ||
  batch?.batch_id ||
  batch?.value;

const getBatchName = (
  batch,
  index
) => {
  const possibleNames = [
    batch?.name,
    batch?.batch_name,
    batch?.title,
    batch?.batch?.name,
    batch?.batch?.batch_name,
  ];

  const name = possibleNames.find(
    (value) =>
      typeof value === "string" &&
      value.trim().length > 0
  );

  return name
    ? name.trim()
    : `Batch ${index + 1}`;
};

const Performance = () => {
  const [batches, setBatches] =
    useState([]);

  const [selectedBatchId, setSelectedBatchId] =
    useState("");

  const [okrs, setOkrs] =
    useState([]);

  const [loadingBatches, setLoadingBatches] =
    useState(true);

  const [loadingPerformance, setLoadingPerformance] =
    useState(false);

  const [error, setError] =
    useState("");

  /*
   * Fetch available batches.
   */
  useEffect(() => {
    const fetchBatches = async () => {
      try {
        setLoadingBatches(true);
        setError("");

        const response =
          await axios.get(
            `${API_URL}/api/batches/`,
            getApiConfig()
          );

        const responseData =
          response?.data;

        const batchData =
          Array.isArray(
            responseData?.data
          )
            ? responseData.data
            : Array.isArray(
              responseData?.items
            )
              ? responseData.items
              : Array.isArray(
                responseData
              )
                ? responseData
                : [];

        setBatches(batchData);

        /*
         * Select the first available batch
         * automatically so the complete
         * dashboard remains visible.
         */
        if (
          batchData.length > 0
        ) {
          const firstBatchId =
            getBatchId(
              batchData[0]
            );

          if (firstBatchId) {
            setSelectedBatchId(
              String(firstBatchId)
            );
          }
        }
      } catch (err) {
        console.error(
          "Failed to load batches:",
          err
        );

        setError(
          err?.response?.data?.detail ||
          "Unable to load batches."
        );

        setBatches([]);
      } finally {
        setLoadingBatches(false);
      }
    };

    fetchBatches();
  }, []);

  /*
   * Fetch performance data for the
   * selected batch.
   */
  useEffect(() => {
    const fetchPerformance =
      async () => {
        /*
         * Do not call the performance API
         * until a batch has been selected.
         */
        if (!selectedBatchId) {
          setOkrs([]);
          return;
        }

        try {
          setLoadingPerformance(true);
          setError("");

          const response =
            await axios.get(
              `${API_URL}/api/performance/`,
              {
                ...getApiConfig(),
                params: {
                  batch_id:
                    selectedBatchId,
                },
              }
            );

          const data =
            response?.data;

          setOkrs(
            Array.isArray(data?.data)
              ? data.data
              : []
          );
        } catch (err) {
          console.error(
            "Failed to load performance data:",
            err
          );

          setError(
            err?.response?.data
              ?.detail ||
            "Unable to load performance data."
          );

          setOkrs([]);
        } finally {
          setLoadingPerformance(false);
        }
      };

    fetchPerformance();
  }, [selectedBatchId]);

  /*
   * The Performance graph always contains a 12-week timeline.
   * Six weeks are visible at a time; the graph scrolls horizontally
   * to reach the remaining weeks.
   */
  const chartWeekCount = 12;

  /*
   * Build a complete 12-week series for every user.
   *
   * For each OKR: actual weekly values are used when present.
   * Missing weeks carry forward the most recent recorded value.
   * Before the first recorded value, the score remains 0.
   * Multiple OKRs for one user are averaged week-by-week.
   */
  const userSeries = useMemo(() => {
    const users = new Map();

    okrs.forEach((okr, index) => {
      const userId =
        okr?.assigned_to ||
        okr?.user_id ||
        okr?.assignee?.id ||
        `fallback-${index}`;

      if (!users.has(userId)) {
        users.set(userId, {
          id: userId,
          name: getDisplayName(okr, users.size),
          weeks: Array.from({ length: chartWeekCount }, () => []),
        });
      }

      const user = users.get(userId);
      let lastRecordedScore = 0;

      for (let week = 1; week <= chartWeekCount; week += 1) {
        const actualScore = getWeeklyScore(okr, week);

        if (actualScore !== null && actualScore !== undefined) {
          lastRecordedScore = actualScore;
        }

        user.weeks[week - 1].push(lastRecordedScore);
      }
    });

    return Array.from(users.values()).map((user) => ({
      ...user,
      scores: user.weeks.map((weekScores) => {
        if (!weekScores.length) {
          return 0;
        }

        return (
          weekScores.reduce((sum, value) => sum + value, 0) /
          weekScores.length
        );
      }),
    }));
  }, [okrs, chartWeekCount]);

  /*
   * IMPORTANT:
   * No artificial user limit.
   *
   * Every user belonging to the
   * selected batch is shown.
   */
  const chartUsers =
    userSeries;

  /*
   * Filter out unrecorded null scores for stats.
   */
  const allScores =
    chartUsers.flatMap(
      (user) => user.scores.filter((s) => typeof s === "number" && s !== null)
    );

  const topScore =
    allScores.length
      ? Math.max(...allScores)
      : 0;

  const lowestScore =
    allScores.length
      ? Math.min(...allScores)
      : 0;

  const averageScore =
    allScores.length
      ? allScores.reduce(
        (sum, score) =>
          sum + score,
        0
      ) / allScores.length
      : 0;

  /*
   * Score distribution using the latest recorded score.
   */
  const distribution = {
    Gladiator: 0,
    Platinum: 0,
    Gold: 0,
    Bronze: 0,
  };

  chartUsers.forEach(
    (user) => {
      const latestScore = user.scores.reduce((latest, score) => {
        return score !== null && score !== undefined ? score : latest;
      }, 0);

      if (
        latestScore >= 90
      ) {
        distribution.Gladiator += 1;
      } else if (
        latestScore >= 80
      ) {
        distribution.Platinum += 1;
      } else if (
        latestScore >= 60
      ) {
        distribution.Gold += 1;
      } else {
        distribution.Bronze += 1;
      }
    }
  );

  const gladiators =
    distribution.Gladiator;

  /*
   * Determine the first available
   * tracker date for week labels.
   */
  const firstAvailableDate =
    okrs
      .flatMap((okr) =>
        Array.isArray(
          okr?.tracker_entries
        )
          ? okr.tracker_entries
          : []
      )
      .map(
        (entry) =>
          entry?.week_start
      )
      .find(Boolean);

  const weekLabels = Array.from(
    { length: chartWeekCount },
    (_, index) =>
      getWeekLabel(
        index + 1,
        firstAvailableDate
      )
  );

  /*
   * SVG chart geometry with horizontal scrolling.
   */
  const stepWidth = 140;
  const chartLeft = 58;
  const chartRight = 40;
  const chartTop = 28;
  const chartBottom = 54;

  const plotWidth = Math.max(
    1,
    (chartWeekCount - 1) * stepWidth
  );

  const chartWidth =
    chartLeft +
    plotWidth +
    chartRight;

  const chartHeight = 340;

  const plotHeight =
    chartHeight -
    chartTop -
    chartBottom;

  const xForWeek = (index) =>
    chartLeft + index * stepWidth;

  const yForScore = (score) =>
    chartTop +
    ((100 - score) /
      100) *
    plotHeight;

  const getLinePoints = (scores) =>
    scores
      .map((score, index) => {
        if (score === null || score === undefined) {
          return null;
        }
        return `${xForWeek(index)},${yForScore(score)}`;
      })
      .filter(Boolean)
      .join(" ");

  const selectedBatch = batches.find(
    (batch) =>
      String(
        getBatchId(batch)
      ) ===
      String(selectedBatchId)
  );

  const selectedBatchName =
    selectedBatch
      ? getBatchName(
        selectedBatch,
        batches.indexOf(
          selectedBatch
        )
      )
      : "Select Batch";

  const isLoading =
    loadingBatches ||
    loadingPerformance;

  return (
    <div className="performance-page">
      {/* =====================================================
          HEADER
      ===================================================== */}

      <div className="performance-page-header">
        <div>
          <h1>Performance</h1>

          <div className="performance-breadcrumb">
            <span>OKR Portal</span>
            <span>›</span>
            <span>
              Performance Analytics
            </span>
          </div>
        </div>

        {/* =================================================
            BATCH SELECTOR
        ================================================= */}

        <div className="performance-cycle-selector">
          <label
            htmlFor="performance-batch"
            className="performance-batch-label"
          >
            Batch
          </label>

          <select
            id="performance-batch"
            value={selectedBatchId}
            onChange={(event) =>
              setSelectedBatchId(
                event.target.value
              )
            }
            disabled={
              loadingBatches ||
              batches.length === 0
            }
          >
            {batches.length ===
              0 ? (
              <option value="">
                No batches available
              </option>
            ) : (
              batches.map(
                (batch, index) => {
                  const batchId =
                    getBatchId(
                      batch
                    );

                  return (
                    <option
                      key={batchId}
                      value={batchId}
                    >
                      {getBatchName(
                        batch,
                        index
                      )}
                    </option>
                  );
                }
              )
            )}
          </select>
        </div>
      </div>

      {/* =====================================================
          WEEKLY VIEW ONLY
      ===================================================== */}

      <div className="performance-tabs">
        <button
          type="button"
          className="performance-tab active"
        >
          Weekly View
        </button>
      </div>

      {error && (
        <div className="performance-state performance-error">
          {error}
        </div>
      )}

      {isLoading ? (
        <div className="performance-state">
          Loading performance...
        </div>
      ) : (
        <div className="performance-layout">
          {/* =================================================
              MAIN PERFORMANCE ANALYTICS
          ================================================= */}

          <section className="performance-card analytics-card">
            <div className="performance-card-header">
              <div>
                <h2>
                  Performance Analytics
                </h2>

                <p>
                  Weekly performance —
                  {selectedBatchName}
                </p>
              </div>
            </div>

            <div className="performance-card-body">
              {/* =================================================
                  MAIN MULTI-USER WEEKLY GRAPH
              ================================================= */}

              <div className="performance-chart-wrapper">
                {chartUsers.length ===
                  0 ? (
                  <div className="performance-chart-empty">
                    No users found in this
                    batch.
                  </div>
                ) : (
                  <div className="performance-chart-scroll-container">
                    <div
                      className="performance-chart"
                      style={{ width: `${chartWidth}px` }}
                    >
                      <svg
                        viewBox={`0 0 ${chartWidth} ${chartHeight}`}
                        role="img"
                        aria-label="Weekly performance analytics by user"
                        style={{
                          width: `${chartWidth}px`,
                          minWidth: `${chartWidth}px`,
                        }}
                      >
                        {/* Horizontal grid */}

                        {[
                          0,
                          20,
                          40,
                          60,
                          80,
                          100,
                        ].map(
                          (value) => (
                            <g key={value}>
                              <line
                                x1={
                                  chartLeft
                                }
                                y1={yForScore(
                                  value
                                )}
                                x2={
                                  chartWidth -
                                  chartRight
                                }
                                y2={yForScore(
                                  value
                                )}
                                className="chart-grid"
                              />

                              <text
                                x={
                                  chartLeft -
                                  12
                                }
                                y={
                                  yForScore(
                                    value
                                  ) +
                                  4
                                }
                                textAnchor="end"
                                className="chart-y-label"
                              >
                                {
                                  value
                                }
                              </text>
                            </g>
                          )
                        )}

                        {/* Week labels */}

                        {weekLabels.map(
                          (
                            label,
                            index
                          ) => (
                            <text
                              key={label}
                              x={xForWeek(
                                index
                              )}
                              y={
                                chartHeight -
                                16
                              }
                              textAnchor="middle"
                              className="chart-x-label"
                            >
                              {
                                label
                              }
                            </text>
                          )
                        )}

                        {/* User lines */}

                        {chartUsers.map(
                          (
                            user,
                            userIndex
                          ) => {
                            const color =
                              SERIES_COLORS[
                              userIndex %
                              SERIES_COLORS.length
                              ];

                            const points =
                              getLinePoints(
                                user.scores
                              );

                            return (
                              <g
                                key={
                                  user.id
                                }
                              >
                                <polyline
                                  points={
                                    points
                                  }
                                  className="performance-series-line"
                                  style={{
                                    stroke:
                                      color,
                                  }}
                                />

                                {user.scores.map(
                                  (
                                    score,
                                    weekIndex
                                  ) => {
                                    if (score === null || score === undefined) {
                                      return null;
                                    }
                                    return (
                                      <circle
                                        key={`${user.id}-${weekIndex}`}
                                        cx={xForWeek(
                                          weekIndex
                                        )}
                                        cy={yForScore(
                                          score
                                        )}
                                        r="4"
                                        className="performance-series-point"
                                        style={{
                                          fill:
                                            color,
                                          stroke:
                                            color,
                                        }}
                                      />
                                    );
                                  }
                                )}
                              </g>
                            );
                          }
                        )}
                      </svg>
                    </div>
                  </div>
                )}
              </div>

              {/* =================================================
                  LEGEND
              ================================================= */}

              {chartUsers.length >
                0 && (
                  <div className="performance-legend">
                    {chartUsers.map(
                      (
                        user,
                        index
                      ) => {
                        const color =
                          SERIES_COLORS[
                          index %
                          SERIES_COLORS.length
                          ];

                        return (
                          <div
                            className="performance-legend-item"
                            key={
                              user.id
                            }
                          >
                            <span
                              className="performance-legend-marker"
                              style={{
                                backgroundColor:
                                  color,
                              }}
                            />

                            <span>
                              {
                                user.name
                              }
                            </span>
                          </div>
                        );
                      }
                    )}
                  </div>
                )}
            </div>
          </section>

          {/* =================================================
              RIGHT COLUMN
          ================================================= */}

          <aside className="performance-right-column">
            {/* =================================================
                SCORE DISTRIBUTION
            ================================================= */}

            <section className="performance-card">
              <div className="performance-card-header">
                <h2>
                  Score Distribution
                </h2>
              </div>

              <div className="performance-card-body">
                <div className="distribution-chart">
                  {[
                    [
                      "90–100",
                      distribution.Gladiator,
                      "gladiator",
                    ],
                    [
                      "80–90",
                      distribution.Platinum,
                      "platinum",
                    ],
                    [
                      "60–80",
                      distribution.Gold,
                      "gold",
                    ],
                    [
                      "<60",
                      distribution.Bronze,
                      "bronze",
                    ],
                  ].map(
                    ([
                      label,
                      count,
                      className,
                    ]) => {
                      const maxCount =
                        Math.max(
                          distribution.Gladiator,
                          distribution.Platinum,
                          distribution.Gold,
                          distribution.Bronze,
                          1
                        );

                      const height =
                        count === 0
                          ? 22
                          : 22 +
                          (count /
                            maxCount) *
                          112;

                      return (
                        <div
                          className="distribution-column"
                          key={label}
                        >
                          <div
                            className={`distribution-value-bar ${className}`}
                            style={{
                              height: `${height}px`,
                            }}
                          >
                            <span>
                              {
                                count
                              }
                            </span>
                          </div>

                          <span className="distribution-label">
                            {
                              label
                            }
                          </span>
                        </div>
                      );
                    }
                  )}
                </div>
              </div>
            </section>

            {/* =================================================
                QUICK STATS
            ================================================= */}

            <section className="performance-card">
              <div className="performance-card-header">
                <h2>
                  Quick Stats
                </h2>
              </div>

              <div className="performance-card-body">
                <div className="quick-stats-grid">
                  <div className="quick-stat">
                    <strong className="quick-stat-green">
                      {topScore.toFixed(
                        1
                      )}
                    </strong>

                    <span>
                      Top Score
                    </span>
                  </div>

                  <div className="quick-stat">
                    <strong className="quick-stat-amber">
                      {lowestScore.toFixed(
                        1
                      )}
                    </strong>

                    <span>
                      Lowest Score
                    </span>
                  </div>

                  <div className="quick-stat">
                    <strong className="quick-stat-blue">
                      {averageScore.toFixed(
                        1
                      )}
                    </strong>

                    <span>
                      Avg Score
                    </span>
                  </div>

                  <div className="quick-stat">
                    <strong className="quick-stat-platinum">
                      {
                        gladiators
                      }
                    </strong>

                    <span>
                      Gladiators
                    </span>
                  </div>
                </div>
              </div>
            </section>
          </aside>
        </div>
      )}
    </div>
  );
};

export default Performance;