import "./index.scss";
import { useState, useContext } from "react";
import { AppContext } from "../../context";
import { useNavigate } from "react-router-dom";
import Cookies from "js-cookie";
import { hostUrl } from "../../variables";
import { Rings } from "react-loader-spinner";

const Index = ({ title, nameValue, descValue, buttonTitle, endpoint, method }) => {
    const { setInvalidate } = useContext(AppContext)
    const token = Cookies.get('token', { path: '/' })
    const [apiData, setApiData] = useState({ name: nameValue, description: descValue })
    const navigate = useNavigate()
    const [loading, setLoading] = useState(false)
    const [state, setState] = useState({ type: "", message: "" })
    const handleChange = (e) => {
        if (state.type) setState({ type: "", message: "" })
        let value = e.target.value
        if (e.target.name === "name") value = value.trim()
        setApiData(prevData => ({ ...prevData, [e.target.name]: value }))
    }
    const handleSubmit = async e => {
        e.preventDefault()
        setState({ type: "", message: "" })
        if (!apiData.name) {
            setState({ type: "error", message: "Provide a name for the api" })
            return;
        }
        setLoading(true)

        try {
            const res = await fetch(`${hostUrl}/api/v1/${endpoint}`, {
                method: method,
                headers: {
                    "Content-Type": "application/json",
                    "x-access-token": token
                },
                body: JSON.stringify(apiData)
            })

            const data = await res.json()
            if (res.status === 401) {
                Cookies.remove("token", { path: '/' })
                navigate("/login", { replace: true, state: { path: location.pathname } })
            }
            if (res.status !== 200 && data.error) {
                setState({ type: "error", message: data.error })
            } else if (res.status === 200) {
                setInvalidate(true)
                navigate(`/my_apis/${data.id}`)
            }

        } catch (err) {
            setState({ type: "error", message: "An error occured" })
        } finally {
            setLoading(false)
        }

    }
    return (
        <div className="create-wrapper">
            <section className="create_header">
                <h2>{title}</h2>
            </section>
            <section className="create_form">
                <form action="." onSubmit={handleSubmit}>
                    <div>
                        <label htmlFor="name">Name</label>
                        <input type="text" id="name" name="name" onChange={handleChange} value={apiData.name} />
                    </div>
                    <div>
                        <label htmlFor="desc">Description</label>
                        <textarea name="description" id="desc" onChange={handleChange} value={apiData.description}></textarea>
                    </div>
                    {
                        state.type === "error" && <div className="api_create_error_card">
                            {state.message}
                        </div>
                    }

                    <button>
                        {
                            loading ?
                                <Rings
                                    height="30"
                                    width="30"
                                    color="#FFF"
                                    radius="6"
                                    wrapperStyle={{}}
                                    wrapperClass="api-create_spinner"
                                    visible={true}
                                    ariaLabel="rings-loading"
                                /> : buttonTitle
                        }
                    </button>
                </form>
            </section>
        </div>
    )
}

export default Index