import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import Login from './pages/Login'
import Register from './pages/Register'
import MyApi from './pages/MyApi'
import CreateAPI from "./pages/CreateAPI"
import MyApiDetail from "./pages/MyApiDetail"
import ModelPage from "./pages/ModelPage"
import CreateModel from "./pages/CreateModel"
import RedirectPage from './components/RedirectPage.jsx'
import AppProvider from './context.jsx';
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
    element: <RequireAuth><MyApi /></RequireAuth>,
    children: [
      {
        path: "",
        element: <HomePage />
      },
      {
        path: "test_endpoint",
        element: <TestEndpoint />
      },
      {
        path: ":apiId",
        element: <MyApiDetail />
      },
      {
        path: "create",
        element: <CreateAPI />
      },
      {
        path: ":apiId/edit",
        element: <EditApiPage />
      },
      {
        path: ":apiId/model/create",
        element: <CreateModel />
      },
      {
        path: ":apiId/model/:modelName",
        element: <ModelPage />
      },
      {
        path: ":apiId/model/:modelName/edit",
        element: <EditModel />
      }

    ]
  },
]);


ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <AppProvider>
      <RouterProvider router={router} />
    </AppProvider>
  </React.StrictMode>,
)
