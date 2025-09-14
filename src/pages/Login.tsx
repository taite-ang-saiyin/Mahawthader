// Your original Login.tsx code is also good as is.
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useNavigate } from "react-router-dom";
import Navbar from "@/components/Navbar";
import { Eye, EyeOff } from "lucide-react";
import loginImage from "@/assets/Signup_login.png";
import axios from "axios";

const Login = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");

    if (!email || !password) {
      setError("Please enter both email and password.");
      setIsLoading(false);
      return;
    }

    try {
      console.log("Attempting to log in with:", { email, password });
      const API_BASE = (import.meta as any).env?.VITE_API_URL || "http://localhost:8000";
      const response = await axios.post(`${API_BASE}/login`, {
        email,
        password,
      });

      console.log("Login successful!", response.data);
      // CORRECTED: Store user data in local storage
      localStorage.setItem("user", JSON.stringify(response.data.user));
      navigate("/chatbot"); // Redirect to the chatbot page after successful login
    } catch (err) {
      console.error("Login error:", err);
      if (axios.isAxiosError(err) && err.response) {
        setError(err.response.data.message || "An unexpected error occurred. Please try again.");
      } else {
        setError("An unexpected error occurred. Please try again.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <Navbar />
      <div className="flex flex-1 items-center justify-center p-6">
        <Card className="w-full max-w-4xl shadow-2xl rounded-lg overflow-hidden flex flex-col md:flex-row">
          {/* Left Side (60%): Login Form */}
          <div className="flex-1 basis-3/5 flex items-center justify-center p-8 md:p-12">
            <div className="w-full max-w-sm">
              <CardHeader className="text-center p-0 mb-6">
                <CardTitle className="text-4xl font-bold">Welcome Back</CardTitle>
                <CardDescription className="text-muted-foreground mt-2 text-base">
                  Log in to continue your journey.
                </CardDescription>
              </CardHeader>
              <CardContent className="grid gap-4 p-0">
                {error && (
                  <div className="bg-destructive/10 text-destructive border border-destructive/20 p-3 rounded-lg text-sm text-center">
                    {error}
                  </div>
                )}
                <form onSubmit={handleLogin} className="grid gap-4">
                  <div className="grid gap-2">
                    <Label htmlFor="email" className="text-lg">Email Address</Label>
                    <Input
                      id="email"
                      type="email"
                      placeholder="name@example.com"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="bg-card focus-visible:ring-0 focus-visible:ring-offset-0 focus:border-primary shadow-sm text-lg"
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="password" className="text-lg">Password</Label>
                    <div className="relative">
                      <Input
                        id="password"
                        type={showPassword ? "text" : "password"}
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        className="bg-card pr-10 focus-visible:ring-0 focus-visible:ring-offset-0 focus:border-primary shadow-sm text-lg"
                      />
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-0 top-0 h-full px-3 py-2 text-muted-foreground hover:bg-transparent"
                      >
                        {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </Button>
                    </div>
                  </div>
                  <Button type="submit" className="w-full text-base" disabled={isLoading}>
                    {isLoading ? "Signing In..." : "Sign In"}
                  </Button>
                </form>
                <div className="mt-4 text-center text-base text-muted-foreground">
                  Don't have an account?{" "}
                  <a href="/signup" className="underline text-primary hover:text-primary/80">
                    Sign up
                  </a>
                </div>
              </CardContent>
            </div>
          </div>

          {/* Right Side (40%): Image */}
          <div className="hidden md:flex basis-2/5 items-center justify-center p-8 md:p-12 bg-primary">
            <img src={loginImage} alt="Legal Illustration" className="w-full h-full object-contain" />
          </div>
        </Card>
      </div>
    </div>
  );
};

export default Login;