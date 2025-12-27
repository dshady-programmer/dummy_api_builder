import './index.scss'
import desktop_logo from "../../assets/icon_lite_desktop.svg"
import { Link, useNavigate } from "react-router-dom"
import avatar from "../../assets/avatar.svg"
import caretDown from "../../assets/caret-white.svg"
import caretUp from "../../assets/caret-up-white.svg"
import { useContext, useState } from 'react'
import { AppContext } from '../../context'
import Cookies from 'js-cookie'
const Index = ({ navs, activeNav, type }) => {
    const context = useContext(AppContext);
    const user = context?.user;
    const [openUserInfo, setOpenUserInfo] = useState(false)
    const [openNav, setOpenNav] = useState(false)

    const navigate = useNavigate();
    const copyTextToClipboard = async (text) => {
        if ('clipboard' in navigator) {
            return await navigator.clipboard.writeText(text);
        } else {
            return document.execCommand('copy', true, text);
        }
    }

    return (
        <header>
            <div>
                <img src={desktop_logo} alt="" onClick={() => navigate('/')} />
                <ul>
                    {navs?.map((nav, index) => {

                        return (<li key={index} className={nav.title === activeNav ? "nav-active" : undefined}>
                            <Link to={nav.path}>{nav.title}</Link>
                        </li>)
                    })}

                    {
                        type === "landing" && <li> <a href='https://github.com/shady-cj/dummy_api_builder/tree/main' target="_blank" rel="noreferrer"> DOCS </a></li>
                    }
                    {
                        type == "apis" && <li>
                            <img src={avatar} alt="" />
                            <img src={openUserInfo ? caretUp : caretDown} alt="" onClick={() => setOpenUserInfo(prev => !prev)} />
                            {
                                openUserInfo && <div>
                                    <h3>{user?.email}</h3>
                                    <p>Api ID &nbsp;<span onClick={(e) => {
                                        copyTextToClipboard(user?.api_token)
                                        e.target.textContent = "copied"
                                        setTimeout(() => {
                                            e.target.textContent = "copy"
                                        }, 3000)
                                    }
                                    }>copy</span></p>
                                    <button onClick={() => {
                                        Cookies.remove("token", { path: '/' })
                                        navigate('/login', { replace: true})
                                    }}>Log out</button>
                                </div>
                            }

                        </li>
                    }

                </ul>
                <div onClick={() => setOpenNav(prevNav => !prevNav)} className={`menu-icon ${openNav ? `slide-out` : ''}`}>
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>

            <nav className={`${openNav ? '' : 'close'}`}>
                <ul>

                    {navs?.map((nav, index) => {

                        return (<li onClick={() => setOpenNav(prevNav => !prevNav)} key={index} className={nav.title === activeNav ? "nav-active" : undefined}>
                            <Link to={nav.path}>{nav.title}</Link>
                        </li>)
                    })}
                    {
                        type === "landing" && <li> <a href='https://github.com/shady-cj/dummy_api_builder/tree/main' target="_blank" rel="noreferrer"> DOCS </a></li>
                    }
                    {
                        type === "apis" && <><li style={{ textDecoration: "none" }}><h3>{user?.email}</h3>
                            <p><span onClick={(e) => {
                                copyTextToClipboard(user?.api_token)
                                e.target.textContent = "copied"
                                setTimeout(() => {
                                    e.target.textContent = "copy"
                                }, 3000)
                            }
                            }>copy</span></p></li>
                            <li style={{ textDecoration: "none" }}>
                                <button onClick={() => {
                                    Cookies.remove("token", { path: '/' })
                                    navigate('/login')
                                }}>Log out</button>
                            </li>
                        </>
                    }
                </ul>
            </nav>
        </header >
    )
}

export default Index
