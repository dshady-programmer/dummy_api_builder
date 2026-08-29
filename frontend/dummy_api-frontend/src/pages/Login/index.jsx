import Header from '../../components/Header';
import Footer from '../../components/Footer';
import "./index.scss"
import desktop_logo from "../../assets/logo_desktop.svg"
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useState } from 'react';
import Cookies from 'js-cookie'
import { hostUrl } from '../../variables';
import { Rings } from "react-loader-spinner"


function Index() {
    const location = useLocation()
    const navigate = useNavigate()
    const [credentials, setCredentials] = useState({ email: "", password: "" })
    const [status, setStatus] = useState({ type: "", message: "" })
    const [loading, setLoading] = useState(false)

    const handleChange = (e) => {
        if (status.type.length)
            setStatus({ type: "", message: "" });
        setCredentials(prevCred => ({ ...prevCred, [e.target.name]: e.target.value.trim() }));
    }
    const handleSubmit = async e => {
        e.preventDefault()
        if (loading) return
        setStatus({ type: "", message: "" });
        if (!credentials.password && !credentials.email) {
            setStatus({ type: "error", message: "All fields must be filled" })
            return;
        }
        setLoading(true)
        try {
            const req = await fetch(`${hostUrl}/api/v1/login`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    "email": credentials.email,
                    "password": credentials.password,
                })
            })
            // console.log(req, req.statusText)
            const data = await req.json();
            if (req.status === 401)
                setStatus({ type: data.status, message: data.message })
            else if (req.status === 200) {
                setStatus({ type: "success", message: "Login Succesful" })
                Cookies.set('token', data.data, { path: '/', expires: (1) })
                setTimeout(() => {
                    if (location.state?.path)
                        navigate(location.state.path)
                    else
                        navigate('/my_apis')
                }, 2000)
            }
        } catch (err) {
            console.log(err)
            setStatus({ type: "error", message: "Sorry!, an error occured, Check your internet connection" })
        } finally {
            setLoading(false)
        }
    }
    const navs = [
        {
            title: "LOGIN",
            path: '/login'
        },
        {
            title: "SIGN UP",
            path: '/register'
        }
    ]

    return (
        <div>
            <Header navs={navs} activeNav="LOGIN" />

            <section className='login-section'>
                <div className='auth-section-wrapper'>
                    <img src={desktop_logo} alt="" />
                    <section>
                        <form onSubmit={handleSubmit}>
                            <div>
                                <label htmlFor="email">Email</label>
                                <input name="email" type="email" onChange={handleChange} placeholder='email@email.com' id="email" />
                            </div>
                            <div>
                                <label htmlFor="password">Password</label>
                                <input name="password" type="password" onChange={handleChange} placeholder='*************' id="password" />
                            </div>
                            {
                                status.type && (<div className={`
                                    form-card
                                    ${status.type === "error" ?
                                        "form-error-card" :
                                        status.type === "redirect" ?
                                            "form-redirect-card" :
                                            "form-success-card"}
                                    `
                                }>
                                    {status.message}
                                </div>)
                            }

                            <button type="submit" disabled={loading}>
                                {loading ?
                                    <Rings
                                        height="30"
                                        width="30"
                                        color="#FFF"
                                        radius="6"
                                        wrapperStyle={{}}
                                        wrapperClass="auth-spinner"
                                        visible={true}
                                        ariaLabel="rings-loading"
                                    /> : "Login"
                                }

                            </button>
                        </form>
                        <Link to="/register">Create a new account</Link>
                    </section>
                </div>
            </section>
            <Footer />
        </div>
    )
}

export default Index
