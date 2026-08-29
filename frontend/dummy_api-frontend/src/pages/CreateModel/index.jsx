import ModelForm from "../../components/ModelForm"
import { useContext, useEffect } from "react"
import { AppContext } from "../../context"
import { useParams } from "react-router-dom"
import ErrorElement from "../../components/ErrorElement"

const Index = () => {
    const params = useParams()
    const { loading, fetchApiDetail, apiDetail, apiDetailNotFound } = useContext(AppContext)
    useEffect(() => {
        let cancelled = false
        if (!apiDetail) fetchApiDetail(params.apiId, cancelled)
        return () => {
            cancelled = true
        }
    }, [params.apiId, apiDetail, fetchApiDetail])
    const mParam = {
        name: "",
        description: "",
        tbl_params: []
    }
    return (
        <>
            {
                loading ? "" : !loading && !apiDetail && apiDetailNotFound ? <ErrorElement /> : <ModelForm fList={[]} mParam={mParam} title={"CREATE NEW MODEL"} btnTitle="CREATE" method="POST" endpoint="create_model" />

            }
        </>
    )
}

export default Index
