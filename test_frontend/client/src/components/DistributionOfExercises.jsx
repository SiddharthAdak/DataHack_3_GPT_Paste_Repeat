import Chart from "chart.js/auto";
import React, { useEffect, useRef, useState } from "react";
import { useDataContext } from "../context/ContextProvider";
export default function DistributionOfExercises() {
  const chartRef = useRef(null);
  // const [data, setData] = useState([]);
  const {state} = useDataContext();
  const {    
    squat,
    bicep_curls,
    pushup,
    shoulder_press,
  } = state;
  const data = {
    labels: ["Squats", "Pushups", "Bicep Curls", "Shoulder Press"],
    datasets: [
      {
        label: "Dataset 1",
        data: [squat, pushup, bicep_curls, shoulder_press],
      },
    ],
  };

  useEffect(() => {
    let chartInstance = null;

    if (chartRef.current) {
      chartInstance = new Chart(chartRef.current, {
        type: "doughnut",
        data,
        options: {
          responsive: true,
          plugins: {
            legend: {
              position: "top",
            },
            title: {
              display: true,
              text: "Distribution of Exercises",
            },
          },
        },
      });
    }

    return () => {
      if (chartInstance) {
        chartInstance.destroy();
      }
    };
  }, []);

  return (
    <div className=" w-96 m-auto mt-4">
      <canvas id="new" ref={chartRef} />
    </div>
  );
}
