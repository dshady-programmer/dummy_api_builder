import React from "react"
import Cookies from "js-cookie";
import { hostUrl } from "./variables";
import { useNavigate } from "react-router-dom";

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
    const navigate = useNavigate();



    const fetchApiDetail = async (apiId) => {
        const token = Cookies.get('token', { path: '/' })
        setLoading(true)
        try {
            const response = await fetch(`${hostUrl}/api/v1/my_api/${apiId}`, {
            headers: {
                    'x-access-token': token
                }
            });
            const data = await response.json();
            if (response.status === 200) {

                setApiDetail(data)
            } else {
                setApiDetail(null)

                if (response.status === 401) {
                    Cookies.remove("token", { path: '/' })
                    navigate("/login", { replace: true, state: { path: location.pathname } })
                }

                
            }
        } catch (err) {
            console.log("error fetching api detail", err)
            setApiDetail(null)
        } finally {
            setLoading(false)
        }

    }
    const fetchApis = async () => {
        const token = Cookies.get('token', { path: '/' })
        setApiLoading(true)
        try {

            const response = await fetch(`${hostUrl}/api/v1/my_apis`, {
                headers: {
                    'x-access-token': token
                }
            });
            const data = await response.json();
            if (response.status === 200) setApis(data)
            else {
                setApis(null)

                if (response.status === 401) {
                    Cookies.remove("token", { path: '/' })
                    navigate("/login", { replace: true, state: { path: location.pathname } })
                }

                
            }
        } catch (err) {
            console.log("error fetchin apis", err)
            setApis(null)
        } finally {

            setApiLoading(false)
        } 
        
    }
    const fetchUser = async () => {
        const token = Cookies.get('token', { path: '/' })
        setUserLoading(true)
        try {

            const response = await fetch(`${hostUrl}/api/v1/me`, {
                headers: {
                    'x-access-token': token
                }
            });
            const data = await response.json();
            if (response.status === 200) setUser(data)
            else {
                setUser(null)

                if (response.status === 401) {
                    Cookies.remove("token", { path: '/' })
                    navigate("/login", { replace: true, state: { path: location.pathname } })
                }
                
            }
        } catch (err) {
            console.log('error fetching user', err)
            setUser(null)
        } finally {

            setUserLoading(false) 
        }
    }
    const fetchModel = async (apiId, modelName) => {
        const token = Cookies.get('token', { path: '/' })
        setLoading(true)
        try {
            
            const response = await fetch(`${hostUrl}/api/v1/my_api/${apiId}/show_model/${modelName}`, {
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
    }
    return (<AppContext.Provider value={{
        user, fetchUser, apis, fetchApis, model, fetchModel,
        loading, userLoading, invalidate, setInvalidate,
        apiDetail, fetchApiDetail, apiLoading
    }}> {children} </AppContext.Provider>)
}
export default AppProvider;