import React from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { AlertTriangle, Clock, Package, Phone, PhoneCall, CheckCircle2, AlertCircle, DollarSign, Loader2, MessageSquare } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { agentApi, AgentActivitySummary, AgentActivityItem } from "@/lib/api";

const ControlTower = () => {
  const { toast } = useToast();
  const [transcriptDialog, setTranscriptDialog] = React.useState<{ open: boolean; content: string; supplierName?: string }>({
    open: false,
    content: "",
    supplierName: undefined,
  });
  const [summary, setSummary] = React.useState<AgentActivitySummary | null>(null);
  const [activities, setActivities] = React.useState<AgentActivityItem[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [loadingTranscript, setLoadingTranscript] = React.useState<string | null>(null);

  // Fetch data on mount
  React.useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const limit = 10; // Use same limit for both summary and recap
        const [summaryData, recapData] = await Promise.all([
          agentApi.getActivitySummary(limit),
          agentApi.getActivityRecap(limit),
        ]);
        setSummary(summaryData);
        setActivities(recapData.activities);
      } catch (error) {
        console.error("Error fetching agent data:", error);
        toast({
          title: "Error",
          description: "Failed to load agent activity data",
          variant: "destructive",
        });
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [toast]);

  const handleUnriskDeliveries = () => {
    toast({
      title: "Unrisking Deliveries",
      description: "AI agents are calling suppliers to follow up on late/uncertain ETAs...",
    });
  };

  const handleRelanceSuppliers = () => {
    toast({
      title: "Relancing Suppliers",
      description: "AI agents are following up with unresponsive suppliers...",
    });
  };

  const handleUpdatePrices = () => {
    toast({
      title: "Price Update Started",
      description: "AI agents are verifying current prices with suppliers...",
    });
  };

  const handleFindNewProducts = () => {
    toast({
      title: "Market Search Initiated",
      description: "AI agents are searching for new products matching your needs...",
    });
  };

  const handleApplyUpdate = async (taskId: string, supplier: string) => {
    try {
      await agentApi.parseConversation(taskId);
      toast({
        title: "Update Applied",
        description: `Information from ${supplier} has been updated in the system`,
      });
    } catch (error) {
      console.error("Error applying update:", error);
      toast({
        title: "Error",
        description: "Failed to apply update",
        variant: "destructive",
      });
    }
  };

  const handleViewTranscript = async (taskId: string | null, conversationId: string | null, supplier: string) => {
    if (!taskId && !conversationId) {
      toast({
        title: "Error",
        description: "No transcript available for this activity",
        variant: "destructive",
      });
      return;
    }

    try {
      setLoadingTranscript(taskId || conversationId || "");
      const transcript = taskId
        ? await agentApi.getTranscriptByTaskId(taskId)
        : await agentApi.getTranscriptByConversationId(conversationId!);
      
      setTranscriptDialog({
        open: true,
        content: transcript.formatted_text || "No transcript content available",
        supplierName: supplier,
      });
    } catch (error) {
      console.error("Error fetching transcript:", error);
      toast({
        title: "Error",
        description: "Failed to load transcript",
        variant: "destructive",
      });
    } finally {
      setLoadingTranscript(null);
    }
  };

  const handleEscalate = (supplier: string) => {
    toast({
      title: "Escalation Created",
      description: `Priority escalation initiated for ${supplier}`,
      variant: "destructive",
    });
  };

  const handleRecall = async (supplier: string, agentName?: string) => {
    try {
      const response = await agentApi.startConversation({
        supplier_name: supplier,
        agent_name: agentName || "products",
      });
      toast({
        title: "Re-calling Supplier",
        description: `Agent is calling ${supplier} again...`,
      });
    } catch (error) {
      console.error("Error starting conversation:", error);
      toast({
        title: "Error",
        description: "Failed to start conversation",
        variant: "destructive",
      });
    }
  };

  // Calculate time saved per category (rough estimates)
  const getTimeSavedForCategory = (count: number, category: string) => {
    const timePerItem: Record<string, number> = {
      delivery_risks: 9,
      followups: 6,
      price_checks: 2,
      product_matches: 6,
    };
    return count * (timePerItem[category] || 0);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Core Services Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-6 border-l-4 border-l-critical hover:shadow-lg transition-shadow cursor-pointer">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-base font-bold text-foreground">Delivery Risks Resolved</p>
              <p className="text-3xl font-bold text-foreground mt-1">
                {summary?.delivery_risks_resolved ?? 0}
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                Saved <strong className="text-critical">
                  {getTimeSavedForCategory(summary?.delivery_risks_resolved ?? 0, "delivery_risks")} min
                </strong> of ETA checks today
              </p>
            </div>
            <div className="p-2 bg-critical/10 rounded-lg">
              <AlertTriangle className="h-5 w-5 text-critical" />
            </div>
          </div>
        </Card>

        <Card className="p-6 border-l-4 border-l-moderate hover:shadow-lg transition-shadow cursor-pointer">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-base font-bold text-foreground">Supplier Follow-ups Sent</p>
              <p className="text-3xl font-bold text-foreground mt-1">
                {summary?.supplier_followups_sent ?? 0}
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                Avoided <strong className="text-moderate">
                  {getTimeSavedForCategory(summary?.supplier_followups_sent ?? 0, "followups")} min
                </strong> of calls & emails
              </p>
            </div>
            <div className="p-2 bg-moderate/10 rounded-lg">
              <Phone className="h-5 w-5 text-moderate" />
            </div>
          </div>
        </Card>

        <Card className="p-6 border-l-4 border-l-low hover:shadow-lg transition-shadow cursor-pointer">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-base font-bold text-foreground">Price Checks Completed</p>
              <p className="text-3xl font-bold text-foreground mt-1">
                {summary?.price_checks_completed ?? 0}
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                Saved <strong className="text-low">
                  {getTimeSavedForCategory(summary?.price_checks_completed ?? 0, "price_checks")} min
                </strong> on manual lookup
              </p>
            </div>
            <div className="p-2 bg-low/10 rounded-lg">
              <DollarSign className="h-5 w-5 text-low" />
            </div>
          </div>
        </Card>

        <Card className="p-6 border-l-4 border-l-primary hover:shadow-lg transition-shadow cursor-pointer">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-base font-bold text-foreground">New Product Matches</p>
              <p className="text-3xl font-bold text-foreground mt-1">
                {summary?.new_product_matches ?? 0}
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                Replaced <strong className="text-primary">
                  {getTimeSavedForCategory(summary?.new_product_matches ?? 0, "product_matches")} min
                </strong> of market scanning
              </p>
            </div>
            <div className="p-2 bg-primary/10 rounded-lg">
              <Package className="h-5 w-5 text-primary" />
            </div>
          </div>
        </Card>
      </div>

      {/* Daily Agents Recap */}
      <Card className="p-6">
        <h2 className="text-lg font-semibold text-foreground mb-4">Daily Agents Recap</h2>
        {activities.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <p>No agent activities found</p>
          </div>
        ) : (
          <div className="space-y-3">
            {activities.map((activity) => {
              // Get task type colors and styling
              const getTaskTypeConfig = () => {
                switch (activity.task_type) {
                  case "delivery_risk":
                    return {
                      borderColor: "border-l-critical",
                      bgColor: "bg-critical/5",
                      iconColor: "text-critical",
                      iconBg: "bg-critical/10",
                      icon: AlertTriangle,
                      title: "Delivery Risk Check",
                      shortTitle: "Delivery",
                    };
                  case "price_update":
                    return {
                      borderColor: "border-l-low",
                      bgColor: "bg-low/5",
                      iconColor: "text-low",
                      iconBg: "bg-low/10",
                      icon: DollarSign,
                      title: "Price Update",
                      shortTitle: "Pricing",
                    };
                  case "product_discovery":
                    return {
                      borderColor: "border-l-primary",
                      bgColor: "bg-primary/5",
                      iconColor: "text-primary",
                      iconBg: "bg-primary/10",
                      icon: Package,
                      title: "Product Discovery",
                      shortTitle: "Discovery",
                    };
                  case "supplier_followup":
                  default:
                    return {
                      borderColor: "border-l-moderate",
                      bgColor: "bg-moderate/5",
                      iconColor: "text-moderate",
                      iconBg: "bg-moderate/10",
                      icon: Phone,
                      title: activity.status === "failed" ? "Supplier Not Responding" : "Supplier Follow-up",
                      shortTitle: "Follow-up",
                    };
                }
              };

              const taskConfig = getTaskTypeConfig();
              const TaskIcon = taskConfig.icon;

              const getStatusIcon = () => {
                if (activity.status === "running" || activity.status === "pending") {
                  // Get background color from icon color
                  let bgColor = "bg-low";
                  if (taskConfig.iconColor === "text-critical") bgColor = "bg-critical";
                  else if (taskConfig.iconColor === "text-low") bgColor = "bg-low";
                  else if (taskConfig.iconColor === "text-primary") bgColor = "bg-primary";
                  else if (taskConfig.iconColor === "text-moderate") bgColor = "bg-moderate";
                  
                  return (
                    <div className="relative">
                      <div className={`h-3 w-3 ${bgColor} rounded-full animate-pulse`}></div>
                      <div className={`absolute top-0 left-0 h-3 w-3 ${bgColor} rounded-full animate-ping`}></div>
                    </div>
                  );
                } else if (activity.status === "completed") {
                  return <CheckCircle2 className={`h-5 w-5 ${taskConfig.iconColor}`} />;
                } else if (activity.status === "failed") {
                  return <AlertCircle className="h-5 w-5 text-critical" />;
                }
                return null;
              };

              const getStatusBadge = () => {
                if (activity.status === "running" || activity.status === "pending") {
                  // Get border color from icon color
                  let borderColor = "border-low/20";
                  if (taskConfig.iconColor === "text-critical") borderColor = "border-critical/20";
                  else if (taskConfig.iconColor === "text-low") borderColor = "border-low/20";
                  else if (taskConfig.iconColor === "text-primary") borderColor = "border-primary/20";
                  else if (taskConfig.iconColor === "text-moderate") borderColor = "border-moderate/20";
                  
                  return (
                    <Badge variant="outline" className={`${taskConfig.bgColor} ${taskConfig.iconColor} ${borderColor}`}>
                      {activity.status === "running" ? "In Progress" : "Pending"}
                    </Badge>
                  );
                } else if (activity.status === "completed") {
                  return (
                    <Badge variant="outline" className="bg-green-500/10 text-green-500 border-green-500/20">
                      Completed
                    </Badge>
                  );
                } else if (activity.status === "failed") {
                  return (
                    <Badge variant="outline" className="bg-critical/10 text-critical border-critical/20">
                      Action Required
                    </Badge>
                  );
                }
                return null;
              };

              const getTaskTitle = () => {
                switch (activity.task_type) {
                  case "delivery_risk":
                    return activity.status === "completed" ? "Delivery Risk Resolved" : "Unrisking Late Delivery";
                  case "price_update":
                    return activity.status === "completed" ? "Price Update Complete" : "Price Update";
                  case "product_discovery":
                    return activity.status === "completed" ? "New Product Match Found" : "Product Discovery";
                  case "supplier_followup":
                    return activity.status === "failed" ? "Supplier Not Responding" : "Supplier Follow-up";
                  default:
                    return "Agent Activity";
                }
              };

              const getTimeAgo = (dateString: string) => {
                const date = new Date(dateString);
                const now = new Date();
                const diffMs = now.getTime() - date.getTime();
                const diffMins = Math.floor(diffMs / 60000);
                const diffHours = Math.floor(diffMs / 3600000);
                const diffDays = Math.floor(diffMs / 86400000);

                if (diffMins < 1) return "Just now";
                if (diffMins < 60) return `${diffMins} min ago`;
                if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? "s" : ""} ago`;
                return `${diffDays} day${diffDays > 1 ? "s" : ""} ago`;
              };

              return (
                <div
                  key={activity.task_id}
                  className={`border-l-4 ${taskConfig.borderColor} ${taskConfig.bgColor} border border-border rounded-lg p-4 hover:shadow-md transition-all`}
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-start gap-3 flex-1">
                      {/* Task Type Icon */}
                      <div className={`p-2 ${taskConfig.iconBg} rounded-lg mt-0.5`}>
                        <TaskIcon className={`h-5 w-5 ${taskConfig.iconColor}`} />
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          {getStatusIcon()}
                          <p className="font-semibold text-foreground">{getTaskTitle()}</p>
                        </div>
                        <p className="text-sm text-muted-foreground mb-1">
                          {activity.supplier_name}
                        </p>
                        {activity.description && (
                          <p className="text-xs text-muted-foreground/80">
                            {activity.description}
                          </p>
                        )}
                      </div>
                    </div>
                    <div className="ml-2">
                      {getStatusBadge()}
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between pt-2 border-t border-border/50">
                    <div className="flex items-center gap-4 text-xs text-muted-foreground">
                      <div className="flex items-center gap-1.5">
                        <Clock className="h-3.5 w-3.5" />
                        <span>
                          {activity.started_at
                            ? `Started ${getTimeAgo(activity.started_at)}`
                            : `Created ${getTimeAgo(activity.created_at)}`}
                        </span>
                      </div>
                      {activity.total_messages > 0 && (
                        <div className="flex items-center gap-1.5">
                          <MessageSquare className="h-3.5 w-3.5" />
                          <span>{activity.total_messages} messages</span>
                        </div>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      {activity.status === "completed" && activity.conversation_id && (
                        <>
                          <Button
                            size="sm"
                            variant="outline"
                            className="h-8"
                            onClick={() => handleApplyUpdate(activity.task_id, activity.supplier_name)}
                          >
                            Apply Update
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            className="h-8"
                            onClick={() =>
                              handleViewTranscript(activity.task_id, activity.conversation_id, activity.supplier_name)
                            }
                            disabled={loadingTranscript === activity.task_id}
                          >
                            {loadingTranscript === activity.task_id ? (
                              <Loader2 className="h-3 w-3 animate-spin" />
                            ) : (
                              "View Transcript"
                            )}
                          </Button>
                        </>
                      )}
                      {activity.status === "failed" && (
                        <>
                          <Button
                            size="sm"
                            variant="destructive"
                            className="h-8"
                            onClick={() => handleEscalate(activity.supplier_name)}
                          >
                            Escalate
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            className="h-8"
                            onClick={() => handleRecall(activity.supplier_name, activity.agent_name)}
                          >
                            Re-call
                          </Button>
                        </>
                      )}
                      {(activity.status === "running" || activity.status === "pending") && (
                        <Button
                          size="sm"
                          variant="ghost"
                          className="h-8"
                          onClick={() => handleRecall(activity.supplier_name, activity.agent_name)}
                        >
                          View Status
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </Card>

      {/* Transcript Dialog */}
      <Dialog open={transcriptDialog.open} onOpenChange={(open) => setTranscriptDialog({ ...transcriptDialog, open })}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>
              Call Transcript{transcriptDialog.supplierName ? ` - ${transcriptDialog.supplierName}` : ""}
            </DialogTitle>
            <DialogDescription>AI agent conversation transcript</DialogDescription>
          </DialogHeader>
          <div className="mt-4 p-4 bg-muted rounded-lg max-h-96 overflow-y-auto">
            <p className="text-sm text-foreground whitespace-pre-wrap">{transcriptDialog.content}</p>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default ControlTower;
