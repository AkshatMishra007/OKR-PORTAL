import React, { useState, useEffect } from "react";
import { Trash2, Trash } from "lucide-react";
import "./Users.css";
import { API_URL } from "../Config/ApiEndpoint";

function Users() {
  const [users, setUsers] = useState({
    data: [],
    page: 1,
    size: 10,
    total: 0,
  });

  const [userOrganization, setUserOrganization] = useState("");
  const [userOrganizationName, setUserOrganizationName] = useState("");
  const [selectedOrganizationFilter, setSelectedOrganizationFilter] =
    useState("");
  const [searchValue, setSearchValue] = useState("");

  const [organizationOptions, setOrganizationOptions] = useState([]);
  const [roleOptions, setRoleOptions] = useState([]);

  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  const [showAddUser, setShowAddUser] = useState(false);
  const [showEditUser, setShowEditUser] = useState(false);

  const [selectedUser, setSelectedUser] = useState(null);

  const [deletePopup, setDeletePopup] = useState(false);
  const [selectedDeleteUser, setSelectedDeleteUser] = useState(null);

  const [userRole, setUserRole] = useState(null);

  // =========================================================
  // ERROR POPUP STATES
  // =========================================================

  const [showErrorPopup, setShowErrorPopup] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  // =========================================================
  // USER FORM
  // =========================================================

  const [userForm, setUserForm] = useState({
    username: "",
    email: "",
    password: "",
    first_name: "",
    last_name: "",
    phone: "",
    designation: "",
    organization_id: "",
    role_id: "",
    description: "",
  });

  const [editUserForm, setEditUserForm] = useState({
    username: "",
    email: "",
    password: "",
    first_name: "",
    last_name: "",
    phone: "",
    designation: "",
    organization_id: "",
    role_id: "",
    description: "",
  });

  // =========================================================
  // CURRENT USER
  // =========================================================

  const getCurrentUser = async () => {
    try {
      const response = await fetch(
        `${API_URL}/api/users/me`,
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error("Failed to fetch current user");
      }

      const data = await response.json();

      console.log("Current user:", data);

      const role =
        data.organization_memberships?.[0]?.role?.name;

      const organization =
        data.organization_memberships?.[0]?.organization_id;

      const organizationName =
        data.organization_memberships?.[0]?.organization_name;

      if (role === "ORG_ADMIN" && organization) {
        setUserForm((prev) => ({
          ...prev,
          organization_id: organization,
        }));
      }

      setUserOrganizationName(organizationName);

      console.log("Current User Role:", role);
      console.log("Current User Organization:", organization);
      console.log(
        "Current User Organization Name:",
        organizationName
      );

      setUserRole(role);
      setUserOrganization(organization);

    } catch (error) {
      console.error(
        "Error fetching current user:",
        error
      );
    }
  };

  useEffect(() => {
    getCurrentUser();
  }, []);

  // =========================================================
  // ORGANIZATION DROPDOWN
  // =========================================================

  const fetchOrganizationsDropdown = async () => {
    try {
      const response = await fetch(
        `${API_URL}/api/organizations/?page=1&size=100`,
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error("Failed to fetch organizations");
      }

      const data = await response.json();

      setOrganizationOptions(data.data);

    } catch (error) {
      console.error(
        "Error fetching organizations:",
        error
      );
    }
  };

  // =========================================================
  // ROLE DROPDOWN
  // =========================================================

  const fetchRolesDropdown = async () => {
    try {
      const response = await fetch(
        `${API_URL}/api/roles/?page=1&size=100`,
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error("Failed to fetch roles");
      }

      const data = await response.json();

      setRoleOptions(data.data);

    } catch (error) {
      console.error(
        "Error fetching roles:",
        error
      );
    }
  };

  // =========================================================
  // FETCH USERS
  // =========================================================

  const fetchUsers = async (
    organizationId = selectedOrganizationFilter
  ) => {
    try {
      let url = "";

      console.log(
        "User role:",
        userRole,
        "Organization:",
        userOrganization
      );

      if (userRole === "ORG_ADMIN") {

        // ORG_ADMIN → users from his organization
        url =
          `${API_URL}/api/users/organization/${userOrganization}`;

      } else if (organizationId) {

        // SUPER_ADMIN → users from the selected organization
        url =
          `${API_URL}/api/users/organization/${organizationId}`;

      } else {

        // SUPER_ADMIN → all users
        url =
          `${API_URL}/api/users/?page=1&size=100`;
      }

      console.log("Users API URL:", url);

      const response = await fetch(url, {
        headers: {
          Authorization:
            `Bearer ${localStorage.getItem("token")}`,
        },
      });

      if (!response.ok) {
        throw new Error("Failed to fetch users");
      }

      const data = await response.json();

      console.log("Users response:", data);

      let allUsers = Array.isArray(data)
        ? data
        : data.data || [];

      if (
        userRole !== "ORG_ADMIN" &&
        !organizationId &&
        !Array.isArray(data)
      ) {
        const responsePageSize = Number(data.size) || 100;
        const totalUsers = Number(data.total) || allUsers.length;
        const totalApiPages = Math.ceil(totalUsers / responsePageSize);

        for (let page = 2; page <= totalApiPages; page += 1) {
          const pageResponse = await fetch(
            `${API_URL}/api/users/?page=${page}&size=${responsePageSize}`,
            {
              headers: {
               Authorization:
              `Bearer ${localStorage.getItem("token")}`,
              },
            }
          );

          if (!pageResponse.ok) {
            throw new Error("Failed to fetch users");
          }

          const pageData = await pageResponse.json();
          allUsers = allUsers.concat(
            Array.isArray(pageData) ? pageData : pageData.data || []
          );
        }
      }

      setUsers({
        data: allUsers,
        page: 1,
        size: pageSize,
        total: allUsers.length,
      });
    } catch (error) {
      console.error(
        "Error fetching users:",
        error
      );
    }
  };

  // =========================================================
  // INITIAL DATA
  // =========================================================

  useEffect(() => {

    if (
      !userRole ||
      (userRole === "ORG_ADMIN" && !userOrganization)
    ) {
      return;
    }

    fetchUsers();

    if (
      userRole === "SUPER_ADMIN" ||
      userRole === "ORG_ADMIN"
    ) {
      fetchOrganizationsDropdown();
      fetchRolesDropdown();
    }

  }, [
    userRole,
    userOrganization,
    selectedOrganizationFilter
  ]);

  // =========================================================
  // SEARCH
  // =========================================================

  const filterUsersBySearch = (usersToFilter, value) => {
    const searchTerm = value.trim().toLowerCase();

    if (!searchTerm) {
      return usersToFilter;
    }

    return usersToFilter.filter((user) =>
      user.first_name?.toLowerCase().includes(searchTerm) ||
      user.last_name?.toLowerCase().includes(searchTerm) ||
      user.username?.toLowerCase().includes(searchTerm) ||
      user.email?.toLowerCase().includes(searchTerm)
    );
  };

  const filteredUsers = filterUsersBySearch(users.data, searchValue);

  const handleSearch = (value) => {
    setSearchValue(value);
    setCurrentPage(1);
  };

  const handleOrganizationFilter = (organizationId) => {
    
    setSelectedOrganizationFilter(organizationId);
    setCurrentPage(1);
  };

  // =========================================================
  // API ERROR HANDLER
  // =========================================================

  const showApiError = async (
    response,
    defaultMessage
  ) => {

    let message = defaultMessage;

    try {

      const data = await response.json();

      console.log(
        "API Error Response:",
        data
      );

      // FastAPI validation error
      //
      // Example:
      // {
      //   "detail": [
      //     {
      //       "loc": ["body", "email"],
      //       "msg": "value is not a valid email address"
      //     }
      //   ]
      // }

      if (Array.isArray(data.detail)) {

        message = data.detail
          .map((error) => {

            if (typeof error === "string") {
              return error;
            }

            return (
              error.msg ||
              "Validation error"
            );

          })
          .join("\n");
      }

      // Normal FastAPI HTTPException
      //
      // Example:
      // {
      //   "detail": "Username already exists"
      // }

      else if (data.detail) {

        message =
          typeof data.detail === "string"
            ? data.detail
            : JSON.stringify(
                data.detail
              );
      }

      // Other API response
      else if (data.message) {

        message = data.message;
      }

    } catch (error) {

      console.error(
        "Error parsing API error:",
        error
      );
    }

    setErrorMessage(message);
    setShowErrorPopup(true);
  };

  // =========================================================
  // CREATE USER
  // =========================================================

  const createUser = async () => {

    try {

      const response = await fetch(
        `${API_URL}/api/users/`,
        {
          method: "POST",

          headers: {
            "Content-Type": "application/json",
            Authorization:
              `Bearer ${localStorage.getItem("token")}`,
          },

          body: JSON.stringify(userForm),
        }
      );

      if (!response.ok) {

        await showApiError(
          response,
          "Unable to create user. Please try again."
        );

        return;
      }

      setShowAddUser(false);

      fetchUsers();

    } catch (error) {

      console.error(
        "Create user error:",
        error
      );

      setErrorMessage(
        "Unable to connect to the server. Please try again."
      );

      setShowErrorPopup(true);
    }
  };

  // =========================================================
  // UPDATE USER
  // =========================================================

  const updateUser = async (user) => {

    console.log(
      "Updating user with data:",
      editUserForm,
      "user is",
      user
    );

    try {

      const response = await fetch(
        `${API_URL}/api/users/${user.id}`,
        {
          method: "PUT",

          headers: {
            "Content-Type": "application/json",
            Authorization:
              `Bearer ${localStorage.getItem("token")}`,
          },

          body: JSON.stringify(
            editUserForm
          ),
        }
      );

      if (!response.ok) {

        await showApiError(
          response,
          "Unable to update user. Please try again."
        );

        return;
      }

      setShowEditUser(false);

      fetchUsers();

    } catch (error) {

      console.error(
        "Update user error:",
        error
      );

      setErrorMessage(
        "Unable to connect to the server. Please try again."
      );

      setShowErrorPopup(true);
    }
  };

  // =========================================================
  // DELETE USER
  // =========================================================

  const deleteUser = async (id) => {

    try {

      const response = await fetch(
        `${API_URL}/api/users/${id}`,
        {
          method: "DELETE",

          headers: {
            Authorization:
              `Bearer ${localStorage.getItem("token")}`,
          },
        }
      );

      if (!response.ok) {

        await showApiError(
          response,
          "Unable to delete user. Please try again."
        );

        return;
      }

      setDeletePopup(false);
      setSelectedDeleteUser(null);

      fetchUsers();

    } catch (error) {

      console.error(
        "Delete user error:",
        error
      );

      setErrorMessage(
        "Unable to connect to the server. Please try again."
      );

      setShowErrorPopup(true);
    }
  };

  // =========================================================
  // PAGINATION
  // =========================================================

  const totalPages =
    Math.max(1, Math.ceil(filteredUsers.length / pageSize));

  const paginatedUsers = filteredUsers.slice(
    (currentPage - 1) * pageSize,
    currentPage * pageSize
  );

  return (
    <section className="page">

      {/* =====================================================
          FILTER BAR
      ===================================================== */}

      <div className="filters-bar">

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
            placeholder="Search users..."
            value={searchValue}
            onChange={(e) =>
              handleSearch(e.target.value)
            }
          />

        </div>
        {userRole === "SUPER_ADMIN" && (
          <select
            className="filter-select"
            value={selectedOrganizationFilter}
            onChange={(e) =>
              handleOrganizationFilter(e.target.value)
            }
          >
            <option value="All">
              All Organizations
            </option>

            {organizationOptions.map((organization) => (
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

      {/* =====================================================
          CARD
      ===================================================== */}

      <div className="card">

        <div className="card-header">

          <div>

            <div className="card-title">
              Users
            </div>

          </div>

          <button
            className="primary-btn"
            onClick={() =>
              setShowAddUser(true)
            }
          >
            + Add User
          </button>

        </div>

        {/* ===================================================
            TABLE
        =================================================== */}

        <div className="user-table-wrap">

          <table className="user-table">

            <thead>

              <tr>

                <th>User</th>
                <th>Username</th>
                <th>Email</th>
                <th>Phone</th>
                <th>Designation</th>
                <th>Status</th>
                <th>Action</th>

              </tr>

            </thead>

            <tbody>

              {paginatedUsers.map(
                (user) => (

                  <tr
                    key={user.id}
                    className="user-row"

                    onClick={() => {

                      setSelectedUser(user);

                      setShowEditUser(true);

                      setEditUserForm({
                        username:
                          user.username,

                        email:
                          user.email,

                        first_name:
                          user.first_name,

                        last_name:
                          user.last_name,

                        phone:
                          user.phone,

                        designation:
                          user.designation,

                        organization_id:
                          user
                            .organization_memberships?.[0]
                            ?.organization_id || "",

                        role_id:
                          user
                            .organization_memberships?.[0]
                            ?.role?.id || "",

                        description:
                          user.description,
                      });

                    }}
                  >

                    <td>

                      <div className="user-info">

                        <strong>
                          {user.first_name}{" "}
                          {user.last_name}
                        </strong>

                      </div>

                    </td>

                    <td>
                      {user.username}
                    </td>

                    <td>
                      {user.email}
                    </td>

                    <td>
                      {user.phone}
                    </td>

                    <td>
                      {user.designation}
                    </td>

                    <td>

                      <span
                        className={`status-badge ${
                          user.is_active
                            ? "active"
                            : "inactive"
                        }`}
                      >
                        {user.is_active
                          ? "Active"
                          : "Inactive"}
                      </span>

                    </td>

                    <td>

                      <button
                        className="user-delete-btn"

                        onClick={(e) => {

                          e.stopPropagation();

                          setSelectedDeleteUser(
                            user.id
                          );

                          setDeletePopup(true);

                        }}

                        title="Delete User"
                      >

                        <Trash
                          size={17}
                          strokeWidth={2}
                        />

                      </button>

                    </td>

                  </tr>

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
              className={`pagination-btn ${
                currentPage !== 1
                  ? "active"
                  : ""
              }`}

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
              {totalPages}

            </span>

            <button
              className={`pagination-btn ${
                currentPage !== totalPages
                  ? "active"
                  : ""
              }`}

              disabled={
                currentPage >= totalPages
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
          ADD USER MODAL
      ===================================================== */}

      {showAddUser && (

        <div
          className="user-modal-overlay"
          onClick={() =>
            setShowAddUser(false)
          }
        >

          <div
            className="user-modal"
            onClick={(e) =>
              e.stopPropagation()
            }
          >

            <div className="user-modal-header">

              <h2 className="user-modal-title">
                Add New User
              </h2>

              <button
                className="user-close-btn"
                onClick={() =>
                  setShowAddUser(false)
                }
              >
                ✕
              </button>

            </div>

            <form
              className="user-form"

              onSubmit={(e) => {

                e.preventDefault();

                createUser();

              }}
            >

              <div className="user-form-grid">

                {/* First Name */}

                <div className="form-group">

                  <label>
                    First Name
                  </label>

                  <input
                    type="text"
                    placeholder="Enter first name"

                    value={
                      userForm.first_name
                    }

                    onChange={(e) =>
                      setUserForm({
                        ...userForm,
                        first_name:
                          e.target.value,
                      })
                    }
                  />

                </div>

                {/* Last Name */}

                <div className="form-group">

                  <label>
                    Last Name
                  </label>

                  <input
                    type="text"
                    placeholder="Enter last name"

                    value={
                      userForm.last_name
                    }

                    onChange={(e) =>
                      setUserForm({
                        ...userForm,
                        last_name:
                          e.target.value,
                      })
                    }
                  />

                </div>

                {/* Username */}

                <div className="form-group">

                  <label>
                    Username
                  </label>

                  <input
                    type="text"
                    placeholder="Enter username"

                    value={
                      userForm.username
                    }

                    onChange={(e) =>
                      setUserForm({
                        ...userForm,
                        username:
                          e.target.value,
                      })
                    }
                  />

                </div>

                {/* Organization */}

                <div className="form-group">

                  <label>
                    Organization
                  </label>

                  {userRole ==="SUPER_ADMIN" ? (

                    <select
                      value={
                        userForm.organization_id
                      }

                      onChange={(e) =>
                        setUserForm({
                          ...userForm,
                          organization_id:
                            e.target.value,
                        })
                      }
                    >

                      <option value="">
                        Select Organization
                      </option>

                      {organizationOptions.map(
                        (organization) => (

                          <option
                            key={
                              organization.id
                            }
                            value={
                              organization.id
                            }
                          >
                            {organization.name}
                          </option>

                        )
                      )}

                    </select>

                  ) : (

                    <input
                      type="text"

                      value={
                        organizationOptions.find(
                          (organization) =>
                            organization.id ===
                            userOrganization
                        )?.name || ""
                      }

                      readOnly
                    />

                  )}

                </div>

                {/* Role */}

                <div className="form-group">

                  <label>
                    Role
                  </label>

                  <select
                    value={
                      userForm.role_id
                    }

                    onChange={(e) =>
                      setUserForm({
                        ...userForm,
                        role_id:
                          e.target.value,
                      })
                    }
                  >

                    <option value="">
                      Select Role
                    </option>

                    {roleOptions.map(
                      (role) => (

                        <option
                          key={role.id}
                          value={role.id}
                        >
                          {role.name}
                        </option>

                      )
                    )}

                  </select>

                </div>

                {/* Email */}

                <div className="form-group">

                  <label>
                    Email
                  </label>

                  <input
                    type="email"
                    placeholder="user@example.com"

                    value={
                      userForm.email
                    }

                    onChange={(e) =>
                      setUserForm({
                        ...userForm,
                        email:
                          e.target.value,
                      })
                    }
                  />

                </div>

                {/* Password */}

                <div className="form-group">

                  <label>
                    Password
                  </label>

                  <input
                    type="password"
                    placeholder="Enter password"

                    value={
                      userForm.password
                    }

                    onChange={(e) =>
                      setUserForm({
                        ...userForm,
                        password:
                          e.target.value,
                      })
                    }
                  />

                </div>

                {/* Phone */}

                <div className="form-group">

                  <label>
                    Phone
                  </label>

                  <input
                    type="text"
                    placeholder="Enter phone number"

                    value={
                      userForm.phone
                    }

                    onChange={(e) =>
                      setUserForm({
                        ...userForm,
                        phone:
                          e.target.value,
                      })
                    }
                  />

                </div>

                {/* Designation */}

                <div className="form-group">

                  <label>
                    Designation
                  </label>

                  <input
                    type="text"
                    placeholder="Enter designation"

                    value={
                      userForm.designation
                    }

                    onChange={(e) =>
                      setUserForm({
                        ...userForm,
                        designation:
                          e.target.value,
                      })
                    }
                  />

                </div>

                {/* Description */}

                <div className="form-group full-width">

                  <label>
                    Description
                  </label>

                  <textarea
                    rows="4"
                    placeholder="Enter description"

                    value={
                      userForm.description
                    }

                    onChange={(e) =>
                      setUserForm({
                        ...userForm,
                        description:
                          e.target.value,
                      })
                    }
                  />

                </div>

              </div>

              <div className="user-modal-footer">

                <button
                  type="button"
                  className="secondary-btn"

                  onClick={() =>
                    setShowAddUser(false)
                  }
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  className="primary-btn"
                >
                  Create User
                </button>

              </div>

            </form>

          </div>

        </div>

      )}

      {/* =====================================================
          EDIT USER MODAL
      ===================================================== */}

      {showEditUser && (

        <div
          className="user-modal-overlay"
          onClick={() =>
            setShowEditUser(false)
          }
        >

          <div
            className="user-modal"
            onClick={(e) =>
              e.stopPropagation()
            }
          >

            <div className="user-modal-header">

              <h2 className="user-modal-title">
                Edit User
              </h2>

              <button
                className="user-close-btn"

                onClick={() =>
                  setShowEditUser(false)
                }
              >
                ✕
              </button>

            </div>

            <form
              className="user-form"

              onSubmit={(e) => {

                e.preventDefault();

                updateUser(
                  selectedUser
                );

              }}
            >

              <div className="user-form-grid">

                {/* First Name */}

                <div className="form-group">

                  <label>
                    First Name
                  </label>

                  <input
                    type="text"
                    placeholder="Enter first name"

                    value={
                      editUserForm.first_name
                    }

                    onChange={(e) =>
                      setEditUserForm({
                        ...editUserForm,
                        first_name:
                          e.target.value,
                      })
                    }
                  />

                </div>

                {/* Last Name */}

                <div className="form-group">

                  <label>
                    Last Name
                  </label>

                  <input
                    type="text"
                    placeholder="Enter last name"

                    value={
                      editUserForm.last_name
                    }

                    onChange={(e) =>
                      setEditUserForm({
                        ...editUserForm,
                        last_name:
                          e.target.value,
                      })
                    }
                  />

                </div>

                {/* Username */}

                <div className="form-group">

                  <label>
                    Username
                  </label>

                  <input
                    type="text"
                    placeholder="Enter username"

                    value={
                      editUserForm.username
                    }

                    onChange={(e) =>
                      setEditUserForm({
                        ...editUserForm,
                        username:
                          e.target.value,
                      })
                    }
                  />

                </div>

                {/* Organization */}

                <div className="form-group">

                  <label>
                    Organization
                  </label>

                  {userRole ===
                  "SUPER_ADMIN" ? (

                    <select
                      value={
                        editUserForm.organization_id
                      }

                      onChange={(e) =>
                        setEditUserForm({
                          ...editUserForm,
                          organization_id:
                            e.target.value,
                        })
                      }
                    >

                      <option value="">
                        Select Organization
                      </option>

                      {organizationOptions.map(
                        (organization) => (

                          <option
                            key={
                              organization.id
                            }
                            value={
                              organization.id
                            }
                          >
                            {organization.name}
                          </option>

                        )
                      )}

                    </select>

                  ) : (

                    <input
                      type="text"

                      value={
                        userOrganizationName ||
                        ""
                      }

                      readOnly
                    />

                  )}

                </div>

                {/* Role */}

                <div className="form-group">

                  <label>
                    Role
                  </label>

                  <select
                    value={
                      editUserForm.role_id
                    }

                    onChange={(e) =>
                      setEditUserForm({
                        ...editUserForm,
                        role_id:
                          e.target.value,
                      })
                    }
                  >

                    <option value="">
                      Select Role
                    </option>

                    {roleOptions.map(
                      (role) => (

                        <option
                          key={role.id}
                          value={role.id}
                        >
                          {role.name}
                        </option>

                      )
                    )}

                  </select>

                </div>

                {/* Email */}

                <div className="form-group">

                  <label>
                    Email
                  </label>

                  <input
                    type="email"
                    placeholder="user@example.com"

                    value={
                      editUserForm.email
                    }

                    onChange={(e) =>
                      setEditUserForm({
                        ...editUserForm,
                        email:
                          e.target.value,
                      })
                    }
                  />

                </div>

                {/* Phone */}

                <div className="form-group">

                  <label>
                    Phone
                  </label>

                  <input
                    type="text"
                    placeholder="Enter phone number"

                    value={
                      editUserForm.phone
                    }

                    onChange={(e) =>
                      setEditUserForm({
                        ...editUserForm,
                        phone:
                          e.target.value,
                      })
                    }
                  />

                </div>

                {/* Designation */}

                <div className="form-group">

                  <label>
                    Designation
                  </label>

                  <input
                    type="text"
                    placeholder="Enter designation"

                    value={
                      editUserForm.designation
                    }

                    onChange={(e) =>
                      setEditUserForm({
                        ...editUserForm,
                        designation:
                          e.target.value,
                      })
                    }
                  />

                </div>
                
                {(userRole === "SUPER_ADMIN" || userRole === "ORG_ADMIN") && (
  <div className="form-group">

    <label>
      Password
    </label>

    <input
      type="password"
      placeholder="Enter Password"
      value={editUserForm.password || ""}
      onChange={(e) =>
        setEditUserForm({
          ...editUserForm,
          password: e.target.value,
        })
      }
    />

  </div>
)}
                {/* Description */}

                <div className="form-group full-width">

                  <label>
                    Description
                  </label>

                  <textarea
                    rows="4"
                    placeholder="Enter description"

                    value={
                      editUserForm.description
                    }

                    onChange={(e) =>
                      setEditUserForm({
                        ...editUserForm,
                        description:
                          e.target.value,
                      })
                    }
                  />

                </div>

              </div>

              <div className="user-modal-footer">

                <button
                  type="button"
                  className="secondary-btn"

                  onClick={() =>
                    setShowEditUser(false)
                  }
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  className="primary-btn"
                >
                  Update User
                </button>

              </div>

            </form>

          </div>

        </div>

      )}

      {/* =====================================================
          DELETE CONFIRMATION POPUP
      ===================================================== */}

      {deletePopup &&
        selectedDeleteUser && (

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
                Delete User?
              </h2>

              <p>
                Are you sure you want to
                delete this user?
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

                    setSelectedDeleteUser(
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
                    deleteUser(
                      selectedDeleteUser
                    )
                  }
                >
                  Yes, Delete
                </button>

              </div>

            </div>

          </div>

        )}

      {/* =====================================================
          ERROR POPUP
      ===================================================== */}

      {showErrorPopup && (

        <div
          className="error-modal-overlay"

          onClick={() =>
            setShowErrorPopup(false)
          }
        >

          <div
            className="error-modal"

            onClick={(e) =>
              e.stopPropagation()
            }
          >

            <div className="error-modal-icon">
              !
            </div>

            <h2>
              Error
            </h2>

            <p>
              {errorMessage}
            </p>

            <div className="error-modal-actions">

              <button
                type="button"
                className="primary-btn"

                onClick={() =>
                  setShowErrorPopup(false)
                }
              >
                OK
              </button>

            </div>

          </div>

        </div>

      )}

    </section>
  );
}

export default Users;