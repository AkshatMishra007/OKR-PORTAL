import { NavLink, useNavigate, useLocation } from "react-router-dom";
import "./Sidebar.css";
import { useEffect, useRef, useState } from "react";
import logo from "../../logo.svg";
import {
  LayoutDashboard,
  Target,
  Users,
  ChartNoAxesCombined,
  Trophy,
  MessageCircleQuestion,
  ClipboardList,
  Building2,
  UserRound,
  UsersRound,
  PanelLeftClose,
} from "lucide-react";
import { hasModuleAccess } from "../../Config/modulePermissions";
import { API_URL } from "../../Config/ApiEndpoint";
function Sidebar({ isOpen, onMenuToggle }) {
  const [profileUser, setProfileUser] = useState(false);
  const [user, setUser] = useState(null);

  const navigate = useNavigate();
  const location = useLocation();

  // Navigation behavior:
  // - Laptop/Desktop: never close the sidebar when navigating.
  // - Mobile: close only when navigating to a different module.
  // - Clicking the module already open does nothing.
  const handleNavClick = (targetPath) => {
    if (
      window.innerWidth <= 768 &&
      location.pathname !== targetPath
    ) {
      onMenuToggle();
    }
  };

  // Reference to the profile section
  const profileRef = useRef(null);

  /*
  |--------------------------------------------------------------------------
  | Open User Profile
  |--------------------------------------------------------------------------
  */
  const openUserProfile = () => {
    console.log("User profile clicked");

    setProfileUser((previousState) => !previousState);
  };

  /*
  |--------------------------------------------------------------------------
  | Close Profile When Clicking Outside
  |--------------------------------------------------------------------------
  */
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (
        profileRef.current &&
        !profileRef.current.contains(event.target)
      ) {
        setProfileUser(false);
      }
    };

    document.addEventListener(
      "mousedown",
      handleClickOutside
    );

    return () => {
      document.removeEventListener(
        "mousedown",
        handleClickOutside
      );
    };
  }, []);

  /*
  |--------------------------------------------------------------------------
  | Get Current Logged-In User
  |--------------------------------------------------------------------------
  */
  useEffect(() => {
    const verifyTokenAndGetUser = async () => {
      const token = localStorage.getItem("token");

      console.log(
        "Retrieved token from localStorage:",
        token
      );

      if (!token) {
        alert(
          "Your session has expired. Please log in again."
        );

        navigate("/");

        return;
      }

      try {
        const response = await fetch(
          `${API_URL}/api/users/me`,
          {
            method: "GET",

            headers: {
              Accept: "application/json",

              Authorization: `Bearer ${token}`,
            },
          }
        );

        console.log(
          "Token verification response status:",
          response.status
        );

        /*
        |--------------------------------------------------------------------------
        | Token Expired / Invalid
        |--------------------------------------------------------------------------
        */

        if (response.status === 401) {
          localStorage.removeItem("token");

          alert(
            "Your session has expired. Please log in again."
          );

          navigate("/");

          return;
        }

        /*
        |--------------------------------------------------------------------------
        | Other API Errors
        |--------------------------------------------------------------------------
        */

        if (!response.ok) {
          throw new Error(
            "Failed to fetch user details"
          );
        }

        /*
        |--------------------------------------------------------------------------
        | Convert Response To JSON
        |--------------------------------------------------------------------------
        */

        const data = await response.json();

        console.log(
          "Logged-in user data:",
          data
        );
        console.log("Data is set to ", data.organization_memberships[0].role.name);
        setUser(data);
      } catch (error) {
        console.error(
          "Error fetching user:",
          error
        );

        alert(
          "Unable to verify your session."
        );

        navigate("/");
      }
    };

    verifyTokenAndGetUser();
  }, [navigate]);

  /*
  |--------------------------------------------------------------------------
  | Logout
  |--------------------------------------------------------------------------
  */

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("refresh_token");

    navigate("/");
  };

  /*
  |--------------------------------------------------------------------------
  | Get User Initials
  |--------------------------------------------------------------------------
  */

  const getUserInitials = () => {
    if (!user) {
      return "...";
    }

    const firstInitial =
      user.first_name?.charAt(0).toUpperCase() || "";

    const lastInitial =
      user.last_name?.charAt(0).toUpperCase() || "";

    return firstInitial + lastInitial;
  };


  //============================================================
  //get user roles

  const userRole =
    user?.organization_memberships?.[0]?.role?.name;
  //===========================================================

  /*
  |--------------------------------------------------------------------------
  | JSX
  |--------------------------------------------------------------------------
  */

  return (
    <>
      <aside className={`sidebar ${isOpen ? "sidebar-open" : ""}`}>
        {isOpen && (
          <button
            className="sidebar-toggle-btn"
            onClick={onMenuToggle}
            aria-label="Close sidebar"
            title="Close sidebar"
          >
            <PanelLeftClose size={18} strokeWidth={2} aria-hidden="true" />
          </button>
        )}

        {/* =====================================================
          LOGO
      ====================================================== */}

        <div className="sidebar-logo">

          <div
            className="logo-mark"
            style={{
              flexDirection: "column",
              alignItems: "flex-start",
              gap: "6px",
            }}
          >

            <div id="sidebar-logo-img">

              <img
                src={logo}
                alt="Logo"
              />

            </div>

            <div
              className="logo-sub"
              style={{
                fontSize: "10px",
                color: "var(--text3)",
                letterSpacing: "1px",
                textTransform: "uppercase",
                paddingLeft: "2px",
              }}
            >
              OKR Portal · Enterprise
            </div>

          </div>

        </div>


        {/* =====================================================
          NAVIGATION
      ====================================================== */}

        <nav className="sidebar-nav">

          {/* ================= MAIN ================= */}

          {(hasModuleAccess(userRole, "DASHBOARD") ||
            hasModuleAccess(userRole, "MY_OKR") ||
            hasModuleAccess(userRole, "TEAM_OKR")) && (
            <div className="nav-section-label">Main</div>
          )}

          {hasModuleAccess(userRole, "DASHBOARD") && (
            <NavLink
              to="/dashboard"
              className="nav-item"
              onClick={() => handleNavClick("/dashboard")}
            >
              <LayoutDashboard size={18} strokeWidth={2} />
              <span>Dashboard</span>
            </NavLink>
          )}

          {hasModuleAccess(userRole, "MY_OKR") && (
            <NavLink
              to="/my-okr"
              className="nav-item"
              onClick={() => handleNavClick("/my-okr")}
            >
              <Target size={18} strokeWidth={2} />
              <span>My OKR</span>
            </NavLink>
          )}

          {hasModuleAccess(userRole, "TEAM_OKR") && (
            <NavLink
              to="/team-okr"
              className="nav-item"
              onClick={() => handleNavClick("/team-okr")}
            >
              <Users size={18} strokeWidth={2} />
              <span>Team OKR</span>
            </NavLink>
          )}

          {/* ================= ANALYTICS ================= */}

          {(hasModuleAccess(userRole, "PERFORMANCE") ||
            hasModuleAccess(userRole, "LEADERBOARD")) && (
            <div className="nav-section-label">Analytics</div>
          )}

          {hasModuleAccess(userRole, "PERFORMANCE") && (
            <NavLink
              to="/performance"
              className="nav-item"
              onClick={() => handleNavClick("/performance")}
            >
              <ChartNoAxesCombined size={18} strokeWidth={2} />
              <span>Performance</span>
            </NavLink>
          )}

          {hasModuleAccess(userRole, "LEADERBOARD") && (
            <NavLink
              to="/leaderboard"
              className="nav-item"
              onClick={() => handleNavClick("/leaderboard")}
            >
              <Trophy size={18} strokeWidth={2} />
              <span>Leaderboard</span>
            </NavLink>
          )}

          {/* ================= SUPPORT ================= */}

          {(hasModuleAccess(userRole, "RAISE_QUERY") ||
            hasModuleAccess(userRole, "MANAGE_QUERY")) && (
            <div className="nav-section-label">Support</div>
          )}

          {hasModuleAccess(userRole, "RAISE_QUERY") && (
            <NavLink
              to="/raise-query"
              className="nav-item"
              onClick={() => handleNavClick("/raise-query")}
            >
              <MessageCircleQuestion size={18} strokeWidth={2} />
              <span>Raise Query</span>
            </NavLink>
          )}

          {hasModuleAccess(userRole, "MANAGE_QUERY") && (
            <NavLink
              to="/manage-query"
              className="nav-item"
              onClick={() => handleNavClick("/manage-query")}
            >
              <ClipboardList size={18} strokeWidth={2} />
              <span>Manage Query</span>
            </NavLink>
          )}

          {/* ================= Org members ================= */}

          {(hasModuleAccess(userRole, "ORGANIZATIONS") ||
            hasModuleAccess(userRole, "ROLES") ||
            hasModuleAccess(userRole, "USERS") ||
            hasModuleAccess(userRole, "BATCHES")) && (
            <>
              <div className="nav-section-label">
                Organization & Users
              </div>

              {hasModuleAccess(userRole, "ORGANIZATIONS") && (
                <NavLink
                  to="/organizations"
                  className="nav-item"
                  onClick={() => handleNavClick("/organizations")}
                >
                  <Building2 size={18} strokeWidth={2} />
                  <span>Organizations</span>
                </NavLink>
              )}

              {hasModuleAccess(userRole, "ROLES") && (
                <NavLink
                  to="/roles"
                  className="nav-item"
                  onClick={() => handleNavClick("/roles")}
                >
                  <UsersRound size={18} strokeWidth={2} />
                  <span>Roles</span>
                </NavLink>
              )}

              {hasModuleAccess(userRole, "USERS") && (
                <NavLink
                  to="/users"
                  className="nav-item"
                  onClick={() => handleNavClick("/users")}
                >
                  <UserRound size={18} strokeWidth={2} />
                  <span>Users</span>
                </NavLink>
              )}

              {hasModuleAccess(userRole, "BATCHES") && (
                <NavLink
                  to="/batches"
                  className="nav-item"
                  onClick={() => handleNavClick("/batches")}
                >
                  <UsersRound size={18} strokeWidth={2} />
                  <span>Batches</span>
                </NavLink>
              )}
            </>
          )}

          {/* ================= Manage OKR ================= */}

          {hasModuleAccess(userRole, "MANAGE_OKR") && (
            <NavLink
              to="/manage-okr"
              className="nav-item"
              onClick={() => handleNavClick("/manage-okr")}
            >
              <UsersRound size={18} strokeWidth={2} />
              <span>Manage OKR</span>
            </NavLink>
          )}

        </nav>


        {/* =====================================================
          USER PROFILE
      ====================================================== */}

        <div
          ref={profileRef}
          className={`sidebar-footer ${profileUser
            ? "show-profile"
            : "hide-profile"
            }`}
          onClick={openUserProfile}
        >

          <div className="user-card">


            {/* ================= AVATAR ================= */}



            {/* ================= USER INFORMATION ================= */}

            <div className="user-info-container">

              <div className="user-name">
                <div className="user-info">
                  <div className="user-avatar">

                    {getUserInitials()}

                  </div>

                  <div>
                    {user
                      ? `${user.first_name} ${user.last_name}`
                      : "Loading..."}

                  </div>
                </div>
                <div>
                  <button
                    className="logout-button"
                    onClick={(event) => {

                      event.stopPropagation();

                      handleLogout();

                    }}
                  >

                    Logout

                  </button>

                </div>
              </div>


              <div className="user-role">

                {user?.organization_memberships?.[0]?.organization_name}

              </div>


              {/* =================================================
                EXTRA PROFILE DETAILS
            ================================================== */}

              {profileUser && (

                <div className="profile-details">

                  <div className="user-contact">

                    📞 {user?.phone || "No phone available"}

                  </div>


                  <div className="user-contact">

                    ✉️ {user?.email || "No email available"}

                  </div>


                  <div className="user-contact">

                    💼 {user?.designation || "No designation available"}

                  </div>


                  <div className="user-contact">

                    📝 {user?.description || "No description available"}

                  </div>


                  {/* ================= LOGOUT ================= */}



                </div>

              )}

            </div>

          </div>

        </div>

      </aside>
    </>
  );
}

export default Sidebar;