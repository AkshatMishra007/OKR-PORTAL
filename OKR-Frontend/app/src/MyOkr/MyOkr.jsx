import { useEffect, useState } from "react";
import "./MyOkr.css";

import {
  FiTrendingUp,
} from "react-icons/fi";

import {
  MdUpdate,
} from "react-icons/md";

import { useNavigate } from "react-router-dom";

import { API_URL } from "../Config/ApiEndpoint";


function MyOkr() {

  const navigate = useNavigate();

  // =========================================================
  // MODAL STATES
  // =========================================================

  const [isProgressModalOpen, setIsProgressModalOpen] =
    useState(false);

  const [isHurdleModalOpen, setIsHurdleModalOpen] =
    useState(false);

  const [isShowOkrModalOpen, setIsShowOkrModalOpen] =
    useState(false);


  // =========================================================
  // SELECTED OKR
  // =========================================================

  const [selectedokr, setSelectedOkr] =
    useState(null);


  // =========================================================
  // WEEKLY DATA
  // =========================================================

  const [weeklyUpdates, setWeeklyUpdates] =
    useState({});

const [trackerEntries, setTrackerEntries] = useState({});
  // =========================================================
  // FOGS / HURDLES
  // =========================================================

  const [fogsHurdlesHistory, setFogsHurdlesHistory] =
    useState({});

  const [activeHistoryTab, setActiveHistoryTab] =
    useState("weekly");

  const [isLoadingFogsHurdles, setIsLoadingFogsHurdles] =
    useState(false);


  // =========================================================
  // WEEK FILTER
  // =========================================================

  /*
    null = no week selected

    When no week is selected:
    latest available update is used.

    When Week 5 is selected:
    latest update <= Week 5 is used.
  */
  const [selectedWeek, setSelectedWeek] =
    useState(null);


  // =========================================================
  // EXPANDED WEEK HISTORY
  // =========================================================

  const [expandedWeeks, setExpandedWeeks] =
    useState({});


  // =========================================================
  // HURDLE FORM
  // =========================================================

  const [hurdleData, setHurdleData] = useState({
    fogs_hurdles: "",
    action_points: "",
  });


  // =========================================================
  // PROGRESS FORM
  // =========================================================

  const [progressData, setProgressData] = useState({
    week_number: "",
    progress: "",
    remarks: "None",
  });


  // =========================================================
  // MY OKR DATA
  // =========================================================

  const [myOkr, setMyOkr] = useState({
    data: [],
    pagination: {
      page: 1,
      size: 10,
      total: 0,
    },
  });


  const [filteredMyOkr, setFilteredMyOkr] =
    useState([]);


  // =========================================================
  // PAGINATION
  // =========================================================

  const [currentPage, setCurrentPage] =
    useState(1);

  const [pageSize, setPageSize] =
    useState(10);


  // =========================================================
  // CURRENT USER
  // =========================================================

  const [UserID, setUserID] =
    useState(null);


  // =========================================================
  // GET BATCH
  // =========================================================

  /*
    Your API response is:

    data: [
      {
        ...
        batch: {
          start_date: "...",
          end_date: "...",
          ...
        }
      }
    ]

    Therefore we get the batch from the first OKR.

    Since My OKR belongs to one user's batch,
    this is sufficient for your current setup.
  */

  const batch =
    myOkr?.data?.length > 0
      ? myOkr.data[0]?.batch
      : null;


  // =========================================================
  // TOGGLE WEEK HISTORY
  // =========================================================

  const toggleWeekHistory = (weekNumber) => {

    setExpandedWeeks((prev) => ({
      ...prev,
      [weekNumber]: !prev[weekNumber],
    }));

  };


  // =========================================================
  // GROUP UPDATES BY WEEK
  // =========================================================

  const groupUpdatesByWeek = (updates) => {

    return updates.reduce(
      (groups, update) => {

        const week =
          update.week_number;

        if (!groups[week]) {
          groups[week] = [];
        }

        groups[week].push(update);

        return groups;

      },
      {}
    );

  };


  // =========================================================
  // GET AVAILABLE WEEKS
  // =========================================================

  const getAvailableWeeks = (batchData) => {

    if (
      !batchData?.start_date ||
      !batchData?.end_date
    ) {
      return [];
    }

    const startDate =
      new Date(batchData.start_date);

    const endDate =
      new Date(batchData.end_date);


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


    if (endDate < startDate) {
      return [];
    }


    const diffInMs =
      endDate - startDate;


    const totalDays =
      Math.floor(
        diffInMs /
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


  // =========================================================
  // GET CURRENT WEEK NUMBER
  // =========================================================

  /*
    This function is ONLY for today's week.

    Before batch:
      0

    During batch:
      1 - 13

    After batch:
      0
  */

  const getCurrentWeekNumber = (batchData) => {

    if (
      !batchData?.start_date ||
      !batchData?.end_date
    ) {
      return 0;
    }


    const today =
      new Date();

    const startDate =
      new Date(
        batchData.start_date
      );

    const endDate =
      new Date(
        batchData.end_date
      );


    today.setHours(
      0,
      0,
      0,
      0
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


    // -----------------------------------------
    // Before batch
    // -----------------------------------------

    if (today < startDate) {
      return 0;
    }


    // -----------------------------------------
    // After batch
    // -----------------------------------------

    if (today > endDate) {
      return 0;
    }


    // -----------------------------------------
    // Inside batch
    // -----------------------------------------

    const diffInMs =
      today - startDate;


    const diffInDays =
      Math.floor(
        diffInMs /
        (1000 * 60 * 60 * 24)
      );


    const weekNumber =
      Math.floor(
        diffInDays / 7
      ) + 1;


    return Math.min(
      Math.max(
        weekNumber,
        1
      ),
      13
    );

  };


  // =========================================================
  // GET WEEK DATE RANGE
  // =========================================================

  const getWeekDateRange = (weekNumber) => {

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
      new Date(startDate);


    weekStart.setDate(
      startDate.getDate() +
      (weekNumber - 1) * 7
    );


    const weekEnd =
      new Date(weekStart);


    weekEnd.setDate(
      weekStart.getDate() + 6
    );


    // Don't exceed batch end
    if (weekEnd > endDate) {
      weekEnd.setTime(
        endDate.getTime()
      );
    }


    const formatDate = (date) =>
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
  // GET LATEST OKR UPDATE
  // =========================================================

  /*
    Important logic:

    selectedWeek = null
      -> latest update overall

    selectedWeek = 5
      -> latest update where week_number <= 5

    Example:

    Updates:
      Week 1 = 2
      Week 3 = 4
      Week 5 = 6
      Week 7 = 8

    Selected Week 5:
      returns Week 5 = 6

    Selected Week 6:
      returns Week 5 = 6

    Selected Week 2:
      returns Week 1 = 2
  */

  const getLatestOkrUpdate = (
    okr,
    weekNumber = selectedWeek
  ) => {

    const updates =
      weeklyUpdates[okr.id] || [];


    if (!updates.length) {
      return null;
    }

    const getLaterUpdate = (latest, current) => {
      const latestWeek = Number(latest.week_number) || 0;
      const currentWeek = Number(current.week_number) || 0;
      const latestTimestamp =
        Date.parse(latest.created_at || latest.updated_at || "") || 0;
      const currentTimestamp =
        Date.parse(current.created_at || current.updated_at || "") || 0;

      return currentWeek > latestWeek ||
        (currentWeek === latestWeek &&
          currentTimestamp > latestTimestamp)
        ? current
        : latest;
    };

    // -----------------------------------------
    // No week selected
    // -----------------------------------------

    if (
      weekNumber === null ||
      weekNumber === "" ||
      weekNumber === undefined
    ) {

      return updates.reduce(
        getLaterUpdate
      );

    }


    const selectedWeekNumber =
      Number(weekNumber);


    if (
      !selectedWeekNumber ||
      selectedWeekNumber <= 0
    ) {
      return null;
    }


    // -----------------------------------------
    // Updates up to selected week
    // -----------------------------------------

    const validUpdates =
      updates.filter(
        (update) =>
          Number(
            update.week_number
          ) <= selectedWeekNumber
      );


    if (!validUpdates.length) {
      return null;
    }


    return validUpdates.reduce(
      getLaterUpdate
    );

  };


  // =========================================================
  // GET TOTAL PROGRESS
  // =========================================================

const getOkrTotalProgress = (
  okr,
  weekNumber = selectedWeek
) => {

  // =========================================================
  // TRACKER OKR
  // =========================================================

  if (
    okr?.tracker_enabled
  ) {

    const entries =
      trackerEntries[
        okr.id
      ] || [];


    if (
      entries.length === 0
    ) {
      return 0;
    }


    const batchStartDate =
      new Date(
        okr?.batch?.start_date
      );


    let week =
      Number(weekNumber) || 0;


    if (week <= 0) {

      week =
        getCurrentWeekNumber(
          okr.batch
        );

    }


    if (week <= 0) {
      return 0;
    }


    const selectedWeekEndDate =
      new Date(
        batchStartDate
      );


    selectedWeekEndDate.setDate(
      selectedWeekEndDate.getDate() +
        (week * 7) -
        1
    );


    const validEntries =
      entries.filter(
        (entry) => {

          if (
            !entry.week_start
          ) {
            return false;
          }


          const weekStartDate =
            new Date(
              entry.week_start
            );


          return (
            weekStartDate <=
            selectedWeekEndDate
          );

        }
      );


    if (
      validEntries.length === 0
    ) {
      return 0;
    }


    // Get the latest tracker entry
    // up to the selected week.

    const latestEntry =
      [...validEntries].sort(
        (a, b) =>
          new Date(
            b.week_start
          ) -
          new Date(
            a.week_start
          )
      )[0];


    return (
      Number(
        latestEntry
          .weekly_completion_efficiency
      ) || 0/(okr.target)*100
    );

  }


  // =========================================================
  // NORMAL OKR
  // =========================================================

  const latestUpdate =
    getLatestOkrUpdate(
      okr,
      weekNumber
    );


  if (!latestUpdate) {
    return 0;
  }


  return (
    Number(
      latestUpdate.progress
    ) || 0
  );

};
  // =========================================================
  // GET EXPECTED PROGRESS TILL WEEK
  // =========================================================

const getExpectedTillWeek = (
  okr,
  weekNumber = selectedWeek
) => {

  const target =
    Number(okr.target) || 0;


  // =========================================================
  // TRACKER OKR
  // =========================================================

  if (
    okr?.tracker_enabled
  ) {

    return target;

  }


  /*
    NORMAL OKR

    If user selected a week,
    use that week.

    Otherwise use current week.

    If today is outside batch:
    currentWeek = 0
    therefore expected = 0.
  */

  let week =
    Number(weekNumber) || 0;


  if (week <= 0) {

    week =
      getCurrentWeekNumber(
        okr.batch
      );

  }


  // -----------------------------------------
  // Prevent invalid calculation
  // -----------------------------------------

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
  // GET PROGRESS % TILL NOW
  // =========================================================

  const getProgressPercentageTillNow = (
    okr,
    weekNumber = selectedWeek
  ) => {

    const actualProgress =
      getOkrTotalProgress(
        okr,
        weekNumber
      );


    const expectedProgress =
      getExpectedTillWeek(
        okr,
        weekNumber
      );


    // -----------------------------------------
    // Prevent division by zero
    // -----------------------------------------

    if (
      expectedProgress <= 0
    ) {
      return 0;
    }


    return (
      actualProgress /
      expectedProgress
    ) * 100;

  };


  // =========================================================
  // GET OVERALL OKR PROGRESS %
  // =========================================================

  const getOkrProgressPercentage = (
    okr,
    weekNumber = selectedWeek
  ) => {

    const progress =
      getOkrTotalProgress(
        okr,
        weekNumber
      );

     console.log("progress id",progress);
    const target =
      Number(okr.target) || 0;


    if (
      target <= 0
    ) {
      return 0;
    }


    return (
      progress /
      target
    ) * 100;

  };


  // =========================================================
  // FETCH CURRENT USER
  // =========================================================

  const fetchUsers = async () => {

    try {

      const response =
        await fetch(
          `${API_URL}/api/users/me`,
          {
            method: "GET",

            headers: {
              "Content-Type":
                "application/json",

              Authorization:
                `Bearer ${localStorage.getItem(
                  "token"
                )}`,
            },
          }
        );


      if (!response.ok) {
        throw new Error(
          "Failed to fetch current user"
        );
      }


      const data =
        await response.json();


      console.log(
        "Current User:",
        data
      );


      setUserID(data.id);


      return data.id;

    } catch (error) {

      console.error(
        "Error fetching user:",
        error
      );


      return null;

    }

  };


  // =========================================================
  // FETCH Tracker Enteries
  // =========================================================
const fetchTrackerEntries = async (okrIds) => {

  try {

    if (!okrIds?.length) {

      setTrackerEntries({});

      return;

    }

    const results = await Promise.all(

      okrIds.map(async (okrId) => {

        const response = await fetch(
          `${API_URL}/api/okrs/${okrId}/tracker-entries?page=1&size=100&sort_by=week_start&sort_order=asc`,
          {
            method: "GET",

            headers: {
              Accept: "*/*",

              Authorization:
                `Bearer ${localStorage.getItem("token")}`,
            },
          }
        );

        if (!response.ok) {

          const errorData =
            await response.json().catch(() => null);

          console.error(
            `Tracker API error for ${okrId}:`,
            errorData
          );

          throw new Error(
            "Failed to fetch tracker entries"
          );
        }

        const result =
          await response.json();

        return [
          okrId,
          result.data || [],
        ];
      })
    );

    const trackerObject =
      Object.fromEntries(results);

    setTrackerEntries(
      trackerObject
    );

    console.log(
      "Tracker Entries:",
      trackerObject
    );

  } catch (error) {

    console.error(
      "Error fetching tracker entries:",
      error
    );

  }

};

  // =========================================================
  // FETCH WEEKLY UPDATES
  // =========================================================

  const fetchWeeklyUpdates = async (
    okrIds
  ) => {

    try {

      if (!okrIds?.length) {

        setWeeklyUpdates({});

        return;

      }


      const results =
        await Promise.all(

          okrIds.map(
            async (okrId) => {

              const response =
                await fetch(
                  `${API_URL}/api/okrs/${okrId}/weekly-updates`,
                  {
                    headers: {
                      Authorization:
                        `Bearer ${localStorage.getItem(
                          "token"
                        )}`,
                    },
                  }
                );


              if (!response.ok) {

                throw new Error(
                  "Failed to fetch weekly updates"
                );

              }


              const result =
                await response.json();


              return [
                okrId,
                result.data || [],
              ];

            }
          )

        );


      const updateObject =
        Object.fromEntries(
          results
        );


      setWeeklyUpdates(
        updateObject
      );


      console.log(
        "Weekly Updates:",
        updateObject
      );

    } catch (error) {

      console.error(
        "Error fetching weekly updates:",
        error
      );

    }

  };


  // =========================================================
  // FETCH MY OKRS
  // =========================================================

  const fetchMyOkr = async (
    userId,
    page = 1,
    size = 10
  ) => {

    if (!userId) {

      console.log(
        "User ID is missing"
      );

      return;

    }


    try {

      const response =
        await fetch(
          `${API_URL}/api/okrs/user/${userId}?page=${page}&size=${size}`,
          {
            method: "GET",

            headers: {
              "Content-Type":
                "application/json",

              Authorization:
                `Bearer ${localStorage.getItem(
                  "token"
                )}`,
            },
          }
        );


      if (!response.ok) {

        throw new Error(
          "Failed to fetch OKRs"
        );

      }


      const data =
        await response.json();


      console.log(
        "My OKRs:",
        data
      );


      setMyOkr(data);


      setFilteredMyOkr(
        data.data || []
      );


      // -----------------------------------------
      // Get OKR IDs
      // -----------------------------------------

      const okrIds =
        (data.data || []).map(
          (okr) => okr.id
        );


      console.log(
        "OKR IDs:",
        okrIds
      );


      // -----------------------------------------
      // Fetch weekly updates
      // -----------------------------------------

await Promise.all([
  fetchWeeklyUpdates(okrIds),
  fetchTrackerEntries(okrIds),
]);

      /*
        If current selected week is not available
        for the new batch, reset it.
      */

      const firstBatch =
        data?.data?.[0]?.batch;


      const availableWeeks =
        getAvailableWeeks(
          firstBatch
        );


      if (
        selectedWeek !== null &&
        !availableWeeks.includes(
          Number(selectedWeek)
        )
      ) {

        setSelectedWeek(null);

      }

    } catch (error) {

      console.error(
        "Error fetching OKRs:",
        error
      );

    }

  };


  // =========================================================
  // LOAD DATA
  // =========================================================

  useEffect(() => {

    const loadData =
      async () => {

        const userId =
          await fetchUsers();


        if (userId) {

          await fetchMyOkr(
            userId,
            currentPage,
            pageSize
          );

        }

      };


    loadData();

  }, [
    currentPage,
    pageSize,
  ]);


  // =========================================================
  // UPDATE PROGRESS MODAL
  // =========================================================

  const updateprogress = (okr) => {

    setSelectedOkr(okr);


    /*
      Reset progress form
      whenever modal opens.
    */

    setProgressData({
      week_number: "",
      progress: "",
      remarks: "None",
    });


    setIsProgressModalOpen(
      true
    );

  };


  // =========================================================
  // UPDATE FOGS / HURDLES MODAL
  // =========================================================

  const updatefogshurdles = (okr) => {

    setSelectedOkr(okr);


    setHurdleData({
      fogs_hurdles: "",
      action_points: "",
    });


    setIsHurdleModalOpen(
      true
    );

  };


  // =========================================================
  // SHOW OKR
  // =========================================================

  const showOkr = (okr) => {

    setSelectedOkr(okr);

    setActiveHistoryTab(
      "weekly"
    );

    setExpandedWeeks({});

    setIsShowOkrModalOpen(
      true
    );

  };


  // =========================================================
  // WEEKLY HISTORY
  // =========================================================

  const showWeeklyHistory = () => {

    setActiveHistoryTab(
      "weekly"
    );

  };


  // =========================================================
  // FOGS HISTORY
  // =========================================================

  const showFogsHurdlesHistory =
    async () => {

      setActiveHistoryTab(
        "fogs"
      );


      if (
        !fogsHurdlesHistory[
          selectedokr?.id
        ]
      ) {

        await fetchFogsHurdlesHistory(
          selectedokr.id
        );

      }

    };


  // =========================================================
  // FETCH FOGS HISTORY
  // =========================================================

  const fetchFogsHurdlesHistory =
    async (okrId) => {

      try {

        setIsLoadingFogsHurdles(
          true
        );


        const response =
          await fetch(
            `${API_URL}/api/okrs/${okrId}/fogs-hurdles?page=1&size=20&sort_by=created_at&sort_order=desc`,
            {
              method: "GET",

              headers: {
                "Content-Type":
                  "application/json",

                Authorization:
                  `Bearer ${localStorage.getItem(
                    "token"
                  )}`,
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


        console.log(
          "FOGS/Hurdles History:",
          result
        );


        setFogsHurdlesHistory(
          (prev) => ({
            ...prev,

            [okrId]:
              result.data || [],
          })
        );

      } catch (error) {

        console.error(
          "Error fetching FOGS/Hurdles history:",
          error
        );

      } finally {

        setIsLoadingFogsHurdles(
          false
        );

      }

    };


  // =========================================================
  // SAVE PROGRESS
  // =========================================================

const handleSaveProgress = async () => {

  // =================================================
  // Validate week
  // =================================================

  if (!progressData.week_number) {
    alert("Please select a week.");
    return;
  }

  // =================================================
  // TRACKER ENABLED
  // =================================================

  if (selectedokr?.tracker_enabled) {

    // -----------------------------------------
    // Validate opportunities received
    // -----------------------------------------

    if (
      progressData.opportunity_received === "" ||
      progressData.opportunity_received === null ||
      progressData.opportunity_received === undefined
    ) {
      alert("Please enter opportunities received.");
      return;
    }

    // -----------------------------------------
    // Validate opportunities completed
    // -----------------------------------------

    if (
      progressData.opportunity_completed === "" ||
      progressData.opportunity_completed === null ||
      progressData.opportunity_completed === undefined
    ) {
      alert("Please enter opportunities completed.");
      return;
    }

    const opportunitiesReceived =
      Number(progressData.opportunity_received);

    const opportunitiesCompleted =
      Number(progressData.opportunity_completed);

    // -----------------------------------------
    // Validate numbers
    // -----------------------------------------

    if (
      Number.isNaN(opportunitiesReceived) ||
      Number.isNaN(opportunitiesCompleted)
    ) {
      alert("Please enter valid opportunity values.");
      return;
    }

    // -----------------------------------------
    // Validate received >= 0
    // -----------------------------------------

    if (opportunitiesReceived < 0) {
      alert(
        "Opportunities received cannot be less than 0."
      );
      return;
    }

    // -----------------------------------------
    // Validate completed >= 0
    // -----------------------------------------

    if (opportunitiesCompleted < 0) {
      alert(
        "Opportunities completed cannot be less than 0."
      );
      return;
    }

    // -----------------------------------------
    // Completed cannot exceed received
    // -----------------------------------------

    if (
      opportunitiesCompleted >
      opportunitiesReceived
    ) {
      alert(
        "Opportunities completed cannot be greater than opportunities received."
      );
      return;
    }

    // =================================================
    // Calculate week_start
    // =================================================

    if (!selectedokr?.batch?.start_date) {
      alert("Batch start date is not available.");
      return;
    }

    const startDate =
      new Date(selectedokr.batch.start_date);

    startDate.setHours(0, 0, 0, 0);

    const weekNumber =
      Number(progressData.week_number);

    const weekStart =
      new Date(startDate);

    weekStart.setDate(
      startDate.getDate() +
      (weekNumber - 1) * 7
    );

    // -----------------------------------------
    // Convert to YYYY-MM-DD
    // -----------------------------------------

    const year =
      weekStart.getFullYear();

    const month =
      String(
        weekStart.getMonth() + 1
      ).padStart(2, "0");

    const day =
      String(
        weekStart.getDate()
      ).padStart(2, "0");

    const weekStartDate =
      `${year}-${month}-${day}`;

    console.log(
      "Tracker week_start:",
      weekStartDate
    );

    // =================================================
    // Save tracker entry
    // =================================================

    try {

      const response =
        await fetch(
          `${API_URL}/api/okrs/${selectedokr.id}/tracker-entries`,
          {
            method: "POST",

            headers: {
              "Content-Type":
                "application/json",

              Authorization:
                `Bearer ${localStorage.getItem(
                  "token"
                )}`,
            },

            body: JSON.stringify({
              week_start:
                weekStartDate,

              opportunities_received:
                opportunitiesReceived,

              opportunities_completed:
                opportunitiesCompleted,
            }),
          }
        );

      // -----------------------------------------
      // Handle API error
      // -----------------------------------------

      if (!response.ok) {

        const errorData =
          await response
            .json()
            .catch(() => null);

        console.error(
          "Save tracker entry error:",
          errorData
        );

        throw new Error(
          errorData?.detail ||
          "Failed to save tracker entry"
        );
      }

      // -----------------------------------------
      // Refresh data
      // -----------------------------------------

      await fetchWeeklyUpdates(
        myOkr.data.map(
          (okr) => okr.id
        )
      );

      // -----------------------------------------
      // Close modal
      // -----------------------------------------

      setIsProgressModalOpen(false);

      // -----------------------------------------
      // Reset form
      // -----------------------------------------

      setProgressData({
        week_number: "",
        progress: "",
        opportunity_received: "",
        opportunity_completed: "",
        remarks: "None",
      });

    } catch (error) {

      console.error(
        "Error saving tracker progress:",
        error
      );

      alert(
        error.message ||
        "Error saving tracker progress. Please try again."
      );
    }

    return;
  }

  // =================================================
  // NORMAL OKR
  // =================================================

  // -----------------------------------------
  // Validate progress
  // -----------------------------------------

  if (
    progressData.progress === "" ||
    progressData.progress === null ||
    progressData.progress === undefined
  ) {
    alert(
      "Please enter the achieved target value."
    );
    return;
  }

  const achievedValue =
    Number(progressData.progress);

  const givenTarget =
    Number(selectedokr.target);

  // -----------------------------------------
  // Validate number
  // -----------------------------------------

  if (Number.isNaN(achievedValue)) {
    alert(
      "Please enter a valid achieved target value."
    );
    return;
  }

  // -----------------------------------------
  // Validate target >= 0
  // -----------------------------------------

  if (achievedValue < 0) {
    alert(
      "Target achieved value cannot be less than 0."
    );
    return;
  }

  // -----------------------------------------
  // Validate target maximum
  // -----------------------------------------

  if (achievedValue > givenTarget) {
    alert(
      "Target achieved value cannot be greater than the given target value."
    );
    return;
  }

  // =================================================
  // Save normal weekly update
  // =================================================

  try {

    const response =
      await fetch(
        `${API_URL}/api/okrs/${selectedokr.id}/weekly-updates`,
        {
          method: "POST",

          headers: {
            "Content-Type":
              "application/json",

            Authorization:
              `Bearer ${localStorage.getItem(
                "token"
              )}`,
          },

          body: JSON.stringify(
            progressData
          ),
        }
      );

    // -----------------------------------------
    // Handle API error
    // -----------------------------------------

    if (!response.ok) {

      const errorData =
        await response
          .json()
          .catch(() => null);

      console.error(
        "Save progress error:",
        errorData
      );

      throw new Error(
        errorData?.detail ||
        "Failed to save progress"
      );
    }

    // -----------------------------------------
    // Refresh data
    // -----------------------------------------

    await fetchWeeklyUpdates(
      myOkr.data.map(
        (okr) => okr.id
      )
    );

    // -----------------------------------------
    // Close modal
    // -----------------------------------------

    setIsProgressModalOpen(false);

    // -----------------------------------------
    // Reset form
    // -----------------------------------------

    setProgressData({
      week_number: "",
      progress: "",
      opportunity_received: "",
      opportunity_completed: "",
      remarks: "None",
    });

  } catch (error) {

    console.error(
      "Error saving progress:",
      error
    );

    alert(
      error.message ||
      "Error saving progress. Please try again."
    );
  }
};


//---------------------------------------------------------------------------------------------
//for tracker entries and progress percentage calculations
//---------------------------------------------------------------------------------------------
const getTrackerEntries = (
  okr
) => {

  return (
    trackerEntries[
      okr.id
    ] || []
  );

};

const getTrackerProgressPercentageTillNow = (
  okr,
  weekNumber = selectedWeek
) => {
   console.log("getTrackerProgressPercentageTillNow")
  const entries =
    getTrackerEntries(
      okr
    );


  if (
    entries.length === 0
  ) {
    return 0;
  }


  const batchStartDate =
    new Date(
      okr?.batch?.start_date
    );

   console.log("Batch Start Date",batchStartDate)
  const selectedWeekEndDate =
    new Date(
      batchStartDate
    );

  selectedWeekEndDate.setDate(
    selectedWeekEndDate.getDate() +
      (
        Number(weekNumber) * 7
      ) 
  );


  const validEntries =
    entries.filter(
      (entry) => {
         console.log(entry)
        if (!entry.week_start) {
          return false;
        }


        const weekStartDate =
          new Date(
            entry.week_start
          );

        console.log(weekStartDate,selectedWeekEndDate)
        return (
          weekStartDate <=
          selectedWeekEndDate
        );

      }
    );

  console.log("Valid enteries",validEntries)
  if (
    validEntries.length === 0
  ) {
    return 0;
  }


  // Latest tracker entry
  // till selected week

  const latestEntry =
    [...validEntries].sort(
      (a, b) =>
        new Date(
          b.updated_at
        ) -
        new Date(
          a.updated_at
        )
    )[0];


  console.log((latestEntry
        .weekly_completion_efficiency
    ) || 0, (okr.target))  
  return (
    (Number(
      latestEntry
        .weekly_completion_efficiency
    ) || 0)/Number(okr.target)*100
  );

};


const getTrackerOkrProgressPercentage = (
  okr,
  weekNumber = selectedWeek
) => {

  const entries =
    getTrackerEntries(
      okr
    );


  if (
    entries.length === 0
  ) {
    return 0;
  }


  const batchStartDate =
    new Date(
      okr?.batch?.start_date
    );


  let week =
    Number(weekNumber) || 0;


  if (week <= 0) {

    week =
      getCurrentWeekNumber(
        okr.batch
      );

  }


  if (week <= 0) {
    return 0;
  }


  const selectedWeekEndDate =
    new Date(
      batchStartDate
    );


  selectedWeekEndDate.setDate(
    selectedWeekEndDate.getDate() +
      (week * 7) 
      
  );


  const validEntries =
    entries.filter(
      (entry) => {

        if (
          !entry.week_start
        ) {
          return false;
        }


        const weekStartDate =
          new Date(
            entry.week_start
          );


        return (
          weekStartDate <=
          selectedWeekEndDate
        );

      }
    );


  if (
    validEntries.length === 0
  ) {
    return 0;
  }


  // Get the latest tracker entry
  // up to the selected week.

  const latestEntry =
    [...validEntries].sort(
      (a, b) =>
        new Date(
          b.updated_at
        ) -
        new Date(
          a.updated_at
        )
    )[0];


  // Tracker overall progress is
  // the same as completion efficiency.

  return (
    (Number(
      latestEntry
        .weekly_completion_efficiency
    ) || 0)/Number(okr.target)*100
  );

};
  // =========================================================
  // SAVE FOGS / HURDLES
  // =========================================================

  const handleSaveHurdles =
    async () => {

      if (
        !hurdleData.fogs_hurdles.trim()
      ) {

        alert(
          "Please enter FOGS."
        );

        return;

      }


      if (
        !hurdleData.action_points.trim()
      ) {

        alert(
          "Please enter action points."
        );

        return;

      }


      try {

        const response =
          await fetch(
            `${API_URL}/api/okrs/${selectedokr.id}/fogs-hurdles`,
            {
              method: "POST",

              headers: {
                "Content-Type":
                  "application/json",

                Authorization:
                  `Bearer ${localStorage.getItem(
                    "token"
                  )}`,
              },

              body:
                JSON.stringify(
                  hurdleData
                ),
            }
          );


        if (!response.ok) {

          throw new Error(
            "Failed to update FOGS / Action Points"
          );

        }


        const data =
          await response.json();


        console.log(
          "FOGS / Action Points updated:",
          data
        );


        // -----------------------------------------
        // Clear cache so next history opens fresh
        // -----------------------------------------

        setFogsHurdlesHistory(
          (prev) => {

            const copy = {
              ...prev,
            };

            delete copy[
              selectedokr.id
            ];

            return copy;

          }
        );


        setIsHurdleModalOpen(
          false
        );


        setHurdleData({
          fogs_hurdles: "",
          action_points: "",
        });

      } catch (error) {

        console.error(
          "Error updating FOGS / Action Points:",
          error
        );


        alert(
          "Error updating FOGS / Action Points."
        );

      }

    };


  // =========================================================
  // PAGINATION
  // =========================================================

  const totalPages =
    Math.ceil(
      myOkr.pagination.total /
      pageSize
    );


  // =========================================================
  // AVAILABLE WEEKS
  // =========================================================

  const availableWeeks =
    getAvailableWeeks(
      batch
    );


  // =========================================================
  // CURRENT WEEK
  // =========================================================

  const currentWeek =
    getCurrentWeekNumber(
      batch
    );


  // =========================================================
  // SELECTED WEEK LABEL
  // =========================================================

  const selectedWeekLabel =
    selectedWeek
      ? `Week ${selectedWeek}`
      : "All Weeks";


  // =========================================================
  // RENDER
  // =========================================================

  return (

    <section
      className="page"
      id="page-my-okr"
    >

      {/* =====================================================
          FILTER BAR
      ===================================================== */}

      <div className="filters-bar">

        {/* ================= SEARCH ================= */}

        <div className="search-wrap">

          <div className="search-icon">

            <svg
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >

              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />

            </svg>

          </div>


          <input
            type="text"
            className="search-input"
            placeholder="Search OKRs..."
            onChange={(e) => {

              const searchTerm =
                e.target.value
                  .toLowerCase()
                  .trim();


              if (
                searchTerm === ""
              ) {

                setFilteredMyOkr(
                  myOkr.data
                );

                return;

              }


              const filtered =
                myOkr.data.filter(
                  (okr) =>
                    okr.objective
                      ?.toLowerCase()
                      .includes(
                        searchTerm
                      ) ||
                    okr.key_results
                      ?.toLowerCase()
                      .includes(
                        searchTerm
                      )
                );


              setFilteredMyOkr(
                filtered
              );

            }}
          />

        </div>


        {/* ================= WEEK FILTER ================= */}

        <div className="week-filter">

          <label htmlFor="week-select">
            Week
          </label>


          <select
            id="week-select"
            value={
              selectedWeek ?? ""
            }
            onChange={(e) => {

              const value =
                e.target.value;


              if (value === "") {

                setSelectedWeek(
                  null
                );

              } else {

                setSelectedWeek(
                  Number(value)
                );

              }

            }}
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
                  {" — "}
                  {getWeekDateRange(
                    week
                  )}

                </option>

              )
            )}

          </select>

        </div>


        {/* ================= CURRENT WEEK INFO ================= */}

        <div
          style={{
            display: "flex",
            alignItems: "center",
            marginLeft: "10px",
            fontSize: "13px",
            color: "#666",
          }}
        >

          {currentWeek > 0 ? (

            <span>
              Current: Week{" "}
              {currentWeek}
            </span>

          ) : (

            <span>
              Outside batch period
            </span>

          )}

        </div>

      </div>


      {/* =====================================================
          MY OKR CARD
      ===================================================== */}

      <div className="card">

        <div className="card-header">

          <div>

            <div className="card-title">
              My OKRs
            </div>

            {batch && (

              <div
                style={{
                  fontSize: "13px",
                  color: "#777",
                  marginTop: "4px",
                }}
              >

                {batch.name}
                {" | "}
                {batch.quarter}
                {" "}
                {batch.year}

              </div>

            )}

          </div>

        </div>


        {/* ===================================================
            MY OKR TABLE
        =================================================== */}

        <div className="organization-table-wrap">

          <table className="organization-table">

            <thead>

              <tr>

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

                <th>
                  Update Progress
                </th>

                <th>
                  Update FOGS Hurdles
                </th>

              </tr>

            </thead>


            <tbody>

              {filteredMyOkr?.length === 0 ? (

                <tr>

                  <td
                    colSpan="10"
                    style={{
                      textAlign: "center",
                      padding: "30px",
                    }}
                  >
                    No OKRs found.
                  </td>

                </tr>

              ) : (

                filteredMyOkr.map(
                  (okr) => {

                    // ---------------------------------------
                    // Values based on selected week
                    // ---------------------------------------

                    const totalProgress =
                      getOkrTotalProgress(
                        okr
                      );


                    const expectedTillWeek =
                      getExpectedTillWeek(
                        okr
                      );


                    const progressPercentageTillNow =
                      getProgressPercentageTillNow(
                        okr
                      );


                    const overallProgressPercentage =
                      getOkrProgressPercentage(
                        okr
                      );


                    const okrCurrentWeek =
                      getCurrentWeekNumber(
                        okr.batch
                      );


                    return (

                      <tr
                        key={okr.id}
                        className="organization-row"
                        onClick={() =>
                          showOkr(
                            okr
                          )
                        }
                      >

                        {/* ================= OBJECTIVE ================= */}

                        <td>

                          <div className="organization-info">

                            <strong>
                              {okr.objective}
                            </strong>

                          </div>

                        </td>


                        {/* ================= KEY RESULT ================= */}

                        <td>
                          {okr.key_results}
                        </td>


                        {/* ================= TARGET ================= */}

                        <td>
                          {okr.target}
                        </td>


                        {/* ================= OKR TYPE ================= */}

                        <td>
                          {okr.okr_type}
                        </td>


                        {/* ================= TOTAL PROGRESS ================= */}

                        <td>

                          <strong>
                            {Number(
                              totalProgress
                            ).toFixed(2)}
                          </strong>

                        </td>


                        {/* ================= EXPECTED ================= */}

                        <td>

                          <div>

                            <strong>
                              {Number(
                                expectedTillWeek
                              ).toFixed(2)}
                            </strong>


                            {selectedWeek ? (

                              <small
                                style={{
                                  display:
                                    "block",
                                  color:
                                    "#777",
                                  marginTop:
                                    "3px",
                                }}
                              >

                                Selected:
                                {" "}
                                Week{" "}
                                {selectedWeek}

                              </small>

                            ) : okrCurrentWeek > 0 ? (

                              <small
                                style={{
                                  display:
                                    "block",
                                  color:
                                    "#777",
                                  marginTop:
                                    "3px",
                                }}
                              >

                                Current:
                                {" "}
                                Week{" "}
                                {okrCurrentWeek}

                              </small>

                            ) : (

                              <small
                                style={{
                                  display:
                                    "block",
                                  color:
                                    "#999",
                                  marginTop:
                                    "3px",
                                }}
                              >

                                Outside batch
                                period

                              </small>

                            )}

                          </div>

                        </td>


                        {/* ================= PROGRESS % TILL NOW ================= */}

                        <td>

                          <div className="okr-progress">

                            <div className="okr-progress-track">

                              <div
                                className={`okr-progress-fill ${
                                  (
                                    okr?.tracker_enabled
                                      ? getTrackerProgressPercentageTillNow(
                                          okr,
                                          selectedWeek
                                        )
                                      : getProgressPercentageTillNow(
                                          okr,
                                          selectedWeek
                                        )
                                  ) < 60
                                    ? "progress-red"
                                    : (
                                        okr?.tracker_enabled
                                          ? getTrackerProgressPercentageTillNow(
                                              okr,
                                              selectedWeek
                                            )
                                          : getProgressPercentageTillNow(
                                              okr,
                                              selectedWeek
                                            )
                                      ) < 80
                                    ? "progress-yellow"
                                    : "progress-green"
                                }`}
                                style={{
                                  width: `${Math.min(
                                    Math.max(
                                      okr?.tracker_enabled
                                        ? getTrackerProgressPercentageTillNow(
                                            okr,
                                            selectedWeek
                                          )
                                        : getProgressPercentageTillNow(
                                            okr,
                                            selectedWeek
                                          ),
                                      0
                                    ),
                                    100
                                  )}%`,
                                }}
                              />

                            </div>

                            <span>

                              {Number(
                                okr?.tracker_enabled
                                  ? getTrackerProgressPercentageTillNow(
                                      okr,
                                      selectedWeek
                                    )
                                  : getProgressPercentageTillNow(
                                      okr,
                                      selectedWeek
                                    )
                              ).toFixed(2)}

                              %

                            </span>

                          </div>

                        </td>

                        {/* ================= OVERALL PROGRESS % ================= */}

                        {(() => {

  const overallProgressPercentage =
    okr?.tracker_enabled
      ? getTrackerOkrProgressPercentage(
          okr,
          selectedWeek
        )
      : getOkrProgressPercentage(
          okr,
          selectedWeek
        );

  return (
    <td>

      <div className="okr-progress">

        <div className="okr-progress-track">

          <div
            className={`okr-progress-fill ${
              overallProgressPercentage < 60
                ? "progress-red"
                : overallProgressPercentage < 80
                ? "progress-yellow"
                : "progress-green"
            }`}
            style={{
              width: `${Math.min(
                Math.max(
                  overallProgressPercentage,
                  0
                ),
                100
              )}%`,
            }}
          />

        </div>

        <span>
          {Number(
            overallProgressPercentage
          ).toFixed(2)}
          %
        </span>

      </div>

    </td>
  );

})()}

                        {/* ================= UPDATE PROGRESS ================= */}

                        <td>

                          <button
                            type="button"
                            className="okr-icon-btn status"
                            title="Update OKR Status"
                            onClick={(e) => {

                              e.stopPropagation();

                              updateprogress(
                                okr
                              );

                            }}
                          >

                            <FiTrendingUp
                              size={17}
                            />

                          </button>

                        </td>


                        {/* ================= FOGS ================= */}

                        <td>

                          <button
                            type="button"
                            className="okr-icon-btn hurdle"
                            title="Update FOGS / Action Points"
                            onClick={(e) => {

                              e.stopPropagation();

                              updatefogshurdles(
                                okr
                              );

                            }}
                          >

                            <MdUpdate
                              size={17}
                            />

                          </button>

                        </td>

                      </tr>

                    );

                  }
                )

              )}

            </tbody>

          </table>

        </div>


        {/* ===================================================
            PAGINATION
        =================================================== */}

        <div className="pagination">

          <div className="pagination-size">

            <span>
              Rows per page:
            </span>


            <select
              value={pageSize}
              onChange={(e) => {

                setPageSize(
                  Number(
                    e.target.value
                  )
                );

                setCurrentPage(
                  1
                );

              }}
            >

              <option value={10}>
                10
              </option>

              <option value={20}>
                20
              </option>

              <option value={30}>
                30
              </option>

              <option value={50}>
                50
              </option>

            </select>

          </div>


          <div className="pagination-pages">

            <button
              className="pagination-btn"
              disabled={
                currentPage === 1
              }
              onClick={() =>
                setCurrentPage(
                  currentPage - 1
                )
              }
            >

              Previous

            </button>


            <span className="pagination-info">

              Page{" "}
              {currentPage}
              {" "}
              of{" "}
              {totalPages}

            </span>


            <button
              className="pagination-btn"
              disabled={
                currentPage ===
                  totalPages ||
                totalPages === 0
              }
              onClick={() =>
                setCurrentPage(
                  currentPage + 1
                )
              }
            >

              Next

            </button>

          </div>

        </div>

      </div>



{/* =====================================================
    PROGRESS MODAL
===================================================== */}

{isProgressModalOpen &&
  selectedokr && (

    <div
      className="progress-modal-overlay"
      onClick={() =>
        setIsProgressModalOpen(false)
      }
    >

      <div
        className="progress-modal-card"
        onClick={(e) =>
          e.stopPropagation()
        }
      >

        {/* HEADER */}

        <div className="progress-modal-header">

          <div>

            <h3>
              Update Progress
            </h3>

            <p>
              Update the achieved
              target for this week.
            </p>

          </div>

          <button
            type="button"
            className="progress-close-btn"
            onClick={() =>
              setIsProgressModalOpen(false)
            }
          >
            ×
          </button>

        </div>


        {/* BODY */}

        <div className="progress-modal-body">

          {/* ================= WEEK ================= */}

          <div className="progress-form-group">

            <label>
              Week Number
            </label>

            <select
              value={
                progressData.week_number
              }
              onChange={(e) =>
                setProgressData({
                  ...progressData,

                  week_number:
                    e.target.value,
                })
              }
            >

              <option value="">
                Select Week
              </option>

              {getAvailableWeeks(
                selectedokr.batch
              ).map(
                (week) => (

                  <option
                    key={week}
                    value={week}
                  >

                    Week {week}
                    {" — "}
                    {getWeekDateRange(
                      week
                    )}

                  </option>

                )
              )}

            </select>

          </div>


          {/* ================= GIVEN TARGET ================= */}

          <div className="progress-form-group">

            <label>
              Given Target Value
            </label>

            <input
              type="number"
              value={
                selectedokr.target
              }
              readOnly
            />

          </div>


          {/* ================= ACHIEVED ================= */}

          {selectedokr?.tracker_enabled ? (

            <>
              {/* ================= OPPORTUNITY RECEIVED ================= */}

              <div className="progress-form-group">

                <label>
                  Opportunity Received Till Date
                </label>

                <input
                  type="number"
                  placeholder="Enter opportunity received"
                  min={0}
                  value={
                    progressData.opportunity_received ?? ""
                  }
                  onChange={(e) =>
                    setProgressData({
                      ...progressData,

                      opportunity_received:
                        e.target.value,
                    })
                  }
                />

              </div>


              {/* ================= OPPORTUNITY COMPLETED ================= */}

              <div className="progress-form-group">

                <label>
                  Opportunity Completed Till Date
                </label>

                <input
                  type="number"
                  placeholder="Enter opportunity completed"
                  min={0}
                  value={
                    progressData.opportunity_completed ?? ""
                  }
                  onChange={(e) =>
                    setProgressData({
                      ...progressData,

                      opportunity_completed:
                        e.target.value,
                    })
                  }
                />

              </div>

            </>

          ) : (

            /* ================= TARGET ACHIEVED ================= */

            <div className="progress-form-group">

              <label>
                Target Value Achieved
              </label>

              <input
                type="number"
                placeholder="Enter achieved value"
                value={
                  progressData.progress
                }
                max={
                  selectedokr.target
                }
                min={0}
                onChange={(e) =>
                  setProgressData({
                    ...progressData,

                    progress:
                      e.target.value,
                  })
                }
              />

            </div>

          )}

        </div>


        {/* FOOTER */}

        <div className="progress-modal-footer">

          <button
            type="button"
            className="progress-cancel-btn"
            onClick={() =>
              setIsProgressModalOpen(false)
            }
          >
            Cancel
          </button>

          <button
            type="button"
            className="progress-save-btn"
            onClick={
              handleSaveProgress
            }
          >
            Save Progress
          </button>

        </div>

      </div>

    </div>

  )}


      {/* =====================================================
          FOGS / HURDLES MODAL
      ===================================================== */}

      {isHurdleModalOpen &&
        selectedokr && (

          <div
            className="progress-modal-overlay"
            onClick={() =>
              setIsHurdleModalOpen(
                false
              )
            }
          >

            <div
              className="progress-modal-card"
              onClick={(e) =>
                e.stopPropagation()
              }
            >

              {/* HEADER */}

              <div className="progress-modal-header">

                <div>

                  <h3>
                    Update FOGS / Hurdles
                  </h3>

                  <p>
                    Update the current FOGS
                    and hurdles for this OKR.
                  </p>

                </div>


                <button
                  type="button"
                  className="progress-close-btn"
                  onClick={() =>
                    setIsHurdleModalOpen(
                      false
                    )
                  }
                >
                  ×
                </button>

              </div>


              {/* BODY */}

              <div className="progress-modal-body">

                <div className="progress-form-group">

                  <label>
                    FOGS/HURDLES
                  </label>


                  <textarea
                    rows="4"
                    placeholder="Enter FOGS..."
                    value={
                      hurdleData.fogs_hurdles
                    }
                    onChange={(e) =>
                      setHurdleData(
                        {
                          ...hurdleData,

                          fogs_hurdles:
                            e.target.value,
                        }
                      )
                    }
                  />

                </div>


                <div className="progress-form-group">

                  <label>
                    Action Points
                  </label>


                  <textarea
                    rows="4"
                    placeholder="Enter action points..."
                    value={
                      hurdleData.action_points
                    }
                    onChange={(e) =>
                      setHurdleData(
                        {
                          ...hurdleData,

                          action_points:
                            e.target.value,
                        }
                      )
                    }
                  />

                </div>

              </div>


              {/* FOOTER */}

              <div className="progress-modal-footer">

                <button
                  type="button"
                  className="progress-cancel-btn"
                  onClick={() =>
                    setIsHurdleModalOpen(
                      false
                    )
                  }
                >

                  Cancel

                </button>


                <button
                  type="button"
                  className="progress-save-btn"
                  onClick={
                    handleSaveHurdles
                  }
                >

                  Save Changes

                </button>

              </div>

            </div>

          </div>

        )}


      {/* =====================================================
          SHOW OKR MODAL
      ===================================================== */}

      {isShowOkrModalOpen &&
        selectedokr && (

          <div
            className="show-okr-modal-overlay"
            onClick={() =>
              setIsShowOkrModalOpen(
                false
              )
            }
          >

            <div
              className="show-okr-modal-card"
              onClick={(e) =>
                e.stopPropagation()
              }
            >

              {/* ================= HEADER ================= */}

              <div className="show-okr-modal-header">

                <div>

                  <h3>
                    OKR Details
                  </h3>

                  <p>
                    View OKR details and
                    weekly progress history.
                  </p>

                </div>


                <button
                  type="button"
                  className="progress-close-btn"
                  onClick={() =>
                    setIsShowOkrModalOpen(
                      false
                    )
                  }
                >
                  ×
                </button>

              </div>


              {/* ================= DETAILS ================= */}

              <div className="show-okr-modal-body">

                <div className="okr-detail-section">

                  <div className="okr-detail-item">

                    <label>
                      Objective
                    </label>

                    <div className="okr-detail-value">
                      {selectedokr.objective}
                    </div>

                  </div>


                  <div className="okr-detail-item">

                    <label>
                      Key Result
                    </label>

                    <div className="okr-detail-value">
                      {selectedokr.key_results}
                    </div>

                  </div>


                  <div className="okr-detail-row">

                    <div className="okr-detail-item">

                      <label>
                        Target
                      </label>

                      <div className="okr-detail-value">
                        {selectedokr.target}
                      </div>

                    </div>


                    <div className="okr-detail-item">

                      <label>
                        OKR Type
                      </label>

                      <div className="okr-detail-value">
                        {selectedokr.okr_type}
                      </div>

                    </div>

                  </div>

                </div>


                {/* ================= HISTORY TABS ================= */}

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


                {/* =================================================
                    WEEKLY HISTORY
                ================================================= */}

                <div className="weekly-history-section">

                  {activeHistoryTab ===
                    "weekly" && (

                    <div className="weekly-history-list">

                      {(() => {

  const isTrackerEnabled =
    selectedokr?.tracker_enabled;


  // =========================================================
  // NORMAL OKR
  // =========================================================

  if (!isTrackerEnabled) {

    const updates =
      weeklyUpdates[
        selectedokr.id
      ] || [];


    const groupedUpdates =
      groupUpdatesByWeek(
        updates
      );


    if (
      updates.length ===
      0
    ) {

      return (

        <div className="no-weekly-updates">

          No weekly updates
          available.

        </div>

      );

    }


    return Object.entries(
      groupedUpdates
    )
      .sort(
        (
          [weekA],
          [weekB]
        ) =>
          Number(
            weekA
          ) -
          Number(
            weekB
          )
      )
      .map(
        (
          [
            weekNumber,
            weekUpdates,
          ]
        ) => {

          const latestUpdate =
            [...weekUpdates]
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
              )[0];


          const progressPercentage =
            Number(
              selectedokr.target
            )
              ? (
                  Number(
                    latestUpdate.progress
                  ) /
                  Number(
                    selectedokr.target
                  )
                ) *
                100
              : 0;


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

                  {" - "}

                  <span className="weekly-history-date">

                    (
                    {
                      getWeekDateRange(
                        Number(
                          weekNumber
                        )
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


              {/* PROGRESS */}

              <div className="weekly-history-progress">

                <div className="weekly-progress-track">

                  <div
                    className={`weekly-progress-fill ${
                      progressPercentage <
                      60
                        ? "progress-red"
                        : progressPercentage <
                          80
                        ? "progress-yellow"
                        : "progress-green"
                    }`}
                    style={{
                      width: `${Math.min(
                        Math.max(
                          progressPercentage,
                          0
                        ),
                        100
                      )}%`,
                    }}
                  />

                </div>


                <span>

                  {
                    latestUpdate.progress
                  }

                  {" / "}

                  {
                    selectedokr.target
                  }

                </span>

              </div>


              {/* REMARK */}

              <div className="weekly-history-remarks">

                <strong>
                  Latest Update:
                </strong>

                {" "}

                {
                  latestUpdate.remarks ||
                  "None"
                }

              </div>


              {/* HISTORY */}

              {isExpanded && (

                <div className="week-update-history">

                  <div className="week-update-history-title">

                    Update History

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
                              }

                              {" / "}

                              {
                                selectedokr.target
                              }

                            </strong>

                          </div>


                          <div className="week-update-history-remarks">

                            <strong>
                              Remarks:
                            </strong>

                            {" "}

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
      );

  }


  // =========================================================
  // TRACKER ENABLED OKR
  // =========================================================

  const trackerData =
    trackerEntries[
      selectedokr.id
    ] || [];


  if (
    trackerData.length ===
    0
  ) {

    return (

      <div className="no-weekly-updates">

        No tracker entries
        available.

      </div>

    );

  }


  // =========================================================
  // GROUP TRACKER ENTRIES BY WEEK
  // =========================================================

  const groupedTrackerEntries =
    trackerData.reduce(
      (
        groups,
        entry
      ) => {

        if (!entry.week_start) {
          return groups;
        }


        const batchStartDate =
          new Date(
            selectedokr?.batch?.start_date
          );

        const weekStartDate =
          new Date(
            entry.week_start
          );


        const diffInDays =
          Math.floor(
            (
              weekStartDate -
              batchStartDate
            ) /
            (
              1000 *
              60 *
              60 *
              24
            )
          );


        const weekNumber =
          Math.floor(
            diffInDays / 7
          ) + 1;


        if (!groups[weekNumber]) {
          groups[weekNumber] = [];
        }


        groups[weekNumber].push(
          entry
        );


        return groups;

      },
      {}
    );


  // =========================================================
  // DISPLAY TRACKER WEEKS
  // =========================================================

  return Object.entries(
    groupedTrackerEntries
  )
    .sort(
      (
        [weekA],
        [weekB]
      ) =>
        Number(
          weekA
        ) -
        Number(
          weekB
        )
    )
    .map(
      (
        [
          weekNumber,
          weekEntries,
        ]
      ) => {

        const latestEntry =
          [...weekEntries]
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
            )[0];


        // Tracker API already provides
        // the efficiency percentage.

        const progressPercentage =
          Number(
            latestEntry
              .weekly_completion_efficiency
          ) || 0;


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

                {" - "}

                <span className="weekly-history-date">

                  (
                  {
                    getWeekDateRange(
                      Number(
                        weekNumber
                      )
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


            {/* PROGRESS */}

            <div className="weekly-history-progress">

              <div className="weekly-progress-track">

                <div
                  className={`weekly-progress-fill ${
                    progressPercentage <
                    60
                      ? "progress-red"
                      : progressPercentage <
                        80
                      ? "progress-yellow"
                      : "progress-green"
                  }`}
                  style={{
                    width: `${Math.min(
                      Math.max(
                        progressPercentage,
                        0
                      ),
                      100
                    )}%`,
                  }}
                />

              </div>


              <span>

                {
                  latestEntry.opportunities_completed
                }

                {" / "}

                {
                  latestEntry.opportunities_received
                }

              </span>

            </div>


            {/* TRACKER SUMMARY */}

            <div className="weekly-history-remarks">

              <strong>
                Completion Efficiency:
              </strong>

              {" "}

              {
                progressPercentage
              }%

              {" | Target: "}

              {
                latestEntry.target
              }%

            </div>


            {/* HISTORY */}

            {isExpanded && (

              <div className="week-update-history">

                <div className="week-update-history-title">

                  Update History

                </div>


                {[
                  ...weekEntries,
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
                              history.opportunities_completed
                            }

                            {" / "}

                            {
                              history.opportunities_received
                            }

                          </strong>

                        </div>


                        <div className="week-update-history-remarks">

                          <strong>
                            Completion Efficiency:
                          </strong>

                          {" "}

                          {
                            history.weekly_completion_efficiency
                          }%

                        </div>


                        <div className="week-update-history-remarks">

                          <strong>
                            Target:
                          </strong>

                          {" "}

                          {
                            history.target
                          }%

                        </div>

                      </div>

                    )
                  )}

              </div>

            )}

          </div>

        );

      }
    );

})()}

                    </div>

                  )}


                  {/* =================================================
                      FOGS HISTORY
                  ================================================= */}

                  {activeHistoryTab ===
                    "fogs" && (

                    <div className="weekly-history-list">

                      {isLoadingFogsHurdles ? (

                        <div className="no-weekly-updates">

                          Loading FOGS/Hurdles
                          history...

                        </div>

                      ) : (

                        (
                          fogsHurdlesHistory[
                            selectedokr.id
                          ] || []
                        ).length === 0 ? (

                          <div className="no-weekly-updates">

                            No FOGS/Hurdles
                            history available.

                          </div>

                        ) : (

                          (
                            fogsHurdlesHistory[
                              selectedokr.id
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

                                <div className="fogs-history-date">

                                  {new Date(
                                    history.created_at
                                  ).toLocaleString(
                                    "en-IN"
                                  )}

                                </div>


                                <div className="fogs-history-field">

                                  <div className="fogs-history-label">

                                    FOGS / Hurdles

                                  </div>


                                  <div className="fogs-history-value">

                                    {
                                      history.fogs_hurdles ||
                                      "None"
                                    }

                                  </div>

                                </div>


                                <div className="fogs-history-field">

                                  <div className="fogs-history-label">

                                    Action Points

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


              {/* ================= FOOTER ================= */}

              <div className="show-okr-modal-footer">

                <button
                  type="button"
                  className="progress-cancel-btn"
                  onClick={() =>
                    setIsShowOkrModalOpen(
                      false
                    )
                  }
                >

                  Close

                </button>

              </div>

            </div>

          </div>

        )}

    </section>

  );

}


export default MyOkr;