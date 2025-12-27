import Cookies from "js-cookie"
import { Navigate } from 'react-router-dom';
const RequireAuth = (props) => {
    const token = Cookies.get('token', { path: '/' });
    console.log('RequireAuth token:', token);
    if (!token) {
        return <Navigate to="/login" state={{ path: location.pathname }} replace={true} />
    }
    return (
        <>
            {props.children}
        </>
    )
}

export default RequireAuth
