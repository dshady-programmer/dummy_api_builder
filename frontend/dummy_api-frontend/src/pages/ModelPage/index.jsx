import "./index.scss"
import { useContext, useEffect } from "react"
import { AppContext } from "../../context"
import { useParams, useNavigate } from "react-router-dom"
import { Bars } from "react-loader-spinner"
import ErrorElement from "../../components/ErrorElement"
import Cookies from "js-cookie"
import { hostUrl } from "../../variables"

const Index = () => {
    const navigate = useNavigate()
    const { fetchModel, model, loading } = useContext(AppContext)
    const token = Cookies.get('token', { path: '/' })
    const params = useParams()
    const apiId = params.apiId
    const modelName = params.modelName


    useEffect(() => {
        fetchModel(apiId, modelName)
    }, [apiId, modelName])

    if (loading) {
        return <div className="loading-wrapper">

            <Bars
                height="80"
                width="80"
                color="#44859F"
                ariaLabel="bars-loading"
                wrapperStyle={{}}
                wrapperClass="loading_element"
                visible={true}
            />
        </div>
    }
    return (
        <div className="modelPage-wrapper">
            {
                !loading && !model ? <ErrorElement /> : <>
                    <section className="modelPage_header">
                        <h2>{model?.name}</h2>
                        <p>{model?.desc}</p>
                    </section>

                    <section className="modelPage_body">
                        <table>
                            <thead>
                                <tr>
                                    <th>
                                        Fields
                                    </th>
                                    <th>
                                        Field Type
                                    </th>
                                    <th>
                                        Field Length
                                    </th>
                                    <th>
                                        Field Constraints
                                    </th>
                                    <th>
                                        FK Ref. Table
                                    </th>
                                </tr>
                            </thead>
                            <tbody>
                                {
                                    model && model.table_params?.map(tbl_param => {
                                        return <tr key={tbl_param.index}>
                                            <td>{tbl_param.name}</td>
                                            <td>{tbl_param.datatype}</td>
                                            <td>{tbl_param.dt_length || "Null"}</td>
                                            <td>{tbl_param.constraints.join(", ")}</td>
                                            <td>{tbl_param.foreign_key_rf || "N/A"}</td>
                                        </tr>
                                    })
                                }

                            </tbody>
                        </table>
                    </section>
                    <section className="modelPage_btns">
                        <button onClick={() => navigate('edit')}>Edit Model</button>
                        <button style={{ backgroundColor: "red" }} onClick={async () => {
                            const res = await fetch(`${hostUrl}/api/v1/my_api/${params.apiId}/delete_model/${params.modelName}`, {
                                method: "DELETE",
                                headers: {
                                    "Content-Type": "application/json",
                                    "x-access-token": token
                                },
                            })
                            if (res.status === 204) {
                                alert("Model deleted successfully")
                            }
                            
                            navigate(`/my_apis/${params.apiId}`)

                        }}>Delete Model</button>
                    </section>
                </>
            }

        </div>
    )
}

export default Index
