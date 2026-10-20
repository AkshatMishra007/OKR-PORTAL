
import React, { useState, useEffect } from "react";
import { Trash2 } from "lucide-react";
import "./Batches.css";
import { API_URL } from "../Config/ApiEndpoint";
function Batches() {

  /* =========================================================
     BATCH DATA
  ========================================================= */
const [organizationUsers, setOrganizationUsers] = useState([]);

const [currentUser,setCurrentUser] = useState(null);

const [batchUsers, setBatchUsers] = useState([]);
const [batchAdmins, setBatchAdmins] = useState([]);

const [userSearch, setUserSearch] = useState("");
const [adminSearch, setAdminSearch] = useState("");


const [userSearchError, setUserSearchError] = useState("");
const [adminSearchError, setAdminSearchError] = useState("");

  const [batches, setBatches] = useState({
    data: [],
    pagination: {
      total: 0,
      page: 1,
      size: 10,
    },
  });

  const [filteredBatches, setFilteredBatches] = useState([]);

  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
const [errorMessage, setErrorMessage] = useState("");

  /* =========================================================
     FILTERS
  ========================================================= */

  const [searchValue, setSearchValue] = useState("");

  const [filters, setFilters] = useState({
    year: "",
    quarter: "",
    organization: "",
  });

  const years = [
    "2024",
    "2025",
    "2026",
    "2027",
    "2028",
    "2029",
    "2030",
  ];


  /* =========================================================
     ORGANIZATIONS
  ========================================================= */

  const [organizations, setOrganizations] = useState([]);


  /* =========================================================
     ADD / EDIT
  ========================================================= */

  const [showAddBatch, setShowAddBatch] = useState(false);
  const [showEditBatch, setShowEditBatch] = useState(false);

  const [selectedBatch, setSelectedBatch] = useState(null);

  const [batchForm, setBatchForm] = useState({
    name: "",
    organization_id: "",
    year: "",
    quarter: "",
    start_date: "",
    end_date: "",
    meeting_day: "",
    batch_users: [],
    batch_admins: [],
  });

const [editBatchForm, setEditBatchForm] = useState({
  organization_id: "",
  name: "",
  year: "",
  quarter: "",
  start_date: "",
  end_date: "",
  meeting_day: "",
  batch_users: [],
  batch_admins: [],
});


const getCurrentUser = async () => {
  try {
    const response = await fetch(`${API_URL}/api/users/me`, {
      headers: {
        Authorization: `Bearer ${localStorage.getItem("token")}`,
      },
    });

    if (!response.ok) {
      throw new Error("Failed to fetch current user");
    }

    const data = await response.json();
    setCurrentUser(data);
  } catch (error) {
    console.error("Error fetching current user:", error);
  }
};




const fetchBatchMembers = async (batchId) => {
  try {
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
      throw new Error("Failed to fetch batch members");
    }

    const data = await response.json();

    console.log("Batch Members:", data);

    const users = data.data?.users || [];
    const admins = data.data?.admins || [];

    setBatchUsers(users);
    setBatchAdmins(admins);

    setEditBatchForm((prev) => ({
      ...prev,
      batch_users: users.map((user) => user.id),
      batch_admins: admins.map((admin) => admin.id),
    }));

  } catch (error) {
    console.error("Error fetching batch members:", error);

    setBatchUsers([]);
    setBatchAdmins([]);
  }
};

  const fetchOrganizationUsers = async (organizationId) => {

    if (!organizationId) {
        setOrganizationUsers([]);
        setBatchUsers([]);
        setBatchAdmins([]);
        return;
    }

    try {

        const response = await fetch(
            `${API_URL}/api/users/organization/${organizationId}`,
            {
                method: "GET",
                headers: {
                    Authorization: `Bearer ${localStorage.getItem("token")}`,
                },
            }
        );

        if (!response.ok) {
            throw new Error("Failed to fetch organization users");
        }

        const data = await response.json();

        console.log("Organization Users:", data);

        setOrganizationUsers(data.data || []);

    } catch (error) {

        console.error(
            "Error fetching organization users:",
            error
        );

        setOrganizationUsers([]);

    }
};

  /* =========================================================
     DELETE
  ========================================================= */

  const [deletePopup, setDeletePopup] = useState(false);
  const [selectedDeleteBatch, setSelectedDeleteBatch] = useState(null);


  /* =========================================================
     FILTER FUNCTION
  ========================================================= */

  const filterBatchData = (
    data,
    search = searchValue,
    currentFilters = filters
  ) => {

    return data.filter((batch) => {

      /* Search */
      const searchMatch =
        search.trim() === "" ||
        batch.name
          ?.toLowerCase()
          .includes(search.toLowerCase());


      /* Year */
      const yearMatch =
        currentFilters.year === "" ||
        String(batch.year) === String(currentFilters.year);


      /* Quarter */
      const quarterMatch =
        currentFilters.quarter === "" ||
        batch.quarter === currentFilters.quarter;


      /* Organization */
      const organizationMatch =
        currentFilters.organization === "" ||
        String(batch.organization_id) ===
          String(currentFilters.organization);


      return (
        searchMatch &&
        yearMatch &&
        quarterMatch &&
        organizationMatch
      );
    });
  };


  /* =========================================================
     APPLY FILTERS
  ========================================================= */

  const applyFilters = (
    search = searchValue,
    currentFilters = filters
  ) => {

    const filtered = filterBatchData(
      batches.data,
      search,
      currentFilters
    );

    setFilteredBatches(filtered);
  };


  /* =========================================================
     SEARCH
  ========================================================= */

  const handleSearch = (value) => {

    setSearchValue(value);

    applyFilters(value, filters);
  };


  /* =========================================================
     FETCH ORGANIZATIONS
  ========================================================= */

  const fetchOrganizations = () => {

    fetch(`${API_URL}/api/organizations/`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${localStorage.getItem("token")}`,
      },
    })
      .then((res) => res.json())
      .then((data) => {

        setOrganizations(data.data || []);

      })
      .catch((error) => {
        console.error("Error fetching organizations:", error);
      });
  };


  /* =========================================================
     FETCH BATCHES
  ========================================================= */

  const fetchBatches = (page = 1, size = 10) => {
    console.log("Curent user is",currentUser);
    let url=""
    if(currentUser.organization_memberships[0].role.name=="ORG_ADMIN")
    {
      url=`${API_URL}/api/batches/?organization_id=${currentUser.organization_memberships[0].organization_id}&page=${page}&size=${size}`
    }
    else
    {
      url=`${API_URL}/api/batches/?page=${page}&size=${size}`
    }
    fetch(
      url,
      {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      }
    )
      .then((res) => res.json())
      .then((data) => {

        setBatches(data);

        console.log("Fetched Batches:", data);

        /*
          Apply current filters to newly fetched data.
        */
        const filtered = filterBatchData(
          data.data || [],
          searchValue,
          filters
        );

        setFilteredBatches(filtered);

      })
      .catch((error) => {
        console.error("Error fetching batches:", error);
      });
  };


  /* =========================================================
     PAGINATION
  ========================================================= */

  const totalPages = Math.ceil(
    batches.pagination.total / pageSize
  );


  /* =========================================================
     INITIAL LOAD
  ========================================================= */

  useEffect(() => {

    getCurrentUser();
  }, []);

  useEffect(() => {
 if (!currentUser) {
    return;
  }
   const membership =
    currentUser.organization_memberships?.[0];

  const role = membership?.role?.name;
  const organizationId = membership?.organization_id;

  if (role === "ORG_ADMIN" && organizationId) {
    setBatchForm((prev) => ({
      ...prev,
      organization_id: organizationId,
    }));

    fetchOrganizationUsers(organizationId);
  }
    fetchBatches(currentPage, pageSize);

  }, [currentUser,currentPage, pageSize]);


  useEffect(() => {

    fetchOrganizations();

  }, []);


  /* =========================================================
     CREATE BATCH
  ========================================================= */

  const createBatch = async () => {
  try {
    // Clear previous error
    setErrorMessage("");

    const response = await fetch(
      `${API_URL}/api/batches/`,
      {
        method: "POST",

        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },

        body: JSON.stringify(batchForm),
      }
    );

    if (response.ok) {
      setShowAddBatch(false);

      setBatchForm({
        name: "",
        organization_id: "",
        year: "",
        quarter: "",
        start_date: "",
        end_date: "",
        meeting_day: "",
      });

      fetchBatches(currentPage, pageSize);

    } else {
      const data = await response.json();

      setErrorMessage(
        data.detail || "Failed to create batch."
      );
    }

  } catch (error) {
    console.error("Create batch error:", error);

    setErrorMessage(
      "Something went wrong while creating the batch."
    );
  }
};


  /* =========================================================
     UPDATE BATCH
  ========================================================= */

  const updateBatch = async (id) => {

    try {

      const response = await fetch(
        `${API_URL}/api/batches/${id}`,
        {
          method: "PUT",

          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },

          body: JSON.stringify(editBatchForm),
        }
      );


      if (response.ok) {

        setShowEditBatch(false);

        setSelectedBatch(null);

        fetchBatches(currentPage, pageSize);

      } else {

        console.error(
          "Failed to update batch:",
          await response.text()
        );

      }

    } catch (error) {

      console.error("Update batch error:", error);

    }
  };


  /* =========================================================
     DELETE BATCH
  ========================================================= */

  const deleteBatch = async (id) => {

    try {

      const response = await fetch(
        `${API_URL}/api/batches/${id}`,
        {
          method: "DELETE",

          headers: {
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
        }
      );


      if (response.ok) {

        setDeletePopup(false);

        setSelectedDeleteBatch(null);

        fetchBatches(currentPage, pageSize);

      } else {

        console.error(
          "Failed to delete batch:",
          await response.text()
        );

      }

    } catch (error) {

      console.error("Delete batch error:", error);

    }
  };

/* ======================User Options===================================*/



const userOptions = organizationUsers.filter((user) => {

  const search = userSearch.toLowerCase().trim();

  if (!search) {
    return false;
  }

  const alreadyUser = batchUsers.some(
    (selectedUser) => selectedUser.id === user.id
  );

  const alreadyAdmin = batchAdmins.some(
    (selectedAdmin) => selectedAdmin.id === user.id
  );

  if (alreadyUser || alreadyAdmin) {
    return false;
  }

  return (
    user.email?.toLowerCase().includes(search) ||
    user.name?.toLowerCase().includes(search)
  );
});



const adminOptions = organizationUsers.filter((user) => {

  const search = adminSearch.toLowerCase().trim();

  if (!search) {
    return false;
  }

  const alreadyAdmin = batchAdmins.some(
    (selectedAdmin) => selectedAdmin.id === user.id
  );

  const alreadyUser = batchUsers.some(
    (selectedUser) => selectedUser.id === user.id
  );

  if (alreadyAdmin || alreadyUser) {
    return false;
  }

  return (
    user.email?.toLowerCase().includes(search) ||
    user.name?.toLowerCase().includes(search)
  );
});
  /* =========================================================
     JSX
  ========================================================= */

  return (

    <section className="page">


      {/* =====================================================
          FILTER BAR
      ===================================================== */}

      <div className="filters-bar">


        {/* Search */}

        <div className="search-wrap">

          <div className="search-icon">
            🔍
          </div>

          <input
            type="text"
            className="search-input"
            placeholder="Search batches..."
            value={searchValue}
            onChange={(e) =>
              handleSearch(e.target.value)
            }
          />

        </div>


        {/* Year */}

        <select
          className="filter-select"
          value={filters.year}
          onChange={(e) => {

            const newFilters = {
              ...filters,
              year: e.target.value,
            };

            setFilters(newFilters);

            applyFilters(
              searchValue,
              newFilters
            );

          }}
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
          className="filter-select"
          value={filters.quarter}
          onChange={(e) => {

            const newFilters = {
              ...filters,
              quarter: e.target.value,
            };

            setFilters(newFilters);

            applyFilters(
              searchValue,
              newFilters
            );

          }}
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


        {/* Organization */}

        {currentUser && currentUser.organization_memberships[0].role.name !== "ORG_ADMIN" && (
          <select
          className="filter-select"
          value={filters.organization}
          onChange={(e) => {

            const newFilters = {
              ...filters,
              organization: e.target.value,
            };

            setFilters(newFilters);

            applyFilters(
              searchValue,
              newFilters
            );

          }}
        >

          <option value="">
            All Organizations
          </option>

          {organizations.map((org) => (

            <option
              key={org.id}
              value={org.id}
            >
              {org.name}
            </option>

          ))}

        </select>

        )}

        {/* Clear Filters */}

        {(searchValue ||
          filters.year ||
          filters.quarter ||
          filters.organization) && (

          <button
            type="button"
            className="clear-filter-btn"
            onClick={() => {

              const emptyFilters = {
                year: "",
                quarter: "",
                organization: "",
              };

              setSearchValue("");

              setFilters(emptyFilters);

              setFilteredBatches(
                batches.data
              );

            }}
          >
            Clear
          </button>

        )}

      </div>


      {/* =====================================================
          BATCH CARD
      ===================================================== */}

      <div className="card">


        {/* Card Header */}

        <div className="card-header">

          <div>

            <div className="card-title">
              Batches
            </div>

          </div>


          <button
            className="primary-btn"
            onClick={() =>
              setShowAddBatch(true)
            }
          >
            + Add Batch
          </button>

        </div>


        {/* ===================================================
            TABLE
        =================================================== */}

        <div className="batch-table-wrap">

          <table className="batch-table">

            <thead>

              <tr>
               {currentUser && currentUser.organization_memberships[0].role.name !== "ORG_ADMIN" && (                
                <th>
                  Organization Name
                </th>)}

                <th>
                  Batch Name
                </th>

                <th>
                  Year
                </th>

                <th>
                  Quarter
                </th>

                <th>
                  Start Date
                </th>

                <th>
                  End Date
                </th>

                <th>
                  Meeting Day
                </th>

                <th>
                  Actions
                </th>

              </tr>

            </thead>


            <tbody>

              {filteredBatches.length > 0 ? (

                filteredBatches.map((batch) => (

                  <tr
                    key={batch.id}
  onClick={async () => {

  setSelectedBatch(batch);

  setUserSearch("");
  setAdminSearch("");
  setUserSearchError("");
  setAdminSearchError("");

  setEditBatchForm({
    organization_id: batch.organization_id,
    name: batch.name,
    year: batch.year,
    quarter: batch.quarter,
    start_date: batch.start_date,
    end_date: batch.end_date,
    meeting_day: batch.meeting_day,
    batch_users: [],
    batch_admins: [],
  });

  await fetchOrganizationUsers(batch.organization_id);

  await fetchBatchMembers(batch.id);

  setShowEditBatch(true);

}}
                  >


                    {/* Organization */}

                    {currentUser && currentUser.organization_memberships[0].role.name !== "ORG_ADMIN" && (                    <td>

                      <strong>

                        {
                          organizations.find(
                            (org) =>
                              org.id ===
                              batch.organization_id
                          )?.name ||
                          "Unknown Organization"
                        }

                      </strong>

                    </td>
)}

                    {/* Batch Name */}

                    <td>
                      {batch.name}
                    </td>


                    {/* Year */}

                    <td>
                      {batch.year}
                    </td>


                    {/* Quarter */}

                    <td>
                      {batch.quarter}
                    </td>


                    {/* Start Date */}

                    <td>

                      {batch.start_date
                        ? new Date(
                            batch.start_date
                          ).toLocaleDateString(
                            "en-GB"
                          )
                        : "-"
                      }

                    </td>


                    {/* End Date */}

                    <td>

                      {batch.end_date
                        ? new Date(
                            batch.end_date
                          ).toLocaleDateString(
                            "en-GB"
                          )
                        : "-"
                      }

                    </td>


                    {/* Meeting Day */}

                    <td>
                      {batch.meeting_day}
                    </td>


                    {/* Delete */}

                    <td>

                      <button
                        className="organization-delete-btn"
                        onClick={(e) => {

                          e.stopPropagation();

                          setSelectedDeleteBatch(
                            batch
                          );

                          setDeletePopup(true);

                        }}
                      >

                        <Trash2 size={17} />

                      </button>

                    </td>

                  </tr>

                ))

              ) : (

                <tr>

                  <td
                    colSpan="8"
                    style={{
                      textAlign: "center",
                      padding: "30px",
                    }}
                  >
                    No batches found
                  </td>

                </tr>

              )}

            </tbody>

          </table>

        </div>


        {/* ===================================================
            PAGINATION
        =================================================== */}

        <div className="pagination">


          {/* Page Size */}

          <div className="pagination-size">

            <span>
              Rows per page
            </span>

            <select
              value={pageSize}
              onChange={(e) => {

                setPageSize(
                  Number(e.target.value)
                );

                setCurrentPage(1);

              }}
            >

              <option value={10}>
                10
              </option>

              <option value={20}>
                20
              </option>

              <option value={50}>
                50
              </option>

            </select>

          </div>


          {/* Pagination */}

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

              Page {currentPage} of{" "}
              {totalPages || 1}

            </span>


            <button
              className="pagination-btn"
              disabled={
                currentPage >=
                totalPages
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
          ADD BATCH MODAL
      ===================================================== */}

{errorMessage && (
  <div className="error-modal-overlay">
    <div className="error-modal">

      <div className="error-modal-header">
        <h3>Error</h3>

        <button
          className="error-modal-close"
          onClick={() => setErrorMessage("")}
        >
          ×
        </button>
      </div>

      <div className="error-modal-body">
        <p>{errorMessage}</p>
      </div>

      <div className="error-modal-footer">
        <button
          className="error-modal-ok"
          onClick={() => setErrorMessage("")}
        >
          OK
        </button>
      </div>

    </div>
  </div>
)}


      {showAddBatch && (

        <div className="batch-modal-overlay">

          <div className="batch-modal">


            {/* Header */}

            <div className="batch-modal-header">


              <h2 className="batch-modal-title">
                Add New Batch
              </h2>

              <button
                className="batch-close-btn"
                onClick={() =>
                  setShowAddBatch(false)
                }
              >
                ✕
              </button>

            </div>


            {/* Form */}

            <form
              className="batch-form"
              onSubmit={(e) => {

                e.preventDefault();

                createBatch();

              }}
            >

              <div className="batch-form-grid">


                {/* Batch Name */}

                <div className="form-group">

                  <label>
                    Batch Name
                  </label>

                  <input
                    type="text"
                    placeholder="Enter batch name"
                    value={batchForm.name}
                    onChange={(e) =>
                      setBatchForm({
                        ...batchForm,
                        name: e.target.value,
                      })
                    }
                  />

                </div>


{/* Organization */}

<div className="form-group">

  <label>
    Organization
  </label>

  {currentUser.organization_memberships[0].role.name === "ORG_ADMIN" ? (
    <input
      type="text"
      value={currentUser.organization_memberships[0].organization_name}
      readOnly
    />
  ) : (
    <select
      value={batchForm.organization_id}
      onChange={(e) => {
        const organizationId = e.target.value;

        setBatchForm({
          ...batchForm,
          organization_id: organizationId,
        });

        fetchOrganizationUsers(organizationId);
      }}
    >
      <option value="">
        Select Organization
      </option>

      {organizations.map((org) => (
        <option
          key={org.id}
          value={org.id}
        >
          {org.name}
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
                    value={batchForm.year}
                    onChange={(e) =>
                      setBatchForm({
                        ...batchForm,
                        year: e.target.value,
                      })
                    }
                  >

                    <option value="">
                      Select Year
                    </option>

                    {Array.from(
                      { length: 10 },
                      (_, i) => {

                        const year =
                          new Date().getFullYear() +
                          i;

                        return (

                          <option
                            key={year}
                            value={year}
                          >
                            {year}
                          </option>

                        );

                      }
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
                      batchForm.quarter
                    }
                    onChange={(e) =>
                      setBatchForm({
                        ...batchForm,
                        quarter:
                          e.target.value,
                      })
                    }
                  >

                    <option value="">
                      Select Quarter
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

                </div>


                {/* Start Date */}

                <div className="form-group">

                  <label>
                    Start Date
                  </label>

                  <input
                    type="date"
                    value={
                      batchForm.start_date
                    }
                    onChange={(e) =>
                      setBatchForm({
                        ...batchForm,
                        start_date:
                          e.target.value,
                      })
                    }
                  />

                </div>


                {/* End Date */}

                <div className="form-group">

                  <label>
                    End Date
                  </label>

                  <input
                    type="date"
                    value={
                      batchForm.end_date
                    }
                    onChange={(e) =>
                      setBatchForm({
                        ...batchForm,
                        end_date:
                          e.target.value,
                      })
                    }
                  />

                </div>


                {/* Meeting Day */}

                <div className="form-group">

                  <label>
                    Meeting Day
                  </label>

                  <select
                    value={
                      batchForm.meeting_day
                    }
                    onChange={(e) =>
                      setBatchForm({
                        ...batchForm,
                        meeting_day:
                          e.target.value,
                      })
                    }
                  >

                    <option value="">
                      Select Meeting Day
                    </option>

                    <option value="MONDAY">
                      MONDAY
                    </option>

                    <option value="TUESDAY">
                      TUESDAY
                    </option>

                    <option value="WEDNESDAY">
                      WEDNESDAY
                    </option>

                    <option value="THURSDAY">
                      THURSDAY
                    </option>

                    <option value="FRIDAY">
                      FRIDAY
                    </option>

                    <option value="SATURDAY">
                      SATURDAY
                    </option>

                    <option value="SUNDAY">
                      SUNDAY
                    </option>

                  </select>

                </div>

              </div>

{/* =========================================================
    BATCH USERS
========================================================= */}

<div className="batch-members-section">

    <h3 className="batch-members-title">
        Batch Users
    </h3>

    <div className="chip-input">

        {/* Selected Batch Users */}
        {batchUsers.map((user) => (

            <div
                className="user-chip"
                key={user.id}
            >

                <span>
                    {user.email}
                </span>

                <button
                    type="button"
                    onClick={() => {

                        // Remove user from UI
                        setBatchUsers(
                            batchUsers.filter(
                                (selectedUser) =>
                                    selectedUser.id !== user.id
                            )
                        );

                        // Remove user ID from API payload
                        setBatchForm({
                            ...batchForm,
                            batch_users:
                                batchForm.batch_users.filter(
                                    (userId) =>
                                        userId !== user.id
                                )
                        });

                    }}
                >
                    ×
                </button>

            </div>

        ))}


        {/* Search Input */}
        <input
            type="text"
            placeholder={
                batchUsers.length === 0
                    ? "Search and add users..."
                    : "Search user..."
            }
            value={userSearch}
            onChange={(e) => {

                const value = e.target.value;

                if (!batchForm.organization_id) {

                    setUserSearchError(
                        "Please select an organization first."
                    );

                    setUserSearch(value);

                    return;
                }

                setUserSearchError("");

                setUserSearch(value);

            }}
        />

    </div>


    {/* Search Error */}
    {userSearchError && (

        <div className="field-error">
            {userSearchError}
        </div>

    )}


    {/* User Search Results */}
    {userSearch &&
        !userSearchError &&
        userOptions.length > 0 && (

        <div className="user-search-results">

            {userOptions.map((user) => (

                <div
                    className="user-search-option"
                    key={user.id}
                    onClick={() => {

                        // Prevent duplicate user
                        if (
                            !batchUsers.some(
                                (selectedUser) =>
                                    selectedUser.id === user.id
                            )
                        ) {

                            // Add complete user object for UI
                            setBatchUsers([
                                ...batchUsers,
                                user
                            ]);

                            // Add only ID for API payload
                            setBatchForm({
                                ...batchForm,
                                batch_users: [
                                    ...batchForm.batch_users,
                                    user.id
                                ]
                            });

                        }

                        // Clear search
                        setUserSearch("");

                        setUserSearchError("");

                    }}
                >

                    <strong>
                        {user.email}
                    </strong>

                    <small>
                        {user.name}
                    </small>

                </div>

            ))}

        </div>

    )}

</div>


{/* =========================================================
    BATCH ADMINS
========================================================= */}

<div className="batch-members-section">

    <h3 className="batch-members-title">
        Batch Admins
    </h3>

    <div className="chip-input">

        {/* Selected Batch Admins */}
        {batchAdmins.map((user) => (

            <div
                className="user-chip admin-chip"
                key={user.id}
            >

                <span>
                    {user.email}
                </span>

                <button
                    type="button"
                    onClick={() => {

                        // Remove admin from UI
                        setBatchAdmins(
                            batchAdmins.filter(
                                (selectedUser) =>
                                    selectedUser.id !== user.id
                            )
                        );

                        // Remove admin ID from API payload
                        setBatchForm({
                            ...batchForm,
                            batch_admins:
                                batchForm.batch_admins.filter(
                                    (userId) =>
                                        userId !== user.id
                                )
                        });

                    }}
                >
                    ×
                </button>

            </div>

        ))}


        {/* Search Input */}
        <input
            type="text"
            placeholder={
                batchAdmins.length === 0
                    ? "Search and add admins..."
                    : "Search admin..."
            }
            value={adminSearch}
            onChange={(e) => {

                const value = e.target.value;

                if (!batchForm.organization_id) {

                    setAdminSearchError(
                        "Please select an organization first."
                    );

                    setAdminSearch(value);

                    return;
                }

                setAdminSearchError("");

                setAdminSearch(value);

            }}
        />

    </div>


    {/* Search Error */}
    {adminSearchError && (

        <div className="field-error">
            {adminSearchError}
        </div>

    )}


    {/* Admin Search Results */}
    {adminSearch &&
        !adminSearchError &&
        adminOptions.length > 0 && (

        <div className="user-search-results">

            {adminOptions.map((user) => (

                <div
                    className="user-search-option"
                    key={user.id}
                    onClick={() => {

                        // Prevent duplicate admin
                        if (
                            !batchAdmins.some(
                                (selectedUser) =>
                                    selectedUser.id === user.id
                            )
                        ) {

                            // Add complete user object for UI
                            setBatchAdmins([
                                ...batchAdmins,
                                user
                            ]);

                            // Add only ID for API payload
                            setBatchForm({
                                ...batchForm,
                                batch_admins: [
                                    ...batchForm.batch_admins,
                                    user.id
                                ]
                            });

                        }

                        // Clear search
                        setAdminSearch("");

                        setAdminSearchError("");

                    }}
                >

                    <div>

                        <strong>
                            {user.name}
                        </strong>

                        <small>
                            {user.email}
                        </small>

                    </div>

                </div>

            ))}

        </div>

    )}

</div>

              {/* Footer */}

              <div className="batch-modal-footer">

                <button
                  type="button"
                  className="secondary-btn"
                  onClick={() =>
                    setShowAddBatch(false)
                  }
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  className="primary-btn"
                >
                  Create Batch
                </button>

              </div>

            </form>

          </div>

        </div>

      )}


      {/* =====================================================
          EDIT BATCH MODAL
      ===================================================== */}

      {showEditBatch && selectedBatch && (

        <div className="batch-modal-overlay">

          <div className="batch-modal">


            {/* Header */}

            <div className="batch-modal-header">

              <h2 className="batch-modal-title">
                Edit Batch
              </h2>

              <button
                className="batch-close-btn"
                onClick={() =>
                  setShowEditBatch(false)
                }
              >
                ✕
              </button>

            </div>


            {/* Form */}

            <form
              className="batch-form"
              onSubmit={(e) => {

                e.preventDefault();

                updateBatch(
                  selectedBatch.id
                );

              }}
            >

              <div className="batch-form-grid">


                {/* Batch Name */}

                <div className="form-group">

                  <label>
                    Batch Name
                  </label>

                  <input
                    type="text"
                    placeholder="Enter batch name"
                    value={
                      editBatchForm.name
                    }
                    onChange={(e) =>
                      setEditBatchForm({
                        ...editBatchForm,
                        name: e.target.value,
                      })
                    }
                  />

                </div>


{/* Organization */}

<div className="form-group">

  <label>
    Organization
  </label>

  {currentUser.organization_memberships[0].role.name === "ORG_ADMIN" ? (
    <input
      type="text"
      value={
        currentUser.organization_memberships[0].organization_name
      }
      readOnly
    />
  ) : (
    <select
      value={batchForm.organization_id}
      onChange={(e) => {
        const organizationId = e.target.value;

        setBatchForm({
          ...batchForm,
          organization_id: organizationId,
        });

        fetchOrganizationUsers(organizationId);
      }}
    >
      <option value="">
        Select Organization
      </option>

      {organizations.map((org) => (
        <option
          key={org.id}
          value={org.id}
        >
          {org.name}
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
                      editBatchForm.year
                    }
                    onChange={(e) =>
                      setEditBatchForm({
                        ...editBatchForm,
                        year: e.target.value,
                      })
                    }
                  >

                    <option value="">
                      Select Year
                    </option>

                    {Array.from(
                      { length: 10 },
                      (_, i) => {

                        const year =
                          new Date().getFullYear() +
                          i;

                        return (

                          <option
                            key={year}
                            value={year}
                          >
                            {year}
                          </option>

                        );

                      }
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
                      editBatchForm.quarter
                    }
                    onChange={(e) =>
                      setEditBatchForm({
                        ...editBatchForm,
                        quarter:
                          e.target.value,
                      })
                    }
                  >

                    <option value="">
                      Select Quarter
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

                </div>


                {/* Start Date */}

                <div className="form-group">

                  <label>
                    Start Date
                  </label>

                  <input
                    type="date"
                    value={
                      editBatchForm.start_date
                    }
                    onChange={(e) =>
                      setEditBatchForm({
                        ...editBatchForm,
                        start_date:
                          e.target.value,
                      })
                    }
                  />

                </div>


                {/* End Date */}

                <div className="form-group">

                  <label>
                    End Date
                  </label>

                  <input
                    type="date"
                    value={
                      editBatchForm.end_date
                    }
                    onChange={(e) =>
                      setEditBatchForm({
                        ...editBatchForm,
                        end_date:
                          e.target.value,
                      })
                    }
                  />

                </div>


                {/* Meeting Day */}

                <div className="form-group">

                  <label>
                    Meeting Day
                  </label>

                  <select
                    value={
                      editBatchForm.meeting_day
                    }
                    onChange={(e) =>
                      setEditBatchForm({
                        ...editBatchForm,
                        meeting_day:
                          e.target.value,
                      })
                    }
                  >

                    <option value="">
                      Select Meeting Day
                    </option>

                    <option value="MONDAY">
                      MONDAY
                    </option>

                    <option value="TUESDAY">
                      TUESDAY
                    </option>

                    <option value="WEDNESDAY">
                      WEDNESDAY
                    </option>

                    <option value="THURSDAY">
                      THURSDAY
                    </option>

                    <option value="FRIDAY">
                      FRIDAY
                    </option>

                    <option value="SATURDAY">
                      SATURDAY
                    </option>

                    <option value="SUNDAY">
                      SUNDAY
                    </option>

                  </select>

                </div>

              </div>
{/* =====================================================
    EDIT BATCH USERS
===================================================== */}

<div className="batch-members-section">

  <h3 className="batch-members-title">
    Batch Users
  </h3>

  <div className="chip-input">

    {batchUsers.map((user) => (

      <div
        className="user-chip"
        key={user.id}
      >

        <span>
          {user.email}
        </span>

        <button
          type="button"
          onClick={() => {

            setBatchUsers(
              batchUsers.filter(
                (selectedUser) =>
                  selectedUser.id !== user.id
              )
            );

            setEditBatchForm({
              ...editBatchForm,
              batch_users:
                editBatchForm.batch_users.filter(
                  (userId) =>
                    userId !== user.id
                )
            });

          }}
        >
          ×
        </button>

      </div>

    ))}

    <input
      type="text"
      placeholder={
        batchUsers.length === 0
          ? "Search and add users..."
          : "Search user..."
      }
      value={userSearch}
      onChange={(e) => {

        const value = e.target.value;

        if (!editBatchForm.organization_id) {

          setUserSearchError(
            "Please select an organization first."
          );

          setUserSearch(value);

          return;
        }

        setUserSearchError("");

        setUserSearch(value);

      }}
    />

  </div>

  {userSearchError && (
    <div className="field-error">
      {userSearchError}
    </div>
  )}

  {userSearch &&
    !userSearchError &&
    userOptions.length > 0 && (

    <div className="user-search-results">

      {userOptions.map((user) => (

        <div
          className="user-search-option"
          key={user.id}
          onClick={() => {

            setBatchUsers([
              ...batchUsers,
              user
            ]);

            setEditBatchForm({
              ...editBatchForm,
              batch_users: [
                ...editBatchForm.batch_users,
                user.id
              ]
            });

            setUserSearch("");

            setUserSearchError("");

          }}
        >

          <strong>
            {user.email}
          </strong>

          <small>
            {user.name}
          </small>

        </div>

      ))}

    </div>

  )}

</div>

{/* =====================================================
    EDIT BATCH ADMINS
===================================================== */}

<div className="batch-members-section">

  <h3 className="batch-members-title">
    Batch Admins
  </h3>

  <div className="chip-input">

    {batchAdmins.map((user) => (

      <div
        className="user-chip admin-chip"
        key={user.id}
      >

        <span>
          {user.email}
        </span>

        <button
          type="button"
          onClick={() => {

            setBatchAdmins(
              batchAdmins.filter(
                (selectedUser) =>
                  selectedUser.id !== user.id
              )
            );

            setEditBatchForm({
              ...editBatchForm,
              batch_admins:
                editBatchForm.batch_admins.filter(
                  (userId) =>
                    userId !== user.id
                )
            });

          }}
        >
          ×
        </button>

      </div>

    ))}

    <input
      type="text"
      placeholder={
        batchAdmins.length === 0
          ? "Search and add admins..."
          : "Search admin..."
      }
      value={adminSearch}
      onChange={(e) => {

        const value = e.target.value;

        if (!editBatchForm.organization_id) {

          setAdminSearchError(
            "Please select an organization first."
          );

          setAdminSearch(value);

          return;
        }

        setAdminSearchError("");

        setAdminSearch(value);

      }}
    />

  </div>

  {adminSearchError && (
    <div className="field-error">
      {adminSearchError}
    </div>
  )}

  {adminSearch &&
    !adminSearchError &&
    adminOptions.length > 0 && (

    <div className="user-search-results">

      {adminOptions.map((user) => (

        <div
          className="user-search-option"
          key={user.id}
          onClick={() => {

            setBatchAdmins([
              ...batchAdmins,
              user
            ]);

            setEditBatchForm({
              ...editBatchForm,
              batch_admins: [
                ...editBatchForm.batch_admins,
                user.id
              ]
            });

            setAdminSearch("");

            setAdminSearchError("");

          }}
        >

          <strong>
            {user.name}
          </strong>

          <small>
            {user.email}
          </small>

        </div>

      ))}

    </div>

  )}

</div>


              {/* Footer */}

              <div className="batch-modal-footer">

                <button
                  type="button"
                  className="secondary-btn"
                  onClick={() =>
                    setShowEditBatch(false)
                  }
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  className="primary-btn"
                >
                  Update Batch
                </button>

              </div>

            </form>

          </div>

        </div>

      )}


      {/* =====================================================
          DELETE MODAL
      ===================================================== */}

      {deletePopup &&
        selectedDeleteBatch && (

        <div
          className="delete-modal-overlay"
          onClick={() =>
            setDeletePopup(false)
          }
        >

          <div
            className="delete-modal"
            onClick={(e) =>
              e.stopPropagation()
            }
          >

            <div className="delete-modal-icon">
              <Trash2 size={22} />
            </div>

            <h2>
              Delete Batch?
            </h2>

            <p>

              Are you sure you want to
              delete{" "}

              <strong>
                {selectedDeleteBatch.name}
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

                  setSelectedDeleteBatch(
                    null
                  );

                }}
              >
                No
              </button>


              <button
                type="button"
                className="delete-confirm-btn"
                onClick={() =>
                  deleteBatch(
                    selectedDeleteBatch.id
                  )
                }
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

export default Batches;

