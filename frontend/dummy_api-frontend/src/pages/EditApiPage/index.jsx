import { useEffect, useContext } from 'react'
import FormCreatePage from "../../components/FormCreatePage"
import { useParams } from 'react-router-dom'
import { AppContext } from '../../context'
import { Bars } from 'react-loader-spinner'
import ErrorElement from "../../components/ErrorElement"
const Index = () => {
    const { fetchApiDetail, apiDetail, apiDetailNotFound, loading } = useContext(AppContext)
    const params = useParams()
    useEffect(() => {
        let cancelled = false
        fetchApiDetail(params.apiId, cancelled)
        return () => cancelled = true
    }, [fetchApiDetail, params.apiId])
    return (
        <>
            {
                loading ? <div className="loading-wrapper">

                    <Bars
                        height="80"
                        width="80"
                        color="#44859F"
                        ariaLabel="bars-loading"
                        wrapperStyle={{}}
                        wrapperClass="loading_element"
                        visible={true}
                    />
                </div> : !loading && !apiDetail && apiDetailNotFound ? <ErrorElement /> :
                    <FormCreatePage title="EDIT API" nameValue={apiDetail.name} descValue={apiDetail.description} buttonTitle="EDIT" endpoint={`update_api/${params.apiId}`} method="PUT" />

            }
        </>
    )
}

export default Index
