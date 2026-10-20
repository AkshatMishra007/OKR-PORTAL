import React, { useEffect, useState } from "react";
import axios from "axios";
import "./ManageQuery.css";
import { API_URL } from "../Config/ApiEndpoint";

const BASE_API_URL =
  API_URL || process.env.REACT_APP_API_URL || "http://localhost:8000";

const STATUS_OPTIONS = [
  "ALL",
  "OPEN",
  "IN_PROGRESS",
  "RESOLVED",
  "CLOSED",
  "REOPENED",
];

const PRIORITY_OPTIONS = [
  "ALL",
  "LOW",
  "MEDIUM",
  "HIGH",
  "URGENT",
];

const ManageQuery = () => {
  const [queries, setQueries] = useState([]);
  const [users, setUsers] = useState([]);

  const [loading, setLoading] = useState(false);
  const [usersLoading, setUsersLoading] = useState(false);
  const [error, setError] = useState("");

  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("ALL");
  const [priority, setPriority] = useState("ALL");

  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  const [totalQueries, setTotalQueries] = useState(0);
  const [totalPages, setTotalPages] = useState(1);

  const [stats, setStats] = useState({
    total: 0,
    pending: 0,
    resolved: 0,
    closed: 0,
  });

  const [selectedQuery, setSelectedQuery] = useState(null);
  const [showDetails, setShowDetails] = useState(false);

  const [activities, setActivities] = useState([]);
  const [activityLoading, setActivityLoading] = useState(false);

  const [selectedAssignee, setSelectedAssignee] = useState("");
  const [selectedStatus, setSelectedStatus] = useState("");

  const [resolutionNote, setResolutionNote] = useState("");

  const [actionLoading, setActionLoading] = useState(false);
  const [actionError, setActionError] = useState("");
  const [actionSuccess, setActionSuccess] = useState("");

  const getAuthConfig = () => ({
    headers: {
      Authorization: `Bearer ${localStorage.getItem("token")}`,
    },
  });

  const fetchQueries = async (page = currentPage) => {
    try {
      setLoading(true);
      setError("");

      const params = new URLSearchParams({
        page: String(page),
        page_size: String(pageSize),
      });

      if (search.trim()) {
        params.append("search", search.trim());
      }

      if (status !== "ALL") {
        params.append("status", status);
      }

      if (priority !== "ALL") {
        params.append("priority", priority);
      }

      const response = await axios.get(
        `${BASE_API_URL}/api/queries/?${params.toString()}`,
        getAuthConfig()
      );

      const data = response.data;

      setQueries(data.items || []);
      setTotalQueries(data.total || 0);
      setTotalPages(data.total_pages || 1);
    } catch (err) {
      console.error("Failed to fetch queries:", err);

      setError(
        err.response?.data?.detail ||
        "Unable to load queries. Please try again."
      );

      setQueries([]);
      setTotalQueries(0);
      setTotalPages(1);
    } finally {
      setLoading(false);
    }
  };

  const fetchUsers = async () => {
    try {
      setUsersLoading(true);

      const response = await axios.get(
        `${BASE_API_URL.replace(/\/$/, "")}/api/users/?page=1&size=100`,
        getAuthConfig()
      );

      const data = response.data;

      setUsers(data.data || []);
    } catch (err) {
      console.error("Failed to fetch users:", err);
      setUsers([]);
    } finally {
      setUsersLoading(false);
    }
  };

  const fetchActivities = async (queryId) => {
    try {
      setActivityLoading(true);

      const response = await axios.get(
        `${BASE_API_URL}/api/queries/${queryId}/activities?page=1&size=20&sort_by=created_at&sort_order=asc`,
        getAuthConfig()
      );

      setActivities(response.data.activities || []);
    } catch (err) {
      console.error("Failed to fetch query activities:", err);
      setActivities([]);
    } finally {
      setActivityLoading(false);
    }
  };

  const fetchDashboardStats = async () => {
    try {
      const response = await axios.get(
        `${BASE_API_URL}/api/queries/dashboard`,
        getAuthConfig()
      );
      const data = response.data;
      const sc = data.status_counts || {};
      const openCount = sc.OPEN || 0;
      const inProgressCount = sc.IN_PROGRESS || 0;
      const reopenedCount = sc.REOPENED || 0;
      const resolvedCount = sc.RESOLVED || 0;
      const closedCount = sc.CLOSED || 0;
      const totalCount = data.total_queries || 0;

      setStats({
        total: totalCount,
        pending: openCount + inProgressCount + reopenedCount,
        resolved: resolvedCount,
        closed: closedCount,
      });
    } catch (err) {
      console.warn("Dashboard stats not available, fallback to query items:", err);
    }
  };

  useEffect(() => {
    fetchQueries();
    fetchDashboardStats();
  }, [currentPage, pageSize, status, priority]);

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleSearch = async (event) => {
    event.preventDefault();

    setCurrentPage(1);
    await fetchQueries(1);
  };

  const handleStatusFilterChange = (event) => {
    setStatus(event.target.value);
    setCurrentPage(1);
  };

  const handlePriorityChange = (event) => {
    setPriority(event.target.value);
    setCurrentPage(1);
  };

  const handlePageSizeChange = (event) => {
    setPageSize(Number(event.target.value));
    setCurrentPage(1);
  };

  const handlePreviousPage = () => {
    if (currentPage > 1) {
      setCurrentPage((page) => page - 1);
    }
  };

  const handleNextPage = () => {
    if (currentPage < totalPages) {
      setCurrentPage((page) => page + 1);
    }
  };

  const getUserName = (userId) => {
    if (!userId) {
      return "-";
    }

    const user = users.find((item) => item.id === userId);

    if (!user) {
      return userId;
    }

    const fullName = `${user.first_name || ""} ${user.last_name || ""
      }`.trim();

    return fullName || user.username || user.email || userId;
  };

  const getStatusClass = (queryStatus) => {
    return `manage-query-status ${queryStatus
      ?.toLowerCase()
      .replace("_", "-")}`;
  };

  const getPriorityClass = (queryPriority) => {
    return `manage-query-priority ${queryPriority?.toLowerCase()}`;
  };

  const formatStatus = (value) => {
    if (!value) {
      return "-";
    }

    return value.replace("_", " ");
  };

  const formatDateTime = (value) => {
    if (!value) {
      return "-";
    }

    return new Date(value).toLocaleString();
  };

  const getAssignedTime = (query, activityList = []) => {
    if (query?.assigned_at) {
      return formatDateTime(query.assigned_at);
    }
    const act = activityList.find(
      (a) =>
        a.activity_type === "ASSIGNED" ||
        a.description?.toLowerCase().includes("assigned")
    );
    if (act?.created_at) {
      return formatDateTime(act.created_at);
    }
    return null;
  };

  const getResolvedTime = (query, activityList = []) => {
    if (query?.resolved_at) {
      return formatDateTime(query.resolved_at);
    }
    const act = activityList.find(
      (a) =>
        a.activity_type === "RESOLVED" ||
        a.description?.toLowerCase().includes("resolved")
    );
    if (act?.created_at) {
      return formatDateTime(act.created_at);
    }
    return null;
  };

  const getClosedTime = (query, activityList = []) => {
    if (query?.closed_at) {
      return formatDateTime(query.closed_at);
    }
    const act = activityList.find(
      (a) =>
        a.activity_type === "CLOSED" ||
        a.description?.toLowerCase().includes("closed")
    );
    if (act?.created_at) {
      return formatDateTime(act.created_at);
    }
    return null;
  };

  const openDetails = async (query) => {
    setSelectedQuery(query);
    setShowDetails(true);

    setSelectedAssignee(query.assigned_to || "");
    setSelectedStatus(query.status || "");
    setResolutionNote("");

    setActionError("");
    setActionSuccess("");

    await fetchActivities(query.id);
  };

  const closeDetails = () => {
    if (actionLoading) {
      return;
    }

    setShowDetails(false);
    setSelectedQuery(null);
    setActivities([]);
    setResolutionNote("");
    setActionError("");
    setActionSuccess("");
  };

  const refreshSelectedQuery = async (queryId, directData = null) => {
    let updatedQuery = directData;

    if (!updatedQuery) {
      const response = await axios.get(
        `${BASE_API_URL}/api/queries/${queryId}`,
        getAuthConfig()
      );
      updatedQuery = response.data;
    }

    setSelectedQuery(updatedQuery);
    setSelectedAssignee(updatedQuery.assigned_to || "");
    setSelectedStatus(updatedQuery.status || "");

    await fetchActivities(queryId);
    await fetchQueries(currentPage);
    await fetchDashboardStats();

    return updatedQuery;
  };

  const handleAssign = async () => {
    if (!selectedQuery) {
      return;
    }

    if (!selectedAssignee) {
      setActionError("Please select a user to assign the query.");
      return;
    }

    try {
      setActionLoading(true);
      setActionError("");
      setActionSuccess("");

      const res = await axios.patch(
        `${BASE_API_URL}/api/queries/${selectedQuery.id}/assign`,
        {
          assigned_to: selectedAssignee,
        },
        getAuthConfig()
      );

      await refreshSelectedQuery(selectedQuery.id, res.data);

      setActionSuccess("Query assigned successfully.");
    } catch (err) {
      console.error("Failed to assign query:", err);

      setActionError(
        err.response?.data?.detail ||
        "Unable to assign the query. Please try again."
      );
    } finally {
      setActionLoading(false);
    }
  };

  const handleStatusUpdate = async () => {
    if (!selectedQuery) {
      return;
    }

    if (!selectedStatus) {
      setActionError("Please select a status.");
      return;
    }

    if (selectedStatus === selectedQuery.status) {
      setActionError("Please select a different status.");
      return;
    }

    try {
      setActionLoading(true);
      setActionError("");
      setActionSuccess("");

      const res = await axios.patch(
        `${BASE_API_URL}/api/queries/${selectedQuery.id}/status`,
        {
          status: selectedStatus,
        },
        getAuthConfig()
      );

      const nowIso = new Date().toISOString();
      const updatedItem = {
        ...res.data,
        status: selectedStatus,
        closed_at: selectedStatus === "CLOSED" ? (res.data.closed_at || nowIso) : res.data.closed_at,
        resolved_at: selectedStatus === "RESOLVED" ? (res.data.resolved_at || nowIso) : res.data.resolved_at,
      };

      await refreshSelectedQuery(selectedQuery.id, updatedItem);

      setActionSuccess("Query status updated successfully.");
    } catch (err) {
      console.error("Failed to update query status:", err);

      setActionError(
        err.response?.data?.detail ||
        "Unable to update the query status. Please try again."
      );
    } finally {
      setActionLoading(false);
    }
  };

  const handleResolve = async () => {
    if (!selectedQuery) {
      return;
    }

    if (!resolutionNote.trim()) {
      setActionError("Please enter a resolution note.");
      return;
    }

    try {
      setActionLoading(true);
      setActionError("");
      setActionSuccess("");

      const res = await axios.patch(
        `${BASE_API_URL}/api/queries/${selectedQuery.id}/resolve`,
        {
          resolution_note: resolutionNote.trim(),
        },
        getAuthConfig()
      );

      setResolutionNote("");

      const nowIso = new Date().toISOString();
      const updatedItem = {
        ...res.data,
        status: "RESOLVED",
        resolved_at: res.data.resolved_at || nowIso,
      };

      await refreshSelectedQuery(selectedQuery.id, updatedItem);

      setActionSuccess("Query resolved successfully.");
    } catch (err) {
      console.error("Failed to resolve query:", err);

      setActionError(
        err.response?.data?.detail ||
        "Unable to resolve the query. Please try again."
      );
    } finally {
      setActionLoading(false);
    }
  };

  const handleCloseQuery = async () => {
    if (!selectedQuery) {
      return;
    }

    try {
      setActionLoading(true);
      setActionError("");
      setActionSuccess("");

      const res = await axios.patch(
        `${BASE_API_URL}/api/queries/${selectedQuery.id}/close`,
        {},
        getAuthConfig()
      );

      const nowIso = new Date().toISOString();
      const updatedItem = {
        ...res.data,
        status: "CLOSED",
        closed_at: res.data.closed_at || nowIso,
      };

      await refreshSelectedQuery(selectedQuery.id, updatedItem);

      setActionSuccess("Query closed successfully.");
    } catch (err) {
      console.error("Failed to close query:", err);

      setActionError(
        err.response?.data?.detail ||
        "Unable to close the query. Please try again."
      );
    } finally {
      setActionLoading(false);
    }
  };

  const getActivityClass = (activityType) => {
    return `manage-query-activity-type ${activityType
      ?.toLowerCase()
      .replace("_", "-")}`;
  };

  return (
    <div className="manage-query-page">
      <div className="manage-query-header">
        <div>
          <h1>Manage Query</h1>
          <p>View and manage employee queries and status breakdown.</p>
        </div>

        <div className="manage-query-stats-grid">
          <div className="manage-query-stat-card total">
            <span className="stat-label">Total Queries</span>
            <strong className="stat-value">{stats.total || totalQueries}</strong>
          </div>

          <div className="manage-query-stat-card pending">
            <span className="stat-label">Pending</span>
            <strong className="stat-value">{stats.pending}</strong>
          </div>

          <div className="manage-query-stat-card resolved">
            <span className="stat-label">Resolved</span>
            <strong className="stat-value">{stats.resolved}</strong>
          </div>

          <div className="manage-query-stat-card closed">
            <span className="stat-label">Closed</span>
            <strong className="stat-value">{stats.closed}</strong>
          </div>
        </div>
      </div>

      <div className="manage-query-filters">
        <form
          className="manage-query-search"
          onSubmit={handleSearch}
        >
          <input
            type="text"
            placeholder="Search queries..."
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />

          <button type="submit">
            Search
          </button>
        </form>

        <div className="manage-query-filter">
          <label htmlFor="query-status">
            Status
          </label>

          <select
            id="query-status"
            value={status}
            onChange={handleStatusFilterChange}
          >
            {STATUS_OPTIONS.map((option) => (
              <option
                key={option}
                value={option}
              >
                {formatStatus(option)}
              </option>
            ))}
          </select>
        </div>

        <div className="manage-query-filter">
          <label htmlFor="query-priority">
            Priority
          </label>

          <select
            id="query-priority"
            value={priority}
            onChange={handlePriorityChange}
          >
            {PRIORITY_OPTIONS.map((option) => (
              <option
                key={option}
                value={option}
              >
                {option}
              </option>
            ))}
          </select>
        </div>
      </div>

      {error && (
        <div className="manage-query-error">
          {error}
        </div>
      )}

      <div className="manage-query-table-container">
        {loading ? (
          <div className="manage-query-loading">
            Loading queries...
          </div>
        ) : queries.length === 0 ? (
          <div className="manage-query-empty">
            No queries found.
          </div>
        ) : (
          <table className="manage-query-table">
            <thead>
              <tr>
                <th>Ticket</th>
                <th>Subject</th>
                <th>Raised By</th>
                <th>Priority</th>
                <th>Status</th>
                <th>Submitted</th>
                <th>Assigned To</th>
                <th>Action</th>
              </tr>
            </thead>

            <tbody>
              {queries.map((query) => (
                <tr key={query.id}>
                  <td>
                    <span className="manage-query-ticket">
                      {query.ticket_number || "-"}
                    </span>
                  </td>

                  <td>
                    <div className="manage-query-subject">
                      {query.subject}
                    </div>

                    <div className="manage-query-message">
                      {query.message}
                    </div>
                  </td>

                  <td>
                    {getUserName(query.user_id)}
                  </td>

                  <td>
                    <span
                      className={getPriorityClass(query.priority)}
                    >
                      {query.priority}
                    </span>
                  </td>

                  <td>
                    <span
                      className={getStatusClass(query.status)}
                    >
                      {formatStatus(query.status)}
                    </span>
                  </td>

                  <td>
                    {query.submitted_at
                      ? new Date(
                        query.submitted_at
                      ).toLocaleDateString()
                      : "-"}
                  </td>

                  <td>
                    {getUserName(query.assigned_to)}
                  </td>

                  <td>
                    <button
                      type="button"
                      className="manage-query-view-button"
                      onClick={() => openDetails(query)}
                    >
                      View
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div className="manage-query-pagination">
        <div className="manage-query-page-size">
          <span>Rows per page:</span>

          <select
            value={pageSize}
            onChange={handlePageSizeChange}
          >
            <option value={10}>10</option>
            <option value={20}>20</option>
            <option value={30}>30</option>
            <option value={50}>50</option>
          </select>
        </div>

        <div className="manage-query-page-controls">
          <span>
            Page {currentPage} of {totalPages}
          </span>

          <button
            type="button"
            onClick={handlePreviousPage}
            disabled={currentPage === 1}
          >
            Previous
          </button>

          <button
            type="button"
            onClick={handleNextPage}
            disabled={currentPage === totalPages}
          >
            Next
          </button>
        </div>
      </div>

      {showDetails && selectedQuery && (
        <div
          className="manage-query-modal-overlay"
          onClick={closeDetails}
        >
          <div
            className="manage-query-modal"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="manage-query-modal-header">
              <div>
                <span className="manage-query-modal-ticket">
                  {selectedQuery.ticket_number || "Query"}
                </span>

                <h2>{selectedQuery.subject}</h2>
              </div>

              <button
                type="button"
                className="manage-query-modal-close"
                onClick={closeDetails}
                disabled={actionLoading}
                aria-label="Close details"
              >
                ×
              </button>
            </div>

            <div className="manage-query-modal-body">
              <div className="manage-query-detail-grid">
                <div className="manage-query-detail-item">
                  <span>Priority</span>

                  <strong>
                    <span
                      className={getPriorityClass(
                        selectedQuery.priority
                      )}
                    >
                      {selectedQuery.priority}
                    </span>
                  </strong>
                </div>

                <div className="manage-query-detail-item">
                  <span>Current Status</span>

                  <strong>
                    <span
                      className={getStatusClass(
                        selectedQuery.status
                      )}
                    >
                      {formatStatus(selectedQuery.status)}
                    </span>
                  </strong>
                </div>

                <div className="manage-query-detail-item">
                  <span>Raised By</span>
                  <strong>
                    {getUserName(selectedQuery.user_id)}
                  </strong>
                </div>

                <div className="manage-query-detail-item">
                  <span>Assigned To</span>
                  <strong>
                    {getUserName(selectedQuery.assigned_to)}
                  </strong>
                </div>
              </div>

              {/* Consolidated Status Timings Box */}
              <div className="manage-query-lifecycle-box">
                <div className="lifecycle-header">
                  <h3>Status Timings & Lifecycle Progress</h3>
                  <span
                    className={getStatusClass(selectedQuery.status)}
                  >
                    {formatStatus(selectedQuery.status)}
                  </span>
                </div>

                <div className="lifecycle-timeline">
                  {/* Step 1: Submitted */}
                  <div className="timeline-step active">
                    <div className="step-indicator">1</div>
                    <div className="step-info">
                      <span className="step-title">Submitted</span>
                      <span className="step-time">
                        {formatDateTime(selectedQuery.submitted_at)}
                      </span>
                    </div>
                  </div>

                  {/* Step 2: Assigned / In Progress */}
                  <div
                    className={`timeline-step ${selectedQuery.assigned_to ||
                        selectedQuery.status !== "OPEN"
                        ? "active"
                        : ""
                      }`}
                  >
                    <div className="step-indicator">2</div>
                    <div className="step-info">
                      <span className="step-title">Assigned / In Progress</span>
                      <span className="step-time">
                        {getAssignedTime(selectedQuery, activities) ||
                          (selectedQuery.assigned_to
                            ? "Assigned"
                            : "Pending Assignment")}
                      </span>
                    </div>
                  </div>

                  {/* Step 3: Resolved */}
                  <div
                    className={`timeline-step ${selectedQuery.status === "RESOLVED" ||
                        selectedQuery.status === "CLOSED" ||
                        selectedQuery.resolved_at ||
                        getResolvedTime(selectedQuery, activities)
                        ? "active"
                        : ""
                      }`}
                  >
                    <div className="step-indicator">3</div>
                    <div className="step-info">
                      <span className="step-title">Resolved</span>
                      <span className="step-time">
                        {getResolvedTime(selectedQuery, activities) ||
                          "Pending Resolution"}
                      </span>
                    </div>
                  </div>

                  {/* Step 4: Closed */}
                  <div
                    className={`timeline-step ${selectedQuery.status === "CLOSED" ||
                        selectedQuery.closed_at ||
                        getClosedTime(selectedQuery, activities)
                        ? "active"
                        : ""
                      }`}
                  >
                    <div className="step-indicator">4</div>
                    <div className="step-info">
                      <span className="step-title">Closed</span>
                      <span className="step-time">
                        {getClosedTime(selectedQuery, activities) ||
                          "Pending Closure"}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="manage-query-message-section">
                <h3>Query Description</h3>

                <div className="manage-query-full-message">
                  {selectedQuery.message}
                </div>
              </div>

              {selectedQuery.resolution_note && (
                <div className="manage-query-resolution-display-section">
                  <h3>Resolution Note</h3>
                  <div className="manage-query-resolution-display-box">
                    {selectedQuery.resolution_note}
                  </div>
                </div>
              )}

              <div className="manage-query-actions-section">
                <h3>Query Management</h3>

                <div className="manage-query-action-grid">
                  <div className="manage-query-action-group">
                    <label htmlFor="query-assignee">
                      Assign To
                    </label>

                    <div className="manage-query-action-row">
                      <select
                        id="query-assignee"
                        value={selectedAssignee}
                        onChange={(event) =>
                          setSelectedAssignee(
                            event.target.value
                          )
                        }
                        disabled={
                          usersLoading || actionLoading
                        }
                      >
                        <option value="">
                          Select user
                        </option>

                        {users.map((user) => {
                          const fullName =
                            `${user.first_name || ""} ${user.last_name || ""
                              }`.trim();

                          return (
                            <option
                              key={user.id}
                              value={user.id}
                            >
                              {fullName ||
                                user.username ||
                                user.email}
                            </option>
                          );
                        })}
                      </select>

                      <button
                        type="button"
                        onClick={handleAssign}
                        disabled={actionLoading}
                      >
                        Assign
                      </button>
                    </div>
                  </div>

                  <div className="manage-query-action-group">
                    <label htmlFor="query-status-update">
                      Update Status
                    </label>

                    <div className="manage-query-action-row">
                      <select
                        id="query-status-update"
                        value={selectedStatus}
                        onChange={(event) =>
                          setSelectedStatus(
                            event.target.value
                          )
                        }
                        disabled={actionLoading}
                      >
                        {STATUS_OPTIONS.filter(
                          (option) => option !== "ALL"
                        ).map((option) => (
                          <option
                            key={option}
                            value={option}
                          >
                            {formatStatus(option)}
                          </option>
                        ))}
                      </select>

                      <button
                        type="button"
                        onClick={handleStatusUpdate}
                        disabled={actionLoading}
                      >
                        Update
                      </button>
                    </div>
                  </div>
                </div>

                <div className="manage-query-resolution">
                  <label htmlFor="resolution-note">
                    Resolution Note
                  </label>

                  <textarea
                    id="resolution-note"
                    placeholder="Enter resolution details..."
                    value={resolutionNote}
                    onChange={(event) =>
                      setResolutionNote(event.target.value)
                    }
                    disabled={
                      actionLoading ||
                      selectedQuery.status === "CLOSED"
                    }
                    rows={4}
                  />

                  <button
                    type="button"
                    className="manage-query-resolve-button"
                    onClick={handleResolve}
                    disabled={
                      actionLoading ||
                      selectedQuery.status === "CLOSED"
                    }
                  >
                    Resolve Query
                  </button>
                </div>

                <div className="manage-query-close-action">
                  <button
                    type="button"
                    className="manage-query-close-query-button"
                    onClick={handleCloseQuery}
                    disabled={
                      actionLoading ||
                      selectedQuery.status === "CLOSED"
                    }
                  >
                    Close Query
                  </button>
                </div>

                {actionError && (
                  <div className="manage-query-action-error">
                    {actionError}
                  </div>
                )}

                {actionSuccess && (
                  <div className="manage-query-action-success">
                    {actionSuccess}
                  </div>
                )}
              </div>

              <div className="manage-query-activity-section">
                <div className="manage-query-activity-header">
                  <h3>Activity History</h3>
                </div>

                {activityLoading ? (
                  <div className="manage-query-activity-loading">
                    Loading activity...
                  </div>
                ) : activities.length === 0 ? (
                  <div className="manage-query-activity-empty">
                    No activity history found.
                  </div>
                ) : (
                  <div className="manage-query-activity-list">
                    {activities.map((activity) => (
                      <div
                        className="manage-query-activity-item"
                        key={activity.id}
                      >
                        <div className="manage-query-activity-icon">
                          {activity.activity_type
                            ?.charAt(0) || "•"}
                        </div>

                        <div className="manage-query-activity-content">
                          <div className="manage-query-activity-top">
                            <span
                              className={getActivityClass(
                                activity.activity_type
                              )}
                            >
                              {formatStatus(
                                activity.activity_type
                              )}
                            </span>

                            <span className="manage-query-activity-date">
                              {formatDateTime(
                                activity.created_at
                              )}
                            </span>
                          </div>

                          <p>
                            {activity.description}
                          </p>

                          <span className="manage-query-activity-user">
                            By:{" "}
                            {getUserName(
                              activity.performed_by
                            )}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ManageQuery;