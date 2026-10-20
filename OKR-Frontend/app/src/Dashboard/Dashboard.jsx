import React, { useMemo, useState ,useEffect} from "react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  PointElement,
  LineElement,
  Tooltip,
  Legend,
  Filler,
} from "chart.js";

import { Bar, Doughnut, Line } from "react-chartjs-2";

import { API_URL } from "../Config/ApiEndpoint";

import {
  Users,
  BarChart3,
  Zap,
  AlertCircle,
  ChevronLeft,
  ChevronRight,
  Settings,
  ArrowRight,
  Info,
} from "lucide-react";

import "./Dashboard.css";

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  PointElement,
  LineElement,
  Tooltip,
  Legend,
  Filler
);

const Dashboard = () => {

  // ============================================================
  // STATE
  // ============================================================



  const [currentUser,setCurrentUser]=useState(null);

  const [selectedWeek, setSelectedWeek] =
    useState(0);

  const [selectedOkrType, setSelectedOkrType] =
    useState("All");

const [
  batchUserPerformance,
  setBatchUserPerformance
] = useState([]);
  // ============================================================
  // DASHBOARD API STATE
  // ============================================================

  // Total Employees
  const [totalEmployees, setTotalEmployees] =
    useState(0);

  const [loadingEmployees, setLoadingEmployees] =
    useState(true);


  // Total Active OKRs
  const [totalActiveOkrs, setTotalActiveOkrs] =
    useState(0);

  const [loadingActiveOkrs, setLoadingActiveOkrs] =
    useState(true);



  // ============================================================
  // OKR DATA
  // ============================================================

  // Actual active OKR objects
  const [okrs, setOkrs] =
    useState([]);


  const [weeklyUpdates, setWeeklyUpdates] =
    useState({});

//======================================================

const [usersData, setUsersData] = useState([]);

const [loadingDashboard, setLoadingDashboard] = useState(true);


const [allorganizations, setAllOrganizations] = useState([]);
const [selectedOrganization, setSelectedOrganization] = useState("ALL");

const [batches, setBatches] = useState([]);
const [selectedBatch, setSelectedBatch] = useState("ALL");

//=====================================================
//Data from API
//=====================================================

//fetch current user

const getCurrentUser = async () => {
  try {
    const response = await fetch(`${API_URL}/api/users/me`, {
      headers: {
        Authorization: `Bearer ${localStorage.getItem("token")}`,
      },
    });

    const userData = await response.json();
    setCurrentUser(userData);
  } catch (error) {
    console.error("Error fetching current user:", error);
  }
};

useEffect(()=>{
  getCurrentUser();
},[])

//=====================================================

//Fetch ORGS
const fetchOrganizations = async () => {
  try {
    // Make sure current user is available
    if (!currentUser) {
      return;
    }

    const membership =
      currentUser.organization_memberships?.[0];

    const role = membership?.role?.name;

    // ==========================================
    // ORG_ADMIN
    // ==========================================
    if (role === "ORG_ADMIN" || role==="BATCH_ADMIN") {

      const userOrganization = membership?.organization;

      if (userOrganization) {
        setAllOrganizations([userOrganization]);
        setSelectedOrganization(userOrganization.organization_id)
      } else {
        setAllOrganizations([]);
      }

      return;
    }

    // ==========================================
    // Other roles
    // ==========================================
    const response = await fetch(
      `${API_URL}/organizations/?page=1&size=100`,
      {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      }
    );

    if (!response.ok) {
      throw new Error("Failed to fetch organizations");
    }

    const data = await response.json();

    setAllOrganizations(data.data || []);

  } catch (error) {
    console.error(
      "Error fetching organizations:",
      error
    );

    setAllOrganizations([]);
  }
};
useEffect(() => {
  if (currentUser) {
    fetchOrganizations();
  }
}, [currentUser]);
//=====================================================

//===============================================

//fetch Batches
const fetchBatches = async (organizationId = null) => {
  try {

    // Make sure current user is loaded
    if (!currentUser) {
      return;
    }

    const membership =
      currentUser.organization_memberships?.[0];

    const role =
      membership?.role?.name;

    const currentUserId =
      currentUser.id;

    const userOrganizationId =
      membership?.organization_id;

    // ==========================================
    // ORG_ADMIN
    // ==========================================

    if (role === "ORG_ADMIN") {

      if (!userOrganizationId) {
        setBatches([]);
        return;
      }

      organizationId =
        userOrganizationId;
    }

    // ==========================================
    // Build URL
    // ==========================================

    let url =
      `${API_URL}/batches/?page=1&size=100`;

    if (organizationId) {
      url += `&organization_id=${organizationId}`;
    }

    // ==========================================
    // Headers
    // ==========================================

    const headers = {
      "Content-Type": "application/json",
      Authorization:
        `Bearer ${localStorage.getItem("token")}`,
    };

    // Backend needs this when user
    // has multiple organizations
    if (userOrganizationId) {
      headers["X-Organization-ID"] =
        userOrganizationId;
    }

    // ==========================================
    // Fetch batches
    // ==========================================

    const response = await fetch(
      url,
      {
        method: "GET",
        headers,
      }
    );

    if (!response.ok) {
      throw new Error(
        "Failed to fetch batches"
      );
    }

    const data =
      await response.json();

    let fetchedBatches =
      data.data || [];

    // ==========================================
    // BATCH_ADMIN
    // Only show batches where current user
    // is an admin
    // ==========================================

    if (role === "BATCH_ADMIN") {

      fetchedBatches =
        fetchedBatches.filter(
          (batch) =>
            batch.admins?.some(
              (admin) =>
                admin.id === currentUserId
            )
        );
    }

    setBatches(
      fetchedBatches
    );

  } catch (error) {

    console.error(
      "Error fetching batches:",
      error
    );

    setBatches([]);
  }
};
//===============================================


//early loading
//===============================
useEffect(() => {

  if (!currentUser) {
    return;
  }


  fetchBatches();

}, [currentUser]);


const filteredBatches = useMemo(() => {
  console.log("inside filtered batches")
   console.log(batches)
  if (selectedOrganization === "ALL") {
    return batches;
  }
   
  return batches.filter(
    (batch) =>
      batch.organization_id ===
      selectedOrganization
  );

}, [batches, selectedOrganization,currentUser]);
//=====================================

const fetchTotalEmployees = async () => {
  try {
    setLoadingEmployees(true);

    if (!currentUser) {
      return;
    }

    const membership =
      currentUser.organization_memberships?.[0];

    const role =
      membership?.role?.name;

    const organizationId =
      membership?.organization_id;


    // ==========================================
    // BATCH_ADMIN
    // Get users from selected batch
    // ==========================================

    if (role === "BATCH_ADMIN") {

      console.log(
        "Batch admin fetching total employees"
      );

      // No batch selected
      if (
        !selectedBatch ||
        selectedBatch === "ALL"
      ) {
        setTotalEmployees(0);
        setUsersData([]);
        return;
      }

      const response = await fetch(
        `${API_URL}/batches/${selectedBatch}`,
        {
          method: "GET",

          headers: {
            "Content-Type": "application/json",

            Authorization:
              `Bearer ${localStorage.getItem("token")}`,

            "X-Organization-ID":
              organizationId,
          },
        }
      );

      if (!response.ok) {
        throw new Error(
          "Failed to fetch batch details"
        );
      }

      const result =
        await response.json();

      const batchUsers =
        result.data?.users || [];

      console.log(
        "Selected batch users:",
        batchUsers
      );

      // ==========================================
      // Total employees in selected batch
      // ==========================================

      setTotalEmployees(
        batchUsers.length
      );

      // ==========================================
      // Store users
      // Performance will be calculated separately
      // ==========================================

      setUsersData(
        batchUsers
      );

      return;
    }


    // ==========================================
    // OTHER ROLES
    // Get users from organization
    // ==========================================

    if (!organizationId) {
      setTotalEmployees(0);
      setUsersData([]);
      return;
    }

    const response = await fetch(
      `${API_URL}/users/?page=1&size=100`,
      {
        method: "GET",

        headers: {
          "Content-Type": "application/json",

          Authorization:
            `Bearer ${localStorage.getItem("token")}`,

          "X-Organization-ID":
            organizationId,
        },
      }
    );

    if (!response.ok) {
      throw new Error(
        "Failed to fetch users"
      );
    }

    const data =
      await response.json();

    // ==========================================
    // Total employees
    // ==========================================

    setTotalEmployees(
      data.pagination?.total ||
      data.total ||
      0
    );

    // ==========================================
    // Organization users
    // ==========================================

    setUsersData(
      data.items ||
      data.data ||
      []
    );

  } catch (error) {

    console.error(
      "Error fetching total employees:",
      error
    );

    setTotalEmployees(0);
    setUsersData([]);

  } finally {

    setLoadingEmployees(false);
  }
};



const fetchActiveOkrs = async () => {
  try {
    setLoadingActiveOkrs(true);

    const response = await fetch(
      `${API_URL}/okrs/?status=ACTIVE&page=1&size=1`,
      {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      }
    );

    if (!response.ok) {
      throw new Error("Failed to fetch active OKRs");
    }

    const data = await response.json();

    setTotalActiveOkrs(
      data.pagination?.total || 0
    );

  } catch (error) {
    console.error(
      "Error fetching active OKRs:",
      error
    );

    setTotalActiveOkrs(0);

  } finally {
    setLoadingActiveOkrs(false);
  }
};



//=====================================================

const fetchWeeklyUpdates = async (okrIds) => {

  try {

    if (!okrIds || okrIds.length === 0) {
      setWeeklyUpdates({});
      return;
    }

    const results = await Promise.all(

      okrIds.map(
        async (okrId) => {

          const response = await fetch(
            `${API_URL}/okrs/${okrId}/weekly-updates`,
            {
              headers: {
                Authorization:
                  `Bearer ${localStorage.getItem("token")}`,
              },
            }
          );

          const result = await response.json();

          if (!response.ok) {
            throw new Error(
              `Failed to fetch weekly updates for OKR ${okrId}`
            );
          }

          return [
            okrId,
            Array.isArray(result.data)
              ? result.data
              : [],
          ];
        }
      )
    );

    const updatesObject =
      Object.fromEntries(results);

    setWeeklyUpdates(updatesObject);

  } catch (error) {

    console.error(
      "Error fetching weekly updates:",
      error
    );

    setWeeklyUpdates({});
  }
};

//======================================================


const getLatestWeekUpdate = (updates, weekNumber) => {
  const weekUpdates = updates.filter(
    (update) =>
      Number(update.week_number) === Number(weekNumber)
  );

  if (weekUpdates.length === 0) {
    return null;
  }

  return [...weekUpdates].sort(
    (a, b) =>
      new Date(b.created_at) -
      new Date(a.created_at)
  )[0];
};

//============================================================

const getProgressPercentage = (okr) => {
  const target = Number(okr.target || 0);

  if (target <= 0) {
    return 0;
  }

  const updates = weeklyUpdates[okr.id] || [];

  if (updates.length === 0) {
    return 0;
  }

  let relevantUpdates = updates;
   

  // If a week is selected,
  // only consider updates from that week.
  if (selectedWeek!=0) {
    relevantUpdates = updates.filter(
      (update) =>
        Number(update.week_number) === Number(selectedWeek)
    );
  } else {
    // No week selected:
    // First find the latest week.
    const latestWeek = Math.max(
      ...updates.map((update) =>
        Number(update.week_number)
      )
    );

    // Then only consider entries from that latest week.
    relevantUpdates = updates.filter(
      (update) =>
        Number(update.week_number) === latestWeek
    );
  }

  if (relevantUpdates.length === 0) {
    return 0;
  }

  // If multiple entries exist for the same week,
  // take the latest updated entry.
  const latestUpdate = relevantUpdates.reduce(
    (latest, current) => {
      if (!latest) {
        return current;
      }

      return new Date(current.updated_at) >
        new Date(latest.updated_at)
        ? current
        : latest;
    },
    null
  );

  const progress = Number(
    latestUpdate.progress || 0
  );

  
  const percentage = (progress / target) * 100;

  
  return Math.min(
    Math.max(percentage, 0),
    100
  );
};

//================================================================

//avearge performance calculation
const averagePerformance = useMemo(() => {

  if (!okrs || okrs.length === 0) {
    return 0;
  }
   
  const totalProgress = okrs.reduce(
    (sum, okr) => {

      return (
        sum +
        getProgressPercentage(okr)
      );

    },
    0
  );
  console.log("Total Progress:", totalProgress);
  console.log("Total okrs:", okrs.length);
  return Math.round(
    totalProgress / okrs.length
  );

}, [okrs, weeklyUpdates,selectedWeek]);


//========================================

const fetchActiveOkrData = async () => {
  try {
    const response = await fetch(
      `${API_URL}/okrs/?status=ACTIVE&page=1&size=100`,
      {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      }
    );

    if (!response.ok) {
      throw new Error(
        "Failed to fetch active OKR data"
      );
    }

    const data = await response.json();

    
    const activeOkrs =
      data.data || [];

    

    setOkrs(activeOkrs);

    const okrIds =
      activeOkrs.map(
        (okr) => okr.id
      );

    await fetchWeeklyUpdates(
      okrIds
    );

  } catch (error) {
    console.error(
      "Error fetching active OKR data:",
      error
    );

    setOkrs([]);
    setWeeklyUpdates({});
  }
};


//=========================================================

//==========================================================
const atRiskCount = useMemo(() => {
  if (!okrs || okrs.length === 0) {
    return 0;
  }

  return okrs.filter((okr) => {
    const progress = getProgressPercentage(okr);

    return progress < 60;
  }).length;

}, [okrs, weeklyUpdates]);

//==========================================================


//==========================================


const filteredOkrsByType = useMemo(() => {
  if (!okrs || okrs.length === 0) {
    return [];
  }

  if (selectedOkrType === "All") {
    return okrs;
  }

  return okrs.filter(
    (okr) => okr.okr_type === selectedOkrType
  );
}, [okrs, selectedOkrType]);

//==========================================

const users = useMemo(() => {
  if (!usersData || usersData.length === 0) {
    return [];
  }

  let filteredOkrs = filteredOkrsByType;

  // Organization filter
  if (selectedOrganization !== "ALL") {
    filteredOkrs = filteredOkrs.filter(
      (okr) =>
        okr.organization_id === selectedOrganization
    );
  }

  // Batch filter
  if (selectedBatch !== "ALL") {
    

    filteredOkrs = filteredOkrs.filter(
      (okr) =>
        okr.batch_id === selectedBatch
    );
  }

  

  // Get only users who have OKRs
  // in the selected organization/batch
  const filteredUsers = usersData.filter((user) =>
    filteredOkrs.some(
      (okr) =>
        okr.assigned_to === user.id
    )
  );

  

  return filteredUsers
    .map((user) => {
      const userOkrs = filteredOkrs.filter(
        (okr) =>
          okr.assigned_to === user.id
      );

      const totalProgress = userOkrs.reduce(
        (sum, okr) =>
          sum + getProgressPercentage(okr),
        0
      );

      const performance =
        userOkrs.length > 0
          ? totalProgress / userOkrs.length
          : 0;

      return {
        name: `${user.first_name || ""} ${
          user.last_name || ""
        }`.trim(),

        team:
          user.department || "N/A",

        performance:
          Number(performance.toFixed(1)),
      };
    })
    .sort(
      (a, b) =>
        b.performance - a.performance
    );

}, [
  usersData,
  okrs,
  weeklyUpdates,
  selectedOrganization,
  selectedBatch,
    selectedOkrType,
    selectedWeek
]);



//===========================================================

//===========================================================

const organizationPerformance = useMemo(() => {

  if (!okrs || okrs.length === 0) {
    return [];
  }

  const organizationMap = {};

  filteredOkrsByType.forEach((okr) => {

    const organizationId =
      okr.organization_id ||
      okr.organization?.id;

    const organizationName =
      okr.organization?.name ||
      "Unknown Organization";

    if (!organizationId) {
      return;
    }

    if (!organizationMap[organizationId]) {
      organizationMap[organizationId] = {
        id: organizationId,
        name: organizationName,
        totalPerformance: 0,
        okrCount: 0,
      };
    }
    
    const performance =
      getProgressPercentage(okr);

    organizationMap[organizationId].totalPerformance +=
      performance;

    organizationMap[organizationId].okrCount += 1;
  });

  return Object.values(organizationMap)
    .map((organization) => ({
      id: organization.id,
      name: organization.name,
      performance: Number(
        (
          organization.totalPerformance /
          organization.okrCount
        ).toFixed(1)
      ),
    }))
    .sort(
      (a, b) =>
        b.performance - a.performance
    );

}, [okrs, weeklyUpdates,selectedOkrType,selectedWeek]);

//===========================================================

const selectedBatchData = useMemo(() => {
  if (selectedBatch === "ALL") {
    return null;
  }

  return batches.find(
    (batch) => batch.id === selectedBatch
  );
}, [batches, selectedBatch]);

//===========================================================




const batchPerformance = useMemo(() => {
  if (!okrs || okrs.length === 0) {
    return [];
  }

  let filteredOkrs = filteredOkrsByType;

  // Filter by selected organization
  if (selectedOrganization !== "ALL") {
    filteredOkrs = filteredOkrs.filter(
      (okr) =>
        okr.organization_id === selectedOrganization
    );
  }

  const batchMap = {};

  filteredOkrs.forEach((okr) => {
    const batchId = okr.batch_id;
    const batchName = okr.batch?.name || "Unknown Batch";

    if (!batchId) {
      return;
    }

    if (!batchMap[batchId]) {
      batchMap[batchId] = {
        id: batchId,
        name: batchName,
        totalPerformance: 0,
        okrCount: 0,
      };
    }

    const performance = getProgressPercentage(okr);

    batchMap[batchId].totalPerformance += performance;
    batchMap[batchId].okrCount += 1;
  });

  return Object.values(batchMap)
    .map((batch) => ({
      id: batch.id,
      name: batch.name,
      performance: Number(
        (
          batch.totalPerformance /
          batch.okrCount
        ).toFixed(1)
      ),
    }))
    .sort(
      (a, b) => b.performance - a.performance
    );

}, [
  okrs,
  weeklyUpdates,
  selectedOrganization,
  selectedOkrType,
  selectedWeek
]);


//batch admin performance//
const batchAdminPerformance =
  useMemo(() => {

    const role =
      currentUser
        ?.organization_memberships?.[0]
        ?.role?.name;


    if (
      role !== "BATCH_ADMIN"
    ) {
      return [];
    }


    if (
      !batches ||
      batches.length === 0
    ) {
      return [];
    }


    /*
    =================================================
    ONLY BATCHES ADMINISTERED BY CURRENT USER
    =================================================
    */

    return batches
      .map((batch) => {

        /*
        ---------------------------------------------
        Find OKRs belonging to this batch
        ---------------------------------------------
        */

        const batchOkrs =
          filteredOkrsByType.filter(
            (okr) =>
              okr.batch_id ===
              batch.id
          );


        /*
        ---------------------------------------------
        No OKR = 0%
        ---------------------------------------------
        */

        if (
          batchOkrs.length === 0
        ) {

          return {

            id:
              batch.id,

            name:
              batch.name,

            performance: 0,
          };
        }


        /*
        ---------------------------------------------
        Calculate total performance
        ---------------------------------------------
        */

        const totalPerformance =
          batchOkrs.reduce(
            (sum, okr) =>
              sum +
              getProgressPercentage(
                okr
              ),
            0
          );


        /*
        ---------------------------------------------
        Average
        ---------------------------------------------
        */

        const performance =
          totalPerformance /
          batchOkrs.length;


        return {

          id:
            batch.id,

          name:
            batch.name,

          performance:
            Number(
              performance.toFixed(1)
            ),
        };

      })
      .sort(
        (a, b) =>
          b.performance -
          a.performance
      );

  }, [
    currentUser,
    batches,
    filteredOkrsByType,
    weeklyUpdates,
    selectedWeek
  ]);

//===========================================================

const organizations = useMemo(() => {

  if (!okrs || okrs.length === 0) {
    return [];
  }

  const organizationMap = {};

  filteredOkrsByType.forEach((okr) => {

    const organizationId =
      okr.organization_id ||
      okr.organization?.id;

    const organizationName =
      okr.organization?.name ||
      "Unknown Organization";

    if (!organizationId) {
      return;
    }

    if (!organizationMap[organizationId]) {
      organizationMap[organizationId] = {
        id: organizationId,
        name: organizationName,
        totalPerformance: 0,
        okrCount: 0,
      };
    }

    const performance =
      getProgressPercentage(okr);

    organizationMap[organizationId].totalPerformance +=
      performance;

    organizationMap[organizationId].okrCount += 1;

  });

  return Object.values(organizationMap)
    .map((organization) => ({
      id: organization.id,
      name: organization.name,
      performance: Number(
        (
          organization.totalPerformance /
          organization.okrCount
        ).toFixed(1)
      ),
    }))
    .sort(
      (a, b) =>
        b.performance - a.performance
    );

}, [okrs, weeklyUpdates, selectedWeek]);


//===========================================================

//===========================================================

const getWeekDateRange = (weekNumber, batch) => {
  const startDate = new Date(batch.start_date);
  const endDate = new Date(batch.end_date);

  const weekStart = new Date(startDate);

  weekStart.setDate(
    startDate.getDate() + (weekNumber - 1) * 7
  );

  const weekEnd = new Date(weekStart);

  weekEnd.setDate(
    weekStart.getDate() + 6
  );

  if (weekEnd > endDate) {
    weekEnd.setTime(endDate.getTime());
  }

  const formatDate = (date) =>
    date.toLocaleDateString("en-IN", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });

  return `${formatDate(weekStart)} - ${formatDate(weekEnd)}`;
};

