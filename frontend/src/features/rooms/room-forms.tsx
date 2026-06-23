"use client";

import { zodResolver } from "@hookform/resolvers/zod";
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
import { useProperties } from "@/features/properties/hooks";
import { useCreateRoom, useCreateRoomType, useRoomTypes } from "./hooks";
import {
  roomSchema,
  roomTypeSchema,
  type RoomTypeInput,
  type RoomTypeValues,
  type RoomValues,
} from "./schema";

export function RoomTypeFormDialog({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const create = useCreateRoomType();
  const { data } = useProperties();
  const properties = data?.results ?? [];

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<RoomTypeInput, unknown, RoomTypeValues>({
    resolver: zodResolver(roomTypeSchema),
    defaultValues: { property: "", name: "", base_rate: 0, max_adults: 2, max_children: 0 },
  });

  useEffect(() => {
    if (open) reset({ property: properties[0]?.id ?? "", name: "", base_rate: 0, max_adults: 2, max_children: 0 });
  }, [open, properties, reset]);

  async function onSubmit(values: RoomTypeValues) {
    await create.mutateAsync(values);
    onOpenChange(false);
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>New room type</DialogTitle>
          <DialogDescription>Define a category of rooms and its base rate.</DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
          <div className="flex flex-col gap-2">
            <Label htmlFor="rt-property">Property</Label>
            <Select id="rt-property" {...register("property")}>
              <option value="">Select a property</option>
              {properties.map((p) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </Select>
            {errors.property && <p className="text-sm text-destructive">{errors.property.message}</p>}
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="rt-name">Name</Label>
            <Input id="rt-name" placeholder="Deluxe King" {...register("name")} />
            {errors.name && <p className="text-sm text-destructive">{errors.name.message}</p>}
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div className="flex flex-col gap-2">
              <Label htmlFor="rt-rate">Base rate</Label>
              <Input id="rt-rate" type="number" step="0.01" {...register("base_rate")} />
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="rt-adults">Max adults</Label>
              <Input id="rt-adults" type="number" min={1} {...register("max_adults")} />
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="rt-children">Max children</Label>
              <Input id="rt-children" type="number" min={0} {...register("max_children")} />
            </div>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Saving…" : "Create room type"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

export function RoomFormDialog({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const create = useCreateRoom();
  const { data: propsData } = useProperties();
  const { data: typesData } = useRoomTypes();
  const properties = propsData?.results ?? [];
  const roomTypes = typesData?.results ?? [];

  const {
    register,
    handleSubmit,
    reset,
    control,
    formState: { errors, isSubmitting },
  } = useForm<RoomValues>({
    resolver: zodResolver(roomSchema),
    defaultValues: { property: "", room_type: "", number: "", floor: "" },
  });

  const selectedProperty = useWatch({ control, name: "property" });
  const typesForProperty = roomTypes.filter((t) => t.property === selectedProperty);

  useEffect(() => {
    if (open) reset({ property: properties[0]?.id ?? "", room_type: "", number: "", floor: "" });
  }, [open, properties, reset]);

  async function onSubmit(values: RoomValues) {
    await create.mutateAsync(values);
    onOpenChange(false);
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>New room</DialogTitle>
          <DialogDescription>Add a physical room to a property.</DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
          <div className="flex flex-col gap-2">
            <Label htmlFor="r-property">Property</Label>
            <Select id="r-property" {...register("property")}>
              <option value="">Select a property</option>
              {properties.map((p) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </Select>
            {errors.property && <p className="text-sm text-destructive">{errors.property.message}</p>}
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="r-type">Room type</Label>
            <Select id="r-type" {...register("room_type")}>
              <option value="">Select a room type</option>
              {typesForProperty.map((t) => (
                <option key={t.id} value={t.id}>{t.name}</option>
              ))}
            </Select>
            {errors.room_type && <p className="text-sm text-destructive">{errors.room_type.message}</p>}
            {selectedProperty && typesForProperty.length === 0 && (
              <p className="text-sm text-muted-foreground">Create a room type for this property first.</p>
            )}
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-2">
              <Label htmlFor="r-number">Room number</Label>
              <Input id="r-number" placeholder="101" {...register("number")} />
              {errors.number && <p className="text-sm text-destructive">{errors.number.message}</p>}
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="r-floor">Floor</Label>
              <Input id="r-floor" placeholder="1" {...register("floor")} />
            </div>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Saving…" : "Create room"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
