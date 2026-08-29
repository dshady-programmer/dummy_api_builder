import React from "react"
import Cookies from "js-cookie";
import { hostUrl } from "./variables";
import { useNavigate } from "react-router-dom";

import { useCallback } from "react";

export const AppContext = React.createContext();

const AppProvider = ({ children }) => {
    const [user, setUser] = React.useState(null)
    const [apis, setApis] = React.useState(null)
    const [model, setModel] = React.useState(null)
    const [loading, setLoading] = React.useState(true)
    const [apiLoading, setApiLoading] = React.useState(false)
    const [userLoading, setUserLoading] = React.useState(false)
    const [invalidate, setInvalidate] = React.useState(false)
    const [apiDetail, setApiDetail] = React.useState(null)
    const [apiDetailNotFound, setApiDetailNotFound] = React.useState(false)
    const navigate = useNavigate();



    const fetchApiDetail = useCallback(async (apiId, cancelled=false, retries=1) => {
        if (loading && retries < 2) return
        const token = Cookies.get('token', { path: '/' })
        setLoading(true)
        try {
            const response = await fetch(`${hostUrl}/api/v1/my_api/${apiId}`, {
            headers: {
                    'x-access-token': token
                }
            });
            const data = await response.json();
            if (cancelled) return // prevent a stale fetch from overriding current request state.
            if (response.status === 200) {

                setApiDetail(data.data)
            } 
            else if (response.status >= 500) {
                if (retries < 4) {
                    setTimeout(
                        () => fetchApiDetail(apiId, false, retries + 1), 
                        1000 * retries ** (Math.round(Math.random() * retries) || 1)
                    )
                }
                
            }
            else {
                setApiDetail(null)

                if (response.status === 401) {
                    Cookies.remove("token", { path: '/' })
                    navigate("/login", { replace: true, state: { path: location.pathname } })
                } else if (response.status === 404) {
                    setApiDetailNotFound(true)
                }

                
            }
        } catch (err) {
            console.log("error fetching api detail", err)
            if (retries < 4) {
                setTimeout(
                    () => fetchApiDetail(apiId, false, retries + 1), 
                    1000 * retries ** (Math.round(Math.random() * retries) || 1)
                )
            }
            setApiDetail(null)
        } finally {
            setLoading(false)
        }

    }, [navigate, loading])
    const fetchApis = useCallback(async (retries=1) => {
        if (apiLoading && retries < 2) return
        const token = Cookies.get('token', { path: '/' })
        setApiLoading(true)
        try {

            const response = await fetch(`${hostUrl}/api/v1/my_apis`, {
                headers: {
                    'x-access-token': token
                }
            });
            const data = await response.json();
            if (response.status === 200) setApis(data.data)
            else if (response.status >= 500) {
                if (retries < 4 && !apis) {
                    setTimeout(
                        () => fetchApis(retries + 1), 
                        1000 * retries ** (Math.round(Math.random() * retries) || 1)
                    )
                }
                
            }
            else {
                setApis(null)
                if (response.status === 401) {
                    Cookies.remove("token", { path: '/' })
                    navigate("/login", { replace: true, state: { path: location.pathname } })
                }

                
            }
        } catch (err) {
            console.log("error fetchin apis", err)
            if (retries < 4 && !apis) {
                setTimeout(
                    () => fetchApis(retries + 1), 
                    1000 * retries ** (Math.round(Math.random() * retries) || 1)
                )
            }
        } finally {
            setApiLoading(false)
        }
        
    }, [navigate, apiLoading, apis])

    const fetchUser = useCallback(async (retries=1) => {
        if (userLoading && retries < 2) return
        const token = Cookies.get('token', { path: '/' })
        setUserLoading(true)
        try {

            const response = await fetch(`${hostUrl}/api/v1/me`, {
                headers: {
                    'x-access-token': token
                }
            });
            const data = await response.json();
            if (response.status === 200) setUser(data.data)
            else if (response.status >= 500) {
                if (retries < 4 && !user) {
                    setTimeout(
                        () => fetchUser(retries + 1), 
                        1000 * retries ** (Math.round(Math.random() * retries) || 1)
                    )
                }
                
            }
            else {
                setUser(null)

                if (response.status === 401) {
                    Cookies.remove("token", { path: '/' })
                    navigate("/login", { replace: true, state: { path: location.pathname } })
                }
                
            }
        } catch (err) {
            console.log('error fetching user', err)
            if (retries < 4 && !user) {
                setTimeout(
                    () => fetchUser(retries + 1), 
                    1000 * retries ** (Math.round(Math.random() * retries) || 1)
                )
            }
            
        } finally {

            setUserLoading(false) 
        }
    }, [navigate, userLoading, user])

    const logoutUser = useCallback(async () => {
        const token = Cookies.get('token', { path: '/' })
        try {
            const response = await fetch(`${hostUrl}/api/v1/logout`, {
                method: "POST",
                headers: {
                    'x-access-token': token
                }
            });
            if (response.status === 200 || response.status == 401) {
                Cookies.remove("token", { path: '/' })
                return true
            }
        } catch (err) {
            console.log("error", err)

        } 
        return false

    }, [])

    const fetchModel = useCallback(async (apiId, modelId) => {
        const token = Cookies.get('token', { path: '/' })
        setLoading(true)
        try {
            
            const response = await fetch(`${hostUrl}/api/v1/my_api/${apiId}/show_model/${modelId}`, {
                headers: {
                    'x-access-token': token
                }
            });
            const data = await response.json();
            if (response.status === 200) setModel(data)
            else {
                setModel(null)

                if (response.status === 401) {
                    Cookies.remove("token", { path: '/' })
                    navigate("/login", { replace: true, state: { path: location.pathname } })
                } 

            }
        } catch (err) {
            console.log('error fetching model', err)
            setModel(null)
        } finally {
            
            setLoading(false)
        }
    }, [navigate])

    return (<AppContext.Provider value={{
        user, fetchUser, apis, fetchApis, model, fetchModel,
        loading, userLoading, invalidate, setInvalidate,
        apiDetail, fetchApiDetail, apiLoading, logoutUser,
        apiDetailNotFound
    }}> {children} </AppContext.Provider>)
}
export default AppProvider;