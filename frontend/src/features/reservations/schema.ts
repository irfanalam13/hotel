import { z } from "zod";

export const bookingSchema = z
  .object({
    property: z.string().min(1, "Property is required"),
    check_in: z.string().min(1, "Check-in date is required"),
    check_out: z.string().min(1, "Check-out date is required"),
    room_type_id: z.string().min(1, "Room type is required"),
    primary_guest: z.string().optional(),
    adults: z.coerce.number().min(1),
    children: z.coerce.number().min(0),
  })
  .refine((d) => d.check_out > d.check_in, {
    message: "Check-out must be after check-in",
    path: ["check_out"],
  });

export type BookingInput = z.input<typeof bookingSchema>;
export type BookingValues = z.output<typeof bookingSchema>;
