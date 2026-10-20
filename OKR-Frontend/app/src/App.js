import logo from './logo.svg';
import RaiseQuery from './RaiseQuery/RaiseQuery';
import ManageQuery from './ManageQuery/ManageQuery';
import './App.css';
import { Routes, Route } from "react-router-dom";
import Login from './Login/Login';
import MyOkr from './MyOkr/MyOkr';
import Layout from './Layout/Layout';
import Roles from './Roles/Roles';
import Batches from './Batches/Batches';
import Dashboard from './Dashboard/Dashboard';
import Organizations from './Organizations/Organizations';
import Users from './Users/Users';
import ManageOKR from './ManageOKR/ManageOKR';
import Leaderboard from './Leaderboard/Leaderboard';
import TeamOkr from './TeamOkr/TeamOkr';
import Performance from './Performance/Performance';
import ProtectedRoute from './components/ProtectedRoute';

function App() {
  return (
    <Routes>

      {/* Public */}
      <Route
        path="/"
        element={<Login />}
      />

      {/* Common Layout */}
      <Route element={<Layout />}>


        <Route
          path="/my-okr"
          element={
            <ProtectedRoute module="MY_OKR">
              <MyOkr />
            </ProtectedRoute>
          }
        />

        <Route
          path="/organizations"
          element={
            <ProtectedRoute module="ORGANIZATIONS">
              <Organizations />
            </ProtectedRoute>
          }
        />

        <Route
          path="/leaderboard"
          element={
            <ProtectedRoute module="LEADERBOARD">
              <Leaderboard />
            </ProtectedRoute>
          }
        />

        <Route
          path="/performance"
          element={
            <ProtectedRoute module="PERFORMANCE">
              <Performance />
            </ProtectedRoute>
          }
        />

        <Route
          path="/users"
          element={
            <ProtectedRoute module="USERS">
              <Users />
            </ProtectedRoute>
          }
        />

        <Route
          path="/roles"
          element={
            <ProtectedRoute module="ROLES">
              <Roles />
            </ProtectedRoute>
          }
        />

        <Route
          path="/batches"
          element={
            <ProtectedRoute module="BATCHES">
              <Batches />
            </ProtectedRoute>
          }
        />

        <Route
          path="/manage-okr"
          element={
            <ProtectedRoute module="MANAGE_OKR">
              <ManageOKR />
            </ProtectedRoute>
          }
        />

        <Route
          path="/raise-query"
          element={
            <ProtectedRoute module="RAISE_QUERY">
              <RaiseQuery />
            </ProtectedRoute>
          }
        />

        <Route
          path="/manage-query"
          element={
            <ProtectedRoute module="MANAGE_QUERY">
              <ManageQuery />
            </ProtectedRoute>
          }
        />


        <Route
          path="/team-okr"
          element={
            <ProtectedRoute module="TEAM_OKR">
              <TeamOkr />
            </ProtectedRoute>
          }
        />


        <Route
          path="/dashboard"
          element={
            <ProtectedRoute module="DASHBOARD">
              <Dashboard />
            </ProtectedRoute>
          }
        />

      </Route>


    </Routes>
  );
}

export default App;