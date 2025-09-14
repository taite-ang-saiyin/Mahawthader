import { useState, useEffect } from "react";
import Navbar from "@/components/Navbar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Download } from "lucide-react";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import axios from "axios";

// Define the Case interface for type safety
interface Case {
  case_id: string;
  case_title: string;
  plaintiff_name: string;
  defendant_name: string;
  verdict_date: string; // ISO date string, e.g., "2025-09-08T23:36:00"
  pdf_path: string; // Path to the verdict PDF
}

const CaseHistory = () => {
  const [cases, setCases] = useState<Case[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch case history from the backend
  useEffect(() => {
    const fetchCaseHistory = async () => {
      try {
        setLoading(true);
        const response = await axios.get("http://localhost:8000/get_case_history");
        // Sort cases by verdict_date (newest first)
        const sortedCases = response.data.sort((a: Case, b: Case) =>
          new Date(b.verdict_date).getTime() - new Date(a.verdict_date).getTime()
        );
        setCases(sortedCases);
        setError(null);
      } catch (err) {
        console.error("Error fetching case history:", err);
        setError("Unable to connect to the server. Please ensure the backend server is running and try again.");
      } finally {
        setLoading(false);
      }
    };

    fetchCaseHistory();
  }, []);

  // Format ISO date to a readable string
  const formatDate = (isoDate: string) => {
    try {
      const date = new Date(isoDate);
      return date.toLocaleDateString("en-US", {
        year: "numeric",
        month: "long",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        timeZone: "Asia/Yangon"
      });
    } catch {
      return "Unknown Date";
    }
  };

  // Truncate long text for display
  const truncateText = (text: string, maxLength: number = 30) => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength - 3) + "...";
  };

  return (
    <>
      <Navbar />
      <div className="min-h-screen bg-background pt-20 px-4">
        <div className="max-w-5xl mx-auto">
          <h1 className="text-3xl font-bold text-foreground mb-8">Case History</h1>
          <Card className="bg-card rounded-lg shadow-lg">
            <CardHeader>
              <CardTitle className="text-xl text-foreground">Previous Legal Case Analyses</CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <p className="text-muted-foreground text-center">Loading case history...</p>
              ) : error ? (
                <p className="text-destructive text-center">{error}</p>
              ) : cases.length === 0 ? (
                <p className="text-muted-foreground text-center">No case history available. Start a new case to generate a verdict.</p>
              ) : (
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="text-foreground">Case Title</TableHead>
                        <TableHead className="text-foreground">Verdict Date</TableHead>
                        <TableHead className="text-foreground">Verdict PDF</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {cases.map((caseItem) => (
                        <TableRow key={caseItem.case_id}>
                          <TableCell className="font-medium text-foreground">
                            <TooltipProvider>
                              <Tooltip>
                                <TooltipTrigger>{truncateText(caseItem.case_title || "Untitled Case")}</TooltipTrigger>
                                <TooltipContent>{caseItem.case_title || "Untitled Case"}</TooltipContent>
                              </Tooltip>
                            </TooltipProvider>
                          </TableCell>
                          
                          
                          <TableCell className="text-foreground">
                            {formatDate(caseItem.verdict_date)}
                          </TableCell>
                          <TableCell>
                            {caseItem.pdf_path ? (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => {
                                  const link = document.createElement("a");
                                  link.href = `http://localhost:8000/download_verdict_pdf/${caseItem.case_id}`;
                                  link.download = `${caseItem.case_id}.pdf`;
                                  document.body.appendChild(link);
                                  link.click();
                                  document.body.removeChild(link);
                                }}
                              >
                                <Download className="h-4 w-4 mr-2" />
                                Download
                              </Button>
                            ) : (
                              <span className="text-muted-foreground">Not available</span>
                            )}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </>
  );
};

export default CaseHistory;