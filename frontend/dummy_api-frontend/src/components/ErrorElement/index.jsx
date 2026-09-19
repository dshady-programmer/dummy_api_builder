import errorImg from "../../assets/errorPage.svg"
import genericErrorImg from "../../assets/genericErrorPage.svg"
import "./index.scss"
const Index = ({notFound = false}) => {
    return (
        <div className="error-element_wrapper">
            
            <img src={notFound ? errorImg : genericErrorImg} alt="" />
        </div>
    )
}

export default Index
