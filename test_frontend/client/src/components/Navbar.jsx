import React from 'react'
import { Link } from 'react-router-dom'
function Navbar() {
  return (
    <div className=' h-[70px] shadow-md flex bg-white fixed top-0 left-0 w-full items-center justify-between px-10'>
        <Link to="/" className=' text-black text-xl cursor-pointer font-semibold'>Datahack</Link>
        <div className=' flex items-center gap-5'>
            <Link to="/uploadvideo" className=' text-black underline font-semibold decoration-4 decoration-indigo-400'>Upload Video</Link>
            <Link to="/analysis" className=' text-black underline font-semibold decoration-4 decoration-indigo-400'>Analysis</Link>
        </div>
    </div>
  )
}

export default Navbar