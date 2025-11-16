import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { Progress } from "@/components/ui/progress";
import { TrendingUp, TrendingDown, Phone, DollarSign, Target, Package, AlertCircle, Loader2, ChevronDown, ChevronUp, Truck, Tag, ShoppingCart, Boxes, Info } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { suppliersApi, SupplierROIResponse, PerformanceBreakdown } from "@/lib/api";

// Component to display performance breakdown
const PerformanceBreakdownView = ({ breakdown }: { breakdown: PerformanceBreakdown }) => {
  const [isOpen, setIsOpen] = useState(false);

  const getScoreColor = (score: number) => {
    if (score >= 80) return "text-green-600";
    if (score >= 60) return "text-yellow-600";
    return "text-red-600";
  };

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen} className="w-full">
      <CollapsibleTrigger asChild>
        <Button variant="ghost" size="sm" className="w-full justify-between">
          <span className="flex items-center gap-2">
            <Info className="h-4 w-4" />
            Performance Details
          </span>
          {isOpen ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </Button>
      </CollapsibleTrigger>
      <CollapsibleContent className="space-y-4 pt-4">
        <div className="text-xs text-muted-foreground mb-3 p-2 bg-muted/50 rounded">
          Performance is calculated as: Delivery (40%) + Price (30%) + Volume (20%) + Diversity (10%)
        </div>

        {/* Delivery Performance */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Truck className="h-4 w-4 text-blue-600" />
              <span className="text-sm font-semibold">Delivery Performance (40%)</span>
            </div>
            <span className={`text-sm font-bold ${getScoreColor(breakdown.delivery_score)}`}>
              {breakdown.delivery_score.toFixed(1)}%
            </span>
          </div>
          <Progress value={breakdown.delivery_score} className="h-2" />
          <div className="text-xs text-muted-foreground grid grid-cols-3 gap-2">
            <span>On-time: {breakdown.delivery_on_time}</span>
            <span>Late: {breakdown.delivery_late}</span>
            <span>Rate: {breakdown.delivery_on_time_rate.toFixed(1)}%</span>
          </div>
        </div>

        {/* Price Competitiveness */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Tag className="h-4 w-4 text-purple-600" />
              <span className="text-sm font-semibold">Price Competitiveness (30%)</span>
            </div>
            <span className={`text-sm font-bold ${getScoreColor(breakdown.price_score)}`}>
              {breakdown.price_score.toFixed(1)}%
            </span>
          </div>
          <Progress value={breakdown.price_score} className="h-2" />
          <div className="text-xs text-muted-foreground">
            {breakdown.price_cheaper_alternatives} cheaper alternatives found across {breakdown.price_product_count} products
          </div>
        </div>

        {/* Order Volume */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <ShoppingCart className="h-4 w-4 text-orange-600" />
              <span className="text-sm font-semibold">Order Volume (20%)</span>
            </div>
            <span className={`text-sm font-bold ${getScoreColor(breakdown.volume_score)}`}>
              {breakdown.volume_score.toFixed(1)}%
            </span>
          </div>
          <Progress value={breakdown.volume_score} className="h-2" />
          <div className="text-xs text-muted-foreground">
            Monthly spend: €{breakdown.volume_monthly_spend.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
        </div>

        {/* Product Diversity */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Boxes className="h-4 w-4 text-teal-600" />
              <span className="text-sm font-semibold">Product Diversity (10%)</span>
            </div>
            <span className={`text-sm font-bold ${getScoreColor(breakdown.diversity_score)}`}>
              {breakdown.diversity_score.toFixed(1)}%
            </span>
          </div>
          <Progress value={breakdown.diversity_score} className="h-2" />
          <div className="text-xs text-muted-foreground">
            {breakdown.diversity_product_count} unique products
          </div>
        </div>
      </CollapsibleContent>
    </Collapsible>
  );
};

const SuppliersROI = () => {
  const { toast } = useToast();
  const [data, setData] = useState<SupplierROIResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await suppliersApi.getSupplierROI();
        setData(response);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : "Failed to load supplier data";
        setError(errorMessage);
        toast({
          title: "Error",
          description: errorMessage,
          variant: "destructive",
        });
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [toast]);

  const handleUpdateCatalog = async (supplierName: string) => {
    try {
      const response = await fetch('/api/agent/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          agent_name: "products",
          supplier_name: supplierName,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to start agent');
      }

      await response.json();

      toast({
        title: "Catalog Update",
        description: `Agent started for ${supplierName}`,
      });
    } catch (error) {
      toast({
        title: "Error",
        description: `Failed to start catalog update for ${supplierName}`,
        variant: "destructive",
      });
      console.error('Error starting agent:', error);
    }
  };

  const handleRemindSupplier = async (supplierName: string) => {
    try {
      const response = await fetch('/api/agent/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          agent_name: "delivery",
          supplier_name: supplierName,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to start agent');
      }

      await response.json();

      toast({
        title: "Follow Up",
        description: `Agent started for ${supplierName}`,
      });
    } catch (error) {
      toast({
        title: "Error",
        description: `Failed to start follow up for ${supplierName}`,
        variant: "destructive",
      });
      console.error('Error starting agent:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="text-center text-muted-foreground">
            {error || "No data available"}
          </div>
        </CardContent>
      </Card>
    );
  }

  const suppliers = data.suppliers;
  const totalSpend = data.total_monthly_spend;
  const avgPerformance = Math.round(data.avg_performance);
  const excellentSuppliers = data.excellent_count;
  const warningSuppliers = data.warning_count;

  return (
    <div className="space-y-6">
      {/* Overview Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="h-5 w-5 text-primary" />
            Strategic ROI Overview
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            <div className="space-y-2">
              <p className="text-sm text-muted-foreground flex items-center gap-1">
                <DollarSign className="h-4 w-4" />
                Total Monthly Spend
              </p>
              <p className="text-2xl font-bold">€{totalSpend.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</p>
            </div>
            <div className="space-y-2">
              <p className="text-sm text-muted-foreground flex items-center gap-1">
                <TrendingUp className="h-4 w-4" />
                Avg Performance
              </p>
              <p className="text-2xl font-bold">{avgPerformance}%</p>
            </div>
            <div className="space-y-2">
              <p className="text-sm text-muted-foreground flex items-center gap-1">
                <Target className="h-4 w-4" />
                Top Performers
              </p>
              <p className="text-2xl font-bold text-green-600">{excellentSuppliers}</p>
            </div>
            <div className="space-y-2">
              <p className="text-sm text-muted-foreground flex items-center gap-1">
                <AlertCircle className="h-4 w-4" />
                Needs Attention
              </p>
              <p className="text-2xl font-bold text-amber-600">{warningSuppliers}</p>
            </div>
          </div>
          <div className="mt-6 p-4 bg-muted/50 rounded-lg">
            <p className="text-sm">
              <strong>Strategic Insight:</strong> {excellentSuppliers} suppliers are performing exceptionally well,
              accounting for{" "}
              {Math.round(
                (suppliers.filter((s) => s.status === "excellent").reduce((sum, s) => sum + s.monthly_spend, 0) /
                  totalSpend) *
                  100,
              )}
              % of total spend. Consider consolidating volumes with top performers to maximize ROI.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Suppliers Needing Attention */}
      {warningSuppliers > 0 && (
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-amber-600" />
            <h2 className="text-xl font-semibold">Suppliers Needing Attention</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {suppliers
              .filter((s) => s.status === "warning")
              .map((supplier) => (
                <Card key={supplier.id} className="hover:shadow-lg transition-shadow border-amber-500/50 bg-amber-50/30">
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between">
                      <CardTitle className="text-lg">{supplier.name}</CardTitle>
                      {supplier.trend === "up" && <TrendingUp className="h-4 w-4 text-green-600" />}
                      {supplier.trend === "down" && <TrendingDown className="h-4 w-4 text-red-600" />}
                    </div>
                    <Badge variant="destructive" className="w-fit mt-1">
                      {supplier.status.charAt(0).toUpperCase() + supplier.status.slice(1)}
                    </Badge>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">Performance</span>
                        <span className="font-semibold">{supplier.performance}%</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">Monthly Spend</span>
                        <span className="font-semibold">€{supplier.monthly_spend.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                      </div>
                    </div>

                    {supplier.issues && supplier.issues.length > 0 && (
                      <div className="space-y-2 pt-2 border-t border-amber-200">
                        <p className="text-xs font-semibold text-amber-700 flex items-center gap-1">
                          <AlertCircle className="h-3 w-3" />
                          Active Issues:
                        </p>
                        <div className="flex flex-wrap gap-1">
                          {supplier.issues.map((issue, idx) => (
                            <Badge key={idx} variant="outline" className="text-xs bg-amber-50 text-amber-700 border-amber-300">
                              {issue}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}

                    {supplier.performance_breakdown && (
                      <div className="pt-2 border-t border-amber-200">
                        <PerformanceBreakdownView breakdown={supplier.performance_breakdown} />
                      </div>
                    )}

                    <div className="flex justify-center pt-2">
                      <Popover>
                        <PopoverTrigger asChild>
                          <Button variant="outline" size="sm" className="w-full">
                            <Phone className="h-4 w-4 mr-2" />
                            Contact
                          </Button>
                        </PopoverTrigger>
                        <PopoverContent className="w-56 p-2">
                          <div className="flex flex-col gap-1">
                            <Button
                              variant="ghost"
                              size="sm"
                              className="w-full justify-start"
                              onClick={() => handleUpdateCatalog(supplier.name)}
                            >
                              <Package className="h-4 w-4 mr-2" />
                              Catalog Update
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="w-full justify-start"
                              onClick={() => handleRemindSupplier(supplier.name)}
                            >
                              <Phone className="h-4 w-4 mr-2" />
                              Follow Up
                            </Button>
                          </div>
                        </PopoverContent>
                      </Popover>
                    </div>
                  </CardContent>
                </Card>
              ))}
          </div>
        </div>
      )}

      {/* All Other Suppliers */}
      <div className="space-y-4">
        <h2 className="text-xl font-semibold">All Suppliers</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {suppliers
            .filter((s) => s.status !== "warning")
            .map((supplier) => (
          <Card key={supplier.id} className="hover:shadow-lg transition-shadow">
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between">
                <CardTitle className="text-lg">{supplier.name}</CardTitle>
                {supplier.trend === "up" && <TrendingUp className="h-4 w-4 text-green-600" />}
                {supplier.trend === "down" && <TrendingDown className="h-4 w-4 text-red-600" />}
              </div>
              <Badge
                variant={
                  supplier.status === "excellent" ? "default" : supplier.status === "good" ? "secondary" : "destructive"
                }
                className="w-fit mt-1"
              >
                {supplier.status.charAt(0).toUpperCase() + supplier.status.slice(1)}
              </Badge>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Performance</span>
                  <span className="font-semibold">{supplier.performance}%</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Monthly Spend</span>
                  <span className="font-semibold">€{supplier.monthly_spend.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                </div>
              </div>

              {supplier.performance_breakdown && (
                <div className="pt-2 border-t">
                  <PerformanceBreakdownView breakdown={supplier.performance_breakdown} />
                </div>
              )}

              <div className="flex justify-center pt-2">
                <Popover>
                  <PopoverTrigger asChild>
                    <Button
                      variant="outline"
                      size="sm"
                      className="w-full"
                    >
                      <Phone className="h-4 w-4 mr-2" />
                      Contact
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-56 p-2">
                    <div className="flex flex-col gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="w-full justify-start"
                        onClick={() => handleUpdateCatalog(supplier.name)}
                      >
                        <Package className="h-4 w-4 mr-2" />
                        Catalog Update
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="w-full justify-start"
                        onClick={() => handleRemindSupplier(supplier.name)}
                      >
                        <Phone className="h-4 w-4 mr-2" />
                        Follow Up
                      </Button>
                    </div>
                  </PopoverContent>
                </Popover>
              </div>
            </CardContent>
              </Card>
            ))}
        </div>
      </div>
    </div>
  );
};

export default SuppliersROI;
