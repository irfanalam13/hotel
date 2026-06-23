import { z } from "zod";

export const ROLE_OPTIONS = [
  { code: "OWNER", label: "Owner" },
  { code: "ADMIN", label: "Organization Admin" },
  { code: "MANAGER", label: "Property Manager" },
  { code: "RECEPTIONIST", label: "Receptionist" },
  { code: "HOUSEKEEPING", label: "Housekeeping" },
  { code: "MAINTENANCE", label: "Maintenance" },
  { code: "ACCOUNTANT", label: "Accountant" },
  { code: "GUEST", label: "Guest" },
  { code: "READ_ONLY", label: "Read only" },
] as const;

export const inviteSchema = z.object({
  email: z.string().email("Enter a valid email"),
  full_name: z.string().optional(),
  role_code: z.string().min(1, "Role is required"),
});
export type InviteValues = z.infer<typeof inviteSchema>;

export const createOrgSchema = z.object({
  name: z.string().min(2, "Name is required"),
  plan: z.enum(["FREE", "STARTER", "PRO", "ENTERPRISE"]),
});
export type CreateOrgValues = z.infer<typeof createOrgSchema>;
