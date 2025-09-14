import { NavLink } from "react-router-dom";
import MainLogo from "@/assets/Main Logo.png";

const Navbar = () => {
  // Check if user is logged in
  const userData = typeof window !== 'undefined' ? localStorage.getItem("user") : null;
  const user = userData ? JSON.parse(userData) : null;
  const handleLogout = () => {
    localStorage.removeItem("user");
    window.location.reload();
  };
  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-primary shadow-lg">
  <div className="w-full px-6">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center space-x-3">
            <img src={MainLogo} alt="Mahawthada" className="h-10 w-auto md:h-12"/>
            <span className="text-xl font-bold text-primary-foreground">မဟော်သဓာ</span>
          </div>
          <div className="hidden md:flex space-x-8 items-center">
            <NavLink to="/" className={({ isActive }) => `px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200 ${isActive ? "bg-secondary text-secondary-foreground" : "text-primary-foreground hover:bg-secondary/50 hover:text-secondary-foreground"}`}>Home</NavLink>
            <NavLink to="/chatbot" className={({ isActive }) => `px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200 ${isActive ? "bg-secondary text-secondary-foreground" : "text-primary-foreground hover:bg-secondary/50 hover:text-secondary-foreground"}`}>Chatbot</NavLink>
            <div className="relative group">
              <span className="px-3 py-2 rounded-md text-sm font-medium text-primary-foreground hover:bg-secondary/50 hover:text-secondary-foreground cursor-pointer">AI Judge</span>
              <div className="absolute left-0 mt-2 w-44 bg-white rounded shadow-lg opacity-0 group-hover:opacity-100 transition-opacity duration-200 z-10">
                <NavLink to="/new-case" className={({ isActive }) => `block px-4 py-2 text-sm ${isActive ? "bg-gray-100 text-black" : "text-black hover:bg-gray-100"}`}>New Case</NavLink>
                <NavLink to="/case-histories" className={({ isActive }) => `block px-4 py-2 text-sm ${isActive ? "bg-gray-100 text-black" : "text-black hover:bg-gray-100"}`}>Case Histories</NavLink>
              </div>
            </div>
            <NavLink to="/about" className={({ isActive }) => `px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200 ${isActive ? "bg-secondary text-secondary-foreground" : "text-primary-foreground hover:bg-secondary/50 hover:text-secondary-foreground"}`}>About Us</NavLink>
            {!user ? (
              <>
                <NavLink to="/signup" className={({ isActive }) => `px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200 ${isActive ? "bg-secondary text-secondary-foreground" : "text-primary-foreground hover:bg-secondary/50 hover:text-secondary-foreground"}`}>Sign Up</NavLink>
                <NavLink to="/login" className={({ isActive }) => `px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200 ${isActive ? "bg-secondary text-secondary-foreground" : "text-primary-foreground hover:bg-secondary/50 hover:text-secondary-foreground"}`}>Login</NavLink>
              </>
            ) : (
              <div className="relative group">
                <span className="px-3 py-2 rounded-md text-sm font-medium text-primary-foreground bg-secondary cursor-pointer">{user.username}</span>
                <div className="absolute right-0 mt-2 w-32 bg-white rounded shadow-lg opacity-0 group-hover:opacity-100 transition-opacity duration-200 z-10">
                  <button onClick={handleLogout} className="block w-full px-4 py-2 text-sm text-red-600 hover:bg-gray-100 text-left">Logout</button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;