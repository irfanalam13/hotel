export interface User {
  id: string;
  email: string;
  full_name: string;
  phone: string;
  is_active: boolean;
  is_staff: boolean;
  created_at: string;
}

export type Plan = "FREE" | "STARTER" | "PRO" | "ENTERPRISE";

export interface Organization {
  id: string;
  name: string;
  slug: string;
  is_active: boolean;
  plan: Plan;
  max_properties: number;
  timezone: string;
  currency: string;
  created_at: string;
}

export interface Membership {
  id: string;
  user: User;
  role_code: string;
  role_name: string;
  is_active: boolean;
  is_default: boolean;
  created_at: string;
}

export interface Role {
  id: string;
  code: string;
  name: string;
  description: string;
  is_system: boolean;
  permissions: string[];
  created_at: string;
}

export interface Property {
  id: string;
  name: string;
  code: string;
  address: string;
  city: string;
  country: string;
  phone: string;
  email: string;
  timezone: string;
  currency: string;
  star_rating: number;
  is_active: boolean;
  created_at: string;
}

export interface RoomType {
  id: string;
  property: string;
  name: string;
  code: string;
  description: string;
  max_adults: number;
  max_children: number;
  base_rate: string;
  capacity: number;
  created_at: string;
}

export type RoomStatus = "vacant_clean" | "vacant_dirty" | "occupied" | "out_of_order";

export interface Room {
  id: string;
  property: string;
  room_type: string;
  room_type_name: string;
  number: string;
  floor: string;
  status: RoomStatus;
  is_active: boolean;
  notes: string;
  created_at: string;
}

export interface Guest {
  id: string;
  property: string;
  first_name: string;
  last_name: string;
  full_name: string;
  email: string;
  phone: string;
  nationality: string;
  address: string;
  date_of_birth: string | null;
  notes: string;
  created_at: string;
}

export type ReservationStatus =
  | "inquiry"
  | "booked"
  | "checked_in"
  | "checked_out"
  | "cancelled"
  | "no_show";

export interface ReservationRoom {
  id: string;
  room_type: string;
  room_type_name: string;
  room: string | null;
  room_number: string | null;
  nightly_rate: string;
  nights: number;
  amount: string;
  adults: number;
  children: number;
}

export interface ReservationCharge {
  id: string;
  kind: string;
  description: string;
  amount: string;
  posted_on: string;
  created_at: string;
}

export interface Reservation {
  id: string;
  code: string;
  status: ReservationStatus;
  property: string;
  primary_guest: string | null;
  check_in: string;
  check_out: string;
  nights: number;
  adults: number;
  children: number;
  source: string;
  special_requests: string;
  internal_notes: string;
  currency: string;
  total_amount: string;
  folio_total: string;
  rooms: ReservationRoom[];
  charges: ReservationCharge[];
  checked_in_at: string | null;
  checked_out_at: string | null;
  created_at: string;
}

export interface AvailabilityRow {
  room_type_id: string;
  room_type: string;
  available: number;
  nightly_rate: string;
  nights: number;
  total_price: string;
}

export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface TokenPair {
  access: string;
  refresh: string;
}
