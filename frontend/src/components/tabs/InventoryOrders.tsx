import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Progress } from "@/components/ui/progress";
import { Search, AlertTriangle, TrendingDown, Phone, TrendingUp, Package, Clock, RefreshCw } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

// Supplier options with prices and delivery times
const supplierOptions = [
  {
    name: "Medisupply SAS",
    rating: 94,
    deliveryTime: "2-3 days",
    prices: {
      "PARA500": 12.50,
      "IBU400": 18.20,
      "AMOX500": 24.90,
      "FUPLU": 8.75
    }
  },
  {
    name: "PharmaCore Europe",
    rating: 82,
    deliveryTime: "3-5 days",
    prices: {
      "PARA500": 11.80,
      "IBU400": 16.50,
      "AMOX500": 26.40,
      "FUPLU": 9.20
    }
  },
  {
    name: "BioMed Labs",
    rating: 78,
    deliveryTime: "5-7 days",
    prices: {
      "PARA500": 13.20,
      "IBU400": 17.90,
      "AMOX500": 22.50,
      "FUPLU": 10.50
    }
  },
  {
    name: "HealthChem Imports",
    rating: 63,
    deliveryTime: "7-10 days",
    prices: {
      "PARA500": 10.90,
      "IBU400": 15.20,
      "AMOX500": 28.00,
      "FUPLU": 7.95
    }
  },
  {
    name: "EuroDrug Supply",
    rating: 85,
    deliveryTime: "2-4 days",
    prices: {
      "PARA500": 12.00,
      "IBU400": 17.50,
      "AMOX500": 23.80,
      "FUPLU": 8.50
    }
  }
];

const products = [
  {
    sku: "PARA500",
    name: "Paracetamol 500mg - 16 tablets",
    category: "Pain Relief",
    supplier: "Medisupply SAS",
    type: "in-house",
    currentPrice: 12.50,
    bestPrice: 10.90,
    sellPrice: 18.90,
    currentMargin: 34,
    bestMargin: 42
  },
  {
    sku: "IBU400",
    name: "Ibuprofen 400mg - 30 tablets",
    category: "Anti-Inflammatory",
    supplier: "PharmaCore Europe",
    type: "in-house",
    currentPrice: 16.50,
    bestPrice: 15.20,
    sellPrice: 24.50,
    currentMargin: 33,
    bestMargin: 38
  },
  {
    sku: "AMOX500",
    name: "Amoxicillin 500mg - 12 capsules",
    category: "Antibiotic",
    supplier: "BioMed Labs",
    type: "in-house",
    currentPrice: 22.50,
    bestPrice: 22.50,
    sellPrice: 32.90,
    currentMargin: 32,
    bestMargin: 32
  },
  {
    sku: "FUPLU",
    name: "Flu Relief Syrup 150ml",
    category: "Cold & Flu",
    supplier: "Medisupply SAS",
    type: "in-house",
    currentPrice: 8.75,
    bestPrice: 7.95,
    sellPrice: 13.90,
    currentMargin: 37,
    bestMargin: 43
  },
  {
    sku: "VITD1000",
    name: "Vitamin D 1000IU - 60 tablets",
    category: "Vitamins",
    supplier: "PharmaCore Europe",
    type: "external",
    currentPrice: 0,
    bestPrice: 14.20,
    sellPrice: 22.90,
    currentMargin: 0,
    bestMargin: 38
  },
  {
    sku: "PROB30",
    name: "Probiotic Complex - 30 capsules",
    category: "Supplements",
    supplier: "BioMed Labs",
    type: "external",
    currentPrice: 0,
    bestPrice: 19.80,
    sellPrice: 34.90,
    currentMargin: 0,
    bestMargin: 43
  }
];