//===========================================================
//===========================================================

const weeks = useMemo(() => {
  if (!selectedBatchData) {
    return [];
  }

  return Array.from({ length: 13 }, (_, index) => {
    const weekNumber = index + 1;

    return {
      week: weekNumber,
      date: getWeekDateRange(
        weekNumber,
        selectedBatchData
      ),
    };
  });
}, [selectedBatchData]);

//===========================================================


// ============================================================
  // STATIC DATA
  // Later this can come from FastAPI
  // ============================================================


//================ALL API CALL USING USE EFFECT========================//
useEffect(() => {
const loadDashboardData = async () => {
try {
setLoadingDashboard(true);

  await fetchTotalEmployees();
  await fetchActiveOkrData();
  await fetchActiveOkrs();

} catch (error) {
  console.error(
    "Error loading dashboard:",
    error
  );
} finally {
  setLoadingDashboard(false);
}


};

loadDashboardData();

}, [currentUser,selectedBatch]);



  const topPerformers = users
    .sort((a, b) => b.performance - a.performance)
    .slice(0, 3);


const calculateBatchUserPerformance = (userId) => {

  const userOkrs = filteredOkrsByType.filter(
    (okr) =>
      okr.assigned_to === userId &&
      okr.batch_id === selectedBatch
  );

  // User has no OKRs
  // Still return 0%
  if (userOkrs.length === 0) {
    return 0;
  }

  const totalPerformance =
    userOkrs.reduce(
      (sum, okr) =>
        sum + getProgressPercentage(okr),
      0
    );

  return Number(
    (
      totalPerformance /
      userOkrs.length
    ).toFixed(1)
  );
};
  // ============================================================
  // WEEK FUNCTIONS
  // ============================================================

  const currentWeek = weeks.find((item) => item.week === selectedWeek);

  const previousWeek = () => {
    setSelectedWeek((prev) => Math.max(1, prev - 1));
  };

  const nextWeek = () => {
    setSelectedWeek((prev) => Math.min(5, prev + 1));
  };

