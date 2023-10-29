import Chart from "chart.js/auto";
import React, { useEffect, useRef, useState } from "react";

export default function CaloriesBurnt() {
  const chartRef = useRef(null);
  const [data, setData] = useState([]);

  useEffect(() => {
    let chartInstance = null;

    if (chartRef.current) {
      chartInstance = new Chart(chartRef.current, {
        type: "line",
        data: {
          labels: ["Mon", "Tue", "Wed", "Thur", "Fri", "Sat", "Sun"],
          datasets: [
            {
              label: "Calories Burnt",
              data: [1000, 1200, 2000, 1500, 1800, 2200, 3000],
              fill: false,
              borderColor: "rgb(75, 192, 192)",
              tension: 0.1,
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
    <div className="flex-[0.5] p-4">
      <canvas id="new" ref={chartRef} />
    </div>
  );
}
