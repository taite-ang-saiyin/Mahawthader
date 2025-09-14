import { Mail, Phone, MapPin, Calendar, Users, Target } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import Navbar from "@/components/Navbar";

const AboutUs = () => {
  const teamMembers = [
    {
      name: "Hsu Sandy Hnin",
      role: "AI Engineer",
      bio: "Undergraduate student at University of Information Technology",
      image: "👩‍💼",
    },
    {
      name: "Kaung Khant Ko",
      role: "AI Architect",
      bio: "Undergraduate student at University of Information Technology",
      image: "👨‍⚖️",
    },
    {
      name: "Phyu Sin Thant",
      role: "Software Engineer",
      bio: "Undergraduate student at University of Information Technology",
      image: "👩‍💻",
    },
    {
      name: "Htet Aung Shine",
      role: "AI engineer",
      bio: "Undergraduate student at University of Information Technology",
      image: "👨‍🎨",
    },
  ];

  const timeline = [
    { year: "2024", event: "AI-Judge Platform Launch", status: "past" },
    { year: "2025", event: "Multi-language Support Expansion", status: "current" },
    { year: "2026", event: "International Legal Framework Integration", status: "future" },
    { year: "2027", event: "Real-time Court Integration", status: "future" },
  ];

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <div className="pt-16">
        {/* Hero Section */}
        <div className="bg-primary text-primary-foreground py-16">
          <div className="max-w-4xl mx-auto px-6 text-center">
            <h1 className="text-4xl font-bold mb-4">About AI-Judge</h1>
            <p className="text-xl opacity-90">
              Revolutionizing legal accessibility through artificial intelligence
            </p>
          </div>
        </div>

        <div className="max-w-6xl mx-auto px-6 py-12">
          {/* Mission Statement */}
          <div className="text-center mb-16">
            <div className="flex justify-center mb-6">
              <Target className="h-16 w-16 text-primary" />
            </div>
            <h2 className="text-3xl font-bold text-foreground mb-6">Our Mission</h2>
            <p className="text-lg text-muted-foreground max-w-3xl mx-auto leading-relaxed">
              To democratize access to legal guidance and judgment through cutting-edge AI technology, 
              ensuring that everyone has access to fair, unbiased, and intelligent legal assistance 
              regardless of their background or financial situation.
            </p>
          </div>

          {/* Team Section */}
          <div className="mb-16">
            <div className="text-center mb-8">
              <Users className="h-12 w-12 text-primary mx-auto mb-4" />
              <h2 className="text-3xl font-bold text-foreground">Meet Our Team</h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {teamMembers.map((member, index) => (
                <Card key={index} className="text-center">
                  <CardContent className="p-6">
                    <div className="text-6xl mb-4">{member.image}</div>
                    <h3 className="text-lg font-semibold text-foreground mb-1">{member.name}</h3>
                    <p className="text-primary font-medium mb-3">{member.role}</p>
                    <p className="text-sm text-muted-foreground">{member.bio}</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>

          {/* Project Timeline */}
          <div className="mb-16">
            <div className="text-center mb-8">
              <Calendar className="h-12 w-12 text-primary mx-auto mb-4" />
              <h2 className="text-3xl font-bold text-foreground">Project Vision Timeline</h2>
            </div>
            <div className="max-w-2xl mx-auto">
              {timeline.map((item, index) => (
                <div key={index} className="flex items-center mb-6">
                  <div className="flex flex-col items-center mr-6">
                    <div
                      className={`w-12 h-12 rounded-full flex items-center justify-center font-bold ${
                        item.status === "current"
                          ? "bg-primary text-primary-foreground"
                          : "bg-muted text-muted-foreground"
                      }`}
                    >
                      {item.year}
                    </div>
                    {index < timeline.length - 1 && (
                      <div className="w-0.5 h-12 bg-border mt-2" />
                    )}
                  </div>
                  <Card className="flex-1">
                    <CardContent className="p-4">
                      <p className="font-medium text-foreground">{item.event}</p>
                      {item.status === "current" && (
                        <span className="inline-block bg-primary text-primary-foreground text-xs px-2 py-1 rounded-full mt-2">
                          Current
                        </span>
                      )}
                    </CardContent>
                  </Card>
                </div>
              ))}
            </div>
          </div>

          {/* Contact Form */}
          <div className="max-w-2xl mx-auto">
            <Card>
              <CardHeader>
                <CardTitle className="text-center flex items-center justify-center space-x-2">
                  <Mail className="h-6 w-6" />
                  <span>Contact Us</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-2">
                      Full Name
                    </label>
                    <Input placeholder="Your full name" disabled />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-2">
                      Email Address
                    </label>
                    <Input type="email" placeholder="your.email@example.com" disabled />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-foreground mb-2">
                    Subject
                  </label>
                  <Input placeholder="What would you like to discuss?" disabled />
                </div>
                <div>
                  <label className="block text-sm font-medium text-foreground mb-2">
                    Message
                  </label>
                  <Textarea
                    placeholder="Tell us more about your inquiry..."
                    className="h-32"
                    disabled
                  />
                </div>
                <Button className="w-full" disabled>Send Message</Button>
                
                <div className="border-t border-border pt-6">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
                    <div className="flex flex-col items-center">
                      <Mail className="h-6 w-6 text-primary mb-2" />
                      <p className="text-sm text-foreground">support@ai-judge.com</p>
                    </div>
                    <div className="flex flex-col items-center">
                      <Phone className="h-6 w-6 text-primary mb-2" />
                      <p className="text-sm text-foreground">+1 (555) 123-4567</p>
                    </div>
                    <div className="flex flex-col items-center">
                      <MapPin className="h-6 w-6 text-primary mb-2" />
                      <p className="text-sm text-foreground">San Francisco, CA</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AboutUs;