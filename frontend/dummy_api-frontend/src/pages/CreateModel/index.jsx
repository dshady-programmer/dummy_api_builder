import ModelForm from "../../components/ModelForm"
import { useContext, useEffect } from "react"
import { AppContext } from "../../context"
import { useParams } from "react-router-dom"
import ErrorElement from "../../components/ErrorElement"
import { Bars } from 'react-loader-spinner'

const Index = () => {
    const params = useParams()
    const { apiDetailLoading, fetchApiDetail, apiDetail, apiDetailNotFound } = useContext(AppContext)

    useEffect(() => {

        const controller = new AbortController();

        if (!apiDetail)
            fetchApiDetail(params.apiId, controller.signal)
        return () => controller.abort() // automatically cancels the fetch and triggers abort error
    }, [params.apiId, fetchApiDetail, apiDetail])

    const mParam = {
        name: "",
        description: "",
        tbl_params: []
    }
    return (
        <>
            {
                apiDetailLoading ? <div className="loading-wrapper">

                    <Bars
                        height="80"
                        width="80"
                        color="#44859F"
                        ariaLabel="bars-loading"
                        wrapperStyle={{}}
                        wrapperClass="loading_element"
                        visible={true}
                    />
                </div> :
                (!apiDetailLoading && !apiDetail) ? <ErrorElement /> :  (!apiDetailLoading && apiDetailNotFound) ? <ErrorElement notFound={true}/>  : 
                
                <ModelForm fList={[]} mParam={mParam} title={"CREATE NEW MODEL"} btnTitle="CREATE" method="POST" endpoint="create_model" />

            }
        </>
    )
}

export default Index
