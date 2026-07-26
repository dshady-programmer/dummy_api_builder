import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import Login from './pages/Login'
import Register from './pages/Register'
import Root from './pages/root.jsx'
import CreateAPI from "./pages/CreateAPI"
import MyApiDetail from "./pages/MyApiDetail"
import ModelPage from "./pages/ModelPage"
import CreateModel from "./pages/CreateModel"
import RedirectPage from './components/RedirectPage.jsx'
import HomePage from "./pages/HomePage"
import EditApiPage from "./pages/EditApiPage"
import EditModel from "./pages/EditModel"
import TestEndpoint from "./pages/TestEndpoint"
import './index.scss'
import {
  createBrowserRouter,
  RouterProvider,
} from "react-router-dom";
import ErrorPage from './error-page.jsx'
import RequireAuth from './components/RequireAuth.jsx'

const router = createBrowserRouter([
  {
    path: "/",
    element: <RedirectPage><App /></RedirectPage>,
    errorElement: <ErrorPage />
  },
  {
    path: '/login',
    element: <RedirectPage><Login /></RedirectPage>,
  },
  {

    path: '/register',
    element: <RedirectPage><Register /></RedirectPage>
  },
  {
    path: '/my_apis',
    element: <RequireAuth><Root /></RequireAuth>,
    children: [
      {
        path: "",
        element: <RequireAuth><HomePage /></RequireAuth>
      },
      {
        path: "test_endpoint",
        element: <RequireAuth><TestEndpoint /></RequireAuth>
      },
      {
        path: ":apiId",
        element: <RequireAuth><MyApiDetail /></RequireAuth>
      },
      {
        path: "create",
        element: <RequireAuth><CreateAPI /></RequireAuth>
      },
      {
        path: ":apiId/edit",
        element: <RequireAuth><EditApiPage /></RequireAuth>
      },
      {
        path: ":apiId/model/create",
        element: <RequireAuth><CreateModel /></RequireAuth>
      },
      {
        path: ":apiId/model/:modelId",
        element: <RequireAuth><ModelPage /></RequireAuth>
      },
      {
        path: ":apiId/model/:modelId/edit",
        element: <RequireAuth><EditModel /></RequireAuth>
      }

    ]
  },
]);


ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
      <RouterProvider router={router} />
  </React.StrictMode>,
)
