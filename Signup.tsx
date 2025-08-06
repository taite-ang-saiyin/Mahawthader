// Your original Signup.tsx code is good as is.
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useNavigate } from "react-router-dom";
import Navbar from "@/components/Navbar";
import { Progress } from "@/components/ui/progress";
import signupImage from "@/assets/Signup_login.png";
import axios from "axios";

const Signup = () => {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const getPasswordStrength = (p: string) => {
    let score = 0;
    if (p.length > 5) score += 20;
    if (p.length > 8) score += 20;
    if (/[A-Z]/.test(p)) score += 20;
    if (/[a-z]/.test(p)) score += 20;
    if (/[0-9]/.test(p)) score += 20;
    return score > 100 ? 100 : score;
  };

  const passwordStrength = getPasswordStrength(password);

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");

    if (!name || !email || !password || !confirmPassword) {
      setError("All fields are required.");
      setIsLoading(false);
      return;
    }
    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      setIsLoading(false);
      return;
    }
    if (password.length < 6) {
      setError("Password must be at least 6 characters long.");
      setIsLoading(false);
      return;
    }

    try {
      const response = await axios.post(
        "http://localhost:5001/signup",
        { name, email, password },
        {
          timeout: 8000,
          headers: {
            "Content-Type": "application/json",
          },
          withCredentials: true,
        }
      );

      console.log("Signup successful:", response.data);
      alert("Account created successfully! Redirecting to login page.");
      navigate("/login");
    } catch (err) {
      console.error("Signup error details:", err);
      if (axios.isAxiosError(err)) {
        if (err.code === "ECONNABORTED") {
          setError("Request timed out. Please try again.");
        } else if (err.code === "ERR_NETWORK") {
          setError(`Cannot connect to server. Please ensure:
            1. Backend server is running on port 5001
            2. No firewall blocking the connection
            3. Check browser console for CORS errors`);
        } else if (err.response) {
          setError(err.response.data.message || "Registration failed. Please try again.");
        }
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
          {/* Left Side (60%): Sign-up Form */}
          <div className="flex-1 basis-3/5 flex items-center justify-center p-8 md:p-12">
            <div className="w-full max-w-sm">
              <CardHeader className="text-center p-0 mb-6">
                <CardTitle className="text-4xl font-bold">Get Started</CardTitle>
                <CardDescription className="text-muted-foreground mt-2 text-base">
                  Create your account in seconds.
                </CardDescription>
              </CardHeader>
              <CardContent className="grid gap-4 p-0">
                {error && (
                  <div className="bg-destructive/10 text-destructive border border-destructive/20 p-3 rounded-lg text-sm text-center">
                    {error}
                  </div>
                )}
                <form onSubmit={handleSignup} className="grid gap-4">
                  <div className="grid gap-2">
                    <Label htmlFor="name" className="text-lg">Full Name</Label>
                    <Input
                      id="name"
                      type="text"
                      placeholder="John Doe"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      className="bg-card focus-visible:ring-0 focus-visible:ring-offset-0 focus:border-primary shadow-sm text-lg"
                    />
                  </div>
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
                    <Input
                      id="password"
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="bg-card focus-visible:ring-0 focus-visible:ring-offset-0 focus:border-primary shadow-sm text-lg"
                    />
                    <Progress value={passwordStrength} className="h-2" />
                    <span className="text-xs text-muted-foreground mt-1">
                      Password strength: {passwordStrength > 60 ? "Strong" : passwordStrength > 30 ? "Medium" : "Weak"}
                    </span>
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="confirm-password" className="text-lg">Confirm Password</Label>
                    <Input
                      id="confirm-password"
                      type="password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      className="bg-card focus-visible:ring-0 focus-visible:ring-offset-0 focus:border-primary shadow-sm text-lg"
                    />
                  </div>
                  <Button type="submit" className="w-full text-base" disabled={isLoading}>
                    {isLoading ? "Creating Account..." : "Create an Account"}
                  </Button>
                </form>
                <div className="mt-4 text-center text-base text-muted-foreground">
                  Already have an account?{" "}
                  <a href="/login" className="underline text-primary hover:text-primary/80">
                    Log in
                  </a>
                </div>
              </CardContent>
            </div>
          </div>
          
          {/* Right Side (40%): Image */}
          <div className="hidden md:flex basis-2/5 items-center justify-center p-8 md:p-12 bg-primary">
            <img src={signupImage} alt="Signup Illustration" className="w-full h-full object-contain" />
          </div>
        </Card>
      </div>
    </div>
  );
};

export default Signup;