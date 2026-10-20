import React, { useState, useEffect } from "react";
import { Trash2 } from "lucide-react";
import "./Roles.css";
import { API_URL } from "../Config/ApiEndpoint";
function Roles()
{

const [roles, setRoles] = useState([]);
const [filteredRoles, setFilteredRoles] = useState([]);

const [currentPage, setCurrentPage] = useState(1);
const [pageSize, setPageSize] = useState(10);

const [showAddRole, setShowAddRole] = useState(false);
const [showEditRole, setShowEditRole] = useState(false);

const [selectedRole, setSelectedRole] = useState(null);

const [deletePopup, setDeletePopup] = useState(false);
const [selectedDeleteRole, setSelectedDeleteRole] = useState(null);

const [roleForm, setRoleForm] = useState({
    name: "",

    description: ""
});

const [editRoleForm, setEditRoleForm] = useState({
    name: "",
    description: ""
});

const fetchRoles = (page = 1, size = 10) => {
  fetch(
    `${API_URL}/api/roles/?page=${page}&size=${size}`,
    {
      headers: {
        Authorization: `Bearer ${localStorage.getItem("token")}`,
      },
    }
  )
    .then((res) => res.json())
    .then((data) => {
      setRoles(data);
      setFilteredRoles(data.data);
    });
};

const totalPages = Math.ceil(
  roles.total / pageSize
);

useEffect(() => {
    fetchRoles(currentPage, pageSize);
}, [currentPage, pageSize]);

const handleSearch = (value) => {

    if (value === "") {

        setFilteredRoles(roles.data);
        return;

    }

    const filtered = roles.data.filter(role =>
        role.name.toLowerCase().includes(value.toLowerCase())
    );

    setFilteredRoles(filtered);

};

const createRole = async () => {

    const response = await fetch(
        `${API_URL}/api/roles/`,
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${localStorage.getItem("token")}`
            },
            body: JSON.stringify(roleForm)
        }
    );

    if (response.ok) {

        setShowAddRole(false);
        fetchRoles(currentPage, pageSize);

    }

};

const updateRole = async (id) => {

    const response = await fetch(
        `${API_URL}/api/roles/${id}`,
        {
            method: "PUT",
            headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${localStorage.getItem("token")}`
            },
            body: JSON.stringify(editRoleForm)
        }
    );

    if (response.ok) {

        setShowEditRole(false);
        fetchRoles(currentPage, pageSize);

    }

};

const deleteRole = async (id) => {

    const response = await fetch(
        `${API_URL}/api/roles/${id}`,
        {
            method: "DELETE",
            headers: {
                Authorization: `Bearer ${localStorage.getItem("token")}`
            }
        }
    );

    if (response.ok) {

        setDeletePopup(false);

        fetchRoles(currentPage, pageSize);

    }

};


