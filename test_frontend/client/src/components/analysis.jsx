import React from "react";
import { WeeklyChart } from "./WeeklyChart";
import DistributionOfExercises from "./DistributionOfExercises";
import CaloriesBurnt from "./CaloriesBurnt";

export default function Analysis() {
  return (
    <div className="mt-24">
      {/* <div className=" w-full flex ">
        <WeeklyChart />
        <CaloriesBurnt />
      </div> */}
      <DistributionOfExercises />
    </div>
  );
}
