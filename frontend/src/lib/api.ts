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
  weekly_use: number;
  stockout_date: string;
  status: 'healthy' | 'low' | 'critical';
  supplier: string;
  supplier_id: string;
  price: number;
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
  current_supplier_id: string;
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
// Default Export
// ============================================================================

export default {
  products: productsApi,
  suppliers: suppliersApi,
  innovativeProducts: innovativeProductsApi,
};

// Export API client for custom requests
export { apiClient };
