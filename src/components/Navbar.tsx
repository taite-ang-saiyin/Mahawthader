import { NavLink } from "react-router-dom";
import { Scale } from "lucide-react";

const Navbar = () => {
  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-primary shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center space-x-2">
            <Scale className="h-8 w-8 text-primary-foreground" />
            <span className="text-xl font-bold text-primary-foreground">AI-Judge</span>
          </div>
          <div className="hidden md:flex space-x-8">
            <NavLink
              to="/"
              className={({ isActive }) =>
                `px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200 ${
                  isActive
                    ? "bg-secondary text-secondary-foreground"
                    : "text-primary-foreground hover:bg-secondary/50 hover:text-secondary-foreground"
                }`
              }
            >
              Home
            </NavLink>
            <NavLink
              to="/chatbot"
              className={({ isActive }) =>
                `px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200 ${
                  isActive
                    ? "bg-secondary text-secondary-foreground"
                    : "text-primary-foreground hover:bg-secondary/50 hover:text-secondary-foreground"
                }`
              }
            >
              Chatbot
            </NavLink>
            <NavLink
              to="/ai-judge"
              className={({ isActive }) =>
                `px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200 ${
                  isActive
                    ? "bg-secondary text-secondary-foreground"
                    : "text-primary-foreground hover:bg-secondary/50 hover:text-secondary-foreground"
                }`
              }
            >
              AI Judge
            </NavLink>
            <NavLink
              to="/about"
              className={({ isActive }) =>
                `px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200 ${
                  isActive
                    ? "bg-secondary text-secondary-foreground"
                    : "text-primary-foreground hover:bg-secondary/50 hover:text-secondary-foreground"
                }`
              }
            >
              About Us
            </NavLink>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;