//===========================================================

const performanceData = useMemo(() => {

  const role =
    currentUser
      ?.organization_memberships?.[0]
      ?.role?.name;

  const isOrgAdmin =
    role === "ORG_ADMIN";

  const isBatchAdmin =
    role === "BATCH_ADMIN";


  // ============================================
  // BATCH ADMIN
  // ============================================

  if (isBatchAdmin) {

    // No batch selected
    // Show only batches assigned to this admin
    if (selectedBatch === "ALL") {
      return batchAdminPerformance;
    }

    // Batch selected
    // Show users of selected batch
    return batchUserPerformance;
  }


  // ============================================
  // ORG ADMIN
  // ============================================

  if (
    isOrgAdmin &&
    selectedBatch === "ALL"
  ) {
    return batchPerformance;
  }


  // ============================================
  // SUPER ADMIN
  // ============================================

  if (
    !isOrgAdmin &&
    selectedOrganization === "ALL"
  ) {
    return organizationPerformance;
  }


  // ============================================
  // ORGANIZATION SELECTED
  // ============================================

  if (selectedBatch === "ALL") {
    return batchPerformance;
  }


  // ============================================
  // BATCH SELECTED
  // ============================================

  return users;

}, [
  currentUser,
  selectedOrganization,
  selectedBatch,

  organizationPerformance,
  batchPerformance,

  batchAdminPerformance,
  batchUserPerformance,

  users
]);




