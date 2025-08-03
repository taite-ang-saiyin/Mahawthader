import { ArrowRight, Scale, MessageCircle, Users, Shield, Clock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useNavigate } from "react-router-dom";
import Navbar from "@/components/Navbar";
import heroLegal from "@/assets/hero-legal.jpg";

const Index = () => {
  const navigate = useNavigate();

  const features = [
    {
      icon: MessageCircle,
      title: "AI Legal Chatbot",
      description: "Get instant answers to your legal questions with our intelligent chatbot powered by advanced AI technology.",
      action: "Ask a Lawyer",
      path: "/chatbot",
    },
    {
      icon: Scale,
      title: "AI Judge Platform",
      description: "Present your case and receive an impartial AI-powered judgment based on legal precedents and evidence.",
      action: "Start Judging",
      path: "/ai-judge",
    },
  ];

  const benefits = [
    {
      icon: Clock,
      title: "24/7 Availability",
      description: "Access legal guidance anytime, anywhere, without waiting for office hours.",
    },
    {
      icon: Shield,
      title: "Unbiased Judgment",
      description: "AI-powered decisions free from human bias and prejudice.",
    },
    {
      icon: Users,
      title: "Accessible to All",
      description: "Legal assistance available regardless of financial background.",
    },
  ];

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      
      {/* Hero Section */}
      <div className="pt-16 bg-gradient-to-br from-background to-muted">
        <div className="max-w-7xl mx-auto px-6 py-16">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <h1 className="text-5xl font-bold text-foreground mb-6 leading-tight">
                AI-Powered Legal
                <span className="block text-primary">Justice Platform</span>
              </h1>
              <p className="text-xl text-muted-foreground mb-8 leading-relaxed">
                Democratizing access to legal guidance through artificial intelligence. 
                Get instant legal advice or impartial AI-powered judgments for your cases.
              </p>
              <div className="flex flex-col sm:flex-row gap-4">
                <Button 
                  size="lg" 
                  className="text-lg px-8 py-6"
                  onClick={() => navigate('/chatbot')}
                >
                  Ask a Lawyer
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
                <Button 
                  variant="outline" 
                  size="lg" 
                  className="text-lg px-8 py-6"
                  onClick={() => navigate('/ai-judge')}
                >
                  Start Judging
                  <Scale className="ml-2 h-5 w-5" />
                </Button>
              </div>
            </div>
            <div className="relative">
              <img 
                src={heroLegal} 
                alt="Legal Justice Illustration" 
                className="w-full h-auto rounded-2xl shadow-2xl"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="py-20 bg-card">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-foreground mb-4">
              Choose Your Legal Solution
            </h2>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              Whether you need quick legal advice or a comprehensive case judgment, 
              our AI platform has you covered.
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {features.map((feature, index) => (
              <Card key={index} className="group hover:shadow-lg transition-all duration-300 border-2 hover:border-primary/50">
                <CardHeader className="text-center pb-4">
                  <div className="mx-auto w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mb-4 group-hover:bg-primary/20 transition-colors">
                    <feature.icon className="h-8 w-8 text-primary" />
                  </div>
                  <CardTitle className="text-2xl text-foreground">{feature.title}</CardTitle>
                </CardHeader>
                <CardContent className="text-center">
                  <p className="text-muted-foreground mb-6 leading-relaxed">
                    {feature.description}
                  </p>
                  <Button 
                    className="w-full"
                    onClick={() => navigate(feature.path)}
                  >
                    {feature.action}
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </div>

      {/* Benefits Section */}
      <div className="py-20 bg-muted/30">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-foreground mb-4">
              Why Choose AI-Judge?
            </h2>
            <p className="text-xl text-muted-foreground">
              Experience the future of legal assistance with our advanced AI platform
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {benefits.map((benefit, index) => (
              <div key={index} className="text-center">
                <div className="mx-auto w-16 h-16 bg-primary rounded-full flex items-center justify-center mb-6">
                  <benefit.icon className="h-8 w-8 text-primary-foreground" />
                </div>
                <h3 className="text-xl font-semibold text-foreground mb-3">
                  {benefit.title}
                </h3>
                <p className="text-muted-foreground leading-relaxed">
                  {benefit.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="py-16 bg-primary text-primary-foreground">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h2 className="text-3xl font-bold mb-4">
            Ready to Experience AI-Powered Legal Assistance?
          </h2>
          <p className="text-xl opacity-90 mb-8">
            Join thousands of users who trust AI-Judge for their legal needs
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button 
              variant="secondary" 
              size="lg"
              onClick={() => navigate('/chatbot')}
            >
              Start with Chatbot
            </Button>
            <Button 
              variant="outline" 
              size="lg"
              className="border-primary-foreground text-primary-foreground hover:bg-primary-foreground hover:text-primary"
              onClick={() => navigate('/about')}
            >
              Learn More
            </Button>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-foreground text-background py-8">
        <div className="max-w-6xl mx-auto px-6 text-center">
          <div className="flex items-center justify-center space-x-2 mb-4">
            <Scale className="h-6 w-6" />
            <span className="text-xl font-bold">AI-Judge</span>
          </div>
          <p className="text-sm opacity-80">
            © 2024 AI-Judge. All rights reserved. Powered by artificial intelligence for accessible legal justice.
          </p>
        </div>
      </footer>
    </div>
  );
};

export default Index;