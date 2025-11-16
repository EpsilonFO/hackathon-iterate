/**
 * API client for backend communication
 * 
 * This module provides a clean, reusable API layer that can be extended
 * for other pages/components.
 */

// ============================================================================
// API Configuration
// ============================================================================

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// ============================================================================
// Type Definitions
// ============================================================================

export interface InventoryProduct {
  id: string;
  sku: string;
  name: string;
  category: string;
  stock: number;
  weeklyUse: number;
  stockoutDate: string;
  status: 'healthy' | 'low' | 'critical';
  supplier: string;
  supplier_id: string;
  currentPrice: number;
  currentPriceSupplier: string;
  bestPrice: number;
  bestPriceSupplier: string;
  bestPriceSupplierId: string;
  sellPrice: number;
  currentMargin: number;
  bestMargin: number;
  currentDeliveryTime: number | null;
  currentDeliverySupplier: string;
  bestDeliveryTime: number | null;
  bestDeliverySupplier: string;
  bestDeliverySupplierId: string;
  marginImprovementPossible: boolean;
  deliveryImprovementPossible: boolean;
  dualImprovementSameSupplier: boolean;
  type: 'in-house' | 'external';
}

export interface ActivePurchaseOrder {
  order_id: string;
  product_name: string;
  quantity: number;
  supplier_name: string;
  estimated_delivery: string;
  actual_delivery: string | null;
  status: 'on_track' | 'delayed' | 'pending';
  order_date: string;
}

export interface SupplierOption {
  id: string;
  name: string;
  price: number;
  delivery_time: string;
  rating: number;
  phone: string;
}

export interface InventoryProductsResponse {
  products: InventoryProduct[];
  total_count: number;
}

export interface PurchaseOrdersResponse {
  orders: ActivePurchaseOrder[];
  total_count: number;
}

export interface SupplierOptionsResponse {
  suppliers: SupplierOption[];
  current_supplier_id: string | null;
}

export interface PerformanceBreakdown {
  delivery_score: number;
  delivery_on_time_rate: number;
  delivery_total_deliveries: number;
  delivery_on_time: number;
  delivery_late: number;
  price_score: number;
  price_cheaper_alternatives: number;
  price_product_count: number;
  volume_score: number;
  volume_monthly_spend: number;
  diversity_score: number;
  diversity_product_count: number;
}

export interface SupplierROI {
  id: string;
  name: string;
  performance: number;
  monthly_spend: number;
  status: 'excellent' | 'good' | 'fair' | 'warning';
  trend: 'up' | 'stable' | 'down';
  issues: string[];
  phone_number: string;
  performance_breakdown?: PerformanceBreakdown;
}

export interface SupplierROIResponse {
  suppliers: SupplierROI[];
  total_count: number;
  total_monthly_spend: number;
  avg_performance: number;
  excellent_count: number;
  warning_count: number;
}

export interface ApiError {
  detail: string;
}

// ============================================================================
// Agent API Types
// ============================================================================

export interface AgentTask {
  task_id: string;
  agent_name: string;
  supplier_name: string;
  status: "pending" | "running" | "completed" | "failed";
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  conversation_id: string | null;
  error: string | null;
  total_messages: number;
}

export interface AgentActivityItem extends AgentTask {
  task_type: "availability" | "delivery" | "products";
  description: string | null;
}

export interface AgentActivitySummary {
  delivery_risks_resolved: number;
  supplier_followups_sent: number;
  price_checks_completed: number;
  new_product_matches: number;
  time_saved_minutes: number;
}

export interface AgentActivityRecap {
  activities: AgentActivityItem[];
  total_count: number;
}

export interface Transcript {
  conversation_id: string;
  supplier_name: string;
  agent_id: string | null;
  timestamp: string;
  messages: Array<{
    role: "agent" | "user" | string;
    text: string;
  }>;
  total_messages: number;
  formatted_text: string;
}

export interface StartConversationRequest {
  agent_name?: string;
  api_key?: string;
  supplier_name?: string;
  product_name?: string;
}

export interface StartConversationResponse {
  task_id: string;
  agent_name: string;
  supplier_name: string;
  status: string;
  message: string;
}

// ============================================================================
// Base API Client
// ============================================================================