const getWeekProgressPercentage = (okr, weekNumber) => {
  const target = Number(okr.target || 0);

  if (target <= 0) {
    return 0;
  }

  const updates = weeklyUpdates[okr.id] || [];

  // Get all updates up to the selected week
  const updatesUntilWeek = updates.filter(
    (update) =>
      Number(update.week_number) <= Number(weekNumber)
  );

  if (updatesUntilWeek.length === 0) {
    return 0;
  }

  // First get the latest entry for each week
  const latestUpdatesByWeek = {};

  updatesUntilWeek.forEach((update) => {
    const week = Number(update.week_number);

    if (
      !latestUpdatesByWeek[week] ||
      new Date(update.updated_at) >
        new Date(latestUpdatesByWeek[week].updated_at)
    ) {
      latestUpdatesByWeek[week] = update;
    }
  });

  // Find the latest available week up to current week
  const availableWeeks = Object.keys(
    latestUpdatesByWeek
  )
    .map(Number)
    .sort((a, b) => b - a);

  const latestWeek = availableWeeks[0];

  const latestUpdate =
    latestUpdatesByWeek[latestWeek];

  const progress = Number(
    latestUpdate.progress || 0
  );

  const percentage =
    (progress / target) * 100;

  return Math.min(
    Math.max(percentage, 0),
    100
  );
};

