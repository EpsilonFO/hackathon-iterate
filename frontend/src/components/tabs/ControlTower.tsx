import React from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { AlertTriangle, Clock, Package, Phone, CheckCircle2, AlertCircle, Loader2, MessageSquare, Truck, Search, Bot, User } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { agentApi, AgentActivityItem, Transcript } from "@/lib/api";

const ControlTower = () => {
  const { toast } = useToast();
  const [transcriptDialog, setTranscriptDialog] = React.useState<{ open: boolean; transcript: Transcript | null; supplierName?: string }>({
    open: false,
    transcript: null,
    supplierName: undefined,
  });
  const [activities, setActivities] = React.useState<AgentActivityItem[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [loadingTranscript, setLoadingTranscript] = React.useState<string | null>(null);

  // Fetch data on mount
  React.useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const limit = 10; // Use same limit for recap
        const recapData = await agentApi.getActivityRecap(limit);
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

  // Calculate counts and time saved from activities
  const calculateStats = () => {
    const stats = {
      availability_checks: 0,
      delivery_checks: 0,
      product_inquiries: 0,
      time_saved_minutes: 0,
    };

    activities.forEach((activity) => {
      // Count completed activities by type
      if (activity.status === "completed") {
        switch (activity.task_type) {
          case "availability":
            stats.availability_checks++;
            break;
          case "delivery":
            stats.delivery_checks++;
            break;
          case "products":
            stats.product_inquiries++;
            break;
        }
      }

      // Calculate time saved: 1 message = 30 seconds = 0.5 minutes
      if (activity.total_messages > 0) {
        stats.time_saved_minutes += activity.total_messages * 0.5;
      }
    });

    return stats;
  };

  const stats = calculateStats();

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
        transcript: transcript,
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


  // Calculate time saved per category based on messages
  const getTimeSavedForCategory = (category: string) => {
    let totalMessages = 0;
    activities.forEach((activity) => {
      if (activity.status === "completed") {
        switch (category) {
          case "availability":
            if (activity.task_type === "availability") {
              totalMessages += activity.total_messages;
            }
            break;
          case "delivery":
            if (activity.task_type === "delivery") {
              totalMessages += activity.total_messages;
            }
            break;
          case "products":
            if (activity.task_type === "products") {
              totalMessages += activity.total_messages;
            }
            break;
        }
      }
    });
    // 1 message = 30 seconds = 0.5 minutes
    return Math.round(totalMessages * 0.5);
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
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="p-6 border-l-4 border-l-primary hover:shadow-lg transition-shadow cursor-pointer">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-base font-bold text-foreground">Availability Checks</p>
              <p className="text-3xl font-bold text-foreground mt-1">
                {stats.availability_checks}
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                Saved <strong className="text-primary">
                  {getTimeSavedForCategory("availability")} min
                </strong> checking product availability
              </p>
            </div>
            <div className="p-2 bg-primary/10 rounded-lg">
              <Package className="h-5 w-5 text-primary" />
            </div>
          </div>
        </Card>

        <Card className="p-6 border-l-4 border-l-critical hover:shadow-lg transition-shadow cursor-pointer">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-base font-bold text-foreground">Delivery Follow Ups</p>
              <p className="text-3xl font-bold text-foreground mt-1">
                {stats.delivery_checks}
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                Saved <strong className="text-critical">
                  {getTimeSavedForCategory("delivery")} min
                </strong> checking delivery status
              </p>
            </div>
            <div className="p-2 bg-critical/10 rounded-lg">
              <Truck className="h-5 w-5 text-critical" />
            </div>
          </div>
        </Card>

        <Card className="p-6 border-l-4 border-l-moderate hover:shadow-lg transition-shadow cursor-pointer">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-base font-bold text-foreground">Product Inquiries</p>
              <p className="text-3xl font-bold text-foreground mt-1">
                {stats.product_inquiries}
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                Saved <strong className="text-moderate">
                  {getTimeSavedForCategory("products")} min
                </strong> getting product information
              </p>
            </div>
            <div className="p-2 bg-moderate/10 rounded-lg">
              <Search className="h-5 w-5 text-moderate" />
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
                  case "availability":
                    return {
                      borderColor: "border-l-primary",
                      bgColor: "bg-primary/5",
                      iconColor: "text-primary",
                      iconBg: "bg-primary/10",
                      icon: Package,
                      title: "Availability Check",
                      shortTitle: "Availability",
                    };
                  case "delivery":
                    return {
                      borderColor: "border-l-critical",
                      bgColor: "bg-critical/5",
                      iconColor: "text-critical",
                      iconBg: "bg-critical/10",
                      icon: Truck,
                      title: "Delivery Check",
                      shortTitle: "Delivery",
                    };
                  case "products":
                  default:
                    return {
                      borderColor: "border-l-moderate",
                      bgColor: "bg-moderate/5",
                      iconColor: "text-moderate",
                      iconBg: "bg-moderate/10",
                      icon: Search,
                      title: activity.status === "failed" ? "Product Inquiry Failed" : "Product Inquiry",
                      shortTitle: "Products",
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
                  case "availability":
                    return activity.status === "completed" ? "Availability Check Complete" : "Checking Availability";
                  case "delivery":
                    return activity.status === "completed" ? "Delivery Check Complete" : "Checking Delivery";
                  case "products":
                    return activity.status === "completed" ? "Product Inquiry Complete" : "Product Inquiry";
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
                      )}
                      {activity.status === "failed" && (
                        <Button
                          size="sm"
                          variant="destructive"
                          className="h-8"
                          onClick={() => handleEscalate(activity.supplier_name)}
                        >
                          Escalate
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
        <DialogContent className="max-w-3xl max-h-[85vh] flex flex-col">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <MessageSquare className="h-5 w-5" />
              Call Transcript{transcriptDialog.supplierName ? ` - ${transcriptDialog.supplierName}` : ""}
            </DialogTitle>
            <DialogDescription>
              {transcriptDialog.transcript?.total_messages || 0} messages • {transcriptDialog.transcript?.timestamp ? new Date(transcriptDialog.transcript.timestamp).toLocaleString() : ""}
            </DialogDescription>
          </DialogHeader>
          <div className="mt-4 flex-1 overflow-y-auto space-y-3 pr-2">
            {transcriptDialog.transcript?.messages && transcriptDialog.transcript.messages.length > 0 ? (
              transcriptDialog.transcript.messages.map((message, index) => {
                const isAgent = message.role === "agent";
                return (
                  <div
                    key={index}
                    className={`flex gap-3 ${isAgent ? "justify-start" : "justify-end"}`}
                  >
                    {isAgent && (
                      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                        <Bot className="h-4 w-4 text-primary" />
                      </div>
                    )}
                    <div
                      className={`flex flex-col max-w-[80%] ${
                        isAgent ? "items-start" : "items-end"
                      }`}
                    >
                      <div
                        className={`px-4 py-2.5 rounded-lg ${
                          isAgent
                            ? "bg-primary/10 text-foreground border border-primary/20"
                            : "bg-muted text-foreground border border-border"
                        }`}
                      >
                        <div className="text-xs font-medium mb-1.5 opacity-70">
                          {isAgent ? "AI Agent" : "Supplier Representative"}
                        </div>
                        <p className="text-sm leading-relaxed whitespace-pre-wrap break-words">
                          {message.text}
                        </p>
                      </div>
                    </div>
                    {!isAgent && (
                      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-muted flex items-center justify-center">
                        <User className="h-4 w-4 text-muted-foreground" />
                      </div>
                    )}
                  </div>
                );
              })
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <p>No transcript content available</p>
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default ControlTower;