return(

<section className="page">

  {/* Search + Add */}

  <div className="filters-bar">

    <div className="search-wrap">

      <div className="search-icon">
        🔍
      </div>

      <input
        type="text"
        className="search-input"
        placeholder="Search roles..."
        onChange={(e) => handleSearch(e.target.value)}
      />

    </div>


  </div>



  {/* Card */}

  <div className="card">

    <div className="card-header">

      <div>

        <div className="card-title">
          Roles
        </div>

        <div className="role-count">
          Showing {filteredRoles.length} roles
        </div>

      </div>

    </div>



    <div className="role-table-wrap">

      <table className="role-table">

        <thead>

          <tr>

            <th>Role Name</th>

            

            <th>Description</th>

            <th>Created On</th>



          </tr>

        </thead>

        <tbody>

          {filteredRoles.map((role) => (

            <tr
              key={role.id}
              onClick={() => {
                setSelectedRole(role);

                setEditRoleForm({
                  name: role.name,
                  description: role.description,
                });

                setShowEditRole(true);
              }}
            >

              <td>

                <strong>
                  {role.name}
                </strong>

              </td>


              <td>

                {role.description}

              </td>

              <td>

                {new Date(role.created_at).toLocaleDateString()}

              </td>


            </tr>

          ))}

        </tbody>

      </table>

    </div>

  {/* Pagination */}

  <div className="pagination">

    <div className="pagination-size">

      <span>
        Rows per page
      </span>

      <select
        value={pageSize}
        onChange={(e) => {

          setPageSize(Number(e.target.value));
          setCurrentPage(1);

        }}
      >

        <option value={10}>10</option>

        <option value={20}>20</option>

        <option value={50}>50</option>

      </select>

    </div>



<div className="pagination-pages">

  <button
    className="pagination-btn"
    disabled={currentPage === 1}
    onClick={() => setCurrentPage(currentPage - 1)}
  >
    Previous
  </button>

  <span className="pagination-info">
    Page {currentPage} of {totalPages}
  </span>

  <button
    className="pagination-btn"
    disabled={currentPage === totalPages}
    onClick={() => setCurrentPage(currentPage + 1)}
  >
    Next
  </button>

</div>

  </div>

  </div>







{showAddRole && (
  <div className="role-modal-overlay">

    <div className="role-modal">

      {/* Header */}

      <div className="role-modal-header">

        <h2 className="role-modal-title">
          Add New Role
        </h2>

        <button
          className="role-close-btn"
          onClick={() => setShowAddRole(false)}
        >
          ✕
        </button>

      </div>

      {/* Form */}

      <form
        className="role-form"
        onSubmit={(e) => {
          e.preventDefault();
          createRole();
        }}
      >

        <div className="role-form-grid">

          {/* Role Name */}

          <div className="form-group">

            <label>Role Name</label>

            <input
              type="text"
              placeholder="Enter role name"
              value={roleForm.name}
              onChange={(e) =>
                setRoleForm({
                  ...roleForm,
                  name: e.target.value,
                })
              }
            />

          </div>

          {/* Role Code */}

          {/* <div className="form-group">

            <label>Role Code</label>

            <input
              type="text"
              placeholder="Enter role code"
              value={roleForm.code}
              onChange={(e) =>
                setRoleForm({
                  ...roleForm,
                  code: e.target.value,
                })
              }
            />

          </div> */}

          {/* Description */}

          <div className="form-group">

            <label>Description</label>

            <textarea
              rows="4"
              placeholder="Enter description"
              value={roleForm.description}
              onChange={(e) =>
                setRoleForm({
                  ...roleForm,
                  description: e.target.value,
                })
              }
            />

          </div>

        </div>

        {/* Footer */}

        <div className="role-modal-footer">

          <button
            type="button"
            className="secondary-btn"
            onClick={() => setShowAddRole(false)}
          >
            Cancel
          </button>

          <button
            type="submit"
            className="primary-btn"
          >
            Create Role
          </button>

        </div>

      </form>

    </div>

  </div>
)}

{showEditRole && (
  <div className="role-modal-overlay">

    <div className="role-modal">

      {/* Header */}

      <div className="role-modal-header">

        <h2 className="role-modal-title">
          Edit Role
        </h2>

        <button
          className="role-close-btn"
          onClick={() => setShowEditRole(false)}
        >
          ✕
        </button>

      </div>

      {/* Form */}

      <form
        className="role-form"
        onSubmit={(e) => {
          e.preventDefault();
          updateRole(selectedRole.id);
        }}
      >

        <div className="role-form-grid">

          {/* Role Name */}

          <div className="form-group">

            <label>Role Name</label>

            <input
              type="text"
              value={editRoleForm.name}
              readOnly={true}
              // onChange={(e) =>
              //   setEditRoleForm({
              //     ...editRoleForm,
              //     name: e.target.value,
              //   })
              //}
            />

          </div>

          {/* Role Code */}

          {/* <div className="form-group">

            <label>Role Code</label>

            <input
              type="text"
              value={editRoleForm.code}
              onChange={(e) =>
                setEditRoleForm({
                  ...editRoleForm,
                  code: e.target.value,
                })
              }
            />

          </div> */}

          {/* Description */}

          <div className="form-group">

            <label>Description</label>

            <textarea
              rows="4"
              value={editRoleForm.description}
              onChange={(e) =>
                setEditRoleForm({
                  ...editRoleForm,
                  description: e.target.value,
                })
              }
            />

          </div>

        </div>

        {/* Footer */}

        <div className="role-modal-footer">

          <button
            type="button"
            className="secondary-btn"
            onClick={() => setShowEditRole(false)}
          >
            Cancel
          </button>

          <button
            type="submit"
            className="primary-btn"
          >
            Update Role
          </button>

        </div>

      </form>

    </div>

  </div>
)}

{deletePopup && selectedDeleteRole && (
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
        Delete Role?
      </h2>

      <p>
        Are you sure you want to delete{" "}
        <strong>
          {selectedDeleteRole.name}
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
            setSelectedDeleteRole(null);
          }}
        >
          No
        </button>

        <button
          type="button"
          className="delete-confirm-btn"
          onClick={() => deleteRole(selectedDeleteRole.id)}
        >
          Yes, Delete
        </button>

      </div>

    </div>
  </div>
)}
</section>

)
}

export default Roles;