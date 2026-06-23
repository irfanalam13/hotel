"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect } from "react";
import { useForm } from "react-hook-form";

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
import type { Guest } from "@/types";
import { useCreateGuest, useUpdateGuest } from "./hooks";
import { guestSchema, type GuestValues } from "./schema";

export function GuestFormDialog({
  open,
  onOpenChange,
  guest,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  guest?: Guest | null;
}) {
  const isEdit = !!guest;
  const create = useCreateGuest();
  const update = useUpdateGuest();
  const { data: propertiesData } = useProperties();
  const properties = propertiesData?.results ?? [];

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<GuestValues>({
    resolver: zodResolver(guestSchema),
    defaultValues: { property: "", first_name: "", last_name: "", email: "", phone: "", nationality: "" },
  });

  useEffect(() => {
    if (open) {
      reset({
        property: guest?.property ?? properties[0]?.id ?? "",
        first_name: guest?.first_name ?? "",
        last_name: guest?.last_name ?? "",
        email: guest?.email ?? "",
        phone: guest?.phone ?? "",
        nationality: guest?.nationality ?? "",
      });
    }
  }, [open, guest, properties, reset]);

  async function onSubmit(values: GuestValues) {
    if (isEdit) {
      await update.mutateAsync({ id: guest!.id, body: values });
    } else {
      await create.mutateAsync(values);
    }
    onOpenChange(false);
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{isEdit ? "Edit guest" : "New guest"}</DialogTitle>
          <DialogDescription>Guest profile details.</DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
          <div className="flex flex-col gap-2">
            <Label htmlFor="property">Property</Label>
            <Select id="property" disabled={isEdit} {...register("property")}>
              <option value="">Select a property</option>
              {properties.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </Select>
            {errors.property && <p className="text-sm text-destructive">{errors.property.message}</p>}
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-2">
              <Label htmlFor="first_name">First name</Label>
              <Input id="first_name" {...register("first_name")} />
              {errors.first_name && (
                <p className="text-sm text-destructive">{errors.first_name.message}</p>
              )}
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="last_name">Last name</Label>
              <Input id="last_name" {...register("last_name")} />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-2">
              <Label htmlFor="email">Email</Label>
              <Input id="email" type="email" {...register("email")} />
              {errors.email && <p className="text-sm text-destructive">{errors.email.message}</p>}
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="phone">Phone</Label>
              <Input id="phone" {...register("phone")} />
            </div>
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="nationality">Nationality</Label>
            <Input id="nationality" {...register("nationality")} />
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Saving…" : isEdit ? "Save changes" : "Add guest"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