const weeklyTrendData = useMemo(() => {
  if (!filteredOkrsByType || filteredOkrsByType.length === 0) {
    return [];
  }

  let filteredOkrs = filteredOkrsByType;

  // ---------------------------------------
  // Organization selected
  // ---------------------------------------
  if (selectedOrganization !== "ALL") {
    filteredOkrs = filteredOkrs.filter(
      (okr) =>
        okr.organization_id === selectedOrganization
    );
  }

  // ---------------------------------------
  // Batch selected
  // ---------------------------------------
  if (selectedBatch !== "ALL") {
    filteredOkrs = filteredOkrs.filter(
      (okr) =>
        okr.batch_id === selectedBatch
    );
  }

  

  // ---------------------------------------
  // Calculate Week 1 - Week 13
  // ---------------------------------------
  return Array.from(
    { length: 13 },
    (_, index) => {
      const weekNumber = index + 1;

      if (filteredOkrs.length === 0) {
        return {
          week: `Week ${weekNumber}`,
          performance: 0,
        };
      }

      const totalPerformance =
        filteredOkrs.reduce(
          (sum, okr) =>
            sum +
            getWeekProgressPercentage(
              okr,
              weekNumber
            ),
          0
        );

      const averagePerformance =
        totalPerformance /
        filteredOkrs.length;

      return {
        week: `Week ${weekNumber}`,
        performance: Number(
          averagePerformance.toFixed(1)
        ),
      };
    }
  );
}, [
  filteredOkrsByType,
  weeklyUpdates,
  selectedOrganization,
  selectedBatch,
  selectedOkrType,
  selectedWeek
]);
//===========================================================



  // ============================================================
  // BAR CHART
  // ============================================================

