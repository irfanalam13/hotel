"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { CalendarCheck } from "lucide-react";
import { useEffect } from "react";
import { useForm, useWatch } from "react-hook-form";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { useActiveOrg } from "@/components/layout/active-org";
import { useGuests } from "@/features/guests/hooks";
import { useProperties } from "@/features/properties/hooks";
import { useRoomTypes } from "@/features/rooms/hooks";
import { addDaysISO, formatMoney, todayISO } from "@/lib/format";
import { useAvailability, useCreateReservation } from "./hooks";
import { bookingSchema, type BookingInput, type BookingValues } from "./schema";

export function ReservationFormDialog({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const { activeOrg } = useActiveOrg();
  const create = useCreateReservation();
  const { data: propsData } = useProperties();
  const { data: typesData } = useRoomTypes();
  const { data: guestsData } = useGuests();
  const properties = propsData?.results ?? [];
  const roomTypes = typesData?.results ?? [];
  const guests = guestsData?.results ?? [];
  const currency = activeOrg?.currency ?? "USD";

  const {
    register,
    handleSubmit,
    reset,
    control,
    formState: { errors, isSubmitting },
  } = useForm<BookingInput, unknown, BookingValues>({
    resolver: zodResolver(bookingSchema),
    defaultValues: {
      property: "",
      check_in: todayISO(),
      check_out: addDaysISO(todayISO(), 1),
      room_type_id: "",
      primary_guest: "",
      adults: 1,
      children: 0,
    },
  });

  const [property, checkIn, checkOut, roomTypeId] = useWatch({
    control,
    name: ["property", "check_in", "check_out", "room_type_id"],
  });

  const typesForProperty = roomTypes.filter((t) => t.property === property);
  const guestsForProperty = guests.filter((g) => g.property === property);

  const availability = useAvailability(
    property && checkIn && checkOut ? { property, check_in: checkIn, check_out: checkOut } : null,
  );
  const selectedRow = availability.data?.find((r) => r.room_type_id === roomTypeId);

  useEffect(() => {
    if (open) {
      reset({
        property: properties[0]?.id ?? "",
        check_in: todayISO(),
        check_out: addDaysISO(todayISO(), 1),
        room_type_id: "",
        primary_guest: "",
        adults: 1,
        children: 0,
      });
    }
  }, [open, properties, reset]);

  async function onSubmit(values: BookingValues) {
    await create.mutateAsync({
      property: values.property,
      check_in: values.check_in,
      check_out: values.check_out,
      primary_guest: values.primary_guest || undefined,
      adults: values.adults,
      children: values.children,
      rooms: [{ room_type_id: values.room_type_id, adults: values.adults, children: values.children }],
    });
    onOpenChange(false);
  }

  const noAvailability = selectedRow && selectedRow.available === 0;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>New reservation</DialogTitle>
          <DialogDescription>Search availability and book a room.</DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
          <div className="flex flex-col gap-2">
            <Label htmlFor="b-property">Property</Label>
            <Select id="b-property" {...register("property")}>
              <option value="">Select a property</option>
              {properties.map((p) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </Select>
            {errors.property && <p className="text-sm text-destructive">{errors.property.message}</p>}
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-2">
              <Label htmlFor="b-in">Check-in</Label>
              <Input id="b-in" type="date" {...register("check_in")} />
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="b-out">Check-out</Label>
              <Input id="b-out" type="date" {...register("check_out")} />
              {errors.check_out && <p className="text-sm text-destructive">{errors.check_out.message}</p>}
            </div>
          </div>

          <div className="flex flex-col gap-2">
            <Label htmlFor="b-type">Room type</Label>
            <Select id="b-type" {...register("room_type_id")}>
              <option value="">Select a room type</option>
              {typesForProperty.map((t) => {
                const row = availability.data?.find((r) => r.room_type_id === t.id);
                return (
                  <option key={t.id} value={t.id}>
                    {t.name}
                    {row ? ` — ${row.available} available` : ""}
                  </option>
                );
              })}
            </Select>
            {errors.room_type_id && (
              <p className="text-sm text-destructive">{errors.room_type_id.message}</p>
            )}
            {selectedRow && (
              <div
                className={`rounded-md border p-3 text-sm ${
                  noAvailability ? "border-destructive/40 bg-destructive/5" : "bg-muted/40"
                }`}
              >
                {noAvailability ? (
                  <span className="text-destructive">No rooms available for these dates.</span>
                ) : (
                  <span>
                    <strong>{selectedRow.available}</strong> available ·{" "}
                    {formatMoney(selectedRow.total_price, currency)} for {selectedRow.nights} night
                    {selectedRow.nights === 1 ? "" : "s"}
                  </span>
                )}
              </div>
            )}
          </div>

          <div className="flex flex-col gap-2">
            <Label htmlFor="b-guest">Primary guest (optional)</Label>
            <Select id="b-guest" {...register("primary_guest")}>
              <option value="">No guest selected</option>
              {guestsForProperty.map((g) => (
                <option key={g.id} value={g.id}>{g.full_name}</option>
              ))}
            </Select>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-2">
              <Label htmlFor="b-adults">Adults</Label>
              <Input id="b-adults" type="number" min={1} {...register("adults")} />
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="b-children">Children</Label>
              <Input id="b-children" type="number" min={0} {...register("children")} />
            </div>
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting || noAvailability}>
              <CalendarCheck className="size-4" />
              {isSubmitting ? "Booking…" : "Book reservation"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
