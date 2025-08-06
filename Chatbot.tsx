import { useState, useEffect } from "react";
import { Send, Upload, Globe, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import Navbar from "@/components/Navbar";
import axios from "axios";

// Define the shape of a message
interface Message {
  id: number;
  text: string;
  isBot: boolean;
}

// Define the shape of a conversation from the API
interface Conversation {
  id: number;
  topic: string;
  messages: { sender: string; text: string; timestamp: string }[];
}

const Chatbot = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isEnglish, setIsEnglish] = useState(true);
  const [currentConversationId, setCurrentConversationId] = useState<number | null>(null);
  const [chatHistory, setChatHistory] = useState<Conversation[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const popularQuestions = [
    "What are my rights as a tenant?",
    "How do I file for divorce?",
    "What is the process for starting a business?",
    "How do I handle a workplace dispute?",
    "What are the requirements for a will?",
    "How do I protect my intellectual property?",
  ];

  const fetchChatHistory = async () => {
    try {
      const userData = localStorage.getItem("user");
      if (!userData) {
        console.error("User not logged in.");
        return;
      }
      const user = JSON.parse(userData);
      const response = await axios.get(`http://localhost:5001/chat/history/${user.id}`);
      setChatHistory(response.data);
      console.log("Chat history fetched:", response.data);
    } catch (err) {
      console.error("Failed to fetch chat history:", err);
    }
  };

  useEffect(() => {
    fetchChatHistory();
  }, []);

  const handleSendMessage = async () => {
    if (!input.trim()) return;

    const userData = localStorage.getItem("user");
    if (!userData) {
      alert("Please log in to use the chatbot.");
      return;
    }
    const user = JSON.parse(userData);
    const userId = user.id;

    const newMessage: Message = {
      id: messages.length + 1,
      text: input,
      isBot: false,
    };
    setMessages((prev) => [...prev, newMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const response = await axios.post("http://localhost:5001/chat", {
        user_id: userId,
        message: newMessage.text,
        conversation_id: currentConversationId,
      });

      const botResponseText = response.data.message;
      const botResponse: Message = {
        id: messages.length + 2,
        text: botResponseText,
        isBot: true,
      };
      setMessages((prev) => [...prev, botResponse]);
      setCurrentConversationId(response.data.conversation_id);
      fetchChatHistory(); // Refresh history to show the new conversation
    } catch (err) {
      console.error("Failed to send message:", err);
      const errorBotResponse: Message = {
        id: messages.length + 2,
        text: "Sorry, I am unable to respond right now. Please try again later.",
        isBot: true,
      };
      setMessages((prev) => [...prev, errorBotResponse]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectConversation = (conversation: Conversation) => {
    const formattedMessages: Message[] = conversation.messages.map((m, index) => ({
      id: index,
      text: m.text,
      isBot: m.sender === 'bot',
    }));
    setMessages(formattedMessages);
    setCurrentConversationId(conversation.id);
  };

  const startNewChat = () => {
    setMessages([]);
    setCurrentConversationId(null);
  };
  
  const handleDeleteConversation = async (conversationId: number) => {
    const confirmDelete = window.confirm("Are you sure you want to delete this conversation?");
    if (!confirmDelete) return;

    try {
      await axios.delete(`http://localhost:5001/chat/history/${conversationId}`);
      alert("Conversation deleted successfully.");
      startNewChat(); // Reset the chat view
      fetchChatHistory(); // Refresh history list
    } catch (err) {
      console.error("Failed to delete conversation:", err);
      alert("Failed to delete conversation. Please try again.");
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <div className="pt-16 flex h-screen">
        {/* Sidebar */}
        <div className="w-80 bg-card border-r border-border p-6 overflow-y-auto flex flex-col">
          <Button onClick={startNewChat} className="w-full mb-4">
            New Chat
          </Button>
          <h2 className="text-lg font-semibold text-foreground mb-4">Chat History</h2>
          <div className="space-y-2 flex-1">
            {chatHistory.map((conversation) => (
              <div key={conversation.id} className="flex items-center justify-between">
                <Button
                  variant="ghost"
                  className="w-full text-left justify-start h-auto p-3 text-wrap"
                  onClick={() => handleSelectConversation(conversation)}
                >
                  {conversation.topic}
                </Button>
                <Button 
                  variant="ghost" 
                  size="sm"
                  onClick={() => handleDeleteConversation(conversation.id)}
                >
                  <Trash2 className="h-4 w-4 text-red-500 hover:text-red-700" />
                </Button>
              </div>
            ))}
          </div>
          <h2 className="text-lg font-semibold text-foreground mt-6 mb-4">Popular Questions</h2>
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
                disabled={isLoading}
              />
              <Button onClick={handleSendMessage} size="sm" disabled={isLoading}>
                {isLoading ? "..." : <Send className="h-4 w-4" />}
              </Button>
              <Button variant="outline" size="sm" disabled>
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