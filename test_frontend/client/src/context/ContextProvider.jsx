import { useContext, createContext, useState } from "react";

const DataContext = createContext();


export const DataContextProvider = ({children}) => {
    const [state, setState] = useState({
        calories: 0,
        squat: 0,
        bicep_curls: 0,
        pushup: 0,
        shoulder_press: 0
    });
    return (
        <DataContext.Provider value = {{state, setState}}>
            {children}
        </DataContext.Provider>
    )
}
export const useDataContext = () => {
    const context = useContext(DataContext);
    return context
}