class ApiClient {
  private baseURL: string;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    
    const config: RequestInit = {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const error: ApiError = await response.json().catch(() => ({
          detail: `HTTP ${response.status}: ${response.statusText}`,
        }));
        throw new Error(error.detail || `Request failed with status ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('An unexpected error occurred');
    }
  }

  async get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET' });
  }

  async post<T>(endpoint: string, data?: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async put<T>(endpoint: string, data?: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }
}

// Create API client instance
const apiClient = new ApiClient(API_BASE_URL);

// ============================================================================
// Products API
// ============================================================================

export const productsApi = {
  /**
   * Get all in-store products with inventory information
   */
  getInStoreProducts: async (): Promise<InventoryProductsResponse> => {
    return apiClient.get<InventoryProductsResponse>('/api/products/in-store');
  },

  /**
   * Get all active purchase orders
   */
  getOrders: async (): Promise<PurchaseOrdersResponse> => {
    return apiClient.get<PurchaseOrdersResponse>('/api/products/orders');
  },

  /**
   * Get all available suppliers for a product
   */
  getProductSuppliers: async (
    productId: string
  ): Promise<SupplierOptionsResponse> => {
    return apiClient.get<SupplierOptionsResponse>(
      `/api/products/${productId}/suppliers`
    );
  },
};

// ============================================================================
// Suppliers API
// ============================================================================

export const suppliersApi = {
  /**
   * Get cheaper supplier alternatives for in-store products
   */
  getCheaperAlternatives: async (
    minSavingsPercent: number = 5.0,
    productId?: string
  ) => {
    const params = new URLSearchParams({
      min_savings_percent: minSavingsPercent.toString(),
    });
    if (productId) {
      params.append('product_id', productId);
    }
    return apiClient.get(`/api/suppliers/cheaper-alternatives?${params}`);
  },

  /**
   * Get supplier ROI and performance metrics
   */
  getSupplierROI: async (): Promise<SupplierROIResponse> => {
    return apiClient.get<SupplierROIResponse>('/api/suppliers/roi');
  },
};

// ============================================================================
// Innovative Products API
// ============================================================================

export const innovativeProductsApi = {
  /**
   * Get list of innovative products not currently in store
   */
  getInnovativeProducts: async (
    minSuppliers: number = 1,
    sortBy: 'price' | 'suppliers' | 'delivery_time' = 'suppliers'
  ) => {
    const params = new URLSearchParams({
      min_suppliers: minSuppliers.toString(),
      sort_by: sortBy,
    });
    return apiClient.get(`/api/products/innovative?${params}`);
  },
};

// ============================================================================
// Agent API
// ============================================================================

export const agentApi = {
  /**
   * Get summary statistics of agent activities
   * Counts activities from the same set shown in the recap (most recent activities)
   */
  getActivitySummary: async (limit: number = 10): Promise<AgentActivitySummary> => {
    const params = new URLSearchParams({
      limit: limit.toString(),
    });
    return apiClient.get<AgentActivitySummary>(`/api/agent/activity/summary?${params}`);
  },

  /**
   * Get recent agent activities for the daily recap
   */
  getActivityRecap: async (limit: number = 10): Promise<AgentActivityRecap> => {
    const params = new URLSearchParams({
      limit: limit.toString(),
    });
    return apiClient.get<AgentActivityRecap>(`/api/agent/activity/recap?${params}`);
  },

  /**
   * Get transcript by conversation_id
   */
  getTranscriptByConversationId: async (conversationId: string): Promise<Transcript> => {
    return apiClient.get<Transcript>(`/api/agent/transcript/${conversationId}`);
  },

  /**
   * Get transcript by task_id
   */
  getTranscriptByTaskId: async (taskId: string): Promise<Transcript> => {
    return apiClient.get<Transcript>(`/api/agent/transcript/task/${taskId}`);
  },

  /**
   * Start a new agent conversation
   */
  startConversation: async (
    request: StartConversationRequest
  ): Promise<StartConversationResponse> => {
    return apiClient.post<StartConversationResponse>('/api/agent/start', request);
  },

  /**
   * Get task status by task_id
   */
  getTaskStatus: async (taskId: string): Promise<AgentTask> => {
    return apiClient.get<AgentTask>(`/api/agent/status/${taskId}`);
  },

  /**
   * List all agent tasks
   */
  listTasks: async (): Promise<AgentTask[]> => {
    return apiClient.get<AgentTask[]>('/api/agent/tasks');
  },

  /**
   * Parse a completed conversation and update CSV
   */
  parseConversation: async (taskId: string): Promise<{ status: string; result: any; task_id: string }> => {
    return apiClient.post(`/api/agent/parse/${taskId}`);
  },
};

// ============================================================================
// Default Export
// ============================================================================

export default {
  products: productsApi,
  suppliers: suppliersApi,
  innovativeProducts: innovativeProductsApi,
  agent: agentApi,
};

// Export API client for custom requests
export { apiClient };
