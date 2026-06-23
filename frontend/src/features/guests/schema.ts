import { z } from "zod";

export const guestSchema = z.object({
  property: z.string().min(1, "Property is required"),
  first_name: z.string().min(1, "First name is required"),
  last_name: z.string().optional(),
  email: z.union([z.string().email("Invalid email"), z.literal("")]).optional(),
  phone: z.string().optional(),
  nationality: z.string().optional(),
});

export type GuestValues = z.infer<typeof guestSchema>;
