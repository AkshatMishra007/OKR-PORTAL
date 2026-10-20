import { useEffect,useState } from "react";
import "./Organizations.css";
import { Trash2 } from "lucide-react";
import {useNavigate} from "react-router-dom";
import { API_URL } from "../Config/ApiEndpoint";

function Organization() {



const navigate=useNavigate();  

const [organizations, setOrganizations] = useState( {data: [],
                                                     pagination: {
                                                         page: 10,
                                                         size: 10,
                                                         total: 0,
                                                     }},);
const [filteredOrganizations, setFilteredOrganizations] = useState([]);
const [currentPage, setCurrentPage] = useState(1);
const [pageSize, setPageSize] = useState(10);
const [showAddOrganization, setShowAddOrganization] = useState(false);
const [showEditOrganization, setShowEditOrganization] = useState(false);
const [selectedOrganization, setSelectedOrganization] = useState(null);

const [deletepopup,setdeletePopup]=useState(false);

const [selectedDeleteOrganization, setSelectedDeleteOrganization] = useState(null);
const [editForm, setEditForm] = useState({
  name: "",

  email: "",
  phone: "",
  website: "",
  logo: "",
  address: "",
  description: "",
  is_active: true,
});


const [organizationForm, setOrganizationForm] = useState({
  name: "",
  description: "",
  logo: "",
  website: "",
  email: "",
  phone: "",
  address: "",
});


const handleOrganizationChange = (e) => {
  const { name, value, files } = e.target;
  console.log("handleOrganizationChange called with event:", e.target);
  if(name==="logo")
  {
    console.log("Logo file selected:", e.target.files[0].name);
  }

   
  setOrganizationForm((prev) => ({
    ...prev,
    [name]: name === "logo" ? files[0] : value,
  }));
};

// const handleCreateOrganization = async (e) => {
//   e.preventDefault();

//   try {
//     const token = localStorage.getItem("token");

//     const response = await fetch(
//       `${API_URL}/api/organizations/`,
//       {
//         method: "POST",

//         headers: {
//           Accept: "application/json",
//           "Content-Type": "application/json",
//           Authorization: `Bearer ${token}`,
//         },

//         body: JSON.stringify({
//           name: organizationForm.name,

//           description: organizationForm.description,
//           logo: organizationForm.logo,
//           website: organizationForm.website,
//           email: organizationForm.email,
//           phone: organizationForm.phone,
//           address: organizationForm.address,
//         }),
//       }
//     );

//     if (!response.ok) {
//       const errorData = await response.json();

//       console.error("Create Organization Error:", errorData);

//       throw new Error("Failed to create organization");
//     }

//     const data = await response.json();

//     console.log("Organization created:", data);

//     // Close modal
//     setShowAddOrganization(false);

//     // Reset form
//     setOrganizationForm({
//       name: "",

//       description: "",
//       logo: "",
//       website: "",
//       email: "",
//       phone: "",
//       address: "",
//     });

//     // Refresh organization list
//     fetchOrganizations(currentPage, pageSize);

//   } catch (error) {
//     console.error("Error creating organization:", error);
//   }
// };

const handleCreateOrganization = async (e) => {
  e.preventDefault();

  try {
    const token = localStorage.getItem("token");

    // Create multipart form data
    const formData = new FormData();

    formData.append("name", organizationForm.name);
    formData.append(
      "description",
      organizationForm.description || ""
    );
    formData.append(
      "website",
      organizationForm.website || ""
    );
    formData.append(
      "email",
      organizationForm.email || ""
    );
    formData.append(
      "phone",
      organizationForm.phone || ""
    );
    formData.append(
      "address",
      organizationForm.address || ""
    );

    // Add logo only if selected
    if (organizationForm.logo) {
      formData.append(
        "logo",
        organizationForm.logo
      );
    }

    const response = await fetch(
      `${API_URL}/api/organizations/`,
      {
        method: "POST",

        headers: {
          Accept: "application/json",
          Authorization: `Bearer ${token}`,
        },

        body: formData,
      }
    );

    if (!response.ok) {
      const errorData = await response.json();

      console.error(
        "Create Organization Error:",
        errorData
      );

      throw new Error(
        "Failed to create organization"
      );
    }

    const data = await response.json();

    console.log(
      "Organization created:",
      data
    );

    // Close modal
    setShowAddOrganization(false);

    // Reset form
    setOrganizationForm({
      name: "",
      description: "",
      logo: null,
      website: "",
      email: "",
      phone: "",
      address: "",
    });

    // Refresh organization list
    fetchOrganizations(
      currentPage,
      pageSize
    );

  } catch (error) {
    console.error(
      "Error creating organization:",
      error
    );
  }
};

const fetchOrganizations = (page = 1, size = 10) => {

  fetch(
    `${API_URL}/api/organizations/?page=${page}&size=${size}`,
    {
      method: "get",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${localStorage.getItem("token")}`,
      },
    }
  )
    .then(response => response.json())
    .then(data => {

      console.log(data);

      setOrganizations(data);
      setFilteredOrganizations(data.data);
  
    })
    .catch(error => {
      console.error("Error fetching organizations:", error);
    });

};
const phone = editForm.phone.replace(/[\s\-()]/g, "")===''?organizationForm.phone.replace(/[\s\-()]/g, ""):editForm.phone.replace(/[\s\-()]/g, "");

const isPhoneValid =
  /^[6-9]\d{9}$/.test(phone) ||
  /^0\d{9,10}$/.test(phone);

useEffect(() => {
  fetchOrganizations(currentPage, pageSize);
 
}, [currentPage, pageSize]);

console.log("Organizations:", organizations);
 const totalPages = Math.ceil(
  organizations.pagination.total / pageSize
);

const deleteOrganization = async (id) => {
  try {
    console.log("Deleting organization:", id);

    const response = await fetch(
      `${API_URL}/api/organizations/${id}`,
      {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      }
    );

    if (!response.ok) {
      throw new Error("Failed to delete organization");
    }

    console.log("Organization deleted successfully");

    // Refresh organization data
    fetchOrganizations(currentPage, pageSize);

  } catch (error) {
    console.error("Delete organization error:", error);
  }
  setdeletePopup(false);
};

const handleEditOrganization = (organization) => {
  setSelectedOrganization(organization);

  setEditForm({
    name: organization.name || "",
    email: organization.email || "",
    phone: organization.phone || "",
    website: organization.website || "",
    logo: organization.logo || "",
    address: organization.address || "",
    description: organization.description || "",
    is_active: organization.is_active,
  });

  setShowEditOrganization(true);
};

const updateOrganization = async (id, updatedData) => {
  try {
    const response = await fetch(
      `${API_URL}/api/organizations/${id}`,
      {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: JSON.stringify(updatedData),
      }
    );
  }
  catch (error) {
    console.error("Update organization error:", error);
  }
}

return (
    <section className="page" id="page-organizations">

      {/* ================= FILTER BAR ================= */}

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
            placeholder="Search organizations..."
            onChange={(e) => {
                
              const searchTerm = e.target.value.toLowerCase();
              if(searchTerm === "") {
                setFilteredOrganizations(organizations.data);
                return;
              }
              const filteredOrganizations = organizations.data.filter((organization) =>
                organization.name.toLowerCase().includes(searchTerm)
              );
              setFilteredOrganizations(filteredOrganizations);
            }}
          />

        </div>

      </div>


      {/* ================= ORGANIZATION CARD ================= */}

      <div className="card">

        <div className="card-header">

          <div>

            <div className="card-title">
              Organizations
            </div>


          </div>

          <button className="primary-btn" onClick={()=>setShowAddOrganization(true)}>
            + Add Organization
          </button>

        </div>


        {/* ================= ORGANIZATION TABLE ================= */}

        <div className="organization-table-wrap">

          <table className="organization-table">

            <thead>

              <tr >

                <th>Organization</th>
                <th>Description</th>
                <th>Email</th>
                <th>Phone</th>
                <th>Website</th>
                <th>Address</th>
                <th>Status</th>
                <th>Action</th>
              </tr>

            </thead>


<tbody>
  {filteredOrganizations?.map((organization) => (
<tr
  key={organization.id}
  className="organization-row"
  onClick={() => handleEditOrganization(organization)}
>
      
      <td>
        <div className="organization-info">
          <strong>{organization.name}</strong>
          
        </div>
      </td>

      <td>{organization.description}</td>

      <td>{organization.email}</td>

      <td>{organization.phone}</td>

      <td>
        <a
          href={organization.website}
          target="_blank"
          rel="noreferrer"
        >
          {organization.website}
        </a>
      </td>

      <td>{organization.address}</td>

      <td>
        <span
          className={`status-badge ${
            organization.is_active ? "active" : "inactive"
          }`}
        >
          {organization.is_active ? "Active" : "Inactive"}
        </span>
      </td>


 <td>
  <button
    className="organization-delete-btn"
    onClick={(e) => {

      e.stopPropagation();
       setSelectedDeleteOrganization(organization.id);
      setdeletePopup(true);
    }}
    title="Delete Organization"
  >
    <Trash2 size={17} strokeWidth={2} />
  </button>
</td>

    </tr>
  ))}
</tbody>

          </table>

        </div>

<div className="pagination">

  <div className="pagination-size">
    <span>Rows per page:</span>

    <select
      value={pageSize}
      onChange={(e) => {
        setPageSize(Number(e.target.value));
        setCurrentPage(1);
      }}
    >
      <option value={10}>10</option>
      <option value={20}>20</option>
      <option value={30}>20</option>
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
      className="pagination-btn "
      disabled={currentPage === totalPages}
      onClick={() => setCurrentPage(currentPage + 1)}
    >
      Next
    </button>

  </div>

</div>
      </div>
{showAddOrganization && (
  <div
    className="organization-modal-overlay"
    onClick={() => setShowAddOrganization(false)}
  >

    <div
      className="organization-modal"
      onClick={(e) => e.stopPropagation()}
    >

      {/* Modal Header */}

      <div className="organization-modal-header">

        <div>
          <h2>Add Organization</h2>

          <p>
            Create a new organization
          </p>
        </div>

        <button
          type="button"
          className="modal-close-btn"
          onClick={() => setShowAddOrganization(false)}
        >
          ×
        </button>

      </div>


      {/* Modal Form */}

    <form
  className="organization-form"
  onSubmit={handleCreateOrganization}
  encType="multipart/form-data"
>
  <div className="organization-form-grid">

    {/* Organization Name */}

    <div className="form-group">
      <label>
        Organization Name
      </label>

      <input
        type="text"
        name="name"
        value={organizationForm.name}
        onChange={handleOrganizationChange}
        placeholder="Enter organization name"
        required
      />
    </div>


    {/* Email */}

    <div className="form-group">
      <label>
        Email
      </label>

      <input
        type="email"
        name="email"
        value={organizationForm.email}
        onChange={handleOrganizationChange}
        placeholder="contact@example.com"
        required
      />
    </div>


    {/* Phone */}

    <div className="form-group">
      <label>
        Phone
      </label>

             <input
  type="tel"
  value={organizationForm.phone}
  onChange={(e) => {
    const value = e.target.value;

    if (/^[0-9\s\-()]*$/.test(value)) {
      setOrganizationForm({
        ...organizationForm,
        phone: value,
      });
    }
    else
    {
      console.log("Invalid input: Only numbers, spaces, dashes, and parentheses are allowed.");
    }
  }}
  maxLength={11}
  className={!isPhoneValid && organizationForm.phone ? "input-error" : ""}
/>

{organizationForm.phone && !isPhoneValid && (
  <small className="error">
    Enter a valid Indian mobile or landline number.
  </small>
)}
    </div>


    {/* Website */}

    <div className="form-group">
      <label>
        Website
      </label>

      <input
        type="url"
        name="website"
        value={organizationForm.website}
        onChange={handleOrganizationChange}
        placeholder="https://example.com"
      />
    </div>


    {/* Logo */}

    <div className="form-group">
      <label>
        Logo
      </label>

      <input
        type="file"
        name="logo"

        accept=".png,image/png"
        onChange={handleOrganizationChange}
        placeholder="Enter logo"
      />
    </div>


    {/* Active Status */}

    <div className="form-group">
      <label>
        Status
      </label>

      <select
        name="is_active"
        value={organizationForm.is_active}
        onChange={handleOrganizationChange}
      >
        <option value="true">
          Active
        </option>

        <option value="false">
          Inactive
        </option>
      </select>
    </div>


    {/* Address */}

    <div className="form-group full-width">
      <label>
        Address
      </label>

      <textarea
        name="address"
        value={organizationForm.address}
        onChange={handleOrganizationChange}
        rows="3"
        placeholder="Enter organization address"
      />
    </div>


    {/* Description */}

    <div className="form-group full-width">
      <label>
        Description
      </label>

      <textarea
        name="description"
        value={organizationForm.description}
        onChange={handleOrganizationChange}
        rows="3"
        placeholder="Enter organization description"
      />
    </div>

  </div>


  {/* Modal Footer */}

  <div className="organization-modal-footer">

    <button
      type="button"
      className="secondary-btn"
      onClick={() => setShowAddOrganization(false)}
    >
      Cancel
    </button>

    <button
      type="submit"
      className="primary-btn"
    >
      Create Organization
    </button>

  </div>

</form>
    </div>

  </div>
)}



{showEditOrganization && selectedOrganization && (
  <div
    className="organization-modal-overlay"
    onClick={() => setShowEditOrganization(false)}
  >

    <div
      className="organization-modal"
      onClick={(e) => e.stopPropagation()}
    >

      {/* Header */}

      <div className="organization-modal-header">

        <div>
          <h2>
            Edit Organization
          </h2>

          <p>
            Update organization information
          </p>
        </div>

        <button
          type="button"
          className="modal-close-btn"
          onClick={() => setShowEditOrganization(false)}
        >
          ×
        </button>

      </div>


      {/* Form */}

      <form className="organization-form">

        <div className="organization-form-grid">

          {/* Organization Name */}

          <div className="form-group">

            <label>
              Organization Name
            </label>

            <input
  type="text"
  value={editForm.name}
  onChange={(e) =>
    setEditForm({
      ...editForm,
      name: e.target.value,
    })
  }
  placeholder="Enter organization name"
/>

          </div>



          {/* Email */}

          <div className="form-group">

            <label>
              Email
            </label>

           <input
  type="email"
  value={editForm.email}
  onChange={(e) =>
    setEditForm({
      ...editForm,
      email: e.target.value,
    })
  }
  placeholder="contact@example.com"
/>

          </div>


          {/* Phone */}

          <div className="form-group">

            <label>
              Phone
            </label>

         <input
  type="tel"
  value={editForm.phone}
  onChange={(e) => {
    const value = e.target.value;

    if (/^[0-9\s\-()]*$/.test(value)) {
      setEditForm({
        ...editForm,
        phone: value,
      });
    }
  }}
  maxLength={11}
  className={!isPhoneValid && editForm.phone ? "input-error" : ""}
/>

{editForm.phone && !isPhoneValid && (
  <small className="error">
    Enter a valid Indian mobile or landline number.
  </small>
)}
          </div>


          {/* Website */}

          <div className="form-group">

            <label>
              Website
            </label>

          <input
  type="url"
  value={editForm.website}
  onChange={(e) =>
    setEditForm({
      ...editForm,
      website: e.target.value,
    })
  }
  placeholder="https://example.com"
/>
          </div>


          {/* Logo */}

          <div className="form-group">

            <label>
              Logo
            </label>

            <input
              type="text"
              value={editForm.logo}
              onChange={(e) =>
                setEditForm({
                  ...editForm,
                  logo: e.target.value,
                })
              }
              placeholder="Enter logo URL"
            />

          </div>


          {/* Status */}

          <div className="form-group">

            <label>
              Status
            </label>

            <select
              value={
                editForm.is_active
                  ? "true"
                  : "false"
              }
              onChange={(e) =>
                setEditForm({
                  ...editForm,
                  is_active: e.target.value === "true",
                })
              }
            >

              <option value="true">
                Active
              </option>

              <option value="false">
                Inactive
              </option>

            </select>

          </div>

          {/* Address */}

          <div className="form-group full-width">

            <label>
              Address
            </label>

            <textarea
              rows="3"
              value={editForm.address}
              onChange={(e) =>
                setEditForm({
                  ...editForm,
                  address: e.target.value,
                })
              }
              placeholder="Enter organization address"
            />

          </div>


          {/* Description */}

          <div className="form-group full-width">

            <label>
              Description
            </label>

            <textarea
              rows="3"
              value={editForm.description}
              onChange={(e) =>
                setEditForm({
                  ...editForm,
                  description: e.target.value,
                })
              }
              placeholder="Enter organization description"
            />

          </div>




        </div>


        {/* Footer */}

        <div className="organization-modal-footer">

          <button
            type="button"
            className="secondary-btn"
            onClick={() => setShowEditOrganization(false)}
          >
            Cancel
          </button>

          <button
            type="submit"
            className="primary-btn"
            onClick={() => {
              // Handle update logic here
              updateOrganization(selectedOrganization.id, editForm);
              setShowEditOrganization(false);
            }}
          >
            Update Organization
          </button>

        </div>

      </form>

    </div>

  </div>
)}


{deletepopup && selectedDeleteOrganization && (
  <div
    className="delete-modal-overlay"
    onClick={() => setdeletePopup(false)}
  >
    <div
      className="delete-modal"
      onClick={(e) => e.stopPropagation()}
    >

      <div className="delete-modal-icon">
        <Trash2 size={22} />
      </div>

      <h2>
        Delete Organization?
      </h2>

      <p>
        Are you sure you want to delete{" "}
        <strong>
          {selectedDeleteOrganization.name}
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
            setdeletePopup(false);
            setSelectedDeleteOrganization(null);
          }}
        >
          No
        </button>

        <button
          type="button"
          className="delete-confirm-btn"
          onClick={()=>deleteOrganization(selectedDeleteOrganization)}
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

export default Organization;