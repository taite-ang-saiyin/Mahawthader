import { useState } from "react";
import { Upload, Scale, FileText, Clock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import Navbar from "@/components/Navbar";

const AIJudge = () => {
  const [caseTitle, setCaseTitle] = useState("");
  const [scenario, setScenario] = useState("");
  const [currentRound, setCurrentRound] = useState(1);
  const [judgment, setJudgment] = useState("");

  const rounds = [
    { round: 1, plaintiff: "", defendant: "", completed: false },
    { round: 2, plaintiff: "", defendant: "", completed: false },
    { round: 3, plaintiff: "", defendant: "", completed: false },
  ];

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <div className="pt-16 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-foreground mb-2">AI Judge Platform</h1>
            <p className="text-muted-foreground">
              Present your case and receive an AI-powered legal judgment
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Case Information */}
            <div className="lg:col-span-2">
              <Card className="mb-6">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Scale className="h-5 w-5" />
                    <span>Case Information</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-2">
                      Case Title
                    </label>
                    <Input
                      value={caseTitle}
                      onChange={(e) => setCaseTitle(e.target.value)}
                      placeholder="Enter the case title..."
                      className="w-full"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-2">
                      Case Scenario
                    </label>
                    <Textarea
                      value={scenario}
                      onChange={(e) => setScenario(e.target.value)}
                      placeholder="Describe the case scenario in detail..."
                      className="w-full h-32"
                    />
                  </div>
                </CardContent>
              </Card>

              
            </div>

          </div>
        </div>
      </div>
    </div>
  );
};

export default AIJudge;