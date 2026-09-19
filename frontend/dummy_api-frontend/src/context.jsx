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
    const [modelLoading, setModelLoading] = React.useState(true)
    const [apiLoading, setApiLoading] = React.useState(true)
    const [userLoading, setUserLoading] = React.useState(false)
    const [invalidate, setInvalidate] = React.useState(false)
    const [apiDetail, setApiDetail] = React.useState(null)
    const [apiDetailLoading, setApiDetaiLoading] = React.useState(true)
    const [apiDetailNotFound, setApiDetailNotFound] = React.useState(false)
    const [modelDetailNotFound, setModelDetailNotFound] = React.useState(false)
    const navigate = useNavigate();



    const fetchApiDetail = useCallback(async (apiId, signal, retries=1) => {
   
        console.log('retries', retries)
        let abortError = false;

        setApiDetaiLoading(true)
        setApiDetailNotFound(false)
        const token = Cookies.get('token', { path: '/' })
        try {
            const response = await fetch(`${hostUrl}/api/v1/my_api/${apiId}`, {
            signal, // prevent a stale fetch from overriding current request state.
            headers: {
                    'x-access-token': token
                }
            });
            const data = await response.json();
            if (response.status === 200) {

                setApiDetail(data.data)
            } 
            else if (response.status >= 500) {
                setApiDetail(null)
                if (retries < 4) {
                    return setTimeout(
                        () => fetchApiDetail(apiId, signal, retries + 1), 
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
            if (err.name === "AbortError") {
                console.log('fetch safely aborted')
                abortError = true
                return
            }
            if (retries < 4) {
                setApiDetail(null)
                return setTimeout(
                    () => fetchApiDetail(apiId, signal, retries + 1), 
                    1000 * retries ** (Math.round(Math.random() * retries) || 1)
                )
            }
            
        } finally {
            if (!abortError)
                setApiDetaiLoading(false)
        }

    }, [navigate])


    const fetchApis = useCallback(async (signal, retries=1) => {
        
        setApiLoading(true)
        let abortError = false

        const token = Cookies.get('token', { path: '/' })
        try {

            const response = await fetch(`${hostUrl}/api/v1/my_apis`, {
                signal,
                headers: {
                    'x-access-token': token
                }
            });
            const data = await response.json();


            if (response.status === 200) {
                setApis(data.data)
                setInvalidate(false)
            }
            else if (response.status >= 500) {
                if (retries < 4) {
                    return setTimeout(
                        () => fetchApis(signal, retries + 1), 
                        1000 * retries ** (Math.round(Math.random() * retries) || 1)
                    )
                }
                setApis(null)
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
            if (err.name === "AbortError") {
                console.log('fetch safely aborted')
                abortError = true
                return
            }
            if (retries < 4) {
                return setTimeout(
                    () => fetchApis(signal, retries + 1), 
                    1000 * retries ** (Math.round(Math.random() * retries) || 1)
                )
            }
            setApis(null)
        } finally {
            if (!abortError)
                setApiLoading(false)
        }
        
    }, [navigate])

    const fetchUser = useCallback(async (signal, retries=1) => {

        let abortError = false
        setUserLoading(true)
        
        const token = Cookies.get('token', { path: '/' })
    
        try {

            const response = await fetch(`${hostUrl}/api/v1/me`, {
                signal, 
                headers: {
                    'x-access-token': token
                }
            });
            const data = await response.json();
            if (response.status === 200) setUser(data.data)
            else if (response.status >= 500) {
                if (retries < 4) {
                    return setTimeout(
                        () => fetchUser(signal, retries + 1), 
                        1000 * retries ** (Math.round(Math.random() * retries) || 1)
                    )
                }
                setUser(null)
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
            if (err.name === "AbortError") {
                console.log('fetch safely aborted')
                abortError = true
                return
            }

            if (retries < 4) {
                return setTimeout(
                    () => fetchUser(signal, retries + 1), 
                    1000 * retries ** (Math.round(Math.random() * retries) || 1)
                )
                
            }
            setUser(null)
            
        } finally {
            if (!abortError)
                setUserLoading(false) 
        }
    }, [navigate])

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

    const fetchModel = useCallback(async (apiId, modelId, signal=undefined, retries=1) => {
        
        let abortError = false
        setModelLoading(true)

        setModelDetailNotFound(false)
        const token = Cookies.get('token', { path: '/' })

        try {
            
            const response = await fetch(`${hostUrl}/api/v1/my_api/${apiId}/show_model/${modelId}`, {
                signal, 
                headers: {
                    'x-access-token': token
                }
            });
            const data = await response.json();
            // console.log('data', data)
            if (response.status === 200) setModel(data.data)
            else if (response.status >= 500) {
                
                if (retries < 4) {
                    setTimeout(
                        () => fetchModel(apiId, modelId, signal, retries + 1), 
                        1000 * retries ** (Math.round(Math.random() * retries) || 1)
                    )
                }
                setModel(null)
            }
            else {
                setModel(null)

                if (response.status === 401) {
                    Cookies.remove("token", { path: '/' })
                    navigate("/login", { replace: true, state: { path: location.pathname } })
                } else if (response.status === 404) {
                    setModelDetailNotFound(true)
                }

            }
        } catch (err) {
            console.log('error fetching model', err)
            if (err.name === "AbortError") {
                console.log('fetch safely aborted')
                abortError = true
                return
            }
            if (retries < 4) {
                setTimeout(
                    () => fetchModel(apiId, modelId, signal, retries + 1), 
                    1000 * retries ** (Math.round(Math.random() * retries) || 1)
                )
            }
            
            setModel(null)
        } finally {
            
            if (!abortError)
                setModelLoading(false)
        }
    }, [navigate])

    return (<AppContext.Provider value={{
        user, fetchUser, apis, fetchApis, model, fetchModel,
        modelLoading, userLoading, invalidate, setInvalidate,
        apiDetail, fetchApiDetail, apiLoading, logoutUser, 
        apiDetailNotFound, apiDetailLoading, modelDetailNotFound
    }}> {children} </AppContext.Provider>)
}
export default AppProvider;