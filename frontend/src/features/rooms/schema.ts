import { z } from "zod";

export const roomTypeSchema = z.object({
  property: z.string().min(1, "Property is required"),
  name: z.string().min(1, "Name is required"),
  base_rate: z.coerce.number().min(0),
  max_adults: z.coerce.number().min(1),
  max_children: z.coerce.number().min(0),
});
export type RoomTypeInput = z.input<typeof roomTypeSchema>;
export type RoomTypeValues = z.output<typeof roomTypeSchema>;

export const roomSchema = z.object({
  property: z.string().min(1, "Property is required"),
  room_type: z.string().min(1, "Room type is required"),
  number: z.string().min(1, "Room number is required"),
  floor: z.string().optional(),
});
export type RoomValues = z.infer<typeof roomSchema>;
