import ModelForm from "../../components/ModelForm"
import { useContext, useEffect } from "react"
import { AppContext } from "../../context"
import { useParams } from "react-router-dom"
import { Bars } from "react-loader-spinner"
import ErrorElement from "../../components/ErrorElement"
const Index = () => {
    const { fetchModel, model, loading, modelDetailNotFound } = useContext(AppContext)
    const params = useParams()
    const apiId = params.apiId
    const modelId = params.modelId
    let mParam = {
        name: "",
        description: "",
        tbl_params: []
    }
    if (model && !loading) {
        mParam = {
            name: model.name,
            description: model.desc,
            tbl_params: model.table_params
        }
    }
    useEffect(() => {
        let cancelled = false
        fetchModel(apiId, modelId, cancelled)
        return () => cancelled = true
    }, [apiId, modelId, fetchModel])
    return (
        <>
            {
                loading ? <div className="loading-wrapper"><Bars height="80" width="80" color="#44859F" ariaLabel="bars-loading"
                    wrapperStyle={{}} wrapperClass="loading_element" visible={true} /> </div> : (!loading && !model) || (!loading && modelDetailNotFound) ? <ErrorElement /> : model ?
                        <ModelForm fList={model.table_params.map(p => p.index)} mParam={mParam} title={"EDIT MODEL"} btnTitle="EDIT" method="PUT" endpoint={`update_model/${modelId}`} />
                        : ""
            }
        </>
    )
}

export default Index