const performanceChartData = useMemo(() => {
  return {
    labels: performanceData.map(
      (item) => item.name
    ),

    datasets: [
      {
        label: "Performance",

        data: performanceData.map(
          (item) => item.performance
        ),

        backgroundColor: [
          "#4f7dff",
          "#22c97a",
          "#8b5cf6",
          "#f5a623",
          "#4f7dff",
          "#22c97a",
          "#8b5cf6",
          "#f5a623",
          "#4f7dff",
          "#22c97a",
        ],

        borderRadius: 5,
        barThickness: 32,
      },
    ],
  };
}, [performanceData]);

useEffect(() => {

  const role =
    currentUser?.organization_memberships?.[0]?.role?.name;

  if (role !== "BATCH_ADMIN") {
    return;
  }

  if (
    !selectedBatch ||
    selectedBatch === "ALL"
  ) {
    setBatchUserPerformance([]);
    return;
  }

  if (!usersData || usersData.length === 0) {
    setBatchUserPerformance([]);
    return;
  }

  const usersWithPerformance =
    usersData.map((user) => ({
      ...user,
      performance:
        calculateBatchUserPerformance(
          user.id
        ),
    }));

  console.log(
    "Batch users with performance:",
    usersWithPerformance
  );

  setBatchUserPerformance(
    usersWithPerformance
  );

}, [
  currentUser,
  selectedBatch,
  usersData,
  okrs,
  weeklyUpdates,
  selectedWeek
]);
const performanceChartTitle = useMemo(() => {

  if (selectedOrganization === "ALL") {
    return "Average Performance by Organization";
  }

  if (selectedBatch === "ALL") {
    return "Average Performance by Batch";
  }

  return "Average Performance by User";

}, [selectedOrganization, selectedBatch]);

  const performanceChartOptions = {
    responsive: true,

    maintainAspectRatio: false,

    plugins: {
      legend: {
        display: false,
      },

      tooltip: {
        callbacks: {
          label: (context) => {
            return ` ${context.raw}%`;
          },
        },
      },
    },

    scales: {
      y: {
        beginAtZero: true,
        max: 100,

        grid: {
          color: "rgba(255,255,255,0.06)",
        },

        ticks: {
          color: "#7d8aa5",
          callback: (value) => `${value}%`,
        },
      },

      x: {
        grid: {
          display: false,
        },

        ticks: {
          color: "#7d8aa5",

          maxRotation: 45,
          minRotation: 45,

          font: {
            size: 10,
          },
        },
      },
    },
  };

  // ============================================================
  // DOUGHNUT CHART
  // ============================================================

  const donutData = {
    labels: ["On Track", "Completed", "At Risk", "Behind"],

    datasets: [
      {
        data: [42, 31, 19, 8],

        backgroundColor: [
          "#4f7dff",
          "#22c97a",
          "#f5a623",
          "#ff4f6a",
        ],

        borderWidth: 0,

        hoverOffset: 5,
      },
    ],
  };

  const donutOptions = {
    responsive: true,

    maintainAspectRatio: false,

    cutout: "68%",

    plugins: {
      legend: {
        display: false,
      },

      tooltip: {
        callbacks: {
          label: (context) => {
            return ` ${context.label}: ${context.raw}%`;
          },
        },
      },
    },
  };

  // ============================================================
  // WEEKLY TREND
  // ============================================================

