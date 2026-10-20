import { useEffect, useState } from "react";
import "./RaiseQuery.css";
import { API_URL } from "../Config/ApiEndpoint";
const BASE_API_URL =
   API_URL || process.env.REACT_APP_API_URL || "http://127.0.0.1:8000";

function RaiseQuery() {
    const [formData, setFormData] = useState({
        subject: "",
        message: "",
        category: "OKR Data Issue",
        priority: "MEDIUM",
    });

    const [recentQueries, setRecentQueries] = useState([]);
    const [users, setUsers] = useState([]);

    const [currentPage, setCurrentPage] = useState(1);
    const [pageSize, setPageSize] = useState(10);

    const [totalQueries, setTotalQueries] = useState(0);
    const [completedQueries, setCompletedQueries] = useState(0);
    const [pendingQueries, setPendingQueries] = useState(0);
    const [totalPages, setTotalPages] = useState(1);

    const [isLoadingQueries, setIsLoadingQueries] = useState(true);
    const [queryListError, setQueryListError] = useState("");

    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState("");

    // Query Details
    const [selectedQuery, setSelectedQuery] = useState(null);
    const [isLoadingDetails, setIsLoadingDetails] = useState(false);
    const [detailsError, setDetailsError] = useState("");

    const fetchUsers = async () => {
        try {
            const token = localStorage.getItem("token");
            const res = await fetch(`${BASE_API_URL}/api/users/?page=1&size=100`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            const data = await res.json();
            setUsers(data.data || data.items || (Array.isArray(data) ? data : []));
        } catch (err) {
            console.error("Failed to fetch users in RaiseQuery:", err);
        }
    };

    useEffect(() => {
        fetchUsers();
    }, []);

    const getUserName = (userId) => {
        if (!userId) return "Not assigned";
        const user = users.find((u) => u.id === userId);
        if (!user) return userId;
        const fullName = `${user.first_name || ""} ${user.last_name || ""}`.trim();
        return fullName || user.username || user.email || userId;
    };

    const fetchQueries = async () => {
        try {
            setIsLoadingQueries(true);
            setQueryListError("");

            const token = localStorage.getItem("token");

            const response = await fetch(
                `${BASE_API_URL}/api/queries/my`,
                {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                }
            );

            const data = await response.json();

            if (!response.ok) {
                throw new Error(
                    typeof data.detail === "string"
                        ? data.detail
                        : JSON.stringify(data.detail || data)
                );
            }
            
            console.log("queries set to ",data);
            setRecentQueries(data.items || []);
            setTotalQueries(data.total || 0);
            setTotalPages(data.total_pages || 1);

            /*
             * RESOLVED + CLOSED = Completed
             */
            const completedStatuses = await Promise.all([
                fetch(
                    `${BASE_API_URL}/api/queries/my?status=RESOLVED&page=1&page_size=1`,
                    {
                        headers: {
                            Authorization: `Bearer ${token}`,
                        },
                    }
                ),
                fetch(
                    `${BASE_API_URL}/api/queries/my?status=CLOSED&page=1&page_size=1`,
                    {
                        headers: {
                            Authorization: `Bearer ${token}`,
                        },
                    }
                ),
            ]);

            const completedData = await Promise.all(
                completedStatuses.map((res) => res.json())
            );

            const resolvedCount =
                completedData[0].total || 0;

            const closedCount =
                completedData[1].total || 0;

            setCompletedQueries(
                resolvedCount + closedCount
            );

            /*
             * OPEN + IN_PROGRESS + REOPENED = Pending
             */
            const pendingStatuses = await Promise.all([
                fetch(
                    `${BASE_API_URL}/api/queries/my?status=OPEN&page=1&page_size=1`,
                    {
                        headers: {
                            Authorization: `Bearer ${token}`,
                        },
                    }
                ),
                fetch(
                    `${BASE_API_URL}/api/queries/my?status=IN_PROGRESS&page=1&page_size=1`,
                    {
                        headers: {
                            Authorization: `Bearer ${token}`,
                        },
                    }
                ),
                fetch(
                    `${BASE_API_URL}/api/queries/my?status=REOPENED&page=1&page_size=1`,
                    {
                        headers: {
                            Authorization: `Bearer ${token}`,
                        },
                    }
                ),
            ]);

            const pendingData = await Promise.all(
                pendingStatuses.map((res) => res.json())
            );

            const openCount =
                pendingData[0].total || 0;

            const inProgressCount =
                pendingData[1].total || 0;

            const reopenedCount =
                pendingData[2].total || 0;

            setPendingQueries(
                openCount +
                inProgressCount +
                reopenedCount
            );
        } catch (err) {
            console.error(
                "Error fetching queries:",
                err
            );

            setQueryListError(
                err.message ||
                "Failed to load queries."
            );
        } finally {
            setIsLoadingQueries(false);
        }
    };

    useEffect(() => {
        fetchQueries();
    }, [currentPage, pageSize]);

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (
            !formData.subject.trim() ||
            !formData.message.trim()
        ) {
            setError(
                "Subject and message are required."
            );
            return;
        }

        setIsSubmitting(true);
        setError("");

        try {
            const token = localStorage.getItem("token");

            const response = await fetch(
                `${BASE_API_URL}/api/queries/`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        Authorization: `Bearer ${token}`,
                    },
                    body: JSON.stringify({
                        subject:
                            formData.subject.trim(),
                        message:
                            formData.message.trim(),
                        priority:
                            formData.priority,
                    }),
                }
            );

            const data = await response.json();

            if (!response.ok) {
                throw new Error(
                    typeof data.detail === "string"
                        ? data.detail
                        : JSON.stringify(
                            data.detail || data
                        )
                );
            }

            if (currentPage === 1) {
                await fetchQueries();
            } else {
                setCurrentPage(1);
            }

            setFormData({
                subject: "",
                message: "",
                category: "OKR Data Issue",
                priority: "MEDIUM",
            });
        } catch (err) {
            console.error(
                "Error submitting query:",
                err
            );

            setError(
                err.message ||
                "Failed to submit query."
            );
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleClear = () => {
        setFormData({
            subject: "",
            message: "",
            category: "OKR Data Issue",
            priority: "MEDIUM",
        });

        setError("");
    };

    const handleChange = (e) => {
        const { id, value } = e.target;

        setFormData((prev) => ({
            ...prev,
            [id]: value,
        }));

        setError("");
    };

    const formatStatus = (status) => {
        if (!status) {
            return "";
        }

        return status
            .replace(/_/g, " ")
            .replace(
                /\b\w/g,
                (char) => char.toUpperCase()
            );
    };

    const getStatusClass = (status) => {
        if (!status) {
            return "";
        }

        return status
            .toLowerCase()
            .replace(/_/g, "-");
    };

    const formatDate = (date) => {
        if (!date) {
            return "";
        }

        return new Date(date).toLocaleDateString(
            "en-GB",
            {
                day: "2-digit",
                month: "short",
                year: "numeric",
            }
        );
    };

    const formatDateTime = (date) => {
        if (!date) {
            return "Not available";
        }

        return new Date(date).toLocaleString(
            "en-GB",
            {
                day: "2-digit",
                month: "short",
                year: "numeric",
                hour: "2-digit",
                minute: "2-digit",
            }
        );
    };

    const getMessagePreview = (message) => {
        if (!message) {
            return "No message provided.";
        }

        const maxLength = 100;

        if (message.length <= maxLength) {
            return message;
        }

        return `${message
            .substring(0, maxLength)
            .trim()}...`;
    };

    /*
     * Fetch complete query details.
     */
    const handleQueryClick = async (query) => {
        try {
            setSelectedQuery(null);
            setDetailsError("");
            setIsLoadingDetails(true);

            const token =
                localStorage.getItem("token");

            const response = await fetch(
                `${BASE_API_URL}/api/queries/${query.id}`,
                {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                }
            );

            const data = await response.json();

            if (!response.ok) {
                throw new Error(
                    typeof data.detail === "string"
                        ? data.detail
                        : JSON.stringify(
                            data.detail || data
                        )
                );
            }

            setSelectedQuery(data);
        } catch (err) {
            console.error(
                "Error fetching query details:",
                err
            );

            setDetailsError(
                err.message ||
                "Failed to load query details."
            );
        } finally {
            setIsLoadingDetails(false);
        }
    };

    const handleCloseDetails = () => {
        setSelectedQuery(null);
        setDetailsError("");
        setIsLoadingDetails(false);
    };

    const handleQueryKeyDown = (e, query) => {
        if (
            e.key === "Enter" ||
            e.key === " "
        ) {
            e.preventDefault();
            handleQueryClick(query);
        }
    };

    const handlePageSizeChange = (e) => {
        setPageSize(
            Number(e.target.value)
        );
        setCurrentPage(1);
    };

    const handlePreviousPage = () => {
        if (currentPage > 1) {
            setCurrentPage(
                (page) => page - 1
            );
        }
    };

    const handleNextPage = () => {
        if (currentPage < totalPages) {
            setCurrentPage(
                (page) => page + 1
            );
        }
    };

    return (
        <div className="raise-query-page">
            <div className="raise-query-layout">

                {/* LEFT: Raise Query Form */}
                <div className="raise-query-card">

                    <div className="raise-query-header">
                        <h1>Raise a Query</h1>

                        <p>
                            Submit any issues or questions
                            to the admin team
                        </p>
                    </div>

                    <form
                        className="raise-query-form"
                        onSubmit={handleSubmit}
                    >

                        <div className="form-group">
                            <label htmlFor="subject">
                                Subject
                            </label>

                            <input
                                id="subject"
                                type="text"
                                placeholder="Enter query subject..."
                                value={formData.subject}
                                onChange={handleChange}
                            />
                        </div>

                        <div className="form-group">
                            <label htmlFor="message">
                                Message
                            </label>

                            <textarea
                                id="message"
                                rows="5"
                                placeholder="Describe your query in detail..."
                                value={formData.message}
                                onChange={handleChange}
                            />
                        </div>

                        <div className="form-row">

                            <div className="form-group">
                                <label htmlFor="category">
                                    Category
                                </label>

                                <select
                                    id="category"
                                    value={
                                        formData.category
                                    }
                                    onChange={
                                        handleChange
                                    }
                                >
                                    <option value="OKR Data Issue">
                                        OKR Data Issue
                                    </option>

                                    <option value="Performance Score Query">
                                        Performance Score Query
                                    </option>

                                    <option value="Access Problem">
                                        Access Problem
                                    </option>

                                    <option value="Award Clarification">
                                        Award Clarification
                                    </option>

                                    <option value="Other">
                                        Other
                                    </option>
                                </select>
                            </div>

                            <div className="form-group">
                                <label htmlFor="priority">
                                    Priority
                                </label>

                                <select
                                    id="priority"
                                    value={
                                        formData.priority
                                    }
                                    onChange={
                                        handleChange
                                    }
                                >
                                    <option value="LOW">
                                        Low
                                    </option>

                                    <option value="MEDIUM">
                                        Medium
                                    </option>

                                    <option value="HIGH">
                                        High
                                    </option>

                                    <option value="URGENT">
                                        Urgent
                                    </option>
                                </select>
                            </div>

                        </div>

                        {error && (
                            <div className="query-error">
                                {error}
                            </div>
                        )}

                        <div className="raise-query-actions">

                            <button
                                type="button"
                                className="query-clear-btn"
                                onClick={handleClear}
                                disabled={isSubmitting}
                            >
                                Clear
                            </button>

                            <button
                                type="submit"
                                className="query-submit-btn"
                                disabled={isSubmitting}
                            >
                                {isSubmitting
                                    ? "Submitting..."
                                    : "Submit Query"}
                            </button>

                        </div>

                    </form>
                </div>

                {/* RIGHT: My Queries */}
                <div className="my-queries-panel">

                    {/* Statistics */}
                    <div className="query-stats">

                        <div className="query-stat-card">
                            <span className="query-stat-label">
                                Total Queries
                            </span>

                            <span className="query-stat-value">
                                {totalQueries}
                            </span>
                        </div>

                        <div className="query-stat-card">
                            <span className="query-stat-label">
                                Completed
                            </span>

                            <span className="query-stat-value">
                                {completedQueries}
                            </span>
                        </div>

                        <div className="query-stat-card">
                            <span className="query-stat-label">
                                Pending
                            </span>

                            <span className="query-stat-value">
                                {pendingQueries}
                            </span>
                        </div>

                    </div>

                    {/* My Queries */}
                    <div className="recent-queries-section">

                        <div className="recent-queries-header">
                            <h2>My Queries</h2>
                        </div>

                        <div className="recent-queries-list">

                            {isLoadingQueries && (
                                <p>
                                    Loading queries...
                                </p>
                            )}

                            {!isLoadingQueries &&
                                queryListError && (
                                    <p>
                                        {queryListError}
                                    </p>
                                )}

                            {!isLoadingQueries &&
                                !queryListError &&
                                recentQueries.length === 0 && (
                                    <p>
                                        No queries found.
                                    </p>
                                )}

                            {!isLoadingQueries &&
                                !queryListError &&
                                recentQueries.map(
                                    (query) => (
                                        <div
                                            className="recent-query-card"
                                            key={query.id}
                                            role="button"
                                            tabIndex={0}
                                            onClick={() =>
                                                handleQueryClick(
                                                    query
                                                )
                                            }
                                            onKeyDown={(e) =>
                                                handleQueryKeyDown(
                                                    e,
                                                    query
                                                )
                                            }
                                            aria-label={`View details for ${query.subject}`}
                                        >
                                            <div className="recent-query-top">

                                                <h3>
                                                    {
                                                        query.subject
                                                    }
                                                </h3>

                                                <span
                                                    className={`query-status ${getStatusClass(
                                                        query.status
                                                    )}`}
                                                >
                                                    {formatStatus(
                                                        query.status
                                                    )}
                                                </span>

                                            </div>

                                            <p className="recent-query-message">
                                                {getMessagePreview(
                                                    query.message
                                                )}
                                            </p>

                                            <p className="recent-query-meta">
                                                Submitted{" "}
                                                {formatDate(
                                                    query.submitted_at
                                                )}
                                            </p>

                                        </div>
                                    )
                                )}

                        </div>

                        {/* Pagination */}
                        {!isLoadingQueries &&
                            !queryListError &&
                            totalQueries > 0 && (
                                <div className="query-pagination">

                                    <div className="query-page-size">
                                        <span>
                                            Rows per page:
                                        </span>

                                        <select
                                            value={
                                                pageSize
                                            }
                                            onChange={
                                                handlePageSizeChange
                                            }
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

                                    <div className="query-pagination-controls">

                                        <button
                                            type="button"
                                            onClick={
                                                handlePreviousPage
                                            }
                                            disabled={
                                                currentPage ===
                                                1
                                            }
                                        >
                                            Previous
                                        </button>

                                        <span>
                                            Page{" "}
                                            {currentPage}{" "}
                                            of{" "}
                                            {totalPages}
                                        </span>

                                        <button
                                            type="button"
                                            onClick={
                                                handleNextPage
                                            }
                                            disabled={
                                                currentPage ===
                                                totalPages
                                            }
                                        >
                                            Next
                                        </button>

                                    </div>

                                </div>
                            )}

                    </div>
                </div>
            </div>

            {/* Query Details Modal */}
            {(isLoadingDetails ||
                detailsError ||
                selectedQuery) && (
                    <div
                        className="query-details-overlay"
                        onClick={handleCloseDetails}
                    >
                        <div
                            className="query-details-modal"
                            onClick={(e) =>
                                e.stopPropagation()
                            }
                        >

                            <div className="query-details-header">
                                <h2>Query Details</h2>

                                <button
                                    type="button"
                                    className="query-details-close"
                                    onClick={
                                        handleCloseDetails
                                    }
                                    aria-label="Close query details"
                                >
                                    ×
                                </button>
                            </div>

                            {isLoadingDetails && (
                                <div className="query-details-loading">
                                    Loading query details...
                                </div>
                            )}

                            {!isLoadingDetails &&
                                detailsError && (
                                    <div className="query-details-error">
                                        {detailsError}
                                    </div>
                                )}

                            {!isLoadingDetails &&
                                !detailsError &&
                                selectedQuery && (
                                    <div className="query-details-body">

                                        {/* Status + Priority */}
                                        <div className="query-details-status-row">

                                            <span
                                                className={`query-status ${getStatusClass(
                                                    selectedQuery.status
                                                )}`}
                                            >
                                                {formatStatus(
                                                    selectedQuery.status
                                                )}
                                            </span>

                                            <span
                                                className={`query-priority ${getStatusClass(
                                                    selectedQuery.priority
                                                )}`}
                                            >
                                                {formatStatus(
                                                    selectedQuery.priority
                                                )}
                                            </span>

                                        </div>

                                        {/* Subject + Message */}
                                        <div className="query-details-content">

                                            <div className="query-detail-box">
                                                <span className="query-detail-label">
                                                    Subject
                                                </span>

                                                <h3>
                                                    {
                                                        selectedQuery.subject
                                                    }
                                                </h3>
                                            </div>

                                            <div className="query-detail-box query-message-box">
                                                <span className="query-detail-label">
                                                    Message
                                                </span>

                                                <div className="query-details-message">
                                                    {
                                                        selectedQuery.message ||
                                                        "No message provided."
                                                    }
                                                </div>
                                            </div>

                                        </div>

                                        {/* Useful Employee Information */}
                                        <div className="query-details-grid">

                                            <div className="query-detail-field">
                                                <label>
                                                    Submitted
                                                </label>

                                                <span>
                                                    {formatDateTime(
                                                        selectedQuery.submitted_at
                                                    )}
                                                </span>
                                            </div>

                                            <div className="query-detail-field">
                                                <label>
                                                    Assigned To
                                                </label>

                                                <span>
                                                    {getUserName(selectedQuery.assigned_to)}
                                                </span>
                                            </div>

                                        </div>

                                        {selectedQuery.resolution_note && (
                                            <div className="query-detail-box query-resolution-box" style={{ marginTop: "14px" }}>
                                                <span className="query-detail-label">
                                                    Resolution Note
                                                </span>

                                                <div className="query-details-message" style={{ background: "var(--bg3)", padding: "12px", borderRadius: "8px", border: "1px solid var(--border)", marginTop: "6px" }}>
                                                    {selectedQuery.resolution_note}
                                                </div>
                                            </div>
                                        )}

                                    </div>
                                )}

                            <div className="query-details-footer">

                                <button
                                    type="button"
                                    className="query-details-close-btn"
                                    onClick={
                                        handleCloseDetails
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

export default RaiseQuery;