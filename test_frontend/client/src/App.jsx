import { useEffect, useRef, useState } from "react";
import VideoUpload from "./pages/VideoUpload";
// import VideoStream from "./components/VideoStream";
import axios from "axios";
import { Route, Routes } from "react-router-dom";
import Navbar from "./components/Navbar";
import { WeeklyChart } from "./components/WeeklyChart";
import Analysis from "./components/analysis";
// import VideoStream from "./components/VideoStream";
// import io from "socket.io-client";
// const socket = io.connect("http://127.0.0.1:5000");
function App() {
  
  return (
    <>
    <Navbar />
      <Routes>
        <Route path="/uploadvideo" element = {<VideoUpload />} />
        <Route path="/analysis" element = {<Analysis />} />
      </Routes>

      {/* <img id="photo" width="400" height="300"></img> */}
    </>
  );
}

export default App;
