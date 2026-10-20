import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import { API_URL } from "../Config/ApiEndpoint";
import { hasModuleAccess } from "../Config/modulePermissions";

function ProtectedRoute({ module, children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchUser = async () => {
      const token = localStorage.getItem("token");

      if (!token) {
        setLoading(false);
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

        if (!response.ok) {
          localStorage.removeItem("token");
          localStorage.removeItem("refresh_token");
          setUser(null);
          return;
        }

        const data = await response.json();
        setUser(data);
      } catch (error) {
        console.error(
          "Failed to verify user:",
          error
        );

        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    fetchUser();
  }, []);

  if (loading) {
    return <div>Loading...</div>;
  }

  if (!user) {
    return <Navigate to="/" replace />;
  }

  const userRole =
    user?.organization_memberships?.[0]?.role?.name;

  if (!hasModuleAccess(userRole, module)) {
    return <Navigate to="/my-okr" replace />;
  }

  return children;
}

export default ProtectedRoute;
