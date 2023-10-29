import { useEffect, useRef, useState } from "react";
import axios from "axios";
import cloudSvg from "../assets/CloudArrowUp.svg"
import { useDataContext } from "../context/ContextProvider";
function VideoUpload() {
    const { state, setState } = useDataContext();

    const [output, setOutput] = useState("");
    const [video, setVideo] = useState(null);
    const [inputPreview, setPreview] = useState("");
    const [loading, setLoading] = useState(false);
    const videoRef = useRef();
    const inputVideoRef = useRef();
    console.log(state);
    const handleClick = async() => {
        const formData = new FormData();
        videoRef.current.src = ""
        formData.append('file', video);
        setLoading(true)
        try {
            let response = await axios.post("http://127.0.0.1:8000/test_video", formData);
            console.log(response);
            setLoading(false)
            setOutput(response.data.video)
            videoRef.current.src = "data:video/mp4;base64,"+response.data.video;
            let { squat_counter, curl_counter, pushup_counter, press_counter } = response.data;
            let {
                
                calories,
                squat,
                bicep_curls,
                pushup,
                shoulder_press,
            } = state;
            let temp = ((squat_counter*6 + curl_counter*3.5 + press_counter*6 + pushup_counter*8)*10*60)/(24*60*60);

            setState({
                calories: calories + temp,
                squat: squat + squat_counter,
                bicep_curls: bicep_curls + curl_counter,
                pushup: pushup + pushup_counter,
                shoulder_press: shoulder_press + press_counter
            })
        } catch (error) {
            console.log(error);
        }
    }
    return (
        <>
            <div id="container" className=" w-screen h-screen flex items-center justify-center">
                <input id="input_video" className="hidden" accept="video/mp4" type="file" onChange={(e) => {
                    let file = e.target.files[0];
                    setVideo(file)
                    const reader = new FileReader();
                    reader.readAsDataURL(file);
                    reader.onload = function () {
                        setPreview(reader.result);
                        inputVideoRef.current.src = reader.result;
                        
                    };
                    
                    }}  />
            
                
                <div>
                    <div className=" flex gap-2">
                        <video id="input_video" className={inputPreview ? "block" : "hidden"} ref={inputVideoRef} width="600" controls></video>
                        <video id="output_video" className={output ? "block" : "hidden"} ref={videoRef} width="600" controls></video>
                        
                    </div>
                    {(!output && !inputPreview) && <div className='border-2 border-gray-400 border-dashed rounded-md flex flex-col justify-center items-center h-[300px] w-[600px] bg-gray-100'>
                    <img src={cloudSvg} alt="" />
                    <div className='text-base text-gray-500 '>Upload Video</div>
                    </div>}
                    
                    <div className=" m-auto w-max h-max mt-3">
                        {!(video) ? <label htmlFor="input_video" className="mt-10 bg-black px-3 py-2 rounded-md text-white">Choose File</label>
                        : 
                        <div className=" flex gap-2">
                            <button className=" bg-black px-3 py-2 rounded-md text-white" 
                            onClick={() => {
                                setVideo(null);
                                setOutput("");
                                setPreview("");
                                videoRef.current.src = "";
                                inputVideoRef.current.src = "";
                                document.getElementById("input_video").value = "";
                            }}
                            >Remove</button>
                            {(!output) && <button className=" bg-black px-3 py-2 rounded-md text-white" onClick={handleClick}>{(!loading) ? "Process File" : "Processing..."}</button>}
                        </div>
                        }

                    </div>
                    
                </div>
                {/* <VideoStream socket = {socket} /> */}
            </div>
        </>
    )
}

export default VideoUpload