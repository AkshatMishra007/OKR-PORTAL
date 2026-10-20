import React, { useState, useEffect, useMemo } from "react";
import {
  Plus,
  Search,
  Eye,
  Pencil,
  Trash2,
  X,
  ChevronLeft,
  ChevronRight,
  ChevronDown,
} from "lucide-react";
import "./ManageOKR.css";

import { API_URL } from "../Config/ApiEndpoint";

function OKR() {


  const [currentUser, setCurrentUser] = useState(null);

  const [deletePopup, setDeletePopup] = useState(false);

  const [currentPage, setCurrentPage] = useState(1);

  const [rowsPerPage, setRowsPerPage] = useState(10);

  const [showAddOKR, setShowAddOKR] = useState(false);

  const [showViewOKR, setShowViewOKR] = useState(false);

  const [selectedOKR, setSelectedOKR] = useState(null);

  const [currentStep, setCurrentStep] = useState(1);


  /* =========================================================
     MOCK DATA
  ========================================================= */
  const [isEditingOKR, setIsEditingOKR] = useState(false);

  const [editOKR, setEditOKR] = useState({
    objective: "",
    target: "",
    key_results: "",
    okr_type: "",
    tracker_enabled: "No",
  });
  const [organizations, setOrganizations] = useState([]);
  const [organizationLoading, setOrganizationLoading] = useState(false);
  const [organizationError, setOrganizationError] = useState("");

  const [availableEmployees, setAvailableEmployees] = useState([]);
  const [employeeLoading, setEmployeeLoading] = useState(false);
  const [employeeError, setEmployeeError] = useState("");




  const startEditingOKR = () => {
    setEditOKR({
      objective: selectedOKR?.objective || "",
      target: selectedOKR?.target || "",
      key_results: selectedOKR?.key_results || "",
      okr_type: selectedOKR?.okr_type || "",
      tracker_enabled: selectedOKR?.tracker_enabled || "No",
    });

    setIsEditingOKR(true);
  };


  /* =========================================================
     FETCH Current user
  ========================================================= */
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


  useEffect(() => {
    getCurrentUser();
  }, [])
  /* =========================================================
     FETCH ORGANIZATIONS
  ========================================================= */

  const fetchOrganizations = async () => {

    try {

      setOrganizationLoading(true);
      setOrganizationError("");

      const response = await fetch(
        `${API_URL}/api/organizations/?page=1&size=10`,
        {
          method: "GET",
          headers: {
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error("Failed to fetch organizations");
      }

      const result = await response.json();

      setOrganizations(result.data || []);

    } catch (error) {

      console.error(
        "Error fetching organizations:",
        error
      );

      setOrganizationError(
        "Unable to load organizations."
      );

      setOrganizations([]);

    } finally {

      setOrganizationLoading(false);

    }
  };

  /* =========================================================
     INITIAL LOAD
  ========================================================= */

  useEffect(() => {

    fetchOrganizations();

  }, []);


  /* =========================================================
     FORM STATE
  ========================================================= */

  const [okrForm, setOkrForm] = useState({

    organization_id: "",
    year: "",
    quarter: "",
    batch_id: "",
    user_id: "",

  });



  const handleEdit = (record) => {

    console.log("Row clicked:", record)
    setSelectedOKR(record);

    setEditOKR({
      objective: record.objective || "",
      target: record.target || "",
      key_results: record.key_results || "",
      okr_type: record.okr_type || "",
      tracker_enabled: record.tracker_enabled || "No",
    });

    setIsEditingOKR(true);
  };

  /* =========================================================
     HANDLE ORGANIZATION CHANGE
  ========================================================= */

  const handleOrganizationChange = (e) => {

    const organizationId = e.target.value;

    setOkrForm({
      ...okrForm,

      organization_id: organizationId,

      // Reset dependent selections
      year: "",
      quarter: "",
      batch_id: "",
      user_id: "",
    });

  };


  const years = [
    "2024",
    "2025",
    "2026",
    "2027",
    "2028",
  ];

  const quarters = [
    {
      value: "JFM",
      label: "JFM",
    },
    {
      value: "AMJ",
      label: "AMJ",
    },
    {
      value: "JAS",
      label: "JAS",
    },
    {
      value: "OND",
      label: "OND",
    },
  ];

  /* =========================================================
     BATCHES
  ========================================================= */

  const [batches, setBatches] = useState([]);
  const [batchLoading, setBatchLoading] = useState(false);
  const [batchError, setBatchError] = useState("");


  /* =========================================================
     FETCH BATCHES
  ========================================================= */

  const fetchBatches = async () => {


    console.log("Fetching batches with context:", okrForm);
    // We need these selections before fetching batches
    if (
      !okrForm.organization_id ||
      !okrForm.year ||
      !okrForm.quarter
    ) {
      setBatches([]);
      return;
    }

    try {

      setBatchLoading(true);
      setBatchError("");

      const params = new URLSearchParams({
        organization_id: okrForm.organization_id,
        quarter: okrForm.quarter,
        year: okrForm.year,
        sort_by: "created_at",
        sort_order: "desc",
        page: "1",
        size: "20",
      });

      const response = await fetch(
        `${API_URL}/api/batches/?${params.toString()}`,
        {
          method: "GET",
          headers: {
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
        }

      );

      if (!response.ok) {
        throw new Error("Failed to fetch batches");
      }

      const result = await response.json();

      setBatches(result.data || []);
      console.log("Fetched Batches:", result.data || []);
    } catch (error) {

      console.error(
        "Error fetching batches:",
        error
      );

      setBatchError(
        "Unable to load batches."
      );

      setBatches([]);

    } finally {

      setBatchLoading(false);

    }
  };

  useEffect(() => {
    console.log("Organization ID:", okrForm.organization_id);
    console.log("Year:", okrForm.year);
    console.log("Quarter:", okrForm.quarter);
    fetchBatches();

  }, [
    okrForm.organization_id,
    okrForm.year,
    okrForm.quarter

  ]);



  const fetchBatchEmployees = async (batchId) => {

    if (!batchId) {
      setAvailableEmployees([]);
      return;
    }

    try {

      setEmployeeLoading(true);
      setEmployeeError("");

      const response = await fetch(
        `${API_URL}/api/batches/${batchId}`,
        {
          method: "GET",
          headers: {
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error(
          "Failed to fetch batch details"
        );
      }

      const result = await response.json();

      console.log(
        "Selected Batch Details:",
        result
      );

      // Users are inside result.data.users
      setAvailableEmployees([
        ...result.data?.users || [],
        ...result.data?.admins || []


      ]
      );

    } catch (error) {

      console.error(
        "Error fetching batch employees:",
        error
      );

      setAvailableEmployees([]);

      setEmployeeError(
        "Unable to load employees."
      );

    } finally {

      setEmployeeLoading(false);

    }

  };

  useEffect(() => {

    if (okrForm.batch_id) {

      fetchBatchEmployees(
        okrForm.batch_id
      );

    } else {

      setAvailableEmployees([]);

    }

  }, [
    okrForm.batch_id
  ]);




  /* =========================================================
     STATE
  ========================================================= */

  const [okrData, setOkrData] = useState([]);

  const [search, setSearch] = useState("");

  const [filters, setFilters] = useState({
    organization_id: "",
    year: "",
    quarter: "",
    batch_id: "",
  });


  /* =========================================================
     ADD OKR CONTEXT
  ========================================================= */

  const [okrContext, setOkrContext] = useState({
    organization_id: "",
    year: "",
    quarter: "",
    batch_id: "",
    user_id: "",

  });


  /* =========================================================
     OKR LIST
  ========================================================= */

  const emptyOKR = {
    objective: "",
    key_results: "",
    target: "",
    okr_type: "Professional",
    tracker_enabled: "No"
  };

  const [okrList, setOkrList] = useState([
    {
      ...emptyOKR,
    },
  ]);


  /* =========================================================
     FILTERED BATCHES
  ========================================================= */

  const availableBatches = useMemo(() => {
    console.log("Filtering batches with context:", okrContext);
    return batches.filter((batch) => {

      if (
        okrContext.organization_id &&
        batch.organization_id !==
        okrContext.organization_id
      ) {
        return false;
      }

      if (
        okrContext.year &&
        batch.year !== Number(okrContext.year)
      ) {
        return false;
      }

      if (
        okrContext.quarter &&
        batch.quarter !== okrContext.quarter
      ) {
        return false;
      }

      return true;

    });

  }, [
    okrContext.organization_id,
    okrContext.year,
    okrContext.quarter,
  ]);


  /* =========================================================
     FILTERED EMPLOYEES
  ========================================================= */

  const availableEmployees1 = useMemo(() => {

    return availableEmployees.filter((employee) => {

      if (
        okrContext.organization_id &&
        employee.organization_id !==
        okrContext.organization_id
      ) {
        return false;
      }

      if (
        okrContext.batch_id &&
        employee.batch_id !==
        okrContext.batch_id
      ) {
        return false;
      }

      return true;

    });

  }, [
    okrContext.organization_id,
    okrContext.batch_id,
  ]);


  /* =========================================================
     FILTERED TABLE DATA
  ========================================================= */

  const filteredOKRs = useMemo(() => {
    console.log("Filtering OKRs with search:", search, "and filters:", filters, "okrs is", okrData);
    return okrData.filter((item) => {

      const searchValue =
        search.toLowerCase().trim();

      if (
        searchValue &&
        !item.assignee.user.first_name.concat(item.assignee.user.last_name)
          .toLowerCase()
          .includes(searchValue) &&
        !item.assignee.user.email
          .toLowerCase()
          .includes(searchValue)
      ) {
        return false;
      }

      if (
        filters.organization_id &&
        item.organization_id !==
        filters.organization_id
      ) {
        return false;
      }

      if (
        filters.year &&
        item.batch.year !== Number(filters.year)
      ) {
        return false;
      }

      if (
        filters.quarter &&
        item.batch.quarter !== filters.quarter
      ) {
        return false;
      }

      if (
        filters.batch_id &&
        item.batch_id !==
        filters.batch_id
      ) {
        return false;
      }



      return true;

    });

  }, [
    okrData,
    search,
    filters,
  ]);


  /* =========================================================
     PAGINATION
  ========================================================= */

  const totalPages = Math.max(
    1,
    Math.ceil(
      filteredOKRs.length / rowsPerPage
    )
  );

  const startIndex =
    (currentPage - 1) *
    rowsPerPage;

  const paginatedOKRs =
    filteredOKRs.slice(
      startIndex,
      startIndex + rowsPerPage
    );

  console.log(paginatedOKRs.map((okr) => okr.id), "paginated okrs");
  /* =========================================================
     FILTER HANDLERS
  ========================================================= */

  const handleFilterChange = (
    field,
    value
  ) => {

    setFilters((prev) => ({
      ...prev,
      [field]: value,
    }));

    setCurrentPage(1);
    handleContextChange(field, value);

  };


  /* =========================================================
     RESET ADD OKR MODAL
  ========================================================= */

  const resetAddOKR = () => {

    const membership =
      currentUser?.organization_memberships?.[0];

    const isOrgAdmin =
      membership?.role?.name === "ORG_ADMIN" ||
      membership?.role?.name === "BATCH_ADMIN";

    const organizationId =
      isOrgAdmin
        ? membership?.organization_id
        : "";

    setOkrContext({
      organization_id: organizationId,
      year: "",
      quarter: "",
      batch_id: "",
      user_id: "",
    });

    setOkrList([
      {
        ...emptyOKR,
      },
    ]);

    setCurrentStep(1);
  };


  /* =========================================================
     OPEN ADD MODAL
  ========================================================= */

  const openAddOKR = () => {

    resetAddOKR();

    setShowAddOKR(true);

  };


  /* =========================================================
     CLOSE ADD MODAL
  ========================================================= */

  const closeAddOKR = () => {

    setShowAddOKR(false);

    resetAddOKR();

  };


  /* =========================================================
     CONTEXT CHANGE
  ========================================================= */

  const handleContextChange = (field, value) => {

    console.log("prev context", okrContext)

    setOkrContext((prev) => {

      const updated = {
        ...prev,
        [field]: value,
      };

      /*
       * When organization changes,
       * reset dependent selections.
       */
      if (field === "organization_id") {

        updated.year = "";
        updated.quarter = "";
        updated.batch_id = "";
        updated.user_id = "";

      }

      /*
       * When year changes,
       * reset quarter, batch and user.
       */
      if (field === "year") {

        updated.quarter = "";
        updated.batch_id = "";
        updated.user_id = "";

      }

      /*
       * When quarter changes,
       * reset batch and user.
       */
      if (field === "quarter") {

        updated.batch_id = "";
        updated.user_id = "";

      }

      /*
       * When batch changes,
       * reset employee.
       */
      if (field === "batch_id") {

        updated.user_id = "";

      }

      console.log("Updated Context:", updated);

      return updated;

    });

    /*
     * Keep OKR form in sync.
     */
    setOkrForm((prev) => ({
      ...prev,
      [field]: value,
    }));

    /*
     * Organization changed
     * → load batches for that organization.
     */
    if (field === "organization_id" && value) {

      fetchBatches(value);

    }

    /*
     * Batch changed
     * → load employees for that batch.
     */
    if (field === "batch_id" && value) {

      fetchBatchEmployees(value);

    }

  };
  /* =========================================================
     ADD NEW OKR
  ========================================================= */

  const addNewOKR = () => {

    setOkrList((prev) => [
      ...prev,
      {
        ...emptyOKR,
      },
    ]);


    console.log("Added new OKR. Current OKR List:", okrList);
  };


  /* =========================================================
     REMOVE OKR
  ========================================================= */

  const removeOKR = (index) => {

    if (okrList.length === 1) {
      return;
    }

    setOkrList((prev) =>
      prev.filter(
        (_, i) => i !== index
      )
    );

  };


  /* =========================================================
     UPDATE OKR
  ========================================================= */

  const updateOKR = (
    index,
    field,
    value
  ) => {

    setOkrList((prev) =>
      prev.map((okr, i) =>
        i === index
          ? {
            ...okr,
            [field]: value,
          }
          : okr
      )
    );

  };

  const handleChangeOKR = (field, value) => {
    setEditOKR((prev) => ({
      ...prev,
      [field]: value,
    }));
  };


  /* =========================================================
     VALIDATE CONTEXT
  ========================================================= */

  const validateContext = () => {
    console.log("validating", okrContext)
    if (!okrContext.organization_id) {
      alert("Please select an organization.");
      return false;
    }

    if (!okrContext.year) {
      alert("Please select a year.");
      return false;
    }

    if (!okrContext.quarter) {
      alert("Please select a quarter.");
      return false;
    }

    if (!okrContext.batch_id) {
      alert("Please select a batch.");
      return false;
    }

    if (!okrContext.user_id) {
      alert("Please select an employee.");
      return false;
    }

    return true;

  };


  /* =========================================================
     VALIDATE OKRs
  ========================================================= */

  const validateOKRs = () => {

    for (let i = 0; i < okrList.length; i++) {

      const okr = okrList[i];

      if (!okr.objective.trim()) {

        alert(
          `Please enter objective for OKR ${i + 1}.`
        );

        return false;

      }

    }

    return true;

  };


  /* =========================================================
     NEXT STEP
  ========================================================= */

  const handleNext = () => {

    if (currentStep === 1) {

      if (!validateContext()) {
        return;
      }

      setCurrentStep(2);

      return;

    }

    if (currentStep === 2) {

      if (!validateOKRs()) {
        return;
      }

      setCurrentStep(3);

    }

  };


  /* =========================================================
     PREVIOUS STEP
  ========================================================= */

  const handleBack = () => {

    if (currentStep > 1) {
      setCurrentStep(
        currentStep - 1
      );
    }

  };

  /* =========================Get all okrs from the api================================*/

  const fetchOKRs = async () => {

    try {
      let url = "";
      console.log("Current User:", currentUser);
      if (
        currentUser &&
        (
          currentUser.organization_memberships?.[0]?.role?.name === "ORG_ADMIN" ||
          currentUser.organization_memberships?.[0]?.role?.name === "BATCH_ADMIN"
        )
      ) {
        url = `${API_URL}/api/okrs/?organization_id=${currentUser.organization_memberships[0].organization_id}&page=1&size=300`
        handleContextChange("organization_id", currentUser.organization_memberships[0].organization_id)
      }
      else {
        url = `${API_URL}/api/okrs/?page=1&size=300`;
      }
      const token =
        localStorage.getItem("token");

      const response = await fetch(
        url,
        {
          method: "GET",

          headers: {
            Authorization:
              `Bearer ${token}`,
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

      console.log(
        "OKR API data:",
        result
      );

      setOkrData(
        result.data || []
      );

    } catch (error) {

      console.error(
        "Error fetching OKRs:",
        error
      );

    }

  };

  useEffect(() => {


    if (!currentUser) {
      return;
    }

    const membership =
      currentUser.organization_memberships?.[0];

    const role =
      membership?.role?.name;

    const organizationId =
      membership?.organization_id;

    if (role === "BATCH_ADMIN" && organizationId) {
      console.log("Organization id set to the", organizationId)
      console.log("current contexts is", okrContext)
      console.log("current form is", okrForm)
      setOkrContext((prev) => ({
        ...prev,
        organization_id: organizationId,
      }));

      setOkrForm((prev) => ({
        ...prev,
        organization_id: organizationId,
      }));
    }

    fetchOKRs();

  }, [currentUser]);
  /*##################### Save okr to api #############################*/
  const saveOKRsToAPI = async () => {

    const token = localStorage.getItem("token");

    const requests = okrList.map((okr) => {
      console.log("Preparing to save OKR:", okr);
      const payload = {
        batch_id: okrContext.batch_id,
        assigned_to: okrContext.user_id,
        objective: okr.objective,
        target: okr.target,
        key_results: okr.key_results,
        okr_type: okr.okr_type,
        tracker_enabled: okr.tracker_enabled,
      };

      console.log(
        "Saving OKR payload:",
        payload
      );

      return fetch(
        `${API_URL}/api/okrs/`,
        {
          method: "POST",

          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },

          body: JSON.stringify(payload),
        }
      ).then(async (response) => {

        if (!response.ok) {

          const errorData =
            await response.json().catch(
              () => ({})
            );

          throw new Error(
            errorData.detail ||
            "Failed to save OKR"
          );

        }

        return response.json();

      });

    });

    return Promise.all(requests);
  };

  /* =========================================================
     SAVE OKRs
  ========================================================= */

  // const handleSaveOKRs = () => {

  //   console.log("Saving OKRs with context:", okrContext);
  //   if (!validateOKRs()) {
  //     return;
  //   }

  //   const organization =
  //     organizations.find(
  //       (org) =>
  //         org.id ===
  //         Number(
  //           okrContext.organization_id
  //         )
  //     );

  //   const batch =
  //     batches.find(
  //       (batch) =>
  //         batch.id ===
  //         Number(
  //           okrContext.batch_id
  //         )
  //     );

  //   const employee =
  //     employees.find(
  //       (employee) =>
  //         employee.id ===
  //         Number(
  //           okrContext.user_id
  //         )
  //     );

  //   const newRecord = {

  //     id:
  //       okrData.length + 1,

  //     organization_id:
  //       Number(
  //         okrContext.organization_id
  //       ),

  //     organization:
  //       organization?.name || "",

  //     year:
  //       okrContext.year,

  //     quarter:
  //       okrContext.quarter,

  //     batch_id:
  //       Number(
  //         okrContext.batch_id
  //       ),

  //     batch:
  //       batch?.name || "",

  //     user_id:
  //       Number(
  //         okrContext.user_id
  //       ),

  //     employee:
  //       employee?.name || "",

  //     email:
  //       employee?.email || "",

  //     status:
  //       "Draft",

  //     last_updated:
  //       "17 Aug 2026",

  //     okrs:
  //       okrList.map(
  //         (okr, index) => ({
  //           ...okr,
  //           id:
  //             Date.now() + index,
  //         })
  //       ),

  //   };


  //   setOkrData((prev) => [
  //     newRecord,
  //     ...prev,
  //   ]);
  //   console.log(okrData);

  //   closeAddOKR();

  //   setCurrentPage(1);

  // };


  const handleSaveOKRs = async () => {

    console.log(
      "Saving OKRs with context:",
      okrContext
    );

    if (!validateOKRs()) {
      return;
    }

    try {

      /*
      ============================================
      SAVE ALL OKRs
      ============================================
      */

      await saveOKRsToAPI();

      /*
      ============================================
      GET UPDATED OKR DATA
      ============================================
      */

      await fetchOKRs();

      /*
      ============================================
      CLOSE MODAL
      ============================================
      */

      closeAddOKR();

      setCurrentPage(1);

    } catch (error) {

      console.error(
        "Error saving OKRs:",
        error
      );

      alert(
        error.message ||
        "Unable to save OKRs."
      );

    }

  };

  /* =========================================================
     VIEW OKRs
  ========================================================= */

  const handleView = (record) => {
    console.log("Viewing OKRs for record:", record);
    setSelectedOKR(record);

    setShowViewOKR(true);

  };


  const deleteModal = (record) => {
    setSelectedOKR(record);
    setDeletePopup(true);
  };



  const saveEditedOKR = async () => {
    if (!selectedOKR) return;


    try {
      const response = await fetch(
        `${API_URL}/api/okrs/${selectedOKR.id}`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
          body: JSON.stringify({
            objective: editOKR.objective,
            target: editOKR.target,
            key_results: editOKR.key_results,
            okr_type: editOKR.okr_type,
            tracker_enabled: editOKR.tracker_enabled,
          }),
        }
      );

      if (!response.ok) {
        const error = await response.text();
        throw new Error(error);
      }

      console.log("OKR updated successfully");

      // Close edit modal
      setIsEditingOKR(false);

      // Clear selected OKR
      setSelectedOKR(null);

      // Refresh OKR table
      fetchOKRs();

    } catch (error) {
      console.error("Error updating OKR:", error);
    }
  };

  const deleteOKR = async () => {
    if (!selectedOKR) return;

    try {
      const response = await fetch(
        `${API_URL}/api/okrs/${selectedOKR.id}`,
        {
          method: "DELETE",
          headers: {
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error("Failed to delete OKR");
      }

      console.log("OKR deleted successfully");

      // Close modal
      setDeletePopup(false);
      setSelectedOKR(null);

      // Refresh OKR list
      fetchOKRs();

    } catch (error) {
      console.error("Error deleting OKR:", error);
    }
  };
  /* =========================================================
     CLOSE VIEW
  ========================================================= */

  const closeView = () => {

    setShowViewOKR(false);

    setSelectedOKR(null);

  };


  /* =========================================================
     RENDER
  ========================================================= */

  return (

    <section className="page">

      {/* =====================================================
          PAGE HEADER
      ===================================================== */}

      <div className="page-header">

        <div>

          <h1>
            Manage OKRs
          </h1>

          <p>
            Create and manage employee OKRs.
          </p>

        </div>

        <button
          type="button"
          className="primary-btn"
          onClick={openAddOKR}
        >

          <Plus size={18} />

          Add OKR

        </button>

      </div>


      {/* =====================================================
          FILTER BAR
      ===================================================== */}

      <div className="filters-bar">

        {/* Search */}

        <div className="search-box">

          <Search size={18} />

          <input
            type="text"
            placeholder="Search employee..."
            value={search}
            onChange={(e) => {

              setSearch(
                e.target.value
              );

              setCurrentPage(1);

            }}
          />

        </div>


        {/* Organization */}

        {currentUser &&
          currentUser?.organization_memberships?.[0]?.role?.name !== "ORG_ADMIN" &&
          currentUser?.organization_memberships?.[0]?.role?.name !== "BATCH_ADMIN" && (
            <select
              value={filters.organization_id}
              onChange={(e) =>
                handleFilterChange(
                  "organization_id",
                  e.target.value
                )

              }
            >
              <option value="">
                All Organizations
              </option>

              {organizations.map((organization) => (
                <option
                  key={organization.id}
                  value={organization.id}
                >
                  {organization.name}
                </option>
              ))}
            </select>
          )}

        {/* Year */}

        <select
          value={filters.year}
          onChange={(e) =>
            handleFilterChange(
              "year",
              e.target.value
            )
          }
        >

          <option value="">
            All Years
          </option>

          {years.map((year) => (

            <option
              key={year}
              value={year}
            >
              {year}
            </option>

          ))}

        </select>


        {/* Quarter */}

        <select
          value={filters.quarter}
          onChange={(e) =>
            handleFilterChange(
              "quarter",
              e.target.value
            )
          }
        >

          <option value="">
            All Quarters
          </option>

          {quarters.map(
            (quarter) => (

              <option
                key={
                  quarter.value
                }
                value={
                  quarter.value
                }
              >
                {quarter.label}
              </option>

            )
          )}

        </select>


        {/* Batch */}

        <select
          value={filters.batch_id}
          onChange={(e) =>
            handleFilterChange(
              "batch_id",
              e.target.value
            )
          }
        >

          <option value="">
            All Batches
          </option>

          {batches.map((batch) => (

            <option
              key={batch.id}
              value={batch.id}
            >
              {batch.name}
            </option>

          ))}

        </select>




      </div>


      {/* =====================================================
          TABLE CARD
      ===================================================== */}

      <div className="card">

        <div className="card-header">

          <div>

            <h2>
              Employee OKRs
            </h2>

            <span>
              {filteredOKRs.length} records
            </span>

          </div>

        </div>


        <div className="table-wrapper">

          <table>

            <thead>

              <tr
              >

                <th>
                  Employee
                </th>

                <th>
                  Organization
                </th>

                <th>
                  Year
                </th>

                <th>
                  Quarter
                </th>

                <th>
                  Batch
                </th>



                <th>
                  Action
                </th>


              </tr>

            </thead>


            <tbody>

              {paginatedOKRs.length === 0 ? (

                <tr>

                  <td
                    colSpan="9"
                    className="empty-table"
                  >
                    No OKRs found.
                  </td>

                </tr>

              ) : (

                paginatedOKRs.map(
                  (record) => (

                    <tr
                      key={
                        record.id
                      }
                      onClick={() =>

                        handleEdit(
                          record
                        )
                      }
                    >

                      {/* Employee */}

                      <td>

                        <div className="employee-cell">

                          <strong>
                            {record.assignee?.user
                              ? `${record.assignee.user.first_name} ${record.assignee.user.last_name}`
                              : "Unknown User"}
                          </strong>


                          <span>
                            {
                              record.email
                            }
                          </span>

                        </div>

                      </td>


                      {/* Organization */}

                      <td>
                        {
                          record.organization.name
                        }
                      </td>


                      {/* Year */}

                      <td>
                        {
                          record.batch.year
                        }
                      </td>


                      {/* Quarter */}

                      <td>

                        <span className="quarter-badge">

                          {
                            record.batch.quarter
                          }

                        </span>

                      </td>


                      {/* Batch */}

                      <td>
                        {
                          record.batch.name
                        }
                      </td>






                      {/* Status */}

                      <td onClick={(e) => {
                        e.stopPropagation();
                        deleteModal(record)
                      }}>
                        <Trash2 width={14} />

                      </td>



                    </tr>

                  )
                )

              )}

            </tbody>

          </table>

        </div>


        {/* =====================================================
            PAGINATION
        ===================================================== */}

        <div className="pagination">

          <div className="rows-per-page">

            <span>
              Rows per page
            </span>

            <select
              value={
                rowsPerPage
              }
              onChange={(e) => {

                setRowsPerPage(
                  Number(
                    e.target.value
                  )
                );

                setCurrentPage(1);

              }}
            >

              <option value="5">
                5
              </option>

              <option value="10">
                10
              </option>

              <option value="20">
                20
              </option>

              <option value="50">
                50
              </option>

            </select>

          </div>


          <div className="pagination-controls">

            <button
              type="button"
              disabled={
                currentPage === 1
              }
              onClick={() =>
                setCurrentPage(
                  (prev) =>
                    Math.max(
                      1,
                      prev - 1
                    )
                )
              }
            >

              <ChevronLeft
                size={18}
              />

            </button>


            <span>

              Page{" "}
              <strong>
                {currentPage}
              </strong>{" "}
              of{" "}
              <strong>
                {totalPages}
              </strong>

            </span>


            <button
              type="button"
              disabled={
                currentPage ===
                totalPages
              }
              onClick={() =>
                setCurrentPage(
                  (prev) =>
                    Math.min(
                      totalPages,
                      prev + 1
                    )
                )
              }
            >

              <ChevronRight
                size={18}
              />

            </button>

          </div>

        </div>

      </div>


      {/* =====================================================
          ADD OKR MODAL
      ===================================================== */}

      {showAddOKR && (

        <div
          className="okr-modal-overlay"
          onClick={closeAddOKR}
        >

          <div
            className="okr-modal"
            onClick={(e) =>
              e.stopPropagation()
            }
          >

            {/* Modal Header */}

            <div className="okr-modal-header">

              <div>

                <h2>
                  Add OKRs
                </h2>

                <p>
                  Create multiple OKRs for an employee.
                </p>

              </div>

              <button
                type="button"
                className="modal-close-btn"
                onClick={closeAddOKR}
              >

                <X size={20} />

              </button>

            </div>


            {/* =================================================
                STEPPER
            ================================================= */}

            <div className="okr-stepper">

              <div
                className={`okr-step ${currentStep >= 1
                  ? "active"
                  : ""
                  }`}
              >

                <div className="step-number">
                  {currentStep > 1
                    ? "✓"
                    : "1"}
                </div>

                <span>
                  Context
                </span>

              </div>


              <div className="step-line"></div>


              <div
                className={`okr-step ${currentStep >= 2
                  ? "active"
                  : ""
                  }`}
              >

                <div className="step-number">
                  {currentStep > 2
                    ? "✓"
                    : "2"}
                </div>

                <span>
                  OKRs
                </span>

              </div>


              <div className="step-line"></div>


              <div
                className={`okr-step ${currentStep >= 3
                  ? "active"
                  : ""
                  }`}
              >

                <div className="step-number">
                  3
                </div>

                <span>
                  Preview
                </span>

              </div>

            </div>


            {/* =================================================
                STEP 1 - CONTEXT
            ================================================= */}

            {currentStep === 1 && (

              <div className="okr-modal-body">

                <div className="section-heading">

                  <h3>
                    OKR Context
                  </h3>

                  <p>
                    Select the employee and OKR cycle.
                  </p>

                </div>


                <div className="okr-form-grid">

                  {/* Organization */}

                  <div className="form-group">

                    <label>
                      Organization
                    </label>

                    {(
                      currentUser?.organization_memberships?.[0]?.role?.name === "ORG_ADMIN" ||
                      currentUser?.organization_memberships?.[0]?.role?.name === "BATCH_ADMIN"
                    ) ? (
                      <input
                        type="text"
                        value={
                          currentUser?.organization_memberships?.[0]?.organization_name || ""
                        }
                        readOnly
                      />
                    ) : (
                      <select
                        value={okrContext.organization_id}
                        onChange={(e) =>
                          handleContextChange(
                            "organization_id",
                            e.target.value
                          )
                        }
                      >
                        <option value="">
                          Select Organization
                        </option>

                        {organizations.map((organization) => (
                          <option
                            key={organization.id}
                            value={organization.id}
                          >
                            {organization.name}
                          </option>
                        ))}
                      </select>
                    )}

                  </div>


                  {/* Year */}

                  <div className="form-group">

                    <label>
                      Year
                    </label>

                    <select
                      value={
                        okrContext.year
                      }
                      onChange={(e) =>
                        handleContextChange(
                          "year",
                          e.target.value
                        )
                      }
                    >

                      <option value="">
                        Select Year
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

                  </div>


                  {/* Quarter */}

                  <div className="form-group">

                    <label>
                      Quarter
                    </label>

                    <select
                      value={
                        okrContext.quarter
                      }
                      onChange={(e) =>
                        handleContextChange(
                          "quarter",
                          e.target.value
                        )
                      }
                    >

                      <option value="">
                        Select Quarter
                      </option>

                      {quarters.map(
                        (quarter) => (

                          <option
                            key={
                              quarter.value
                            }
                            value={
                              quarter.value
                            }
                          >
                            {
                              quarter.label
                            }
                          </option>

                        )
                      )}

                    </select>

                  </div>


                  {/* Batch */}

                  <div className="form-group">

                    <label>
                      Batch
                    </label>

                    <select
                      value={
                        okrContext.batch_id
                      }
                      onChange={(e) =>
                        handleContextChange(
                          "batch_id",
                          e.target.value
                        )
                      }
                    >

                      <option value="">
                        Select Batch
                      </option>

                      {batches.map(
                        (batch) => (

                          <option
                            key={
                              batch.id
                            }
                            value={
                              batch.id
                            }
                          >
                            {
                              batch.name
                            }
                          </option>

                        )
                      )}

                    </select>

                  </div>


                  {/* Employee */}

                  <div className="form-group full-width">

                    <label>
                      Employee
                    </label>

                    <select
                      value={
                        okrContext.user_id
                      }
                      onChange={(e) =>
                        handleContextChange(
                          "user_id",
                          e.target.value
                        )
                      }
                      disabled={
                        !okrContext.batch_id
                      }
                    >

                      <option value="">
                        Select Employee
                      </option>

                      {availableEmployees.map(
                        (employee) => (

                          <option
                            key={
                              employee.id
                            }
                            value={
                              employee.id
                            }
                          >
                            {
                              employee.name
                            }
                            {" - "}
                            {
                              employee.email
                            }
                          </option>

                        )
                      )}

                    </select>

                  </div>

                </div>


                {/* Context Summary */}

                {okrContext.user_id && (

                  <div className="context-summary">

                    <div className="context-summary-title">
                      Selected Employee
                    </div>

                    {(() => {

                      const employee =
                        availableEmployees.find(
                          (item) =>
                            String(item.id) === String(okrContext.user_id)
                        );


                      const batch =
                        batches.find(
                          (item) =>
                            String(item.id) === String(okrContext.batch_id)
                        );

                      return (

                        <div className="context-summary-content">

                          <div>

                            <strong>
                              {employee?.name}
                            </strong>

                            <span>
                              {employee?.email}
                            </span>

                          </div>

                          <div>

                            <strong>
                              Batch
                            </strong>

                            <span>
                              {batch?.name}
                            </span>

                          </div>

                          <div>

                            <strong>
                              Period
                            </strong>

                            <span>
                              {
                                okrContext.quarter
                              }{" "}
                              {
                                okrContext.year
                              }
                            </span>

                          </div>

                        </div>

                      );

                    })()}

                  </div>

                )}

              </div>

            )}


            {/* =================================================
                STEP 2 - OKRS
            ================================================= */}

            {currentStep === 2 && (

              <div className="okr-modal-body">

                <div className="section-heading">

                  <h3>
                    Add OKRs
                  </h3>

                  <p>
                    Add one or more OKRs for the selected employee.
                  </p>

                </div>


                <div className="selected-employee-mini">

                  {(() => {

                    const employee =
                      availableEmployees.find(
                        (item) =>
                          String(item.id) === String(okrContext.user_id)

                      );

                    return (

                      <>

                        <div>

                          <strong>
                            {employee?.name}
                          </strong>

                          <span>
                            {employee?.email}
                          </span>

                        </div>

                        <span>
                          {
                            okrContext.quarter
                          }{" "}
                          {
                            okrContext.year
                          }
                        </span>

                      </>

                    );

                  })()}

                </div>


                <div className="okr-list">

                  {okrList.map(
                    (okr, index) => (

                      <div
                        className="okr-entry"
                        key={index}
                      >

                        <div className="okr-entry-header">

                          <h4>
                            OKR {index + 1}
                          </h4>

                          {okrList.length > 1 && (

                            <button
                              type="button"
                              className="remove-okr-btn"
                              onClick={() =>
                                removeOKR(
                                  index
                                )
                              }
                            >

                              <Trash2
                                size={16}
                              />

                              Remove

                            </button>

                          )}

                        </div>


                        <div className="okr-form-grid">

                          {/* Objective */}

                          <div className="form-group full-width">

                            <label>
                              Objective
                            </label>

                            <input
                              type="text"
                              placeholder="Enter objective"
                              value={
                                okr.objective
                              }
                              onChange={(e) =>
                                updateOKR(
                                  index,
                                  "objective",
                                  e.target.value
                                )
                              }
                            />

                          </div>


                          {/* Description */}

                          <div className="form-group full-width">

                            <label>
                              Key Results
                            </label>

                            <textarea
                              rows="3"
                              placeholder="Enter key results"
                              value={
                                okr.key_results
                              }
                              onChange={(e) =>
                                updateOKR(
                                  index,
                                  "key_results",
                                  e.target.value
                                )
                              }
                            />

                          </div>


                          {/* Target */}

                          <div className="form-group full-width">

                            <label>
                              Target
                            </label>

                            <input
                              type="text"
                              placeholder="Enter measurable target"
                              value={
                                okr.target
                              }
                              onChange={(e) =>
                                updateOKR(
                                  index,
                                  "target",
                                  e.target.value
                                )
                              }
                            />

                          </div>

                          {/* OKR Type */}

                          <div className="form-group">

                            <label>
                              OKR Type
                            </label>

                            <select name="okr_type" value={okr.okr_type} onChange={(e) => updateOKR(index, "okr_type", e.target.value)}>

                              <option value="Professional">Professional</option>
                              <option value="Personal">Personal</option>
                            </select>
                          </div>

                          {/* Tracker enabled */}

                          <div className="form-group">

                            <label>
                              Is tracker enabled?
                            </label>

                            <select name="tracker_enabled" value={okr.tracker_enabled} onChange={(e) => updateOKR(index, "tracker_enabled", e.target.value)}>
                              <option value="Yes">Yes</option>
                              <option value="No">No</option>
                            </select>
                          </div>

                        </div>


                      </div>

                    )
                  )}

                </div>


                <button
                  type="button"
                  className="add-another-okr-btn"
                  onClick={addNewOKR}
                >

                  <Plus size={17} />

                  Add Another OKR

                </button>

              </div>

            )}


            {/* =================================================
                STEP 3 - PREVIEW
            ================================================= */}

            {currentStep === 3 && (

              <div className="okr-modal-body">

                <div className="section-heading">

                  <h3>
                    Preview
                  </h3>

                  <p>
                    Review the OKRs before saving.
                  </p>

                </div>


                {/* Context Preview */}

                <div className="preview-context">

                  {(() => {

                    const organization = organizations.find(
                      (item) =>
                        String(item.id) ===
                        String(okrContext.organization_id)
                    );

                    const batch = batches.find(
                      (item) =>
                        String(item.id) ===
                        String(okrContext.batch_id)
                    );

                    const employee = availableEmployees.find(
                      (item) =>
                        String(item.id) ===
                        String(okrContext.user_id)
                    );

                    console.log("Preview Organization:", organization);
                    console.log("Preview Batch:", batch);
                    console.log("Preview Employee:", employee);

                    return (

                      <>

                        <div className="preview-context-main">

                          <div className="preview-avatar">
                            {employee?.name
                              ?.charAt(0)
                              ?.toUpperCase()}
                          </div>

                          <div>

                            <h3>
                              {employee?.name || "Unknown Employee"}
                            </h3>

                            <span>
                              {employee?.email || "No email"}
                            </span>

                          </div>

                        </div>


                        <div className="preview-context-grid">

                          <div>

                            <label>
                              Organization
                            </label>

                            <strong>
                              {organization?.name || "N/A"}
                            </strong>

                          </div>


                          <div>

                            <label>
                              Batch
                            </label>

                            <strong>
                              {batch?.name || "N/A"}
                            </strong>

                          </div>


                          <div>

                            <label>
                              Year
                            </label>

                            <strong>
                              {okrContext.year || "N/A"}
                            </strong>

                          </div>


                          <div>

                            <label>
                              Quarter
                            </label>

                            <strong>
                              {okrContext.quarter || "N/A"}
                            </strong>

                          </div>

                        </div>

                      </>

                    );

                  })()}


                </div>


                {/* OKR Preview */}

                <div className="preview-okr-list">

                  <div className="preview-list-header">

                    <h3>
                      OKRs
                    </h3>

                    <span>
                      {okrList.length}{" "}
                      OKR
                      {
                        okrList.length !== 1
                          ? "s"
                          : ""
                      }
                    </span>

                  </div>


                  {okrList.map(
                    (okr, index) => (

                      <div
                        className="preview-okr-card"
                        key={index}
                      >

                        <div className="preview-okr-number">
                          {index + 1}
                        </div>

                        <div className="preview-okr-content">

                          <h4>
                            {
                              okr.objective ||
                              "Untitled Objective"
                            }
                          </h4>

                          {okr.description && (

                            <p>
                              {
                                okr.description
                              }
                            </p>

                          )}

                          {okr.target && (

                            <div className="preview-target">

                              <span>
                                Target
                              </span>

                              <strong>
                                {
                                  okr.target
                                }
                              </strong>

                            </div>

                          )}

                        </div>

                      </div>

                    )
                  )}

                </div>

              </div>

            )}


            {/* =================================================
                MODAL FOOTER
            ================================================= */}

            <div className="okr-modal-footer">

              <button
                type="button"
                className="secondary-btn"
                onClick={
                  currentStep === 1
                    ? closeAddOKR
                    : handleBack
                }
              >

                {currentStep === 1
                  ? "Cancel"
                  : "Back"}

              </button>


              {currentStep < 3 ? (

                <button
                  type="button"
                  className="primary-btn"
                  onClick={handleNext}
                >

                  Next

                  <ChevronRight
                    size={18}
                  />

                </button>

              ) : (

                <button
                  type="button"
                  className="primary-btn"
                  onClick={
                    handleSaveOKRs
                  }
                >

                  Save OKRs

                </button>

              )}

            </div>

          </div>

        </div>

      )}


      {isEditingOKR && selectedOKR && (

        <div
          className="okr-modal-overlay"
          onClick={() => setIsEditingOKR(false)}
        >

          <div
            className="okr-view-modal"
            onClick={(e) => e.stopPropagation()}
          >

            {/* =====================================================
          HEADER
      ===================================================== */}

            <div className="okr-modal-header">

              <div>
                <h2>
                  Employee OKR
                </h2>

                <p>
                  Update OKR details.
                </p>
              </div>

              <button
                type="button"
                className="modal-close-btn"
                onClick={() => setIsEditingOKR(false)}
              >
                <X size={20} />
              </button>

            </div>


            {/* =====================================================
          EMPLOYEE INFORMATION
      ===================================================== */}

            <div className="view-employee-header">

              <div className="preview-avatar">

                {selectedOKR.assignee?.user
                  ? `${selectedOKR.assignee.user.first_name?.charAt(0) || ""}`
                    .toUpperCase()
                  : "?"}

              </div>


              <div>

                <h3>
                  {selectedOKR.assignee?.user
                    ? `${selectedOKR.assignee.user.first_name || ""} ${selectedOKR.assignee.user.last_name || ""
                      }`.trim()
                    : "Unknown Employee"}
                </h3>

                <span>
                  {selectedOKR.assignee?.user?.email || "No email"}
                </span>

              </div>


              <span
                className={`status-badge ${selectedOKR.status?.toLowerCase() || ""
                  }`}
              >
                {selectedOKR.status || "-"}
              </span>

            </div>


            {/* =====================================================
          CYCLE INFORMATION - READ ONLY
      ===================================================== */}

            <div className="view-cycle-grid">

              <div>
                <label>
                  Organization
                </label>

                <strong>
                  {selectedOKR.organization?.name || "-"}
                </strong>
              </div>


              <div>
                <label>
                  Batch
                </label>

                <strong>
                  {selectedOKR.batch?.name || "-"}
                </strong>
              </div>


              <div>
                <label>
                  Year
                </label>

                <strong>
                  {selectedOKR.batch?.year || "-"}
                </strong>
              </div>


              <div>
                <label>
                  Quarter
                </label>

                <strong>
                  {selectedOKR.batch?.quarter || "-"}
                </strong>
              </div>

            </div>


            {/* =====================================================
          EDITABLE OKR DETAILS
      ===================================================== */}

            <div className="view-okr-list">

              <div className="view-okr-card">

                <div className="view-okr-header">

                  <span>
                    OKR Details
                  </span>

                </div>


                {/* =================================================
              OBJECTIVE
          ================================================= */}

                <div className="edit-field">

                  <label>
                    Objective
                  </label>

                  <input
                    type="text"
                    className="okr-form-input"
                    value={editOKR.objective}
                    placeholder="Enter objective"
                    onChange={(e) =>
                      handleChangeOKR("objective", e.target.value)
                    }
                  />

                </div>


                {/* =================================================
              TARGET
          ================================================= */}

                <div className="edit-field">

                  <label>
                    Target
                  </label>

                  <input
                    type="number"
                    className="okr-form-input"
                    value={editOKR.target}
                    placeholder="Enter target"
                    onChange={(e) =>
                      handleChangeOKR("target", e.target.value)
                    }
                  />

                </div>


                {/* =================================================
              KEY RESULTS
          ================================================= */}

                <div className="edit-field">

                  <label>
                    Key Results
                  </label>

                  <textarea
                    className="okr-form-textarea"
                    value={editOKR.key_results}
                    placeholder="Enter key results"
                    onChange={(e) =>
                      handleChangeOKR("key_results", e.target.value)
                    }
                  />

                </div>


                {/* =================================================
              OKR TYPE + TRACKER
          ================================================= */}

                <div className="okr-edit-meta-grid">


                  {/* =================================================
                OKR TYPE
            ================================================= */}

                  <div className="edit-field">

                    <label>
                      OKR Type
                    </label>

                    <div className="okr-select-wrapper form-group">


                      <select name="okr_type" value={editOKR.okr_type} onChange={(e) =>
                        handleChangeOKR("okr_type", e.target.value)
                      }>

                        <option value="Professional">Professional</option>
                        <option value="Personal">Personal</option>
                      </select>
                    </div>

                  </div>


                  {/* =================================================
                TRACKER ENABLED
            ================================================= */}
                  <div className="edit-field">
                    <label>
                      Is tracker enabled?
                    </label>

                    <div className="form-group">


                      <select name="tracker_enabled" value={editOKR.tracker_enabled} onChange={(e) =>
                        handleChangeOKR("tracker_enabled", e.target.value)
                      }>
                        <option value="Yes">Yes</option>
                        <option value="No">No</option>
                      </select>
                    </div>
                  </div>


                </div>

              </div>

            </div>


            {/* =====================================================
          FOOTER
      ===================================================== */}

            <div className="okr-modal-footer">

              <button
                type="button"
                className="secondary-btn"
                onClick={() => setIsEditingOKR(false)}
              >
                Cancel
              </button>


              <button
                type="button"
                className="save-btn"
                onClick={saveEditedOKR}
              >
                Save Changes
              </button>

            </div>

          </div>

        </div>

      )}

      {deletePopup && selectedOKR && (
        <div
          className="delete-modal-overlay"
          onClick={() => setDeletePopup(false)}
        >
          <div
            className="delete-modal"
            onClick={(e) => e.stopPropagation()}
          >

            <div className="delete-modal-icon">
              <Trash2 size={22} />
            </div>

            <h2>
              Delete User?
            </h2>

            <p>
              Are you sure you want to delete{" "}
              <strong>
                {selectedOKR.objective}
              </strong>
              ?
            </p>

            <p className="delete-warning">
              This action cannot be undone.
            </p>


            <div className="delete-modal-actions">

              <button
                type="button"
                className="secondary-btn"
                onClick={() => {
                  setDeletePopup(false);
                  setSelectedOKR(null);
                }}
              >
                No
              </button>

              <button
                type="button"
                className="delete-confirm-btn"
                onClick={() => deleteOKR(selectedOKR)}
              >
                Yes, Delete
              </button>

            </div>

          </div>
        </div>
      )}


    </section>

  );

}

export default OKR;