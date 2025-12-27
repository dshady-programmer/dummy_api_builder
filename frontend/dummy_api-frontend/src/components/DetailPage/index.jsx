import "./index.scss";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useContext, useEffect } from "react";
import { AppContext } from "../../context";
import { Bars } from "react-loader-spinner";
import ErrorElement from "../ErrorElement"
import Cookies from "js-cookie";
import { hostUrl } from "../../variables";

const Index = () => {
    const token = Cookies.get("token", { path: '/' })
    const params = useParams()
    const navigate = useNavigate();
    const { setInvalidate, loading, fetchApiDetail, apiDetail } = useContext(AppContext)
    const deleteAPI = async () => {
        const confirmDelete = confirm("Are you sure you want to delete this API? This action cannot be undone.")
        if (!confirmDelete) return;
        const res = await fetch(`${hostUrl}/api/v1/delete_api/${params.apiId}`, {
                                    method: "DELETE",
                                    headers: {
                                        "Content-Type": "application/json",
                                        "x-access-token": token
                                    },
                                })
        if (res.status === 204) {
            setInvalidate(true)
        } 
        navigate('/my_apis')
    }


    useEffect(() => {
        fetchApiDetail(params.apiId)
    }, [params.apiId])

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
        <div className="detail-wrapper">
            {
                !loading && !apiDetail ? <ErrorElement /> :
                    <>
                        <section className="detail_header">
                            <h2>{apiDetail?.name}</h2>
                            <p>
                                {apiDetail?.description}
                            </p>
                        </section>
                        <section className="detail-list_models">
                            {apiDetail && apiDetail.tables && apiDetail.tables.map(table => {
                                return <article key={table?.id}>
                                    <Link to={`model/${table?.name}`}>
                                        {table?.name}
                                    </Link>
                                </article>
                            })}
                        </section>
                        <section className="detail_footer">
                            <button onClick={() => navigate('model/create')}>
                                Add Model
                            </button>
                            <button onClick={() => navigate('edit')}>
                                Edit API
                            </button>
                            <button style={{ backgroundColor: 'red' }} onClick={deleteAPI}>
                                Delete API
                            </button>
                            <button onClick={() => navigate("/my_apis/test_endpoint")}>
                                Test Endpoint
                            </button>

                        </section>
                    </>
            }

        </div>
    )
}

export default Index
