import { useState, useEffect } from "react";
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
import { productsApi, agentApi, type InventoryProduct, type SupplierOption } from "@/lib/api";

const InventoryOrders = () => {
  const { toast } = useToast();
  const [products, setProducts] = useState<InventoryProduct[]>([]);
  const [supplierOptions, setSupplierOptions] = useState<SupplierOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingSuppliers, setLoadingSuppliers] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [productTypeFilter, setProductTypeFilter] = useState<"all" | "in-house" | "external">("all");
  const [displayLimit, setDisplayLimit] = useState(10);

  // Helper function to round to 1 decimal place
  const round1 = (value: number): number => Math.round(value * 10) / 10;

  // Filter products based on search query and product type
  const filteredProducts = products.filter((product) => {
    // Filter by product type
    if (productTypeFilter !== "all" && product.type !== productTypeFilter) {
      return false;
    }
    
    // Filter by search query
    if (!searchQuery.trim()) return true;
    
    const query = searchQuery.toLowerCase().trim();
    return (
      product.name.toLowerCase().includes(query) ||
      product.category.toLowerCase().includes(query) ||
      product.supplier.toLowerCase().includes(query) ||
      product.currentPriceSupplier.toLowerCase().includes(query) ||
      product.bestPriceSupplier.toLowerCase().includes(query)
    );
  });

  // Sort products by improvement priority
  const sortedProducts = [...filteredProducts].sort((a, b) => {
    // Priority order:
    // 1. Dual improvement (same supplier has both best price and delivery)
    // 2. Both improvements (best price and faster delivery, but different suppliers)
    // 3. Best price only
    // 4. Faster delivery only
    // 5. No improvements
    
    const getPriority = (product: InventoryProduct): number => {
      if (product.dualImprovementSameSupplier) return 1;
      if (product.marginImprovementPossible && product.deliveryImprovementPossible) return 2;
      if (product.marginImprovementPossible) return 3;
      if (product.deliveryImprovementPossible) return 4;
      return 5;
    };
    
    return getPriority(a) - getPriority(b);
  });

  // Limit displayed products
  const displayedProducts = sortedProducts.slice(0, displayLimit);
  const hasMoreProducts = sortedProducts.length > displayLimit;
  const showLessButton = displayLimit > 10 && sortedProducts.length <= displayLimit;
  const [detailsDialog, setDetailsDialog] = useState<{ open: boolean; product: InventoryProduct | null }>({ open: false, product: null });
  const [createPODialog, setCreatePODialog] = useState<{ open: boolean; product: InventoryProduct | null }>({ open: false, product: null });
  const [switchSupplierDialog, setSwitchSupplierDialog] = useState<{ open: boolean; product: InventoryProduct | null }>({ open: false, product: null });
  const [poForm, setPOForm] = useState({
    quantity: "",
    supplier: "",
    notes: "",
    urgency: "normal"
  });

  const handleCheckAvailability = async (productName: string, supplierName: string) => {
    try {
      const response = await agentApi.startConversation({
        agent_name: "availability",
        product_name: productName,
        supplier_name: supplierName,
      });

      toast({
        title: "Checking Availability",
        description: `Voice agent is calling ${supplierName} for ${productName}`,
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
  // Fetch products and orders on component mount
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const productsResponse = await productsApi.getInStoreProducts();
        setProducts(productsResponse.products);
      } catch (error) {
        toast({
          title: "Error",
          description: error instanceof Error ? error.message : "Failed to load data",
          variant: "destructive",
        });
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [toast]);

  // Reset display limit when filters change
  useEffect(() => {
    setDisplayLimit(10);
  }, [searchQuery, productTypeFilter]);

  // Fetch suppliers when switch supplier dialog opens
  useEffect(() => {
    const fetchSuppliers = async () => {
      if (switchSupplierDialog.open && switchSupplierDialog.product) {
        try {
          setLoadingSuppliers(true);
          const response = await productsApi.getProductSuppliers(switchSupplierDialog.product.id);
          setSupplierOptions(response.suppliers);
        } catch (error) {
          toast({
            title: "Error",
            description: error instanceof Error ? error.message : "Failed to load suppliers",
            variant: "destructive",
          });
        } finally {
          setLoadingSuppliers(false);
        }
      }
    };
    fetchSuppliers();
  }, [switchSupplierDialog.open, switchSupplierDialog.product, toast]);

  const handleViewDetails = (product: InventoryProduct) => {
    setDetailsDialog({ open: true, product });
  };

  const handleCreatePO = (product: InventoryProduct) => {
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

  const handleSwitchSupplier = (product: InventoryProduct) => {
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
        <div className="flex items-center gap-4 flex-wrap">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input 
              placeholder="Search products by name, SKU, category, or supplier..." 
              className="pl-10"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery("")}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-muted-foreground hover:text-foreground text-xl leading-none"
                aria-label="Clear search"
              >
                ×
              </button>
            )}
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant={productTypeFilter === "all" ? "default" : "outline"}
              size="sm"
              onClick={() => setProductTypeFilter("all")}
            >
              All
            </Button>
            <Button
              variant={productTypeFilter === "in-house" ? "default" : "outline"}
              size="sm"
              onClick={() => setProductTypeFilter("in-house")}
            >
              In-House
            </Button>
            <Button
              variant={productTypeFilter === "external" ? "default" : "outline"}
              size="sm"
              onClick={() => setProductTypeFilter("external")}
            >
              New Products
            </Button>
          </div>
          {(searchQuery || productTypeFilter !== "all") && (
            <div className="text-sm text-muted-foreground whitespace-nowrap">
              {sortedProducts.length} {sortedProducts.length === 1 ? 'product' : 'products'}
            </div>
          )}
        </div>
      </Card>

      {/* Product List */}
      {loading ? (
        <Card className="p-6">
          <div className="flex items-center justify-center gap-2">
            <RefreshCw className="h-4 w-4 animate-spin" />
            <span>Loading products...</span>
          </div>
        </Card>
      ) : (
        <div className="space-y-4">
          {searchQuery && sortedProducts.length === 0 && (
            <Card className="p-6">
              <div className="text-center text-muted-foreground">
                <p className="text-sm">No products found matching "{searchQuery}"</p>
                <Button 
                  variant="link" 
                  className="mt-2"
                  onClick={() => setSearchQuery("")}
                >
                  Clear search
                </Button>
              </div>
            </Card>
          )}
          {displayedProducts.map((product) => {
            // Determine if product should be highlighted
            const isExternal = product.type === "external";
            const hasMarginImprovement = product.marginImprovementPossible;
            const hasDeliveryImprovement = product.deliveryImprovementPossible;
            const hasDualImprovement = product.dualImprovementSameSupplier;
            
            // Determine border color based on improvement type
            let borderClass = "";
            if (isExternal) {
              borderClass = "border-l-4 border-l-blue-500";
            } else if (hasDualImprovement) {
              borderClass = "border-l-4 border-l-purple-500";
            } else if (hasMarginImprovement && hasDeliveryImprovement) {
              borderClass = "border-l-4 border-l-purple-500";
            } else if (hasMarginImprovement) {
              borderClass = "border-l-4 border-l-green-500";
            } else if (hasDeliveryImprovement) {
              borderClass = "border-l-4 border-l-orange-500";
            }
            
            return (
          <Card key={product.id} className={`p-4 hover:shadow-md transition-shadow ${borderClass}`}>
            <div className="flex items-center gap-4">
              {/* Product Info - Compact One Line */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-3 flex-wrap">
                  <h4 className="font-semibold text-foreground truncate">{product.name}</h4>
                  {product.type === "external" ? (
                    <Badge className="bg-blue-500 text-white text-xs">
                      <Package className="h-3 w-3 mr-1" />
                      New
                    </Badge>
                  ) : (
                    <Badge variant="outline" className="bg-muted/50 text-xs">
                      In-House
                    </Badge>
                  )}
                  {!isExternal && hasDualImprovement && (
                    <Badge className="bg-purple-500 text-white text-xs">
                      <TrendingUp className="h-3 w-3 mr-1" />
                      Better Price & Faster
                    </Badge>
                  )}
                  {!isExternal && !hasDualImprovement && hasMarginImprovement && (
                    <Badge className="bg-green-500 text-white text-xs">
                      <TrendingUp className="h-3 w-3 mr-1" />
                      Better Price
                    </Badge>
                  )}
                  {!isExternal && !hasDualImprovement && hasDeliveryImprovement && (
                    <Badge className="bg-orange-500 text-white text-xs">
                      <Clock className="h-3 w-3 mr-1" />
                      Faster
                    </Badge>
                  )}
                </div>
                
                {/* Main Info Row */}
                <div className="flex items-center gap-6 mt-2 flex-wrap">
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-muted-foreground">Price:</span>
                    <span className="text-sm font-semibold">
                      {product.type === "external" 
                        ? `€${product.bestPrice.toFixed(2)}`
                        : `€${product.currentPrice.toFixed(2)}`}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-muted-foreground">Delivery:</span>
                    <span className="text-sm font-semibold">
                      {product.type === "external"
                        ? (product.bestDeliveryTime ? `${product.bestDeliveryTime}d` : 'N/A')
                        : (product.currentDeliveryTime ? `${product.currentDeliveryTime}d` : 'N/A')}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-muted-foreground">Supplier: </span>
                    <span className="text-sm font-semibold">
                      {product.type === "external" 
                        ? product.bestPriceSupplier 
                        : product.currentPriceSupplier}
                    </span>
                  </div>
                  {product.type === "in-house" && (
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-muted-foreground">Margin:</span>
                      <span className="text-sm font-semibold">{round1(product.currentMargin)}%</span>
                    </div>
                  )}
                </div>

                {/* Improvement Info - Only if exists */}
                {(hasMarginImprovement || hasDeliveryImprovement) && (
                  <div className="mt-2 pt-2 border-t border-border/50">
                    <div className="flex items-center gap-4 flex-wrap text-xs">
                      {hasMarginImprovement && (
                        <div className="flex items-center gap-1.5">
                          <TrendingDown className="h-3 w-3 text-green-600" />
                          <span className="text-muted-foreground">Best price:</span>
                          <span className="font-semibold text-green-600">€{product.bestPrice.toFixed(2)}</span>
                          <span className="text-muted-foreground">({product.bestPriceSupplier})</span>
                          <span className="text-green-600">Save €{(product.currentPrice - product.bestPrice).toFixed(2)}</span>
                        </div>
                      )}
                      {hasDeliveryImprovement && product.bestDeliveryTime && (
                        <div className="flex items-center gap-1.5">
                          <Clock className="h-3 w-3 text-orange-600" />
                          <span className="text-muted-foreground">Fastest:</span>
                          <span className="font-semibold text-orange-600">{product.bestDeliveryTime}d</span>
                          <span className="text-muted-foreground">({product.bestDeliverySupplier})</span>
                          <span className="text-orange-600">{product.currentDeliveryTime! - product.bestDeliveryTime}d faster</span>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>

              {/* Actions */}
              <div className="flex-shrink-0">
                <Button onClick={() => handleCheckAvailability(product.name, product.supplier)} size="sm" variant="outline" className="flex items-center gap-2">
                  <Phone className="h-3 w-3" />
                  Check availability
                </Button>
              </div>
            </div>
          </Card>
          );
          })}
          
          {/* See More / Show Less Button */}
          {(hasMoreProducts || showLessButton) && (
            <div className="flex justify-center pt-4">
              {hasMoreProducts ? (
                <Button
                  variant="outline"
                  onClick={() => setDisplayLimit(prev => prev + 10)}
                  className="w-full max-w-xs"
                >
                  See more ({sortedProducts.length - displayLimit} remaining)
                </Button>
              ) : (
                <Button
                  variant="outline"
                  onClick={() => setDisplayLimit(10)}
                  className="w-full max-w-xs"
                >
                  Show less
                </Button>
              )}
            </div>
          )}
        </div>
      )}

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
                {loadingSuppliers ? (
                  <div className="flex items-center justify-center gap-2 py-4">
                    <RefreshCw className="h-4 w-4 animate-spin" />
                    <span>Loading suppliers...</span>
                  </div>
                ) : supplierOptions.length === 0 ? (
                  <p className="text-sm text-muted-foreground py-4">No suppliers available</p>
                ) : (
                  supplierOptions.map((supplier) => {
                    const isCurrentSupplier = supplier.id === switchSupplierDialog.product.supplier_id;
                  
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
                              <p className="font-semibold text-lg">€{supplier.price.toFixed(2)}</p>
                            </div>
                            <div>
                              <p className="text-muted-foreground">Delivery Time</p>
                              <p className="font-medium">{supplier.delivery_time}</p>
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
                  })
                )}
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
