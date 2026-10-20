import { useEffect, useRef, useState } from "react";
import "./TeamOkr.css";
import { API_URL } from "../Config/ApiEndpoint";

function TeamOkr() {
  // =========================================================
  // BASIC STATES
  // =========================================================

  const [batches, setBatches] = useState([]);
  const [selectedBatchId, setSelectedBatchId] = useState("");

  const [okrs, setOkrs] = useState([]);
  const [filteredOkrs, setFilteredOkrs] = useState([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  const [organizations, setOrganizations] = useState([]);
  const [selectedOrganizationId, setSelectedOrganizationId] = useState("");

  const [currentUser, setCurrentUser] = useState(null);

  const [loadingOrganizations, setLoadingOrganizations] =
    useState(false);

  const [weeklyUpdates, setWeeklyUpdates] = useState({});
  const [trackerEntries, setTrackerEntries] = useState({});
  const [loadingTrackerEntries, setLoadingTrackerEntries] =
    useState({});
  const [trackerEntryErrors, setTrackerEntryErrors] =
    useState({});
  const [loadingWeeklyUpdates, setLoadingWeeklyUpdates] =
    useState({});
  const [weeklyUpdateErrors, setWeeklyUpdateErrors] =
    useState({});
  const weeklyUpdatesInFlight = useRef({});
  const trackerEntriesInFlight = useRef({});

  const [searchValue, setSearchValue] = useState("");

  const [filters, setFilters] = useState({
    year: "",
    quarter: "",
  });

  const [loadingBatches, setLoadingBatches] = useState(false);
  const [loadingOkrs, setLoadingOkrs] = useState(false);

  const [error, setError] = useState("");

  // =========================================================
  // WEEK FILTER
  // =========================================================

  const [selectedWeek, setSelectedWeek] = useState("");

  // =========================================================
  // OKR VIEW MODAL STATES
  // =========================================================

  const [selectedOkr, setSelectedOkr] = useState(null);

  const [isShowOkrModalOpen, setIsShowOkrModalOpen] =
    useState(false);

  const [activeHistoryTab, setActiveHistoryTab] =
    useState("weekly");

  const [expandedWeeks, setExpandedWeeks] =
    useState({});

  // =========================================================
  // FOGS / HURDLES HISTORY
  // =========================================================

  const [fogsHurdlesHistory, setFogsHurdlesHistory] =
    useState({});

  const [isLoadingFogsHurdles, setIsLoadingFogsHurdles] =
    useState(false);

  // =========================================================
  // YEARS
  // =========================================================

  const currentYear = new Date().getFullYear();

  const years = Array.from(
    { length: 5 },
    (_, index) => currentYear - index
  );

  // =========================================================
  // FETCH CURRENT USER
  // =========================================================

  const fetchCurrentUser = async () => {
    try {
      const response = await fetch(
        `${API_URL}/api/users/me`,
        {
          headers: {
            Authorization:
              `Bearer ${localStorage.getItem("token")}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error("Failed to fetch current user");
      }

      return await response.json();
    } catch (error) {
      console.error(
        "Error fetching current user:",
        error
      );

      throw error;
    }
  };

  useEffect(() => {
    const loadCurrentUser = async () => {
      try {
        const user = await fetchCurrentUser();

        setCurrentUser(user);
      } catch (error) {
        console.error(
          "Failed to load current user:",
          error
        );
      }
    };

    loadCurrentUser();
  }, []);

  // =========================================================
  // GET USER ROLE
  // =========================================================

  const userRole =
    currentUser
      ?.organization_memberships?.[0]
      ?.role?.name || "";

  // =========================================================
  // FETCH ORGANIZATIONS
  // =========================================================

  const fetchOrganizations = async () => {
    try {
      setLoadingOrganizations(true);
      setError("");

      const response = await fetch(
        `${API_URL}/api/organizations/?page=1&size=100`,
        {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
            Authorization:
              `Bearer ${localStorage.getItem("token")}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error(
          "Failed to fetch organizations"
        );
      }

      const result = await response.json();

      const allOrganizations =
        result.data || [];

      setOrganizations(allOrganizations);
    } catch (error) {
      console.error(
        "Error fetching organizations:",
        error
      );

      setOrganizations([]);
    } finally {
      setLoadingOrganizations(false);
    }
  };

  useEffect(() => {
    if (userRole === "SUPER_ADMIN") {
      fetchOrganizations();
    }
  }, [currentUser]);

  // =========================================================
  // FETCH BATCHES
  // =========================================================

  const fetchBatches = async () => {
    try {
      setLoadingBatches(true);
      setError("");

      if (!currentUser) {
        return;
      }

      const loggedInUserId =
        currentUser.id;

      const membership =
        currentUser.organization_memberships?.[0];

      let response;

      // ======================================================
      // SUPER ADMIN
      // ======================================================

      if (userRole === "SUPER_ADMIN") {
        if (!selectedOrganizationId) {
          setBatches([]);
          setSelectedBatchId("");
          setSelectedWeek("");
          return;
        }

        response = await fetch(
          `${API_URL}/api/batches/?organization_id=${selectedOrganizationId}&sort_by=created_at&sort_order=desc&page=1&size=100`,
          {
            method: "GET",
            headers: {
              "Content-Type": "application/json",
              "X-Organization-ID":
                selectedOrganizationId,
              Authorization:
                `Bearer ${localStorage.getItem("token")}`,
            },
          }
        );
      }

      // ======================================================
      // ORG ADMIN / BATCH ADMIN
      // ======================================================

      else {
        if (!membership) {
          setBatches([]);
          setSelectedBatchId("");
          setSelectedWeek("");
          return;
        }

        const organizationId =
          membership.organization_id;

        response = await fetch(
          `${API_URL}/api/batches/?organization_id=${organizationId}&sort_by=created_at&sort_order=desc&page=1&size=100`,
          {
            method: "GET",
            headers: {
              "Content-Type": "application/json",
              "X-Organization-ID":
                organizationId,
              Authorization:
                `Bearer ${localStorage.getItem("token")}`,
            },
          }
        );
      }

      if (!response.ok) {
        throw new Error(
          "Failed to fetch batches"
        );
      }

      const result =
        await response.json();

      const allBatches =
        result.data || [];

      let visibleBatches = [];

      // ======================================================
      // SUPER ADMIN
      // ======================================================

      if (userRole === "SUPER_ADMIN") {
        visibleBatches = allBatches;
      }

      // ======================================================
      // ORG ADMIN
      // ======================================================

      else if (userRole === "ORG_ADMIN") {
        visibleBatches = allBatches;
      }

      // ======================================================
      // BATCH ADMIN
      // ======================================================

      else {
        visibleBatches =
          allBatches.filter(
            (batch) =>
              batch.admins?.some(
                (admin) =>
                  admin.id ===
                  loggedInUserId
              )
          );
      }

      setBatches(visibleBatches);

      setSelectedBatchId("");
      setSelectedWeek("");
    } catch (error) {
      console.error(
        "Error fetching batches:",
        error
      );

      setError(
        "Failed to load batches."
      );

      setBatches([]);
      setSelectedBatchId("");
      setSelectedWeek("");
    } finally {
      setLoadingBatches(false);
    }
  };

  // =========================================================
  // FETCH WEEKLY UPDATES
  // =========================================================

  const fetchWeeklyUpdatesBatch = async (okrIds) => {
    try {
      if (
        !okrIds ||
        okrIds.length === 0
      ) {
        setWeeklyUpdates({});
        return;
      }

      const results =
        await Promise.all(
          okrIds.map(
            async (okrId) => {
              try {
              const response =
                await fetch(
                  `${API_URL}/api/okrs/${okrId}/weekly-updates`,
                  {
                    headers: {
                      Authorization:
                        `Bearer ${localStorage.getItem("token")}`,
                    },
                  }
                );

              const result =
                await response.json();

              if (!response.ok) {
                throw new Error(
                  `Failed to fetch weekly updates for OKR ${okrId}`
                );
              }

              const updates = Array.isArray(result.data)
                ? result.data
                : [];

              setWeeklyUpdates((previous) => ({
                ...previous,
                [okrId]: updates,
              }));
              setWeeklyUpdateErrors((previous) => {
                const next = { ...previous };
                delete next[okrId];
                return next;
              });

              return [
                okrId,
                updates,
              ];
              } catch (error) {
                console.error(
                  `Error fetching weekly updates for OKR ${okrId}:`,
                  error
                );
                setWeeklyUpdateErrors((previous) => ({
                  ...previous,
                  [okrId]: "Failed to load weekly updates. Please try again.",
                }));
                return [okrId, null];
              }
            }
          )
        );

      const updatesObject =
        Object.fromEntries(
          results.filter(([, updates]) => updates !== null)
        );

      setWeeklyUpdates((previous) => ({
        ...previous,
        ...updatesObject,
      }));
    } catch (error) {
      console.error(
        "Error fetching weekly updates:",
        error
      );
      okrIds?.forEach((okrId) => {
        setWeeklyUpdateErrors((previous) => ({
          ...previous,
          [okrId]: "Failed to load weekly updates. Please try again.",
        }));
      });
    }
  };

  const fetchWeeklyUpdates = async (okrIds) => {
    const updatesToLoad = [
      ...new Set(okrIds),
    ].filter(
      (okrId) =>
        !Object.prototype.hasOwnProperty.call(
          weeklyUpdates,
          okrId
        ) &&
        !weeklyUpdatesInFlight.current[okrId]
    );

    updatesToLoad.forEach((okrId) => {
      weeklyUpdatesInFlight.current[okrId] = true;
    });

    setLoadingWeeklyUpdates((previous) => {
      const next = { ...previous };
      updatesToLoad.forEach((okrId) => {
        next[okrId] = true;
      });
      return next;
    });

    for (
      let startIndex = 0;
      startIndex < updatesToLoad.length;
      startIndex += 8
    ) {
      const batch = updatesToLoad.slice(
        startIndex,
        startIndex + 8
      );

      setWeeklyUpdateErrors((previous) => {
        const next = { ...previous };
        batch.forEach((okrId) => {
          delete next[okrId];
        });
        return next;
      });

      try {
        await fetchWeeklyUpdatesBatch(batch);
      } finally {
        batch.forEach((okrId) => {
          delete weeklyUpdatesInFlight.current[okrId];
        });
        setLoadingWeeklyUpdates((previous) => {
          const next = { ...previous };
          batch.forEach((okrId) => {
            next[okrId] = false;
          });
          return next;
        });
      }
    }
  };

  const fetchTrackerEntriesBatch = async (okrIds) => {
    const results = await Promise.all(
      okrIds.map(async (okrId) => {
        try {
          const response = await fetch(
            `${API_URL}/api/okrs/${okrId}/tracker-entries?page=1&size=100&sort_by=week_start&sort_order=asc`,
            {
              method: "GET",
              headers: {
                Accept: "*/*",
                Authorization: `Bearer ${localStorage.getItem("token")}`,
              },
            }
          );

          if (!response.ok) {
            throw new Error(
              `Failed to fetch tracker entries for OKR ${okrId}`
            );
          }

          const result = await response.json();
          const entries = Array.isArray(result.data)
            ? result.data
            : [];

          setTrackerEntries((previous) => ({
            ...previous,
            [okrId]: entries,
          }));
          setTrackerEntryErrors((previous) => {
            const next = { ...previous };
            delete next[okrId];
            return next;
          });

          return [okrId, entries];
        } catch (error) {
          console.error(
            `Error fetching tracker entries for OKR ${okrId}:`,
            error
          );
          setTrackerEntryErrors((previous) => ({
            ...previous,
            [okrId]: "Failed to load tracker history. Please try again.",
          }));
          return [okrId, null];
        }
      })
    );

    const fetchedEntries = Object.fromEntries(
      results.filter(([, entries]) => entries !== null)
    );
    setTrackerEntries((previous) => ({
      ...previous,
      ...fetchedEntries,
    }));
  };

  const fetchTrackerEntries = async (okrIds) => {
    const entriesToLoad = [
      ...new Set(okrIds),
    ].filter(
      (okrId) =>
        !Object.prototype.hasOwnProperty.call(
          trackerEntries,
          okrId
        ) &&
        !trackerEntriesInFlight.current[okrId]
    );

    entriesToLoad.forEach((okrId) => {
      trackerEntriesInFlight.current[okrId] = true;
    });

    setLoadingTrackerEntries((previous) => {
      const next = { ...previous };
      entriesToLoad.forEach((okrId) => {
        next[okrId] = true;
      });
      return next;
    });
    setTrackerEntryErrors((previous) => {
      const next = { ...previous };
      entriesToLoad.forEach((okrId) => {
        delete next[okrId];
      });
      return next;
    });

    for (
      let startIndex = 0;
      startIndex < entriesToLoad.length;
      startIndex += 8
    ) {
      const batch = entriesToLoad.slice(
        startIndex,
        startIndex + 8
      );

      try {
        await fetchTrackerEntriesBatch(batch);
      } finally {
        batch.forEach((okrId) => {
          delete trackerEntriesInFlight.current[okrId];
        });
        setLoadingTrackerEntries((previous) => {
          const next = { ...previous };
          batch.forEach((okrId) => {
            next[okrId] = false;
          });
          return next;
        });
      }
    }
  };

  // =========================================================
  // FETCH OKRs
  // =========================================================

  const fetchOkrs = async () => {
    try {
      setLoadingOkrs(true);
      setError("");

      if (!currentUser) {
        return;
      }

      const userOrganizationId =
        currentUser
          ?.organization_memberships?.[0]
          ?.organization_id;

      const response = await fetch(
        `${API_URL}/api/okrs/?page=1&size=300`,
        {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
            Authorization:
              `Bearer ${localStorage.getItem("token")}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error(
          "Failed to fetch OKRs"
        );
      }

      const result =
        await response.json();

      const allOkrs =
        result.data || [];

      let batchOkrs = [];

      // ======================================================
      // SUPER ADMIN
      // ======================================================

      if (userRole === "SUPER_ADMIN") {
        batchOkrs = selectedBatchId
          ? allOkrs.filter(
              (okr) =>
                okr.batch_id ===
                selectedBatchId
            )
          : allOkrs.filter(
              (okr) =>
                !selectedOrganizationId ||
                okr.organization_id ===
                  selectedOrganizationId
            );
      }

      // ======================================================
      // ORG ADMIN
      // ======================================================

      else if (userRole === "ORG_ADMIN") {
        const organizationOkrs =
          allOkrs.filter(
            (okr) =>
              okr.organization_id ===
              userOrganizationId
          );

        batchOkrs = selectedBatchId
          ? organizationOkrs.filter(
              (okr) =>
                okr.batch_id ===
                selectedBatchId
            )
          : organizationOkrs;
      }

      // ======================================================
      // BATCH ADMIN
      // ======================================================

      else {
        const adminBatchIds =
          batches.map(
            (batch) => batch.id
          );

        batchOkrs = selectedBatchId
          ? allOkrs.filter(
              (okr) =>
                okr.batch_id ===
                  selectedBatchId &&
                adminBatchIds.includes(
                  okr.batch_id
                )
            )
          : allOkrs.filter(
              (okr) =>
                adminBatchIds.includes(
                  okr.batch_id
                )
            );
      }

      setOkrs(batchOkrs);
      fetchWeeklyUpdates(
        batchOkrs.map((okr) => okr.id)
      ).catch((error) => {
        console.error(
          "Error loading OKR weekly updates:",
          error
        );
      });
      fetchTrackerEntries(
        batchOkrs
          .filter((okr) => okr.tracker_enabled)
          .map((okr) => okr.id)
      ).catch((error) => {
        console.error(
          "Error loading tracker entries:",
          error
        );
      });

    } catch (error) {
      console.error(
        "Error fetching OKRs:",
        error
      );

      setError(
        "Failed to load OKRs."
      );

      setOkrs([]);
    } finally {
      setLoadingOkrs(false);
    }
  };

  // =========================================================
  // SEARCH
  // =========================================================

  const handleSearch = (value) => {
    setSearchValue(value);
  };

  // =========================================================
  // APPLY FILTERS
  // =========================================================

  const applyFilters = (
    search,
    currentFilters,
    batchId,
    organizationId
  ) => {
    let result = [...okrs];

    // ======================================================
    // ORGANIZATION
    // ======================================================

    if (organizationId) {
      result =
        result.filter(
          (okr) =>
            okr.organization_id ===
            organizationId
        );
    }

    // ======================================================
    // BATCH
    // ======================================================

    if (batchId) {
      result =
        result.filter(
          (okr) =>
            okr.batch_id ===
            batchId
        );
    }

    // ======================================================
    // YEAR
    // ======================================================

    if (currentFilters.year) {
      result =
        result.filter(
          (okr) =>
            String(
              okr.batch?.year
            ) ===
            String(
              currentFilters.year
            )
        );
    }

    // ======================================================
    // QUARTER
    // ======================================================

    if (currentFilters.quarter) {
      result =
        result.filter(
          (okr) =>
            okr.batch?.quarter ===
            currentFilters.quarter
        );
    }

    // ======================================================
    // SEARCH
    // ======================================================

    if (search.trim()) {
      const searchText =
        search
          .toLowerCase()
          .trim();

      result =
        result.filter(
          (okr) => {
            const objective =
              (
                okr.objective ||
                ""
              ).toLowerCase();

            const keyResult =
              (
                okr.key_results ||
                ""
              ).toLowerCase();

            const employeeName =
              getEmployeeName(okr).toLowerCase();

            return (
              objective.includes(
                searchText
              ) ||
              keyResult.includes(
                searchText
              ) ||
              employeeName.includes(
                searchText
              )
            );
          }
        );
    }

    const getEmployeeNameForSort = (okr) => {
      if (okr.user?.name) {
        return okr.user.name;
      }

      if (okr.user?.first_name || okr.user?.last_name) {
        return `${okr.user?.first_name || ""} ${
          okr.user?.last_name || ""
        }`.trim();
      }

      if (
        okr.assignee?.user?.first_name ||
        okr.assignee?.user?.last_name
      ) {
        return `${okr.assignee?.user?.first_name || ""} ${
          okr.assignee?.user?.last_name || ""
        }`.trim();
      }

      if (okr.user_name) {
        return okr.user_name;
      }

      if (okr.assignee?.user?.username) {
        return okr.assignee.user.username;
      }

      return "N/A";
    };

    const getOkrTypeOrder = (okrType) => {
      const type = String(okrType || "").toLowerCase();

      if (type === "professional") {
        return 0;
      }

      if (type === "personal") {
        return 1;
      }

      return 2;
    };

    result.sort((a, b) => {
      const employeeComparison = getEmployeeNameForSort(a).localeCompare(
        getEmployeeNameForSort(b),
        undefined,
        { sensitivity: "base" }
      );

      if (employeeComparison !== 0) {
        return employeeComparison;
      }

      return getOkrTypeOrder(a.okr_type) - getOkrTypeOrder(b.okr_type);
    });

    setFilteredOkrs(result);
  };

  // =========================================================
  // GET CURRENT BATCH
  // =========================================================

  const selectedBatch =
    batches.find(
      (batch) =>
        batch.id ===
        selectedBatchId
    );

  // =========================================================
  // GET AVAILABLE WEEKS
  // BASED ON SELECTED BATCH
  // =========================================================

  const getAvailableWeeks = (
    batch
  ) => {
    if (
      !batch?.start_date ||
      !batch?.end_date
    ) {
      return [];
    }

    const startDate =
      new Date(
        batch.start_date
      );

    const endDate =
      new Date(
        batch.end_date
      );

    startDate.setHours(
      0,
      0,
      0,
      0
    );

    endDate.setHours(
      0,
      0,
      0,
      0
    );

    if (
      endDate < startDate
    ) {
      return [];
    }

    const differenceInMilliseconds =
      endDate -
      startDate;

    const totalDays =
      Math.floor(
        differenceInMilliseconds /
          (1000 * 60 * 60 * 24)
      ) + 1;

    const totalWeeks =
      Math.ceil(
        totalDays / 7
      );

    const weekCount =
      Math.min(
        totalWeeks,
        13
      );

    return Array.from(
      {
        length: weekCount,
      },
      (_, index) =>
        index + 1
    );
  };

  const availableWeeks =
    getAvailableWeeks(
      selectedBatch
    );

  // =========================================================
  // GET WEEK DATE RANGE
  // BASED ON SELECTED BATCH
  // =========================================================

  const getWeekDateRange = (
    weekNumber,
    batch = selectedBatch
  ) => {
    if (
      !batch?.start_date ||
      !batch?.end_date ||
      !weekNumber
    ) {
      return "";
    }

    const startDate =
      new Date(
        batch.start_date
      );

    const endDate =
      new Date(
        batch.end_date
      );

    startDate.setHours(
      0,
      0,
      0,
      0
    );

    endDate.setHours(
      0,
      0,
      0,
      0
    );

    const weekStart =
      new Date(
        startDate
      );

    weekStart.setDate(
      weekStart.getDate() +
        (Number(weekNumber) - 1) *
          7
    );

    const weekEnd =
      new Date(
        weekStart
      );

    weekEnd.setDate(
      weekEnd.getDate() + 6
    );

    // Don't allow displayed week end
    // to go beyond batch end date.
    if (
      weekEnd > endDate
    ) {
      weekEnd.setTime(
        endDate.getTime()
      );
    }

    const formatDate =
      (date) =>
        date.toLocaleDateString(
          "en-IN",
          {
            day: "2-digit",
            month: "short",
            year: "numeric",
          }
        );

    return `${formatDate(
      weekStart
    )} - ${formatDate(
      weekEnd
    )}`;
  };

  // =========================================================
  // GET LATEST UPDATE FOR SELECTED WEEK
  //
  // If Week 5 selected:
  // use latest update where week_number <= 5
  // =========================================================

  const getLatestOkrUpdate = (
    okr,
    weekNumber = selectedWeek
  ) => {
    const updates =
      weeklyUpdates[okr.id] || [];

    if (
      !updates ||
      updates.length === 0
    ) {
      return null;
    }

    // ======================================================
    // NO WEEK SELECTED
    // ======================================================

    if (
      weekNumber === "" ||
      weekNumber === null ||
      weekNumber === undefined
    ) {
      return [
        ...updates,
      ].sort(
        (a, b) =>
          Number(
            b.week_number || 0
          ) -
          Number(
            a.week_number || 0
          )
      )[0];
    }

    const selectedWeekNumber =
      Number(
        weekNumber
      );

    if (
      selectedWeekNumber <= 0
    ) {
      return null;
    }

    const validUpdates =
      updates.filter(
        (update) =>
          Number(
            update.week_number || 0
          ) <=
          selectedWeekNumber
      );

    if (
      validUpdates.length === 0
    ) {
      return null;
    }

    return [
      ...validUpdates,
    ].sort(
      (a, b) =>
        Number(
          b.week_number || 0
        ) -
        Number(
          a.week_number || 0
        )
    )[0];
  };

  // =========================================================
  // TOTAL PROGRESS
  // =========================================================

  const getOkrTotalProgress = (
    okr
  ) => {
    const latestUpdate =
      getLatestOkrUpdate(
        okr,
        selectedWeek
      );

    if (!latestUpdate) {
      return 0;
    }

    return Number(
      latestUpdate.progress || 0
    );
  };

  // =========================================================
  // EXPECTED TILL WEEK
  //
  // If no week selected => 0
  // =========================================================

  const getExpectedTillWeek = (
    okr
  ) => {
    const target =
      Number(
        okr.target || 0
      );

    const week =
      Number(
        selectedWeek || 0
      );

    if (
      target <= 0 ||
      week <= 0
    ) {
      return 0;
    }

    return (
      target / 13
    ) * week;
  };

  // =========================================================
  // PROGRESS % TILL NOW
  // =========================================================

  const getProgressPercentageTillNow = (
    okr
  ) => {
    const actualProgress =
      getOkrTotalProgress(
        okr
      );

    const expectedProgress =
      getExpectedTillWeek(
        okr
      );

    if (
      expectedProgress <= 0
    ) {
      return 0;
    }

    const percentage =
      (actualProgress /
        expectedProgress) *
      100;

    return Math.min(
      Math.max(
        percentage,
        0
      ),
      100
    );
  };

  // =========================================================
  // OVERALL PROGRESS %
  // =========================================================

  const getOverallProgressPercentage = (
    okr
  ) => {
    const target =
      Number(
        okr.target || 0
      );

    const actualProgress =
      getOkrTotalProgress(
        okr
      );

    if (
      target <= 0
    ) {
      return 0;
    }

    const percentage =
      (actualProgress /
        target) *
      100;

    return Math.min(
      Math.max(
        percentage,
        0
      ),
      100
    );
  };

  const getTrackerBatch = (okr) =>
    okr.batch ||
    batches.find(
      (batch) =>
        String(batch.id) ===
        String(okr.batch_id)
    );

  const getCurrentWeekNumber = (batch) => {
    if (!batch?.start_date || !batch?.end_date) {
      return 0;
    }

    const today = new Date();
    const startDate = new Date(batch.start_date);
    const endDate = new Date(batch.end_date);
    today.setHours(0, 0, 0, 0);
    startDate.setHours(0, 0, 0, 0);
    endDate.setHours(0, 0, 0, 0);

    if (today < startDate || today > endDate) {
      return 0;
    }

    const elapsedDays = Math.floor(
      (today - startDate) / (1000 * 60 * 60 * 24)
    );

    return Math.min(
      Math.max(Math.floor(elapsedDays / 7) + 1, 1),
      13
    );
  };

  const getLatestTrackerEntry = (
    okr,
    weekNumber = selectedWeek,
    useCurrentWeekWhenUnselected = false
  ) => {
    const entries = trackerEntries[okr.id] || [];
    const batch = getTrackerBatch(okr);

    if (!entries.length || !batch?.start_date) {
      return null;
    }

    let selectedWeekNumber = Number(weekNumber) || 0;

    if (
      useCurrentWeekWhenUnselected &&
      selectedWeekNumber <= 0
    ) {
      selectedWeekNumber = getCurrentWeekNumber(batch);
    }

    if (selectedWeekNumber <= 0) {
      return null;
    }

    const cutoffDate = new Date(batch.start_date);
    cutoffDate.setDate(
      cutoffDate.getDate() + selectedWeekNumber * 7
    );

    const validEntries = entries.filter((entry) => {
      if (!entry.week_start) {
        return false;
      }

      const entryWeekStart = new Date(entry.week_start);
      return (
        !Number.isNaN(entryWeekStart.getTime()) &&
        entryWeekStart <= cutoffDate
      );
    });

    if (!validEntries.length) {
      return null;
    }

    return [...validEntries].sort((a, b) => {
      const aTimestamp =
        new Date(a.updated_at).getTime() || 0;
      const bTimestamp =
        new Date(b.updated_at).getTime() || 0;
      return bTimestamp - aTimestamp;
    })[0];
  };

  const getTrackerTotalProgress = (
    okr,
    weekNumber = selectedWeek
  ) => {
    const latestEntry = getLatestTrackerEntry(
      okr,
      weekNumber,
      true
    );

    return Number(
      latestEntry?.weekly_completion_efficiency || 0
    );
  };

  const getTrackerProgressPercentageTillNow = (
    okr,
    weekNumber = selectedWeek
  ) => {
    const target = Number(okr.target) || 0;

    if (target <= 0) {
      return 0;
    }

    const latestEntry = getLatestTrackerEntry(
      okr,
      weekNumber
    );

    return (
      (Number(
        latestEntry?.weekly_completion_efficiency
      ) || 0) /
      target
    ) * 100;
  };

  const getTrackerOkrProgressPercentage = (
    okr,
    weekNumber = selectedWeek
  ) => {
    const target = Number(okr.target) || 0;

    if (target <= 0) {
      return 0;
    }

    const latestEntry = getLatestTrackerEntry(
      okr,
      weekNumber,
      true
    );

    return (
      (Number(
        latestEntry?.weekly_completion_efficiency
      ) || 0) /
      target
    ) * 100;
  };

  // =========================================================
  // PROGRESS COLOR
  // =========================================================

  const getProgressClass = (
    percentage
  ) => {
    if (
      percentage <= 60
    ) {
      return "team-progress-red";
    }

    if (
      percentage <= 80
    ) {
      return "team-progress-yellow";
    }

    return "team-progress-green";
  };

  // =========================================================
  // GET EMPLOYEE NAME
  // =========================================================

  const getEmployeeName = (
    okr
  ) => {
    if (okr.user?.name) {
      return okr.user.name;
    }

    if (
      okr.user?.first_name ||
      okr.user?.last_name
    ) {
      return `${okr.user?.first_name || ""} ${
        okr.user?.last_name || ""
      }`.trim();
    }

    if (
      okr.assignee?.user?.first_name ||
      okr.assignee?.user?.last_name
    ) {
      return `${okr.assignee?.user?.first_name || ""} ${
        okr.assignee?.user?.last_name || ""
      }`.trim();
    }

    if (okr.user_name) {
      return okr.user_name;
    }

    if (
      okr.assignee?.user?.username
    ) {
      return okr.assignee.user.username;
    }

    return "N/A";
  };

  // =========================================================
  // SELECTED OKR WEEKLY UPDATES
  // =========================================================

  const updates =
    selectedOkr
      ? weeklyUpdates[
          selectedOkr.id
        ] || []
      : [];

  // =========================================================
  // GROUP UPDATES BY WEEK
  // =========================================================

  const groupUpdatesByWeek = (
    weeklyData
  ) => {
    return weeklyData.reduce(
      (
        groups,
        update
      ) => {
        const week =
          update.week_number;

        if (
          !groups[week]
        ) {
          groups[week] = [];
        }

        groups[week].push(
          update
        );

        return groups;
      },
      {}
    );
  };

  const groupedUpdates =
    groupUpdatesByWeek(
      updates
    );

  // =========================================================
  // GET LATEST UPDATE OF A WEEK
  // =========================================================

  const getLatestUpdate = (
    weekUpdates
  ) => {
    if (
      !weekUpdates ||
      weekUpdates.length === 0
    ) {
      return {
        progress: 0,
        remarks: "None",
      };
    }

    return [
      ...weekUpdates,
    ].sort(
      (a, b) =>
        new Date(
          b.created_at
        ) -
        new Date(
          a.created_at
        )
    )[0];
  };

  // =========================================================
  // SHOW WEEKLY HISTORY
  // =========================================================

  const showWeeklyHistory = () => {
    setActiveHistoryTab(
      "weekly"
    );
  };

  // =========================================================
  // SHOW FOGS / HURDLES HISTORY
  // =========================================================

  const showFogsHurdlesHistory =
    async () => {
      setActiveHistoryTab(
        "fogs"
      );

      if (!selectedOkr) {
        return;
      }

      if (
        fogsHurdlesHistory[
          selectedOkr.id
        ]
      ) {
        return;
      }

      try {
        setIsLoadingFogsHurdles(
          true
        );

        const response =
          await fetch(
            `${API_URL}/api/okrs/${selectedOkr.id}/fogs-hurdles?page=1&size=20&sort_by=created_at&sort_order=desc`,
            {
              headers: {
                Authorization:
                  `Bearer ${localStorage.getItem("token")}`,
              },
            }
          );

        if (!response.ok) {
          throw new Error(
            "Failed to fetch FOGS/Hurdles history"
          );
        }

        const result =
          await response.json();

        const history =
          Array.isArray(
            result.data
          )
            ? result.data
            : [];

        setFogsHurdlesHistory(
          (previous) => ({
            ...previous,
            [selectedOkr.id]:
              history,
          })
        );
      } catch (error) {
        console.error(
          "Error fetching FOGS/Hurdles:",
          error
        );

        setFogsHurdlesHistory(
          (previous) => ({
            ...previous,
            [selectedOkr.id]:
              [],
          })
        );
      } finally {
        setIsLoadingFogsHurdles(
          false
        );
      }
    };

  // =========================================================
  // TOGGLE WEEK HISTORY
  // =========================================================

  const toggleWeekHistory = (
    weekNumber
  ) => {
    setExpandedWeeks(
      (previous) => ({
        ...previous,
        [weekNumber]:
          !previous[
            weekNumber
          ],
      })
    );
  };

  // =========================================================
  // OPEN OKR MODAL
  // =========================================================

  const handleShowOkr = (
    okr
  ) => {
    setSelectedOkr(
      okr
    );

    setActiveHistoryTab(
      "weekly"
    );

    setExpandedWeeks({});

    setIsShowOkrModalOpen(
      true
    );

    if (okr.tracker_enabled) {
      fetchTrackerEntries([okr.id]).catch((error) => {
        console.error(
          `Error loading tracker history for OKR ${okr.id}:`,
          error
        );
      });
    }

  };

  // =========================================================
  // CLOSE OKR MODAL
  // =========================================================

  const closeOkrModal = () => {
    setIsShowOkrModalOpen(
      false
    );

    setSelectedOkr(
      null
    );

    setActiveHistoryTab(
      "weekly"
    );

    setExpandedWeeks({});
  };

  // =========================================================
  // CLEAR FILTERS
  // =========================================================

  const clearFilters = () => {
    setSearchValue("");

    setSelectedBatchId("");

    setSelectedWeek("");

    setFilters({
      year: "",
      quarter: "",
    });
  };

  // =========================================================
  // EFFECT - FETCH BATCHES
  // =========================================================

  useEffect(() => {
    if (!currentUser) {
      return;
    }

    if (
      userRole ===
      "SUPER_ADMIN"
    ) {
      if (
        selectedOrganizationId
      ) {
        fetchBatches();
      } else {
        setBatches([]);
        setSelectedBatchId("");
        setSelectedWeek("");
      }

      return;
    }

    fetchBatches();
  }, [
    currentUser,
    selectedOrganizationId,
  ]);

  // =========================================================
  // EFFECT - FETCH OKRs
  // =========================================================

  useEffect(() => {
    if (!currentUser) {
      return;
    }

    /*
      For SUPER_ADMIN:
      OKRs can be loaded even before batch selection
      if organization is selected.

      For other roles:
      load after batches are available.
    */

    if (
      userRole ===
      "SUPER_ADMIN"
    ) {
      if (
        selectedOrganizationId
      ) {
        fetchOkrs();
      }

      return;
    }

    if (
      batches.length > 0
    ) {
      fetchOkrs();
    }
  }, [
    currentUser,
    batches,
    selectedBatchId,
    selectedOrganizationId,
  ]);

  // =========================================================
  // EFFECT - APPLY UI FILTERS
  // =========================================================

  useEffect(() => {
    applyFilters(
      searchValue,
      filters,
      selectedBatchId,
      selectedOrganizationId
    );
  }, [
    okrs,
    searchValue,
    filters,
    selectedBatchId,
    selectedOrganizationId,
  ]);

  useEffect(() => {
    setCurrentPage(1);
  }, [filteredOkrs]);

  // =========================================================
  // RENDER
  // =========================================================

  const totalPages = Math.ceil(filteredOkrs.length / pageSize);
  const paginatedOkrs = filteredOkrs.slice(
    (currentPage - 1) * pageSize,
    currentPage * pageSize
  );

  return (
    <div className="page">

      {/* =====================================================
          PAGE HEADER
      ====================================================== */}

      <div className="page-header">
        <div>
          <h2>
            Team OKR
          </h2>

          <p>
            View and monitor OKRs of your team.
          </p>
        </div>
      </div>

      {/* =====================================================
          FILTER BAR
      ====================================================== */}

      <div className="filters-bar">

        {/* SEARCH */}

        <div className="search-wrap">
          <span className="search-icon">
            🔍
          </span>

          <input
            type="text"
            className="search-input"
            placeholder="Search employee or objective..."
            value={searchValue}
            onChange={(e) =>
              handleSearch(
                e.target.value
              )
            }
          />
        </div>

        {/* ===================================================
            ORGANIZATION
        ==================================================== */}

        {userRole ===
          "SUPER_ADMIN" && (
          <select
            className="filter-select"
            value={
              selectedOrganizationId
            }
            onChange={(e) => {
              setSelectedOrganizationId(
                e.target.value
              );

              setSelectedBatchId("");

              setSelectedWeek("");
            }}
          >
            <option value="">
              Select Organization
            </option>

            {organizations.map(
              (
                organization
              ) => (
                <option
                  key={
                    organization.id
                  }
                  value={
                    organization.id
                  }
                >
                  {
                    organization.name
                  }
                </option>
              )
            )}
          </select>
        )}

        {/* ===================================================
            BATCH
        ==================================================== */}

        <select
          className="filter-select"
          value={
            selectedBatchId
          }
          onChange={(e) => {
            setSelectedBatchId(
              e.target.value
            );

            // Reset week whenever
            // batch changes
            setSelectedWeek("");
          }}
        >
          <option value="">
            Select Batch
          </option>

          {batches.map(
            (batch) => (
              <option
                key={batch.id}
                value={batch.id}
              >
                {batch.name}
              </option>
            )
          )}
        </select>

        {/* ===================================================
            WEEK
        ==================================================== */}

        <select
          className="filter-select"
          value={
            selectedWeek
          }
          onChange={(e) =>
            setSelectedWeek(
              e.target.value
            )
          }
          disabled={
            !selectedBatchId ||
            availableWeeks.length ===
              0
          }
        >
          <option value="">
            All Weeks
          </option>

          {availableWeeks.map(
            (week) => (
              <option
                key={week}
                value={week}
              >
                Week {week}
                {" "}
                (
                {
                  getWeekDateRange(
                    week
                  )
                }
                )
              </option>
            )
          )}
        </select>

        {/* ===================================================
            YEAR
        ==================================================== */}

        <select
          className="filter-select"
          value={
            filters.year
          }
          onChange={(e) =>
            setFilters(
              (previous) => ({
                ...previous,
                year:
                  e.target.value,
              })
            )
          }
        >
          <option value="">
            All Years
          </option>

          {years.map(
            (year) => (
              <option
                key={year}
                value={year}
              >
                {year}
              </option>
            )
          )}
        </select>

        {/* ===================================================
            QUARTER
        ==================================================== */}

        <select
          className="filter-select"
          value={
            filters.quarter
          }
          onChange={(e) =>
            setFilters(
              (previous) => ({
                ...previous,
                quarter:
                  e.target.value,
              })
            )
          }
        >
          <option value="">
            All Quarters
          </option>

          <option value="JFM">
            JFM
          </option>

          <option value="AMJ">
            AMJ
          </option>

          <option value="JAS">
            JAS
          </option>

          <option value="OND">
            OND
          </option>
        </select>

        {/* ===================================================
            CLEAR
        ==================================================== */}

        <button
          type="button"
          className="clear-filter-btn"
          onClick={
            clearFilters
          }
        >
          Clear
        </button>
      </div>

      {/* =====================================================
          SELECTED BATCH INFORMATION
      ====================================================== */}

      {selectedBatch && (
        <div
          style={{
            marginBottom: "15px",
            padding: "10px 14px",
            background: "#f8fafc",
            borderRadius: "8px",
            fontSize: "13px",
          }}
        >
          <strong>
            Batch Period:
          </strong>{" "}
          {new Date(
            selectedBatch.start_date
          ).toLocaleDateString(
            "en-IN",
            {
              day: "2-digit",
              month: "short",
              year: "numeric",
            }
          )}
          {" - "}
          {new Date(
            selectedBatch.end_date
          ).toLocaleDateString(
            "en-IN",
            {
              day: "2-digit",
              month: "short",
              year: "numeric",
            }
          )}

          {selectedWeek && (
            <>
              {" | "}
              <strong>
                Selected:
              </strong>{" "}
              Week{" "}
              {selectedWeek}
            </>
          )}
        </div>
      )}

      {/* =====================================================
          OKR TABLE CARD
      ====================================================== */}

      <div className="card">

        <div className="card-header">
          <div>
            <h3 className="card-title">
              {selectedBatch
                ? selectedBatch.name
                : "Team OKRs"}
            </h3>

            <p>
              {filteredOkrs.length} OKR
              {filteredOkrs.length !==
              1
                ? "s"
                : ""}
            </p>
          </div>
        </div>

        {/* ===================================================
            LOADING
        ==================================================== */}

        {loadingBatches ||
        loadingOkrs ? (
          <div className="no-data">
            Loading...
          </div>
        ) : error ? (
          <div className="no-data">
            {error}
          </div>
        ) : filteredOkrs.length ===
          0 ? (
          <div className="no-data">
            No OKRs found.
          </div>
        ) : (
          <div className="batch-table-wrap">

            <table className="batch-table">

              <thead>
                <tr>

                  <th>
                    Employee
                  </th>

                  <th>
                    Objective
                  </th>

                  <th>
                    Key Result
                  </th>

                  <th>
                    Target
                  </th>

                  <th>
                    OKR Type
                  </th>

                  <th>
                    Total Progress
                  </th>

                  <th>
                    Expected Till Week
                  </th>

                  <th>
                    Progress % Till Now
                  </th>

                  <th>
                    Overall Progress %
                  </th>

                </tr>
              </thead>

              <tbody>

                {paginatedOkrs.map(
                  (okr) => {

                    const hasProgressData =
                      Object.prototype.hasOwnProperty.call(
                        okr.tracker_enabled
                          ? trackerEntries
                          : weeklyUpdates,
                        okr.id
                      );

                    const totalProgress =
                      okr.tracker_enabled
                        ? getTrackerTotalProgress(okr)
                        : getOkrTotalProgress(okr);

                    const expectedTillWeek =
                      getExpectedTillWeek(
                        okr
                      );

                    const progressTillNow =
                      okr.tracker_enabled
                        ? getTrackerProgressPercentageTillNow(okr)
                        : getProgressPercentageTillNow(okr);

                    const overallProgress =
                      okr.tracker_enabled
                        ? getTrackerOkrProgressPercentage(okr)
                        : getOverallProgressPercentage(okr);

                    return (
                      <tr
                        key={
                          okr.id
                        }
                        onClick={() =>
                          handleShowOkr(
                            okr
                          )
                        }
                        style={{
                          cursor:
                            "pointer",
                        }}
                      >

                        {/* EMPLOYEE */}

                        <td>
                          {getEmployeeName(
                            okr
                          )}
                        </td>

                        {/* OBJECTIVE */}

                        <td>
                          <div className="team-okr-objective">
                            {
                              okr.objective ||
                              "N/A"
                            }
                          </div>
                        </td>

                        {/* KEY RESULT */}

                        <td>
                          <div className="team-okr-objective">
                            {
                              okr.key_results ||
                              "N/A"
                            }
                          </div>
                        </td>

                        {/* TARGET */}

                        <td>
                          {okr.target ??
                            "N/A"}
                        </td>

                        {/* OKR TYPE */}

                        <td>
                          {
                            okr.okr_type ||
                            "N/A"
                          }
                        </td>

                        {/* TOTAL PROGRESS */}

                        <td>
                          <strong>
                            {
                              hasProgressData
                                ? totalProgress
                                : "—"
                            }
                          </strong>

                        </td>

                        {/* EXPECTED TILL WEEK */}

                        <td>
                          {expectedTillWeek.toFixed(
                            2
                          )}
                        </td>

                        {/* PROGRESS % TILL NOW */}

                        <td>
                          {hasProgressData ? (
                            <div className="okr-progress">

                            <div className="okr-progress-track">

                              <div
                                className={`okr-progress-fill ${getProgressClass(
                                  progressTillNow
                                )}`}
                                style={{
                                  width: `${Math.min(
                                    Math.max(
                                      progressTillNow,
                                      0
                                    ),
                                    100
                                  )}%`,
                                }}
                              />

                            </div>

                            <span>
                              {progressTillNow.toFixed(
                                2
                              )}
                              %
                            </span>

                          </div>
                          ) : (
                            "—"
                          )}
                        </td>

                        {/* OVERALL PROGRESS */}

                        <td>
                          {hasProgressData ? (
                            <div className="okr-progress">

                            <div className="okr-progress-track">

                              <div
                                className={`okr-progress-fill ${getProgressClass(
                                  overallProgress
                                )}`}
                                style={{
                                  width: `${Math.min(
                                    Math.max(
                                      overallProgress,
                                      0
                                    ),
                                    100
                                  )}%`,
                                }}
                              />

                            </div>

                            <span>
                              {overallProgress.toFixed(
                                2
                              )}
                              %
                            </span>

                          </div>
                          ) : (
                            "—"
                          )}
                        </td>

                      </tr>
                    );
                  }
                )}

              </tbody>

            </table>
          </div>
        )}

        {!loadingBatches &&
          !loadingOkrs &&
          !error &&
          filteredOkrs.length > 0 && (
            <div className="team-okr-pagination">
              <div className="team-okr-pagination-size">
                <label htmlFor="team-okr-page-size">
                  Rows per page:
                </label>
                <select
                  id="team-okr-page-size"
                  value={pageSize}
                  onChange={(e) => {
                    setPageSize(Number(e.target.value));
                    setCurrentPage(1);
                  }}
                >
                  <option value={10}>10</option>
                  <option value={20}>20</option>
                  <option value={30}>30</option>
                  <option value={50}>50</option>
                </select>
              </div>

              <div className="team-okr-pagination-pages">
                <button
                  type="button"
                  disabled={currentPage <= 1}
                  onClick={() =>
                    setCurrentPage((page) => Math.max(1, page - 1))
                  }
                >
                  Previous
                </button>
                <span>
                  Page {currentPage} of {totalPages}
                </span>
                <button
                  type="button"
                  disabled={currentPage >= totalPages}
                  onClick={() =>
                    setCurrentPage((page) =>
                      Math.min(totalPages, page + 1)
                    )
                  }
                >
                  Next
                </button>
              </div>
            </div>
          )}
      </div>

      {/* =====================================================
          OKR DETAILS MODAL
      ====================================================== */}

      {isShowOkrModalOpen &&
        selectedOkr && (
          <div
            className="show-okr-modal-overlay"
            onClick={
              closeOkrModal
            }
          >

            <div
              className="show-okr-modal-card"
              onClick={(e) =>
                e.stopPropagation()
              }
            >

              {/* =========================================
                  HEADER
              ========================================== */}

              <div className="show-okr-modal-header">

                <div>
                  <h3>
                    OKR Details
                  </h3>

                  <p>
                    View OKR details and
                    weekly progress
                    history.
                  </p>
                </div>

                <button
                  type="button"
                  className="progress-close-btn"
                  onClick={
                    closeOkrModal
                  }
                >
                  ×
                </button>

              </div>

              {/* =========================================
                  BODY
              ========================================== */}

              <div className="show-okr-modal-body">

                {/* =======================================
                    OKR DETAILS
                ======================================== */}

                <div className="okr-detail-section">

                  {/* OBJECTIVE */}

                  <div className="okr-detail-item">
                    <label>
                      Objective
                    </label>

                    <div className="okr-detail-value">
                      {
                        selectedOkr.objective ||
                        "N/A"
                      }
                    </div>
                  </div>

                  {/* KEY RESULT */}

                  <div className="okr-detail-item">
                    <label>
                      Key Result
                    </label>

                    <div className="okr-detail-value">
                      {
                        selectedOkr.key_results ||
                        "N/A"
                      }
                    </div>
                  </div>

                  {/* TARGET + TYPE */}

                  <div className="okr-detail-row">

                    <div className="okr-detail-item">
                      <label>
                        Target
                      </label>

                      <div className="okr-detail-value">
                        {
                          selectedOkr.target ??
                          "N/A"
                        }
                      </div>
                    </div>

                    <div className="okr-detail-item">
                      <label>
                        OKR Type
                      </label>

                      <div className="okr-detail-value">
                        {
                          selectedOkr.okr_type ||
                          "N/A"
                        }
                      </div>
                    </div>

                  </div>

                </div>

                {/* =======================================
                    HISTORY TABS
                ======================================== */}

                <div className="history">

                  <button
                    type="button"
                    className={`history-tab ${
                      activeHistoryTab ===
                      "weekly"
                        ? "active"
                        : ""
                    }`}
                    onClick={
                      showWeeklyHistory
                    }
                  >
                    Weekly Progress History
                  </button>

                  <button
                    type="button"
                    className={`history-tab ${
                      activeHistoryTab ===
                      "fogs"
                        ? "active"
                        : ""
                    }`}
                    onClick={
                      showFogsHurdlesHistory
                    }
                  >
                    FOGS/Hurdles History
                  </button>

                </div>

                {/* =======================================
                    HISTORY CONTENT
                ======================================== */}

                <div className="weekly-history-section">

                  {/* =====================================
                      WEEKLY HISTORY
                  ====================================== */}

                  {activeHistoryTab === "weekly" &&
                    selectedOkr.tracker_enabled && (
                    <div className="weekly-history-list">
                      {loadingTrackerEntries[selectedOkr.id] ? (
                        <div className="no-weekly-updates">
                          Loading tracker history...
                        </div>
                      ) : trackerEntryErrors[selectedOkr.id] ? (
                        <div className="no-weekly-updates">
                          {trackerEntryErrors[selectedOkr.id]}
                        </div>
                      ) : (() => {
                        const trackerData =
                          trackerEntries[selectedOkr.id] || [];
                        const trackerBatch =
                          selectedOkr.batch ||
                          batches.find(
                            (batch) =>
                              String(batch.id) ===
                              String(selectedOkr.batch_id)
                          );

                        if (!trackerData.length) {
                          return (
                            <div className="no-weekly-updates">
                              No tracker entries available.
                            </div>
                          );
                        }

                        const groupedTrackerEntries =
                          trackerData.reduce((groups, entry) => {
                            if (
                              !entry.week_start ||
                              !trackerBatch?.start_date
                            ) {
                              return groups;
                            }

                            const batchStartDate = new Date(
                              trackerBatch.start_date
                            );
                            const entryWeekStart = new Date(
                              entry.week_start
                            );

                            if (
                              Number.isNaN(batchStartDate.getTime()) ||
                              Number.isNaN(entryWeekStart.getTime())
                            ) {
                              return groups;
                            }

                            const daysFromBatchStart = Math.floor(
                              (entryWeekStart - batchStartDate) /
                                (1000 * 60 * 60 * 24)
                            );
                            const weekNumber =
                              Math.floor(daysFromBatchStart / 7) + 1;

                            if (weekNumber < 1) {
                              return groups;
                            }

                            if (!groups[weekNumber]) {
                              groups[weekNumber] = [];
                            }

                            groups[weekNumber].push(entry);
                            return groups;
                          }, {});

                        const sortedWeeks = Object.entries(
                          groupedTrackerEntries
                        ).sort(
                          ([weekA], [weekB]) =>
                            Number(weekA) - Number(weekB)
                        );

                        if (!sortedWeeks.length) {
                          return (
                            <div className="no-weekly-updates">
                              No tracker entries available.
                            </div>
                          );
                        }

                        return sortedWeeks.map(
                          ([weekNumber, weekEntries]) => {
                            const latestEntry = [...weekEntries].sort(
                              (a, b) =>
                                new Date(
                                  b.created_at || b.updated_at
                                ) -
                                new Date(
                                  a.created_at || a.updated_at
                                )
                            )[0];
                            const efficiency =
                              Number(
                                latestEntry.weekly_completion_efficiency
                              ) || 0;
                            const isExpanded =
                              expandedWeeks[weekNumber] || false;

                            return (
                              <div
                                className="weekly-history-item"
                                key={weekNumber}
                              >
                                <div className="weekly-history-header">
                                  <div className="weekly-history-week">
                                    Week {weekNumber}
                                    {" - "}
                                    <span className="weekly-history-date">
                                      (
                                      {getWeekDateRange(
                                        Number(weekNumber),
                                        trackerBatch
                                      )}
                                      )
                                    </span>
                                  </div>

                                  <button
                                    type="button"
                                    className="show-history-btn"
                                    onClick={() =>
                                      toggleWeekHistory(weekNumber)
                                    }
                                  >
                                    {isExpanded
                                      ? "Hide History"
                                      : "Show History"}
                                  </button>
                                </div>

                                <div className="weekly-history-progress">
                                  <div className="weekly-progress-track">
                                    <div
                                      className={`weekly-progress-fill ${
                                        efficiency < 60
                                          ? "progress-red"
                                          : efficiency < 80
                                          ? "progress-yellow"
                                          : "progress-green"
                                      }`}
                                      style={{
                                        width: `${Math.min(
                                          Math.max(efficiency, 0),
                                          100
                                        )}%`,
                                      }}
                                    />
                                  </div>
                                  <span>
                                    {latestEntry.opportunities_completed ?? 0}
                                    {" / "}
                                    {latestEntry.opportunities_received ?? 0}
                                  </span>
                                </div>

                                <div className="weekly-history-remarks">
                                  <strong>Completion Efficiency:</strong>
                                  {" "}
                                  {efficiency}%
                                  {" | Target: "}
                                  {latestEntry.target ?? 0}%
                                </div>

                                {isExpanded && (
                                  <div className="week-update-history">
                                    <div className="week-update-history-title">
                                      Update History
                                    </div>
                                    {[...weekEntries]
                                      .sort(
                                        (a, b) =>
                                          new Date(
                                            b.created_at || b.updated_at
                                          ) -
                                          new Date(
                                            a.created_at || a.updated_at
                                          )
                                      )
                                      .map((history, index) => (
                                        <div
                                          className="week-update-history-item"
                                          key={
                                            history.id ||
                                            `${weekNumber}-${history.created_at || history.updated_at}-${index}`
                                          }
                                        >
                                          <div className="week-update-history-top">
                                            <span>
                                              {new Date(
                                                history.created_at ||
                                                  history.updated_at
                                              ).toLocaleString("en-IN")}
                                            </span>
                                            <strong>
                                              {history.opportunities_completed ?? 0}
                                              {" / "}
                                              {history.opportunities_received ?? 0}
                                            </strong>
                                          </div>
                                          <div className="week-update-history-remarks">
                                            <strong>Completion Efficiency:</strong>
                                            {" "}
                                            {Number(
                                              history.weekly_completion_efficiency
                                            ) || 0}
                                            %
                                          </div>
                                          <div className="week-update-history-remarks">
                                            <strong>Target:</strong>
                                            {" "}
                                            {history.target ?? 0}%
                                          </div>
                                        </div>
                                      ))}
                                  </div>
                                )}
                              </div>
                            );
                          }
                        );
                      })()}
                    </div>
                  )}

                  {activeHistoryTab === "weekly" &&
                    !selectedOkr.tracker_enabled && (
                    <div className="weekly-history-list">

                      {loadingWeeklyUpdates[selectedOkr.id] ? (
                        <div className="no-weekly-updates">
                          Loading weekly updates...
                        </div>
                      ) : weeklyUpdateErrors[selectedOkr.id] ? (
                        <div className="no-weekly-updates">
                          {weeklyUpdateErrors[selectedOkr.id]}
                        </div>
                      ) : updates.length ===
                      0 ? (
                        <div className="no-weekly-updates">
                          No weekly updates
                          available.
                        </div>
                      ) : (
                        Object.entries(
                          groupedUpdates
                        )
                          .sort(
                            (
                              [
                                weekA,
                              ],
                              [
                                weekB,
                              ]
                            ) =>
                              Number(
                                weekA
                              ) -
                              Number(
                                weekB
                              )
                          )
                          .map(
                            ([
                              weekNumber,
                              weekUpdates,
                            ]) => {

                              const latestUpdate =
                                getLatestUpdate(
                                  weekUpdates
                                );

                              const progressPercentage =
                                Number(
                                  selectedOkr.target
                                )
                                  ? (
                                      Number(
                                        latestUpdate.progress ||
                                          0
                                      ) /
                                      Number(
                                        selectedOkr.target
                                      )
                                    ) *
                                    100
                                  : 0;

                              const safePercentage =
                                Math.min(
                                  Math.max(
                                    progressPercentage,
                                    0
                                  ),
                                  100
                                );

                              const isExpanded =
                                expandedWeeks[
                                  weekNumber
                                ] ||
                                false;

                              return (
                                <div
                                  className="weekly-history-item"
                                  key={
                                    weekNumber
                                  }
                                >

                                  {/* WEEK HEADER */}

                                  <div className="weekly-history-header">

                                    <div className="weekly-history-week">

                                      Week{" "}
                                      {
                                        weekNumber
                                      }

                                      <span className="weekly-history-date">
                                        (
                                        {
                                          getWeekDateRange(
                                            Number(
                                              weekNumber
                                            ),
                                            selectedOkr.batch ||
                                              selectedBatch
                                          )
                                        }
                                        )
                                      </span>

                                    </div>

                                    <button
                                      type="button"
                                      className="show-history-btn"
                                      onClick={() =>
                                        toggleWeekHistory(
                                          weekNumber
                                        )
                                      }
                                    >
                                      {isExpanded
                                        ? "Hide History"
                                        : "Show History"}
                                    </button>

                                  </div>

                                  {/* LATEST PROGRESS */}

                                  <div className="weekly-history-progress">

                                    <div className="weekly-progress-track">

                                      <div
                                        className={`weekly-progress-fill ${
                                          safePercentage <
                                          60
                                            ? "progress-red"
                                            : safePercentage <
                                              80
                                            ? "progress-yellow"
                                            : "progress-green"
                                        }`}
                                        style={{
                                          width: `${safePercentage}%`,
                                        }}
                                      />

                                    </div>

                                    <span>
                                      {
                                        latestUpdate.progress
                                      }{" "}
                                      /{" "}
                                      {
                                        selectedOkr.target
                                      }
                                    </span>

                                  </div>

                                  {/* LATEST REMARK */}

                                  <div className="weekly-history-remarks">

                                    <strong>
                                      Latest
                                      Update:
                                    </strong>{" "}

                                    {
                                      latestUpdate.remarks ||
                                      "None"
                                    }

                                  </div>

                                  {/* UPDATE HISTORY */}

                                  {isExpanded && (
                                    <div className="week-update-history">

                                      <div className="week-update-history-title">
                                        Update
                                        History
                                      </div>

                                      {[
                                        ...weekUpdates,
                                      ]
                                        .sort(
                                          (
                                            a,
                                            b
                                          ) =>
                                            new Date(
                                              b.created_at
                                            ) -
                                            new Date(
                                              a.created_at
                                            )
                                        )
                                        .map(
                                          (
                                            history
                                          ) => (
                                            <div
                                              className="week-update-history-item"
                                              key={
                                                history.id
                                              }
                                            >

                                              <div className="week-update-history-top">

                                                <span>
                                                  {new Date(
                                                    history.created_at
                                                  ).toLocaleString(
                                                    "en-IN"
                                                  )}
                                                </span>

                                                <strong>
                                                  {
                                                    history.progress
                                                  }{" "}
                                                  /{" "}
                                                  {
                                                    selectedOkr.target
                                                  }
                                                </strong>

                                              </div>

                                              <div className="week-update-history-remarks">

                                                <strong>
                                                  Remarks:
                                                </strong>{" "}

                                                {
                                                  history.remarks ||
                                                  "None"
                                                }

                                              </div>

                                            </div>
                                          )
                                        )}

                                    </div>
                                  )}

                                </div>
                              );
                            }
                          )
                      )}

                    </div>
                  )}

                  {/* =====================================
                      FOGS / HURDLES HISTORY
                  ====================================== */}

                  {activeHistoryTab ===
                    "fogs" && (
                    <div className="weekly-history-list">

                      {isLoadingFogsHurdles ? (
                        <div className="no-weekly-updates">
                          Loading
                          FOGS/Hurdles
                          history...
                        </div>
                      ) : (
                        (
                          fogsHurdlesHistory[
                            selectedOkr.id
                          ] || []
                        ).length === 0 ? (
                          <div className="no-weekly-updates">
                            No
                            FOGS/Hurdles
                            history
                            available.
                          </div>
                        ) : (
                          (
                            fogsHurdlesHistory[
                              selectedOkr.id
                            ] || []
                          ).map(
                            (
                              history
                            ) => (
                              <div
                                className="fogs-history-item"
                                key={
                                  history.id
                                }
                              >

                                {/* DATE */}

                                <div className="fogs-history-date">
                                  {new Date(
                                    history.created_at
                                  ).toLocaleString(
                                    "en-IN"
                                  )}
                                </div>

                                {/* FOGS */}

                                <div className="fogs-history-field">

                                  <div className="fogs-history-label">
                                    FOGS /
                                    Hurdles
                                  </div>

                                  <div className="fogs-history-value">
                                    {
                                      history.fogs_hurdles ||
                                      "None"
                                    }
                                  </div>

                                </div>

                                {/* ACTION POINTS */}

                                <div className="fogs-history-field">

                                  <div className="fogs-history-label">
                                    Action
                                    Points
                                  </div>

                                  <div className="fogs-history-value">
                                    {
                                      history.action_points ||
                                      "None"
                                    }
                                  </div>

                                </div>

                              </div>
                            )
                          )
                        )
                      )}

                    </div>
                  )}

                </div>

              </div>

              {/* =========================================
                  FOOTER
              ========================================== */}

              <div className="show-okr-modal-footer">

                <button
                  type="button"
                  className="progress-cancel-btn"
                  onClick={
                    closeOkrModal
                  }
                >
                  Close
                </button>

              </div>

            </div>

          </div>
        )}

    </div>
  );
}

export default TeamOkr;