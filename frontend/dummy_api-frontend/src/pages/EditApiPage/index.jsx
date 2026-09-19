import { useEffect, useContext } from 'react'
import FormCreatePage from "../../components/FormCreatePage"
import { useParams } from 'react-router-dom'
import { AppContext } from '../../context'
import { Bars } from 'react-loader-spinner'
import ErrorElement from "../../components/ErrorElement"
const Index = () => {
    const { fetchApiDetail, apiDetail, apiDetailNotFound, apiDetailLoading } = useContext(AppContext)
    const params = useParams()
    useEffect(() => {

        const controller = new AbortController();

        if (!apiDetail)
            fetchApiDetail(params.apiId, controller.signal)
        return () => controller.abort() // automatically cancels the fetch and triggers abort error
    }, [params.apiId, fetchApiDetail, apiDetail])

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
                </div> : (!apiDetailLoading && !apiDetail) ? <ErrorElement /> :  (!apiDetailLoading && apiDetailNotFound) ? <ErrorElement notFound={true}/> :
                    <FormCreatePage title="EDIT API" nameValue={apiDetail.name} descValue={apiDetail.description} buttonTitle="EDIT" endpoint={`update_api/${params.apiId}`} method="PUT" />

            }
        </>
    )
}

export default Index
