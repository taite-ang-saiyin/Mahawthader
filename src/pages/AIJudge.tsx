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

              {/* Document Upload */}
              <Card className="mb-6">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <FileText className="h-5 w-5" />
                    <span>Evidence Upload</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="border-2 border-dashed border-border rounded-lg p-6 text-center">
                      <Upload className="h-8 w-8 text-secondary mx-auto mb-2" />
                      <p className="text-sm text-foreground font-medium">Plaintiff Documents</p>
                      <p className="text-xs text-muted-foreground mb-3">
                        Upload evidence, contracts, photos
                      </p>
                      <Button variant="outline" size="sm">
                        Choose Files
                      </Button>
                    </div>
                    <div className="border-2 border-dashed border-border rounded-lg p-6 text-center">
                      <Upload className="h-8 w-8 text-secondary mx-auto mb-2" />
                      <p className="text-sm text-foreground font-medium">Defendant Documents</p>
                      <p className="text-xs text-muted-foreground mb-3">
                        Upload evidence, contracts, photos
                      </p>
                      <Button variant="outline" size="sm">
                        Choose Files
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>

            </div>

            {/* Judgment Panel */}
            <div>
              <Card className="sticky top-20">
                <CardHeader>
                  <CardTitle className="text-center">Final Judgment</CardTitle>
                </CardHeader>
                <CardContent>
                  {judgment ? (
                    <div className="space-y-4">
                      <div className="bg-primary/10 border border-primary/20 rounded-lg p-4">
                        <h3 className="font-semibold text-foreground mb-2">AI Judgment</h3>
                        <p className="text-sm text-foreground">{judgment}</p>
                      </div>
                      <div className="flex justify-center">
                        <Badge variant="secondary">Case Resolved</Badge>
                      </div>
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <Scale className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                      <p className="text-muted-foreground mb-4">
                        Complete all case information and statements to receive judgment
                      </p>
                      <Button 
                        className="w-full"
                        onClick={() => setJudgment("Based on the evidence and statements presented, the AI Judge determines that...")}
                      >
                        Start Judgment
                      </Button>
                    </div>
                  )}
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