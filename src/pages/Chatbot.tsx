import { useState } from "react";
import { Send, Upload, Globe } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import Navbar from "@/components/Navbar";

const Chatbot = () => {
  const [messages, setMessages] = useState([
    {
      id: 1,
      text: "Hello! I'm your AI legal assistant. How can I help you with your legal questions today?",
      isBot: true,
    },
  ]);
  const [input, setInput] = useState("");
  const [isEnglish, setIsEnglish] = useState(true);

  const popularQuestions = [
    "What are my rights as a tenant?",
    "How do I file for divorce?",
    "What is the process for starting a business?",
    "How do I handle a workplace dispute?",
    "What are the requirements for a will?",
    "How do I protect my intellectual property?",
  ];

  const handleSendMessage = () => {
    if (!input.trim()) return;

    const newMessage = {
      id: messages.length + 1,
      text: input,
      isBot: false,
    };

    setMessages([...messages, newMessage]);
    setInput("");

    // Simulate bot response
    setTimeout(() => {
      const botResponse = {
        id: messages.length + 2,
        text: "I understand your question. Let me provide you with relevant legal information...",
        isBot: true,
      };
      setMessages((prev) => [...prev, botResponse]);
    }, 1000);
  };

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <div className="pt-16 flex h-screen">
        {/* Sidebar */}
        <div className="w-80 bg-card border-r border-border p-6 overflow-y-auto">
          <h2 className="text-lg font-semibold text-foreground mb-4">Popular Questions</h2>
          <div className="space-y-2">
            {popularQuestions.map((question, index) => (
              <Button
                key={index}
                variant="ghost"
                className="w-full text-left justify-start h-auto p-3 text-wrap"
                onClick={() => setInput(question)}
              >
                {question}
              </Button>
            ))}
          </div>
        </div>

        {/* Main Chat Area */}
        <div className="flex-1 flex flex-col">
          {/* Header */}
          <div className="bg-card border-b border-border p-4 flex justify-between items-center">
            <h1 className="text-xl font-semibold text-foreground">Legal Assistant Chat</h1>
            <div className="flex items-center space-x-3">
              <Globe className="h-5 w-5 text-secondary" />
              <span className="text-sm text-foreground">Burmese</span>
              <Switch checked={isEnglish} onCheckedChange={setIsEnglish} />
              <span className="text-sm text-foreground">English</span>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.isBot ? "justify-start" : "justify-end"}`}
              >
                <Card
                  className={`max-w-md ${
                    message.isBot
                      ? "bg-card border-border"
                      : "bg-primary text-primary-foreground border-primary"
                  }`}
                >
                  <CardContent className="p-3">
                    <p className="text-sm">{message.text}</p>
                  </CardContent>
                </Card>
              </div>
            ))}
          </div>

          {/* Input Area */}
          <div className="bg-card border-t border-border p-4">
            <div className="flex space-x-2">
              <Input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Type your legal question here..."
                onKeyPress={(e) => e.key === "Enter" && handleSendMessage()}
                className="flex-1"
              />
              <Button onClick={handleSendMessage} size="sm">
                <Send className="h-4 w-4" />
              </Button>
              <Button variant="outline" size="sm">
                <Upload className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Chatbot;