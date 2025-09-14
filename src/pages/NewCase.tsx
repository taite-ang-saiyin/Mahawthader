import { useState, useEffect, FormEvent, useRef } from "react";
import { Upload, Scale, FileText, Send, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import axios from "axios";
import Navbar from "@/components/Navbar";
 

// Define the Message interface for type safety
interface ChatMessage {
  id: number;
  text: string;
  isBot: boolean;
  role: string;
}

// Define the CaseState interface for type safety
interface CaseState {
  status: string;
  current_round: number;
  current_speaker: string;
  language: string;
  final_verdict?: string; // Optional verdict text
}

const NewCase = () => {
  const [caseTitle, setCaseTitle] = useState("");
  const [scenario, setScenario] = useState("");
  const [plaintiffName, setPlaintiffName] = useState("");
  const [defendantName, setDefendantName] = useState("");
  const [currentRound, setCurrentRound] = useState(1);
  const [judgment, setJudgment] = useState("");
  const [showChat, setShowChat] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [userRole, setUserRole] = useState("plaintiff");
  const [caseId, setCaseId] = useState<string | null>(null);
  const [plaintiffFiles, setPlaintiffFiles] = useState<File[]>([]);
  const [defendantFiles, setDefendantFiles] = useState<File[]>([]);
  const [isFormComplete, setIsFormComplete] = useState(false);
  const [language, setLanguage] = useState<string>("en");
  const [caseState, setCaseState] = useState<CaseState | null>(null);
  const [hasDownloaded, setHasDownloaded] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const [showErrors, setShowErrors] = useState(false);

  const errorMessages: Record<string, Record<string, string>> = {
    my: {
      startCase: "အမှုစတင်ရာတွင် အမှားဖြစ်ပေါ်ခဲ့သည်။ ကျေးဇူးပြု၍ ထပ်မံကြိုးစားပါ။",
      submitMessage: "မက်ဆေ့ချ်ပို့ရန် မအောင်မြင်ပါ။ ကျေးဇူးပြု၍ ထပ်မံကြိုးစားပါ။",
      fetchVerdict: "စီရင်ချက်ရယူရာတွင် အမှားဖြစ်ပေါ်ခဲ့သည်။ ကျေးဇူးပြု၍ ထပ်မံကြိုးစားပါ။",
    },
    ja: {
      startCase: "事件の開始中にエラーが発生しました。もう一度お試しください。",
      submitMessage: "メッセージの送信に失敗しました。もう一度お試しください。",
      fetchVerdict: "判決の取得中にエラーが発生しました。もう一度お試しください。",
    },
    en: {
      startCase: "Error starting case. Please try again.",
      submitMessage: "Error submitting message. Please try again.",
      fetchVerdict: "Error fetching verdict. Please try again.",
    },
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>, type: string) => {
    const newFiles = Array.from(event.target.files || []);
    if (newFiles.length === 0) return;

    if (type === "plaintiff") {
      const updatedFiles = [...plaintiffFiles, ...newFiles].slice(0, 3); // Append and limit to 3
      if (updatedFiles.length > 3) {
        alert("You can upload at most 3 files for the plaintiff.");
        return;
      }
      setPlaintiffFiles(updatedFiles);
    } else {
      const updatedFiles = [...defendantFiles, ...newFiles].slice(0, 3); // Append and limit to 3
      if (updatedFiles.length > 3) {
        alert("You can upload at most 3 files for the defendant.");
        return;
      }
      setDefendantFiles(updatedFiles);
    }
    event.target.value = "";
  };

  const handleDeleteFile = (index: number, type: string) => {
    if (type === "plaintiff") {
      setPlaintiffFiles(plaintiffFiles.filter((_, i) => i !== index));
    } else {
      setDefendantFiles(defendantFiles.filter((_, i) => i !== index));
    }
  };

  const handleEditFile = (index: number, type: string, event: React.ChangeEvent<HTMLInputElement>) => {
    const newFile = event.target.files?.[0];
    if (newFile) {
      if (type === "plaintiff") {
        const updatedFiles = [...plaintiffFiles];
        updatedFiles[index] = newFile;
        setPlaintiffFiles(updatedFiles);
      } else {
        const updatedFiles = [...defendantFiles];
        updatedFiles[index] = newFile;
        setDefendantFiles(updatedFiles);
      }
    }
    event.target.value = "";
  };

  useEffect(() => {
    setIsFormComplete(
      caseTitle.trim() !== "" &&
      scenario.trim() !== "" &&
      plaintiffName.trim() !== "" &&
      defendantName.trim() !== "" &&
      plaintiffFiles.length >= 1 &&
      plaintiffFiles.length <= 3 &&
      defendantFiles.length >= 1 &&
      defendantFiles.length <= 3
    );
  }, [caseTitle, scenario, plaintiffName, defendantName, plaintiffFiles, defendantFiles]);

  const handleStartJudgment = async (event: FormEvent) => {
    event.preventDefault();
    if (!isFormComplete) {
      setShowErrors(true);
      return;
    }

    const formData = new FormData();
    formData.append("case_title", caseTitle);
    formData.append("scenario", scenario);
    formData.append("plaintiff_name", plaintiffName);
    formData.append("defendant_name", defendantName);
    plaintiffFiles.forEach((file) => formData.append("plaintiff_files", file));
    defendantFiles.forEach((file) => formData.append("defendant_files", file));

    try {
      const response = await axios.post("http://localhost:8000/start_case", formData, {
        headers: { "Content-Type": "multipart/form-data; charset=UTF-8" },
      });

      const { case_id, initial_analysis, current_speaker, current_round, language: detected_language } = response.data;

      setCaseId(case_id);
      setLanguage(detected_language);
      setMessages([{ id: 1, text: initial_analysis, isBot: true, role: "AI Judge" }]);
      setUserRole(current_speaker || "plaintiff");
      setCurrentRound(current_round || 1);
      setShowChat(true);
      setJudgment("");
      setHasDownloaded(false);
    } catch (error) {
      console.error(error);
      setMessages([{
        id: 1,
        text: errorMessages[language]?.startCase || errorMessages.en.startCase,
        isBot: true,
        role: "AI Judge",
      }]);
    }
  };

  const handleSendMessage = async () => {
    if (!input.trim() || !caseId || judgment) return;
    const effectiveRole = userRole || "plaintiff";
    const newMessage: ChatMessage = { id: messages.length + 1, text: input, isBot: false, role: effectiveRole };
    setMessages((prev) => [...prev, newMessage]);
    const currentInput = input;
    setInput("");

    try {
      const formData = new FormData();
      formData.append("message", currentInput);
      formData.append("role", effectiveRole);

      const response = await axios.post(`http://localhost:8000/submit_message/${caseId}`, formData, {
        headers: { "Content-Type": "multipart/form-data; charset=UTF-8" },
      });

      const { response: judgeResponse, current_speaker, current_round, status, language: updated_language } = response.data;
      setLanguage(updated_language || language);

      setMessages((prev) => [
        ...prev,
        { id: prev.length + 1, text: judgeResponse, isBot: true, role: "AI Judge" },
      ]);
      setUserRole(current_speaker || effectiveRole);
      setCurrentRound(current_round || currentRound);
    } catch (error) {
      console.error(error);
      setMessages((prev) => [
        ...prev,
        { id: prev.length + 1, text: errorMessages[language]?.submitMessage || errorMessages.en.submitMessage, isBot: true, role: "AI Judge" },
      ]);
    }
  };

  const fetchVerdict = async () => {
    if (!caseId || hasDownloaded) return;
    try {
      // Fetch the PDF for download
      const pdfResponse = await axios.get(`http://localhost:8000/get_verdict/${caseId}`, {
        responseType: "blob",
      });

      if (pdfResponse.headers["content-type"] === "application/pdf") {
        const blob = pdfResponse.data;
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        const filename = pdfResponse.headers["content-disposition"]?.split("filename=")[1]?.replace(/"/g, "") || `verdict_${caseId}.pdf`;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
        setHasDownloaded(true);
      } else {
        console.error("Unexpected response type for PDF:", pdfResponse.headers["content-type"]);
      }
    } catch (error) {
      console.error("Error downloading verdict PDF:", error);
    }
  };

  // Poll case state to detect verdict_rendered and update judgment
  useEffect(() => {
    let interval: NodeJS.Timeout | null = null;
    if (caseId && !judgment && !hasDownloaded) {
      interval = setInterval(async () => {
        try {
          const response = await axios.get(`http://localhost:8000/get_case_state/${caseId}`);
          const state: CaseState = response.data;
          setCaseState(state);
          if (state.status === "verdict_rendered" && state.final_verdict) {
            setJudgment(state.final_verdict); // Set verdict text
            await fetchVerdict(); // Trigger PDF download
            if (interval) clearInterval(interval); // Stop polling
          }
        } catch (error) {
          console.error("Error polling case state:", error);
          setJudgment(errorMessages[language]?.fetchVerdict || errorMessages.en.fetchVerdict);
          if (interval) clearInterval(interval);
        }
      }, 3000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [caseId, judgment, hasDownloaded, language]);

  useEffect(() => {
    if (messagesEndRef.current) messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <div className="pt-16 p-3 max-w-8xl mx-20" style={{ minHeight: '100vh' }}>
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-foreground mb-2">AI Judge Platform</h1>
        </div>

        <div className={`grid grid-cols-1 ${showChat ? "lg:grid-cols-3" : "lg:grid-cols-1"} gap-3 transition-all duration-500 ease-in-out`}  style={{ height:'100%' }}>
          {/* Left / Chat/Form Column */}
          <div className={`${showChat ? (judgment ? "lg:col-span-1" : "lg:col-span-2") : "lg:col-span-1"} transition-all duration-500 ease-in-out`} >
            {!showChat ? (
              <form onSubmit={handleStartJudgment}>
                {/* Case Info Card */}
                <Card className="mb-3">
                  <CardHeader>
                    <CardTitle className="flex items-center space-x-2">
                      <Scale className="h-5 w-5" />
                      <span>Case Information</span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <Input
                      value={caseTitle}
                      onChange={(e) => setCaseTitle(e.target.value)}
                      placeholder="Case Title"
                    />
                    {showErrors && caseTitle.trim() === "" && (
                      <div className="text-red-600 text-sm mt-1 flex items-center gap-1">
                        <AlertCircle className="h-4 w-4" />
                        Please enter a case title.
                      </div>
                    )}
                    <Input
                      value={plaintiffName}
                      onChange={(e) => setPlaintiffName(e.target.value)}
                      placeholder="Plaintiff Name"
                    />
                    {showErrors && plaintiffName.trim() === "" && (
                      <div className="text-red-600 text-sm mt-1 flex items-center gap-1">
                        <AlertCircle className="h-4 w-4" />
                        Plaintiff name is required.
                      </div>
                    )}
                    <Input
                      value={defendantName}
                      onChange={(e) => setDefendantName(e.target.value)}
                      placeholder="Defendant Name"
                    />
                    {showErrors && defendantName.trim() === "" && (
                      <div className="text-red-600 text-sm mt-1 flex items-center gap-1">
                        <AlertCircle className="h-4 w-4" />
                        Defendant name is required.
                      </div>
                    )}
                    <Textarea
                      value={scenario}
                      onChange={(e) => setScenario(e.target.value)}
                      placeholder="Case Scenario"
                      className="w-full h-32"
                    />
                    {showErrors && scenario.trim() === "" && (
                      <div className="text-red-600 text-sm mt-1 flex items-center gap-1">
                        <AlertCircle className="h-4 w-4" />
                        Please describe the case scenario.
                      </div>
                    )}
                  </CardContent>
                </Card>

                {/* Evidence Upload Card */}
                <Card className="mb-3">
                  <CardHeader>
                    <CardTitle className="flex items-center space-x-2">
                      <FileText className="h-5 w-5" />
                      <span>Evidence Upload</span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="flex flex-col md:flex-row gap-4">
                    {/* Plaintiff */}
                    <div className="flex-1 flex flex-col items-center justify-center p-4 border-2 border-dashed border-gray-400 rounded-md">
                      <Upload className="text-4xl mb-2 text-secondary" />
                      <p className="font-semibold text-foreground mb-4">Plaintiff Documents</p>
                      {plaintiffFiles.length === 0 && (
                        <div>
                          <input
                            type="file"
                            multiple
                            className="hidden"
                            id="plaintiff-upload"
                            accept=".pdf,.txt"
                            onChange={(e) => handleFileUpload(e, "plaintiff")}
                          />
                          <label
                            htmlFor="plaintiff-upload"
                            className="px-4 py-2 bg-blue-500 text-white rounded cursor-pointer hover:bg-blue-600"
                          >
                            Choose Files
                          </label>
                        </div>
                      )}
                      {plaintiffFiles.length > 0 && (
                        <div className="mt-2 w-full">
                          <ul className="text-sm text-foreground max-h-32 overflow-y-auto w-full space-y-2">
                            {plaintiffFiles.map((file, index) => (
                              <li key={index} className="flex items-center justify-between py-1">
                                <span className="truncate flex-1">{file.name}</span>
                                <div className="flex gap-2 items-center">
                                  <input
                                    type="file"
                                    className="hidden"
                                    id={`plaintiff-edit-${index}`}
                                    accept=".pdf,.txt"
                                    onChange={(e) => handleEditFile(index, "plaintiff", e)}
                                  />
                                  <label
                                    htmlFor={`plaintiff-edit-${index}`}
                                    className="px-2 py-1 bg-white text-black border border-black rounded cursor-pointer hover:bg-black hover:text-white text-xs flex items-center justify-center h-6"
                                  >
                                    Edit
                                  </label>
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => handleDeleteFile(index, "plaintiff")}
                                    className="text-xs bg-black text-white border-black hover:bg-white hover:text-black h-6"
                                  >
                                    Delete
                                  </Button>
                                </div>
                              </li>
                            ))}
                          </ul>
                          {plaintiffFiles.length < 3 && (
                            <div>
                              <input
                                type="file"
                                multiple
                                className="hidden"
                                id="plaintiff-upload-add"
                                accept=".pdf,.txt"
                                onChange={(e) => handleFileUpload(e, "plaintiff")}
                              />
                              <label
                                htmlFor="plaintiff-upload-add"
                                className="mt-2 px-4 py-2 bg-green-500 text-white rounded cursor-pointer hover:bg-green-600 text-sm"
                              >
                                Add File
                              </label>
                            </div>
                          )}
                        </div>
                      )}
                      {showErrors && (plaintiffFiles.length < 1 || plaintiffFiles.length > 3) && (
                        <div className="text-red-600 text-sm mt-2 flex items-center gap-1 w-full">
                          <AlertCircle className="h-4 w-4" />
                          Upload between 1 and 3 plaintiff files (.pdf or .txt).
                        </div>
                      )}
                    </div>
                    {/* Defendant */}
                    <div className="flex-1 flex flex-col items-center justify-center p-4 border-2 border-dashed border-gray-400 rounded-md">
                      <Upload className="text-4xl mb-2 text-secondary" />
                      <p className="font-semibold text-foreground mb-4">Defendant Documents</p>
                      {defendantFiles.length === 0 && (
                        <div>
                          <input
                            type="file"
                            multiple
                            className="hidden"
                            id="defendant-upload"
                            accept=".pdf,.txt"
                            onChange={(e) => handleFileUpload(e, "defendant")}
                          />
                          <label
                            htmlFor="defendant-upload"
                            className="px-4 py-2 bg-blue-500 text-white rounded cursor-pointer hover:bg-blue-600"
                          >
                            Choose Files
                          </label>
                        </div>
                      )}
                      {defendantFiles.length > 0 && (
                        <div className="mt-2 w-full">
                          <ul className="text-sm text-foreground max-h-32 overflow-y-auto w-full space-y-2">
                            {defendantFiles.map((file, index) => (
                              <li key={index} className="flex items-center justify-between py-1">
                                <span className="truncate flex-1">{file.name}</span>
                                <div className="flex gap-2 items-center">
                                  <input
                                    type="file"
                                    className="hidden"
                                    id={`defendant-edit-${index}`}
                                    accept=".pdf,.txt"
                                    onChange={(e) => handleEditFile(index, "defendant", e)}
                                  />
                                  <label
                                    htmlFor={`defendant-edit-${index}`}
                                    className="px-2 py-1 bg-white text-black border border-black rounded cursor-pointer hover:bg-black hover:text-white text-xs flex items-center justify-center h-6"
                                  >
                                    Edit
                                  </label>
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => handleDeleteFile(index, "defendant")}
                                    className="text-xs bg-black text-white border-black hover:bg-white hover:text-black h-6"
                                  >
                                    Delete
                                  </Button>
                                </div>
                              </li>
                            ))}
                          </ul>
                          {defendantFiles.length < 3 && (
                            <div>
                              <input
                                type="file"
                                multiple
                                className="hidden"
                                id="defendant-upload-add"
                                accept=".pdf,.txt"
                                onChange={(e) => handleFileUpload(e, "defendant")}
                              />
                              <label
                                htmlFor="defendant-upload-add"
                                className="mt-2 px-4 py-2 bg-green-500 text-white rounded cursor-pointer hover:bg-green-600 text-sm"
                              >
                                Add File
                              </label>
                            </div>
                          )}
                        </div>
                      )}
                      {showErrors && (defendantFiles.length < 1 || defendantFiles.length > 3) && (
                        <div className="text-red-600 text-sm mt-2 flex items-center gap-1 w-full">
                          <AlertCircle className="h-4 w-4" />
                          Upload between 1 and 3 defendant files (.pdf or .txt).
                        </div>
                      )}
                    </div>
                  </CardContent>
                  <div className="text-center p-4">
                    <Button type="submit" className="w-full">
                      Start Judgment
                    </Button>
                  </div>
                </Card>
              </form>
            ) : (
              // Chat UI
              <div className="flex flex-col h-[600px] w-full transition-all duration-500 ease-in-out">
                <div className="flex-1 overflow-y-auto p-3 space-y-3 bg-card border border-border rounded-lg pretty-scrollbar">
                  {messages.map((msg) => (
                    <div key={msg.id} className={`flex ${msg.isBot ? "justify-start" : "justify-end"}`}>
                      <Card
                        className={`max-w-md ${
                          msg.isBot
                            ? "bg-secondary text-secondary-foreground border-secondary"
                            : msg.role === "plaintiff"
                            ? "bg-blue-100 text-blue-900 border-blue-200"
                            : "bg-red-100 text-red-900 border-red-200"
                        }`}
                      >
                        <CardContent className="p-3">
                          <p className="text-sm">
                            {msg.isBot ? "AI Judge: " : `${msg.role}: `}
                            {msg.text}
                          </p>
                        </CardContent>
                      </Card>
                    </div>
                  ))}
                  <div ref={messagesEndRef} />
                </div>

                {/* Input Box */}
                <div className="bg-card border-t border-border p-4 flex space-x-2">
                  <Input
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder={`Type your case details as ${userRole}...`}
                    onKeyPress={(e) => e.key === "Enter" && handleSendMessage()}
                    className="flex-1"
                    disabled={!!judgment}
                  />
                  <Button onClick={handleSendMessage} size="sm" disabled={!!judgment}>
                    <Send className="h-4 w-4" />
                  </Button>
                  <p className="text-xs text-muted-foreground mt-2">
                    Current role: {userRole} (Round: {currentRound})
                  </p>
                </div>
              </div>
            )}
          </div>

          {showChat && (
            <div className={`${judgment ? "lg:col-span-2" : "lg:col-span-1"} transition-all duration-500 ease-in-out`}>
              <Card className={`sticky top-20 w-full overflow-y-auto transition-all duration-500 ease-in-out h-[600px] pretty-scrollbar`}>
                <CardHeader>
                  <CardTitle className="text-center">Final Judgment</CardTitle>
                </CardHeader>
                <CardContent>
                  {judgment ? (
                    <div className="border rounded-lg p-4 bg-gray-50 whitespace-pre-line text-sm text-foreground">
                      {judgment}
                    </div>
                  ) : (
                    <div className="text-center py-8 text-muted-foreground">Awaiting final judgment…</div>
                  )}
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default NewCase;