import "./index.scss"
import { useContext, useState, useEffect, useRef } from "react"
import { AppContext } from "../../context"
import { useParams, useNavigate } from "react-router-dom"
import { Bars } from "react-loader-spinner"
import ErrorElement from "../../components/ErrorElement"
import Cookies from "js-cookie"
import { hostUrl } from "../../variables"



const Index = () => {
    const navigate = useNavigate()
    const { fetchModel, model, user, loading } = useContext(AppContext)
    const [openSeedPopup, setOpenSeedPopup] = useState(false)
    const token = Cookies.get('token', { path: '/' })
    const params = useParams()
    const apiId = params.apiId
    const modelName = params.modelName

    const deleteModel = async () => {
        const confirmDelete = confirm("Are you sure you want to delete this model? This action cannot be undone.")
        if (!confirmDelete) return;
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

    }
    const truncateTable = async () => {
        const confirmTruncate = confirm("Are you sure you want to truncate this model's table? This means all data in the table will be permanently deleted. This action cannot be undone.")
        if (!confirmTruncate) return;
        const res = await fetch(`${hostUrl}/api/v1/my_api/${params.apiId}/truncate_model/${params.modelName}`, {
                        method: "DELETE",   
                        headers: {
                            "Content-Type": "application/json",
                            "x-access-token": token
                        }, 
                    })
        if (res.status === 204) {
            fetchModel(apiId, modelName)
            alert("Model table truncated successfully")

        }
    }

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
                        {model ? <p><strong>Number of Entries:</strong> {model?.number_of_entries}</p> : ""}
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
                        <button onClick={() => setOpenSeedPopup(true)}>Seed Table</button>
                        <button style={{ backgroundColor: "red" }} onClick={truncateTable}>Truncate Table</button>
                        <button style={{ backgroundColor: "red" }} onClick={deleteModel}>Delete Model</button>
                    </section>
                    <SeedPopup openSeedPopup={openSeedPopup} user={user} model={model} setOpenSeedPopup={setOpenSeedPopup} refetchModel={() => fetchModel(apiId, modelName)}/>
                </>
            }

        </div>
    )
}


const SeedPopup = ({ openSeedPopup, setOpenSeedPopup, user, model, refetchModel }) => {
    const token = Cookies.get('token', { path: '/' })
    const [loading, setLoading] = useState(false)
    const [formResponse, setFormResponse] = useState(null)
    const stateChanged = useRef(false)
    const navigate = useNavigate()

    const closePopup = () => {
        setFormResponse(null)
        setOpenSeedPopup(false)
        if (stateChanged.current) refetchModel()
    }

    const handleFormSubmit = async (e) => {
        e.preventDefault()
        const formId = e.target.id
        const formData = new FormData(e.target)
        console.log("user", user, model)
        if (formId === "autogenerate_form") {
            const numRows = formData.get('num_rows') || 100

            // Handle auto-generate
        } else {

            const csvFile = formData.get('csv_file')
            const delimiter = formData.get('delimiter') || ","
            if (!loading && csvFile && csvFile.size > 0) {
                // Handle CSV import
                setLoading(true)

                const csvFormData = new FormData()
                csvFormData.append('csv_file', csvFile)
                csvFormData.append('delimiter', delimiter)
                try {
                    const response = await fetch(`${hostUrl}/api/v1/${user?.api_token}/my_api/${model?.api_name}/model/${model?.name}`, {
                        method: "POST",
                        headers: {
                            'x-access-token': token
                        },
                        body: csvFormData
                    })
                    if (response.status === 200) {
                        setFormResponse(await response.json())    
                    } else {
                        if (response.status === 400) {
                            setFormResponse(await response.json())
                        } else if (response.status === 401) {
                            Cookies.remove("token", { path: '/' })
                            navigate("/login", { replace: true, state: { path: location.pathname } })
                        }
                        else {
                            alert("An error occurred while seeding the table from CSV")
                        }
                    }
                } catch (err) {
                    alert("An error occurred while seeding the table from CSV")   
                } finally {
                    stateChanged.current = true
                }
            }
        }

        e.target.reset()
        setLoading(false)
        
      }
      
    return (
        <div className={`seedPopup-wrapper${openSeedPopup ? ' seedPopup-open' : ''}`}>
            <div className="seedPopup-container">
                <div className="seedPopup-box">
                    <div>

                        <h2 className="seedPopup-box__header">Seed Table</h2>
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" onClick={closePopup}>
                            <path d="M18.3 5.7a1 1 0 0 0-1.4 0L12 10.6 7.1 5.7a1 1 0 1 0-1.4 1.4L10.6 12l-4.9 4.9a1 1 0 0 0 1.4 1.4L12 13.4l4.9 4.9a1 1 0 0 0 1.4-1.4L13.4 12l4.9-4.9a1 1 0 0 0 0-1.4z"/>
                        </svg>
                    </div>


                    <div className="seedPopup-body">
                        {
                            formResponse ?
                                <div className="response_data">
                                    <pre>
                                        {JSON.stringify(formResponse, undefined, 2)}
                                    </pre>
                                </div>
                            : ""
                        } 
                        <div className="seedPopup-box__csv_import">
                            <h3>Import from CSV</h3>
                            <form method="POST" encType="multipart/form-data" id="csv_import_form" onSubmit={handleFormSubmit}>
                                <div>

                                    <label htmlFor="">CSV</label>
                                    <input type="file" name="csv_file" accept=".csv" />
                                </div>
                                <div>
                                    <label htmlFor="">Delimiter</label>
                                    <input type="text" name="delimiter" placeholder="Default is comma(,)" maxLength={1} />
                                </div>

                                <button type="submit" disabled={loading}>{loading ? "Seeding..." : "Seed Table"}</button>
                                
  
                            </form>

                        </div>
                        <div className="seedPopup-box__auto_generate" >
                            <h3>Auto Generate</h3>
                            <form method="POST" id="autogenerate_form" onSubmit={handleFormSubmit}>
                                
                                <div>
                                    <label htmlFor="">Number of Rows</label>
                                    <input type="number" name="num_rows" placeholder="Default is 100" min={1} max={100} />
                                </div>
                                
                                <button type="submit">Seed Table</button>
                            </form>
                        </div>
                    </div>
                </div>

            </div>
        </div>
    )
}

export default Index
