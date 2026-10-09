export interface Store {
  id: string;
  name: string;
  category: string;
  lat: number;
  lon: number;
  address: string;
  phone: string | null;
  has_own_website: boolean;
  raw_website: string | null;
  portal_urls: string[];
  sns_urls: string[];
  email: string | null;
  email_source_url: string | null;
  email_confidence: "HIGH" | "MEDIUM" | "LOW" | "NONE" | null;
  genre?: string;
  google_maps_url?: string;
  data_source?: string;
}

export interface SearchCenter {
  lat: number;
  lon: number;
  display_name: string;
}

export interface SearchResponse {
  status: string;
  data_source?: string;
  center: SearchCenter;
  radius_meters: number;
  total_found: number;
  without_website_count: number;
  with_contact_count: number;
  stores: Store[];
}