const InventoryOrders = () => {
  const { toast } = useToast();
  const [detailsDialog, setDetailsDialog] = useState<{ open: boolean; product: any | null }>({ open: false, product: null });
  const [createPODialog, setCreatePODialog] = useState<{ open: boolean; product: any | null }>({ open: false, product: null });
  const [switchSupplierDialog, setSwitchSupplierDialog] = useState<{ open: boolean; product: any | null }>({ open: false, product: null });
  const [poForm, setPOForm] = useState({
    quantity: "",
    supplier: "",
    notes: "",
    urgency: "normal"
  });

  const handleCheckAvailability = async (productName: string) => {
    try {
      const response = await fetch('/api/agent/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          agent_name: "products",
          product_name: productName,
        }),
      });

      if (!response.ok) {
        const errorData = await response.text();
        console.error('API Error:', errorData);
        throw new Error(`Failed to start agent: ${response.status} ${response.statusText}`);
      }

      await response.json();

      toast({
        title: "Checking Availability",
        description: `Voice agent is calling suppliers for ${productName}`,
      });
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : `Failed to start availability check for ${productName}`,
        variant: "destructive",
      });
      console.error('Error starting agent:', error);
    }
  };

  const handleViewDetails = (product: any) => {
    setDetailsDialog({ open: true, product });
  };

  const handleCreatePO = (product: any) => {
    const suggestedQty = Math.ceil(product.weeklyUse * 4);
    setPOForm({
      quantity: suggestedQty.toString(),
      supplier: product.supplier,
      notes: "",
      urgency: product.status === "critical" ? "urgent" : "normal"
    });
    setCreatePODialog({ open: true, product });
  };

  const handleSubmitPO = () => {
    toast({
      title: "Purchase Order Created",
      description: `PO created for ${createPODialog.product?.name} - ${poForm.quantity} units from ${poForm.supplier}`,
    });
    setCreatePODialog({ open: false, product: null });
    setPOForm({ quantity: "", supplier: "", notes: "", urgency: "normal" });
  };

  const handleTrackPO = (poNumber: string) => {
    toast({
      title: "Tracking Purchase Order",
      description: `Opening tracking details for ${poNumber}`,
    });
  };

  const handleSwitchSupplier = (product: any) => {
    setSwitchSupplierDialog({ open: true, product });
  };

  const handleSelectSupplier = (supplierName: string) => {
    toast({
      title: "Supplier Switched",
      description: `${switchSupplierDialog.product?.name} supplier changed to ${supplierName}`,
    });
    setSwitchSupplierDialog({ open: false, product: null });
  };

  return (
    <div className="space-y-6">
      {/* Search and Filters */}
      <Card className="p-4">
        <div className="flex items-center gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input 
              placeholder="Search products by name, SKU, or category..." 
              className="pl-10"
            />
          </div>
          <Button variant="outline">Filter</Button>
        </div>
      </Card>

      {/* Product List */}
      <div className="space-y-4">
        {products.map((product) => (
          <Card key={product.sku} className="p-6 hover:shadow-lg transition-shadow">
            <div className="flex items-start gap-4">
              {/* Product Image Placeholder */}
              <div className="w-16 h-16 bg-muted rounded-lg flex items-center justify-center flex-shrink-0">
                <span className="text-xs text-muted-foreground font-mono">{product.sku}</span>
              </div>

              {/* Product Info */}
              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <h4 className="font-semibold text-foreground">{product.name}</h4>
                      {product.type === "external" ? (
                        <Badge className="bg-blue-50 text-blue-700 border-blue-300">
                          <Package className="h-3 w-3 mr-1" />
                          New Opportunity
                        </Badge>
                      ) : (
                        <Badge variant="outline" className="bg-muted/50">
                          In-House
                        </Badge>
                      )}
                    </div>
                    <p className="text-sm text-muted-foreground">{product.category}</p>
                  </div>
                </div>

                {/* Pricing & Margin Metrics */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                  <div className="bg-primary/5 p-3 rounded-lg border border-primary/10">
                    <p className="text-xs text-muted-foreground mb-1">Best Available Price</p>
                    <p className="text-xl font-bold text-primary">€{product.bestPrice.toFixed(2)}</p>
                    {product.type === "in-house" && product.bestPrice < product.currentPrice && (
                      <p className="text-xs text-success flex items-center gap-1 mt-1">
                        <TrendingDown className="h-3 w-3" />
                        €{(product.currentPrice - product.bestPrice).toFixed(2)} savings
                      </p>
                    )}
                  </div>
                  <div className="bg-success/5 p-3 rounded-lg border border-success/10">
                    <p className="text-xs text-muted-foreground mb-1">Best Margin</p>
                    <p className="text-xl font-bold text-success">{product.bestMargin}%</p>
                    {product.type === "in-house" && product.bestMargin > product.currentMargin && (
                      <p className="text-xs text-success flex items-center gap-1 mt-1">
                        <TrendingUp className="h-3 w-3" />
                        +{product.bestMargin - product.currentMargin}% potential
                      </p>
                    )}
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground mb-1">Sell Price</p>
                    <p className="text-lg font-semibold text-foreground">€{product.sellPrice.toFixed(2)}</p>
                    {product.type === "in-house" && (
                      <p className="text-xs text-muted-foreground mt-1">Current: {product.currentMargin}%</p>
                    )}
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground mb-1">Best Supplier</p>
                    <p className="text-sm font-medium text-foreground">{product.supplier}</p>
                    {product.type === "external" && (
                      <p className="text-xs text-blue-600 mt-1">High margin opportunity</p>
                    )}
                  </div>
                </div>

                {/* External product info */}
                {product.type === "external" && (
                  <div className="mt-4 bg-blue-50 border border-blue-200 rounded-lg p-3">
                    <p className="text-sm font-medium text-blue-900 flex items-center gap-2">
                      <TrendingUp className="h-4 w-4" />
                      High-Margin Expansion Opportunity
                    </p>
                    <p className="text-xs text-blue-700 mt-1">
                      New product with {product.bestMargin}% margin potential • Never purchased before
                    </p>
                  </div>
                )}

                {/* Actions */}
                <div className="flex gap-2 mt-4">
                  <Button onClick={() => handleCheckAvailability(product.name)} size="sm" className="flex items-center gap-2">
                    <Phone className="h-3 w-3" />
                    Check Availability
                  </Button>
                </div>
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* Active Purchase Orders */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-foreground mb-4">Active Purchase Orders</h3>
        <div className="space-y-3">
          <div className="flex items-center justify-between p-4 rounded-lg border border-border">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-1">
                <span className="font-mono text-sm font-medium text-foreground">PO-3421</span>
                <Badge variant="destructive">Delayed</Badge>
                <span className="text-sm text-muted-foreground">BioMed Labs</span>
              </div>
              <p className="text-sm text-foreground">Amoxicillin 500mg - 200 units</p>
              <p className="text-xs text-muted-foreground mt-1">
                Expected: Feb 10 → Revised: Feb 15 (+5 days)
              </p>
            </div>
            <Button onClick={() => handleTrackPO("PO-3421")} size="sm" variant="outline">Track</Button>
          </div>

          <div className="flex items-center justify-between p-4 rounded-lg border border-border">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-1">
                <span className="font-mono text-sm font-medium text-foreground">PO-3427</span>
                <Badge className="bg-success text-success-foreground">On Track</Badge>
                <span className="text-sm text-muted-foreground">Medisupply SAS</span>
              </div>
              <p className="text-sm text-foreground">Paracetamol 500mg - 300 units</p>
              <p className="text-xs text-muted-foreground mt-1">Expected: Feb 11 (in 4 days)</p>
            </div>
            <Button onClick={() => handleTrackPO("PO-3427")} size="sm" variant="outline">Track</Button>
          </div>

          <div className="flex items-center justify-between p-4 rounded-lg border border-border">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-1">
                <span className="font-mono text-sm font-medium text-foreground">PO-3431</span>
                <Badge className="bg-warning text-warning-foreground">Pending</Badge>
                <span className="text-sm text-muted-foreground">PharmaCore Europe</span>
              </div>
              <p className="text-sm text-foreground">Ibuprofen 400mg - 500 units</p>
              <p className="text-xs text-muted-foreground mt-1">Missing ETA confirmation</p>
            </div>
            <Button onClick={() => handleTrackPO("PO-3431")} size="sm" variant="outline">Track</Button>
          </div>
        </div>
      </Card>

      {/* Product Details Dialog */}
      <Dialog open={detailsDialog.open} onOpenChange={(open) => setDetailsDialog({ open, product: null })}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{detailsDialog.product?.name}</DialogTitle>
            <DialogDescription>SKU: {detailsDialog.product?.sku}</DialogDescription>
          </DialogHeader>
          {detailsDialog.product && (
            <div className="space-y-6">
              {/* Stock & Forecast */}
              <div className="grid grid-cols-2 gap-4">
                <Card className="p-4">
                  <div className="space-y-2">
                    <p className="text-sm text-muted-foreground">Current Stock</p>
                    <p className="text-3xl font-bold">{detailsDialog.product.stock}</p>
                    <Progress value={(detailsDialog.product.stock / 500) * 100} className="h-2" />
                  </div>
                </Card>
                <Card className="p-4">
                  <div className="space-y-2">
                    <p className="text-sm text-muted-foreground">Weekly Consumption</p>
                    <p className="text-3xl font-bold">{detailsDialog.product.weeklyUse}</p>
                    <div className="flex items-center gap-2 text-sm text-warning">
                      <TrendingUp className="h-4 w-4" />
                      <span>High demand</span>
                    </div>
                  </div>
                </Card>
              </div>

              {/* Stockout Forecast */}
              <Card className="p-4 border-warning bg-warning/5">
                <div className="flex items-start gap-3">
                  <AlertTriangle className="h-5 w-5 text-warning mt-0.5" />
                  <div>
                    <p className="font-semibold">Projected Stockout</p>
                    <p className="text-sm text-muted-foreground">
                      Expected on {detailsDialog.product.stockoutDate}
                    </p>
                    <p className="text-sm mt-2">
                      Recommended reorder quantity: <span className="font-bold">{Math.ceil(detailsDialog.product.weeklyUse * 4)} units</span> (4 weeks supply)
                    </p>
                  </div>
                </div>
              </Card>

              {/* Supplier Information */}
              <div>
                <h4 className="font-semibold mb-3">Supplier Information</h4>
                <Card className="p-4">
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Current Supplier</span>
                      <span className="font-medium">{detailsDialog.product.supplier}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Lead Time</span>
                      <span className="font-medium">3-5 days</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Unit Price</span>
                      <span className="font-medium">€4.20</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Reliability Score</span>
                      <Badge variant="secondary">94%</Badge>
                    </div>
                  </div>
                </Card>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setDetailsDialog({ open: false, product: null })}>
              Close
            </Button>
            <Button onClick={() => {
              setDetailsDialog({ open: false, product: null });
              handleCreatePO(detailsDialog.product);
            }}>
              Create Purchase Order
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Create PO Dialog */}
      <Dialog open={createPODialog.open} onOpenChange={(open) => setCreatePODialog({ open, product: null })}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Create Purchase Order</DialogTitle>
            <DialogDescription>
              {createPODialog.product?.name} (SKU: {createPODialog.product?.sku})
            </DialogDescription>
          </DialogHeader>
          {createPODialog.product && (
            <div className="space-y-6">
              {/* Current Status Overview */}
              <div className="grid grid-cols-2 gap-4">
                <Card className="p-4">
                  <div className="space-y-2">
                    <p className="text-sm text-muted-foreground">Current Stock</p>
                    <p className="text-3xl font-bold">{createPODialog.product.stock}</p>
                    <Progress value={(createPODialog.product.stock / 500) * 100} className="h-2" />
                  </div>
                </Card>
                <Card className="p-4">
                  <div className="space-y-2">
                    <p className="text-sm text-muted-foreground">Recommended Order</p>
                    <p className="text-3xl font-bold">{Math.ceil(createPODialog.product.weeklyUse * 4)}</p>
                    <div className="flex items-center gap-2 text-sm">
                      <Package className="h-4 w-4 text-muted-foreground" />
                      <span className="text-muted-foreground">4 weeks supply</span>
                    </div>
                  </div>
                </Card>
              </div>

              {/* Risk Alert */}
              {createPODialog.product.status === "critical" && (
                <Card className="p-4 border-critical bg-critical/5">
                  <div className="flex items-start gap-3">
                    <AlertTriangle className="h-5 w-5 text-critical mt-0.5" />
                    <div>
                      <p className="font-semibold">Critical Stock Level</p>
                      <p className="text-sm text-muted-foreground">
                        Expected stockout: {createPODialog.product.stockoutDate}
                      </p>
                    </div>
                  </div>
                </Card>
              )}

              {/* Order Configuration */}
              <div>
                <h4 className="font-semibold mb-3">Order Configuration</h4>
                <Card className="p-4">
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="quantity">Order Quantity *</Label>
                      <Input
                        id="quantity"
                        type="number"
                        value={poForm.quantity}
                        onChange={(e) => setPOForm({ ...poForm, quantity: e.target.value })}
                        placeholder="Enter quantity"
                      />
                      <p className="text-xs text-muted-foreground">
                        Recommended: {Math.ceil(createPODialog.product.weeklyUse * 4)} units based on consumption rate
                      </p>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="supplier">Supplier *</Label>
                      <Select value={poForm.supplier} onValueChange={(value) => setPOForm({ ...poForm, supplier: value })}>
                        <SelectTrigger>
                          <SelectValue placeholder="Select supplier" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="Medisupply SAS">
                            <div className="flex items-center justify-between w-full">
                              <span>Medisupply SAS</span>
                              <span className="text-xs text-muted-foreground ml-4">3-5 days • €4.20</span>
                            </div>
                          </SelectItem>
                          <SelectItem value="PharmaCore Europe">
                            <div className="flex items-center justify-between w-full">
                              <span>PharmaCore Europe</span>
                              <span className="text-xs text-muted-foreground ml-4">2-3 days • €4.50</span>
                            </div>
                          </SelectItem>
                          <SelectItem value="BioMed Labs">
                            <div className="flex items-center justify-between w-full">
                              <span>BioMed Labs</span>
                              <span className="text-xs text-muted-foreground ml-4">5-7 days • €3.90</span>
                            </div>
                          </SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="urgency">Priority Level</Label>
                      <Select value={poForm.urgency} onValueChange={(value) => setPOForm({ ...poForm, urgency: value })}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="urgent">
                            <div className="flex items-center gap-2">
                              <AlertTriangle className="h-4 w-4 text-critical" />
                              <span>Urgent - Expedited shipping</span>
                            </div>
                          </SelectItem>
                          <SelectItem value="normal">
                            <div className="flex items-center gap-2">
                              <Clock className="h-4 w-4 text-muted-foreground" />
                              <span>Normal - Standard delivery</span>
                            </div>
                          </SelectItem>
                          <SelectItem value="low">
                            <div className="flex items-center gap-2">
                              <TrendingDown className="h-4 w-4 text-muted-foreground" />
                              <span>Low Priority</span>
                            </div>
                          </SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="notes">Additional Notes</Label>
                      <Textarea
                        id="notes"
                        value={poForm.notes}
                        onChange={(e) => setPOForm({ ...poForm, notes: e.target.value })}
                        placeholder="Add special instructions, delivery preferences, or other requirements..."
                        rows={3}
                      />
                    </div>
                  </div>
                </Card>
              </div>

              {/* Order Summary */}
              <div>
                <h4 className="font-semibold mb-3">Order Summary</h4>
                <Card className="p-4">
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-muted-foreground">Product</span>
                      <span className="font-medium">{createPODialog.product.name}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-muted-foreground">Quantity</span>
                      <span className="font-medium">{poForm.quantity || "—"} units</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-muted-foreground">Unit Price</span>
                      <span className="font-medium">€4.20</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-muted-foreground">Supplier</span>
                      <span className="font-medium">{poForm.supplier || "—"}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-muted-foreground">Priority</span>
                      <Badge variant={poForm.urgency === "urgent" ? "destructive" : "secondary"}>
                        {poForm.urgency}
                      </Badge>
                    </div>
                    <div className="h-px bg-border my-2" />
                    <div className="flex justify-between items-center">
                      <span className="text-base font-semibold">Total Cost</span>
                      <span className="text-2xl font-bold">
                        €{poForm.quantity ? (parseFloat(poForm.quantity) * 4.2).toFixed(2) : "—"}
                      </span>
                    </div>
                    <div className="flex justify-between items-center text-sm">
                      <span className="text-muted-foreground">Expected Delivery</span>
                      <span className="text-muted-foreground">3-5 business days</span>
                    </div>
                  </div>
                </Card>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreatePODialog({ open: false, product: null })}>
              Cancel
            </Button>
            <Button onClick={handleSubmitPO} disabled={!poForm.quantity || !poForm.supplier}>
              Validate & Create Order
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Switch Supplier Dialog */}
      <Dialog open={switchSupplierDialog.open} onOpenChange={(open) => setSwitchSupplierDialog({ open, product: null })}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Switch Supplier</DialogTitle>
            <DialogDescription>
              Compare suppliers for {switchSupplierDialog.product?.name} (SKU: {switchSupplierDialog.product?.sku})
            </DialogDescription>
          </DialogHeader>
          {switchSupplierDialog.product && (
            <div className="space-y-3">
              <div className="bg-muted/50 p-3 rounded-lg">
                <p className="text-sm text-muted-foreground">Current Supplier</p>
                <p className="font-semibold">{switchSupplierDialog.product.supplier}</p>
              </div>
              
              <div className="space-y-2">
                <p className="text-sm font-medium">Available Suppliers</p>
                {supplierOptions.map((supplier) => {
                  const price = supplier.prices[switchSupplierDialog.product.sku as keyof typeof supplier.prices];
                  const isCurrentSupplier = supplier.name === switchSupplierDialog.product.supplier;
                  
                  return (
                    <Card 
                      key={supplier.name} 
                      className={`p-4 hover:shadow-md transition-shadow ${isCurrentSupplier ? 'border-primary bg-primary/5' : ''}`}
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1 space-y-2">
                          <div className="flex items-center gap-2">
                            <h4 className="font-semibold">{supplier.name}</h4>
                            {isCurrentSupplier && (
                              <Badge variant="outline" className="text-xs">Current</Badge>
                            )}
                          </div>
                          
                          <div className="grid grid-cols-3 gap-4 text-sm">
                            <div>
                              <p className="text-muted-foreground">Unit Price</p>
                              <p className="font-semibold text-lg">€{price.toFixed(2)}</p>
                            </div>
                            <div>
                              <p className="text-muted-foreground">Delivery Time</p>
                              <p className="font-medium">{supplier.deliveryTime}</p>
                            </div>
                            <div>
                              <p className="text-muted-foreground">Rating</p>
                              <div className="flex items-center gap-1">
                                <span className="font-medium">{supplier.rating}%</span>
                                <Badge 
                                  variant={supplier.rating >= 90 ? "default" : supplier.rating >= 75 ? "secondary" : "destructive"}
                                  className="text-xs"
                                >
                                  {supplier.rating >= 90 ? "Excellent" : supplier.rating >= 75 ? "Good" : "Fair"}
                                </Badge>
                              </div>
                            </div>
                          </div>
                        </div>
                        
                        <Button
                          size="sm"
                          disabled={isCurrentSupplier}
                          onClick={() => handleSelectSupplier(supplier.name)}
                        >
                          {isCurrentSupplier ? "Selected" : "Select"}
                        </Button>
                      </div>
                    </Card>
                  );
                })}
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setSwitchSupplierDialog({ open: false, product: null })}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default InventoryOrders;
