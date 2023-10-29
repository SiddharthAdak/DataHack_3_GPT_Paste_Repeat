import Chart from "chart.js/auto";
import React, { useEffect, useRef, useState } from "react";

export function WeeklyChart() {
  const chartRef = useRef(null);
  const [data, setData] = useState([]);
  
  useEffect(() => {
    let chartInstance = null;

    if (chartRef.current) {
      chartInstance = new Chart(chartRef.current, {
        type: "bar",
        data: {
          labels: ["Mon", "Tue", "Wed", "Thur", "Fri", "Sat", "Sun"],
          datasets: [
            {
              label: "Weekly Analysis",
              data: [65, 59, 80, 81, 56, 55, 40], // change kar do yeh wala
              backgroundColor: "rgb(255, 99, 132)",
            },
          ],
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
    <div className=" flex-[0.5] p-4">
      <canvas id="new" ref={chartRef} />
    </div>
  );
}
