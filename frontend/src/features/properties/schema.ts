import { z } from "zod";

export const propertySchema = z.object({
  name: z.string().min(1, "Name is required"),
  city: z.string().optional(),
  country: z.string().optional(),
  phone: z.string().optional(),
  email: z.union([z.string().email("Invalid email"), z.literal("")]).optional(),
  star_rating: z.coerce.number().min(0).max(5),
});

export type PropertyInput = z.input<typeof propertySchema>;
export type PropertyValues = z.output<typeof propertySchema>;
