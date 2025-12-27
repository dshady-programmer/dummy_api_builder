import "./index.scss"
import { useState, useContext, useCallback } from "react"
import { endpointPrefix } from "../../variables";
import { AppContext } from "../../context";
import CodeMirror from '@uiw/react-codemirror';
import {json} from "@codemirror/lang-json"
// import {javascript} from "@codemirror/lang-javascript"

// hostUrl / api / v1 / <your_api_Id>/my_api/<Api_name>/model/<Model_name>/<optional:model_id></optional:model_id>

const Index = () => {
    const [endpointParam, setEndpointParam] = useState({ "method": "GET", "data": "", "api": "", "model": "", "model_id": "", "query_params": "" });
    const [response, setResponse] = useState(null)
    const { user } = useContext(AppContext)

    const copyTextToClipboard = async (text) => {
        if ('clipboard' in navigator) {
            return await navigator.clipboard.writeText(text);
        } else {
            return document.execCommand('copy', true, text);
        }
    }

    const copyEndpoint = (e) => {
        if (!endpointParam.api || !endpointParam.model) {
            alert("Fill in the api name and the model name")
            return
        }
        let fullUrlPath = `${endpointPrefix}${user.api_token}/my_api/${endpointParam.api}/model/${endpointParam.model}/${endpointParam.model_id}`
        if (endpointParam.query_params) fullUrlPath = `${fullUrlPath}?${endpointParam.query_params}`
        copyTextToClipboard(fullUrlPath)
        e.target.textContent = "copied"
        setTimeout(() => {
            e.target.textContent = "here"
        }, 3000)
    }

    const handleChange = (e) => {
        setEndpointParam(prev => ({ ...prev, [e.target.name]: e.target.name === "data" ? e.target.value : e.target.value.trim() }))
    }
    const handleDataChange = useCallback((val, viewUpdate) => {

        setEndpointParam(prev => ({ ...prev, data: val.trim() }));
    }, []);

    const handleSubmit = async (e) => {

        e.preventDefault()
        console.log("endpointParam", endpointParam)
        setResponse(null)
        if (!endpointParam.api || !endpointParam.model) {
            return;
        }
        let fullUrlPath = `${endpointPrefix}${user.api_token}/my_api/${endpointParam.api}/model/${endpointParam.model}/${endpointParam.model_id}`
        if (["POST", "PUT"].includes(endpointParam.method)) {

            if (!endpointParam.data) return;
            try {
                const data = JSON.parse(endpointParam.data.trim())

                const resp = await fetch(fullUrlPath, {
                    method: endpointParam.method,
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        "entries": data
                    })
                })
                const resp_data = await resp.json()
                setResponse(resp_data)
            } catch (err) {
                setResponse(err.message)
                return;
            }


        }
        else {
            try {

                if (endpointParam.query_params) fullUrlPath = `${fullUrlPath}?${endpointParam.query_params}`
                const resp = await fetch(fullUrlPath, {
                    method: endpointParam.method
                })
                if (resp.status == 204) {
                    setResponse({ "message": "Deleted Successfully" })
                    return;
                }
                const resp_data = await resp.json()

                setResponse(resp_data)
            }
            catch (err) {
                setResponse(err)
            }
        }


    }
    return (
        <div className="test_endpoint-wrapper">
            <h2>Test Your API</h2>
            <section className="endpoint_info">
                <p>
                    Fill in the API name and MODEL name you want query below and copy your full path <a onClick={copyEndpoint}>here</a>
                </p>
                <p>
                    Format: <b>{"<your_api_Id>/my_api/<Api_name>/model/<Model_name>/<optional: model_id>"}</b>

                </p>
                <small>Refer to the <a href="https://github.com/shady-cj/dummy_api_builder/blob/main/README.md" target="_blank" rel="noreferrer">docs</a> for more info</small>
            </section>
            <section className="endpoint_form">
                <form action="" onSubmit={handleSubmit}>
                    <div>
                        <label htmlFor="url">Api</label>
                        <input type="text" onChange={handleChange} id="api" name="api" value={endpointParam.api} placeholder={`<Api_name>`} />
                    </div>
                    <div>
                        <label htmlFor="url">Model</label>
                        <input type="text" onChange={handleChange} id="model" name="model" value={endpointParam.model} placeholder={`<Model_name>`} />
                    </div>
                    <div>
                        <label htmlFor="url">Query ID</label>
                        <input type="text" onChange={handleChange} id="model_id" name="model_id" value={endpointParam.model_id} placeholder={`<Optional: Model_ID>`} />
                    </div>
                    <div>
                        <label htmlFor="url">Query Params</label>
                        <input type="text" onChange={handleChange} id="query_params" name="query_params" value={endpointParam.query_params} placeholder={`<field_name>=<value>`} />
                    </div>

                    <div>
                        <label htmlFor="method">Method</label>
                        <select name="method" id="method" onChange={handleChange} value={endpointParam.method}>
                            <option value="GET">GET</option>
                            <option value="POST">POST</option>
                            <option value="PUT">PUT</option>
                            <option value="DELETE">DELETE</option>
                        </select>
                    </div>
                    <div>
                        <label htmlFor="data">Data</label>
                        <CodeMirror name="data" id="data" value={endpointParam.data} height="200px" extensions={[json()]} onChange={handleDataChange} />
                        {/* <textarea name="data" id="data" onChange={handleChange} value={endpointParam.data}></textarea> */}

                    </div>

                    <button>Send</button>
                </form>
            </section>

            {
                response && <section className="response_section">
                    <h2>Response</h2>
                    <div className="response_data">
                        <pre>
                            {JSON.stringify(response, undefined, 3)}
                        </pre>
                    </div>
                </section>
            }

        </div>
    )
}

export default Index