const trendData = {
  labels: weeklyTrendData.map(
    (item) => item.week
  ),

  datasets: [
    {
      label: "Average Performance",
      data: weeklyTrendData.map(
        (item) => item.performance
      ),
      borderColor: "#4f7dff",
      backgroundColor: "rgba(79,125,255,0.10)",
      fill: true,
      tension: 0.4,
      pointRadius: 4,
      pointHoverRadius: 6,
      pointBackgroundColor: "#4f7dff",
    },
  ],
};


  const trendOptions = {
    responsive: true,

    maintainAspectRatio: false,

    plugins: {
      legend: {
        display: false,
      },
    },

    scales: {
      y: {
        min: 0,
        max: 100,

        grid: {
          color: "rgba(255,255,255,0.06)",
        },

        ticks: {
          color: "#7d8aa5",

          callback: (value) => `${value}%`,
        },
      },

      x: {
        grid: {
          display: false,
        },

        ticks: {
          color: "#7d8aa5",
        },
      },
    },
  };

  // ============================================================
  // AWARD BANDS
  // ============================================================

  const awardBands = [
    {
      range: "90–100",
      title: "Gladiator",
      icon: "🏆",
      color: "#4f7dff",
      label: "Blue",
    },
    {
      range: "80–90",
      title: "Platinum",
      icon: "🥈",
      color: "#a8b8d0",
      label: "Platinum",
    },
    {
      range: "60–80",
      title: "Gold",
      icon: "🥇",
      color: "#ffd166",
      label: "Yellow",
    },
    {
      range: "Below 60",
      title: "Bronze",
      icon: "🥉",
      color: "#ff4f6a",
      label: "Red",
    },
  ];

  // ============================================================
  // RENDER
  // ============================================================

  return (
    <section className="dashboard-page">

      {/* ========================================================
          PAGE HEADER
      ======================================================== */}

      <div className="dashboard-page-header">
        <div>
          <h1>Dashboard</h1>

          <p>
            Monitor organization OKR performance and progress
          </p>
        </div>


      </div>

        <div className="dashboard-filters-mobile">
        {/* ====================================================
            FILTERS
        ==================================================== */}

        <div className="card">

          <div className="card-header">

            <div className="card-title">
              Filters
            </div>

          </div>


          <div className="card-body">

            <div className="filters">

{/* Organization */}

{/* Organization */}

{/* Organization */}

{currentUser?.organization_memberships?.[0]?.role?.name ===
"ORG_ADMIN" || currentUser?.organization_memberships?.[0]?.role?.name ===
"BATCH_ADMIN"? (

<input
  type="text"
  className="filter-select"
  value={
    currentUser?.organization_memberships?.[0]
      ?.organization_name || ""
  }
  readOnly
/>

) : (

<select
  className="filter-select"
  value={selectedOrganization}
  onChange={(e) =>
    setSelectedOrganization(e.target.value)
  }
>
  <option value="ALL">
    All Organizations
  </option>

  {allorganizations.map((organization) => (
    <option
      key={organization.id}
      value={organization.id}
    >
      {organization.name}
    </option>
  ))}
</select>

)}

{/* BATCH */}

<select
className="filter-select"
value={selectedBatch}
onChange={(e) =>
  setSelectedBatch(e.target.value)
}
>
<option value="ALL">
  All Batches
</option>

{filteredBatches.map((batch) => (
  <option
    key={batch.id}
    value={batch.id}
  >
    {batch.name}
  </option>
))}
</select>

              {/* WEEK */}

              <select
className="filter-select"
value={selectedWeek}
onChange={(e) =>
  setSelectedWeek(Number(e.target.value))
}
>
<option value="">
  All Weeks
</option>

{weeks
  .slice()
  .reverse()
  .map((week) => (
    <option
      value={week.week}
      key={week.week}
    >
      Week {week.week} — {week.date}
    </option>
  ))}
</select>

              {/* OKR TYPE */}

              <select
                className="filter-select"
                value={selectedOkrType}
                onChange={(e) =>
                  setSelectedOkrType(e.target.value)
                }
              >

                <option value="All">
                  All OKR Types
                </option>

                <option value="Professional">
                  Professional
                </option>

                <option value="Personal">
                  Personal
                </option>

              </select>

            </div>

          </div>

        </div>


        </div>

      {/* ========================================================
          METRICS
      ======================================================== */}

      <div className="metrics-grid">

        {/* TOTAL EMPLOYEES */}

        <div className="metric-card blue">

          <div className="metric-icon blue">
            <Users size={22} />
          </div>

          <div className="metric-label">
            Total Employees
          </div>

          <div className="metric-value">
            {loadingEmployees ? (
              <span className="loading-text">Loading...</span>
            ) : (
              totalEmployees
            )}
          </div>



        </div>


        {/* AVG PERFORMANCE */}

        <div className="metric-card green">

          <div className="metric-icon green">
            <BarChart3 size={22} />
          </div>

          <div className="metric-label">
            Avg Performance
          </div>

          <div
            className="metric-value"
            style={{ color: "var(--green)" }}
          >
            {averagePerformance}%
          </div>


        </div>


        {/* ACTIVE OKRS */}

        <div className="metric-card amber">

          <div className="metric-icon amber">
            <Zap size={22} />
          </div>

          <div className="metric-label">
            Active OKRs
          </div>

          <div className="metric-value">
            {loadingActiveOkrs ? (
              <span className="loading-text">Loading...</span>
            ) : (
              totalActiveOkrs
            )}
          </div>



        </div>


        {/* AT RISK */}

        <div className="metric-card red">

          <div className="metric-icon red">
            <AlertCircle size={22} />
          </div>

          <div className="metric-label">
            At Risk
          </div>

          <div
            className="metric-value"
            style={{ color: "var(--red)" }}
          >
            {atRiskCount}
          </div>


        </div>

      </div>


      {/* ========================================================
          PERFORMANCE + AWARD / FILTER
      ======================================================== */}

      <div className="content-grid">

        {/* ======================================================
            PERFORMANCE CHART
        ====================================================== */}

        <div className="card">

          <div className="card-header">

            <div>

              <div className="card-title">
                {performanceChartTitle}
              </div>

              <div className="card-subtitle">
                Week {selectedWeek} — {currentWeek?.date}
              </div>

            </div>



          </div>


          <div className="card-body">

            <div className="chart-container large">

              <Bar
                data={performanceChartData}
                options={performanceChartOptions}
              />

            </div>

          </div>

        </div>


        {/* ======================================================
            RIGHT SIDE
        ====================================================== */}

        <div className="dashboard-right-column">


          {/* ====================================================
              AWARD BANDS
          ==================================================== */}

          <div className="card award-card">

            <div className="card-header">

              <div className="card-title">
                Award Bands
              </div>

              
            </div>


            <div className="card-body award-body">

              <div className="award-table">

                {awardBands.map((award) => (

                  <div
                    className="award-row"
                    key={award.title}
                  >

                    <div
                      className="score-range"
                      style={{
                        color: award.color,
                      }}
                    >
                      {award.range}
                    </div>


                    <div className="award-badge">

                      <div
                        className="badge-icon"
                        style={{
                          background: `${award.color}22`,
                        }}
                      >
                        {award.icon}
                      </div>

                      <span>
                        {award.title}
                      </span>

                    </div>


                    <div className="award-color">

                      <div
                        className="award-color-dot"
                        style={{
                          background: award.color,
                        }}
                      />

                      <span>
                        {award.label}
                      </span>

                    </div>

                  </div>

                ))}

              </div>

            </div>

          </div>

          <div className="dashboard-filters-desktop">
        {/* ====================================================
            FILTERS
        ==================================================== */}

        <div className="card">

          <div className="card-header">

            <div className="card-title">
              Filters
            </div>

          </div>


          <div className="card-body">

            <div className="filters">

{/* Organization */}

{/* Organization */}

{/* Organization */}

{currentUser?.organization_memberships?.[0]?.role?.name ===
"ORG_ADMIN" || currentUser?.organization_memberships?.[0]?.role?.name ===
"BATCH_ADMIN"? (

<input
  type="text"
  className="filter-select"
  value={
    currentUser?.organization_memberships?.[0]
      ?.organization_name || ""
  }
  readOnly
/>

) : (

<select
  className="filter-select"
  value={selectedOrganization}
  onChange={(e) =>
    setSelectedOrganization(e.target.value)
  }
>
  <option value="ALL">
    All Organizations
  </option>

  {allorganizations.map((organization) => (
    <option
      key={organization.id}
      value={organization.id}
    >
      {organization.name}
    </option>
  ))}
</select>

)}

{/* BATCH */}

<select
className="filter-select"
value={selectedBatch}
onChange={(e) =>
  setSelectedBatch(e.target.value)
}
>
<option value="ALL">
  All Batches
</option>

{filteredBatches.map((batch) => (
  <option
    key={batch.id}
    value={batch.id}
  >
    {batch.name}
  </option>
))}
</select>

              {/* WEEK */}

              <select
className="filter-select"
value={selectedWeek}
onChange={(e) =>
  setSelectedWeek(Number(e.target.value))
}
>
<option value="">
  All Weeks
</option>

{weeks
  .slice()
  .reverse()
  .map((week) => (
    <option
      value={week.week}
      key={week.week}
    >
      Week {week.week} — {week.date}
    </option>
  ))}
</select>

              {/* OKR TYPE */}

              <select
                className="filter-select"
                value={selectedOkrType}
                onChange={(e) =>
                  setSelectedOkrType(e.target.value)
                }
              >

                <option value="All">
                  All OKR Types
                </option>

                <option value="Professional">
                  Professional
                </option>

                <option value="Personal">
                  Personal
                </option>

              </select>

            </div>

          </div>

        </div>


          </div>


        </div>

      </div>


      {/* ========================================================
          BOTTOM SECTION
      ======================================================== */}

      <div className="content-grid thirds">




        {/* ======================================================
            WEEKLY TREND
        ====================================================== */}

        <div className="card">

          <div className="card-header">

            <div className="card-title">
              Weekly Trend
            </div>

          </div>


          <div className="card-body">

            <div className="chart-container trend">

              <Line
                data={trendData}
                options={trendOptions}
              />

            </div>

          </div>

        </div>


        {/* ======================================================
            TOP PERFORMERS
        ====================================================== */}

        <div className="card">

          <div className="card-header">

            <div className="card-title">
              Top Performers
            </div>



          </div>


          <div className="card-body">

            <div className="progress-circles">

              {topPerformers.map((user) => (

                <ProgressCircle
                  key={user.name}
                  name={user.name}
                  team={user.team}
                  value={user.performance}
                />

              ))}

            </div>

          </div>

        </div>

      </div>

    </section>
  );
};


// ================================================================
// PROGRESS CIRCLE COMPONENT
// ================================================================

const ProgressCircle = ({
  name,

  value,
}) => {

  const radius = 30;

  const circumference = 2 * Math.PI * radius;

  const offset =
    circumference -
    (value / 100) * circumference;


  let stroke = "#4f7dff";

  if (value >= 90) {
    stroke = "#22c97a";
  } else if (value >= 80) {
    stroke = "#4f7dff";
  } else if (value >= 60) {
    stroke = "#f5a623";
  } else {
    stroke = "#ff4f6a";
  }


  return (

    <div className="progress-circle-item">

      <svg
        className="circle-svg"
        viewBox="0 0 72 72"
      >

        <circle
          className="circle-bg"
          cx="36"
          cy="36"
          r={radius}
        />

        <circle
          className="circle-fill"
          cx="36"
          cy="36"
          r={radius}
          stroke={stroke}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
        />

        <text
          className="circle-text"
          x="36"
          y="40"
          textAnchor="middle"
        >
          {value.toFixed(1)}
        </text>

      </svg>


      <div className="circle-name">
        {name}
      </div>


    </div>

  );
};


export default Dashboard;