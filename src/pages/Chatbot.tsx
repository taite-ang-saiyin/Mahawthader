import { useState, useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Send, Upload, Globe, Trash2, Pencil } from "lucide-react";
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
  const [isOnline, setIsOnline] = useState(true);
  const [currentConversationId, setCurrentConversationId] = useState<number | null>(null);
  const [chatHistory, setChatHistory] = useState<Conversation[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editingTitle, setEditingTitle] = useState<string>("");
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  // Lightweight language detector for UI typography (frontend only)
  const detectLang = (text: string): "my" | "en" | "zh" | "ja" => {
    const hasMyanmar = /[\u1000-\u109F\uAA60-\uAA7F\uA9E0-\uA9FF]/.test(text);
    if (hasMyanmar) return "my";
    const hasKana = /[\u3040-\u30ff]/.test(text);
    if (hasKana) return "ja";
    const hasCJK = /[\u4e00-\u9fff]/.test(text);
    if (hasCJK) return "zh";
    return "en";
  };

  const langFontClass = (lang: string) => {
    switch (lang) {
      case "my":
        return "font-sans antialiased";
      case "zh":
        return "font-sans antialiased tracking-normal";
      case "ja":
        return "font-sans antialiased";
      default:
        return "";
    }
  };

  // Safe minimal Markdown cleanup before rendering
  // Final client-side cleanup to avoid duplicate sentences/lines and fix noisy markdown
  const cleanForDisplay = (raw: string) => {
    const lang = detectLang(raw);
    let text = raw
      // normalize multiple asterisks "****" -> "**"
      .replace(/\*{3,}/g, "**")
      // collapse >2 blank lines
      .replace(/\n{3,}/g, "\n\n");

    // Deduplicate consecutive identical lines and bullet items
    const lines = text.split(/\n/);
    const dedupedLines: string[] = [];
    let prev = "";
    for (const line of lines) {
      const trimmed = line.trim();
      const isBullet = /^(-|\*|•)\s+/.test(trimmed);
      if (trimmed && (trimmed === prev || (isBullet && trimmed === prev))) {
        continue;
      }
      dedupedLines.push(line);
      prev = trimmed;
    }
    text = dedupedLines.join("\n");

    // Deduplicate consecutive sentences by language punctuation
    const splitBy = lang === "my" ? /(?<=။)\s+/ : (lang === "zh" || lang === "ja") ? /(?<=。)\s+/ : /(?<=[.!?])\s+/;
    const sentences = text.split(splitBy);
    const pruned: string[] = [];
    let last = "";
    for (const s of sentences) {
      const sn = s.trim();
      if (!sn) continue;
      if (sn === last) continue;
      pruned.push(s);
      last = sn;
    }
    text = pruned.join(" ");
    return text.trim();
  };

  // HTML escaper for custom lightweight Markdown transformer
  const escapeHtml = (s: string) =>
    s
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");

  // Optional minimal Markdown -> HTML (kept for cases where ReactMarkdown isn't desired)
  const markdownLiteToHtml = (md: string) => {
    let html = escapeHtml(md);
    // Headings
    html = html.replace(/^###\s+(.*)$/gim, '<h3 class="text-base font-semibold mt-2 mb-1">$1<\/h3>');
    html = html.replace(/^##\s+(.*)$/gim, '<h2 class="text-lg font-semibold mt-2 mb-1">$1<\/h2>');
    html = html.replace(/^#\s+(.*)$/gim, '<h1 class="text-xl font-bold mt-2 mb-1">$1<\/h1>');
    // Bold
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1<\/strong>');
    // Bullets -> list items
    html = html
      .replace(/^(?:\-|\*|•)\s+(.*)$/gim, '<li class="ml-5 list-disc">$1<\/li>')
      .replace(/(<li[\s\S]*?<\/li>\s*)+/gim, (m) => `<ul class="my-2">${m}<\/ul>`);
    // Paragraphs (split by double newline)
    html = html
      .split(/\n\n+/)
      .map((p) => (p.match(/^<h[1-3]|^<ul/) ? p : `<p class="leading-relaxed">${p.replace(/\n/g, '<br/>')}<\/p>`))
      .join("\n");
    return html;
  };

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
      const API_BASE = (import.meta as any).env?.VITE_API_URL || "http://localhost:8000";
      const response = await axios.get(`${API_BASE}/chat/history/${user.id}`);
      setChatHistory(response.data);
      console.log("Chat history fetched:", response.data);
    } catch (err) {
      console.error("Failed to fetch chat history:", err);
    }
  };

  useEffect(() => {
    fetchChatHistory();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

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
      const requestData = {
        user_id: userId,
        message: newMessage.text,
        conversation_id: currentConversationId,
        mode: isOnline ? "online" : "offline",
      };
      
      console.log("🔍 FRONTEND: Sending request data:", requestData);
      console.log("🔍 FRONTEND: User ID type:", typeof userId);
      console.log("🔍 FRONTEND: Conversation ID type:", typeof currentConversationId);
      console.log("🔍 FRONTEND: Mode:", isOnline ? "online" : "offline");
      
      const API_BASE = (import.meta as any).env?.VITE_API_URL || "http://localhost:8000";
      const response = await axios.post(`${API_BASE}/chat`, requestData);

      // FIX: Changed 'response.data.message' to 'response.data.answer'
      const botResponseText = cleanForDisplay(response.data.answer);
      console.log(botResponseText);
      const botResponse: Message = {
        id: messages.length + 2,
        text: botResponseText,
        isBot: true,
      };
      setMessages((prev) => [...prev, botResponse]);
      setCurrentConversationId(response.data.conversation_id);
      fetchChatHistory(); // Refresh history to show the new conversation
    } catch (err: any) {
      console.error("❌ FRONTEND: Failed to send message:", err);
      console.error("❌ FRONTEND: Error response:", err.response?.data);
      console.error("❌ FRONTEND: Error status:", err.response?.status);
      
      let errorMessage = "Sorry, I am unable to respond right now. Please try again later.";
      
      if (err.response?.status === 422) {
        errorMessage = "Invalid request format. Please check your input and try again.";
      } else if (err.response?.status === 500) {
        errorMessage = "Server error. Please try again later.";
      }
      
      const errorBotResponse: Message = {
        id: messages.length + 2,
        text: errorMessage,
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
      const API_BASE = (import.meta as any).env?.VITE_API_URL || "http://localhost:8000";
      await axios.delete(`${API_BASE}/chat/history/${conversationId}`);
      alert("Conversation deleted successfully.");
      startNewChat(); // Reset the chat view
      fetchChatHistory(); // Refresh history list
    } catch (err) {
      console.error("Failed to delete conversation:", err);
      alert("Failed to delete conversation. Please try again.");
    }
  };

  const handleEditClick = (conversation: Conversation) => {
    setEditingId(conversation.id);
    setEditingTitle(conversation.topic);
  };

  const handleSaveTitle = async (conversationId: number) => {
    try {
      const API_BASE = (import.meta as any).env?.VITE_API_URL || "http://localhost:8000";
      await axios.patch(`${API_BASE}/chat/history/${conversationId}`, { topic: editingTitle });
      setEditingId(null);
      setEditingTitle("");
      fetchChatHistory();
    } catch (err) {
      console.error("Failed to update title:", err);
      alert("Failed to update title. Please try again.");
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
              <div key={conversation.id} className="flex items-center space-x-2">
                {editingId === conversation.id ? (
                  <>
                    <Input
                      value={editingTitle}
                      onChange={(e) => setEditingTitle(e.target.value)}
                      className="flex-1 h-8"
                    />
                    <Button size="sm" onClick={() => handleSaveTitle(conversation.id)}>Save</Button>
                    <Button size="sm" variant="secondary" onClick={() => { setEditingId(null); setEditingTitle(""); }}>Cancel</Button>
                  </>
                ) : (
                  <>
                    <Button
                      variant="ghost"
                      className="flex-1 text-left justify-start h-auto p-3 text-wrap"
                      onClick={() => handleSelectConversation(conversation)}
                    >
                      {conversation.topic}
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleEditClick(conversation)}
                    >
                      <Pencil className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDeleteConversation(conversation.id)}
                    >
                      <Trash2 className="h-4 w-4 text-red-500 hover:text-red-700" />
                    </Button>
                  </>
                )}
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
              <span className="text-sm text-foreground">Offline</span>
              <Switch checked={isOnline} onCheckedChange={setIsOnline} />
              <span className="text-sm text-foreground">Online</span>
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
                  className={`max-w-2xl ${
                    message.isBot
                      ? "bg-card border-border"
                      : "bg-primary text-primary-foreground border-primary"
                  }`}
                >
                  <CardContent className={`p-4 ${langFontClass(detectLang(message.text))}`}>
                    <div className="prose prose-sm max-w-none prose-headings:mb-2 prose-p:my-2 prose-ul:my-2">
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={{
                          h1: ({ node, ...props }) => <h1 className="text-xl font-bold mt-2 mb-1" {...props} />,
                          h2: ({ node, ...props }) => <h2 className="text-lg font-semibold mt-2 mb-1" {...props} />,
                          h3: ({ node, ...props }) => <h3 className="text-base font-semibold mt-2 mb-1" {...props} />,
                          p: ({ node, ...props }) => <p className="leading-relaxed" {...props} />,
                          ul: ({ node, ...props }) => <ul className="my-2 list-disc pl-6" {...props} />,
                          li: ({ node, ...props }) => <li className="my-0.5" {...props} />,
                          a: ({ node, ...props }) => <a className="underline" target="_blank" rel="noreferrer" {...props} />,
                          table: ({ node, ...props }) => <div className="overflow-x-auto"><table className="table-auto w-full" {...props} /></div>,
                        }}
                      >
                        {message.text}
                      </ReactMarkdown>
                    </div>
                  </CardContent>
                </Card>
              </div>
            ))}
            {isLoading && (
              <div className="flex justify-start">
                <Card className="max-w-2xl bg-card border-border">
                  <CardContent className="p-4">
                    <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                      <span className="inline-block w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                      <span className="inline-block w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                      <span className="inline-block w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                      <span>Thinking…</span>
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}
            <div ref={messagesEndRef} />
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
