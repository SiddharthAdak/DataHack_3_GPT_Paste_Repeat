import { useRef, useEffect, useState } from "react";
import axios from "axios";
function VideoStream({socket}) {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const intervalRef = useRef(null);
  const [stream, setStream] = useState(null);
  const [isVideo, setIsVideo] = useState(null);
  const FPS = 10;
  const width = 400
  const height = 300
  useEffect(() => {
    
    if (isVideo) {
      getVideo();
      intervalRef.current = setInterval(() => {
        var canvas = canvasRef.current;
        var context = canvas.getContext('2d');
        context.drawImage(videoRef.current, 0, 0, width, height);
        const frameData = canvas.toDataURL('image/jpeg');
        console.log(frameData);
        socket.emit('image', frameData);
      }, 1000/FPS);
    }
    
    return () => {
      clearInterval(intervalRef.current);
    };
  }, [videoRef, isVideo]);
  const getVideo = () => {
    navigator.mediaDevices
      .getUserMedia({ video: true, audio: false })
      .then((stream) => {
        let video = videoRef.current;
        setStream(stream);
        video.srcObject = stream;
        
        video.play();
        // intervalRef.current = setInterval
        
      })
      .catch((err) => {
        console.error("error:", err);
      });
  };

  return (
    <div className="">
      <video id="videoElement" className="w-[400px] h-[300px] block rounded-md mx-auto mb-5" ref={videoRef} />
      <div>
        {isVideo ? (
          <button
            className=" bg-black text-white w-40 px-3 py-2 rounded-md"
            onClick={() => {
              videoRef.current.srcObject = null;
              setIsVideo(false);
              if (stream) {
                stream.getTracks().forEach((track) => {
                  track.stop();
                });
              }
            }}
          >
            cancel
          </button>
        ):
        (
          <button
            className=" bg-black text-white w-40 px-3 py-2 rounded-md"
            onClick={() => {
              setIsVideo(true);
            }}
          >
            Start video
          </button>
        )}
      </div>
      <canvas ref={canvasRef} id="canvas" width="400" height="300"></canvas>
    </div>
  );
}

export default VideoStream;
