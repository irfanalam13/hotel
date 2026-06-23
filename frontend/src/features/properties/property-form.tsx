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
import type { Property } from "@/types";
import { useCreateProperty, useUpdateProperty } from "./hooks";
import { propertySchema, type PropertyInput, type PropertyValues } from "./schema";

export function PropertyFormDialog({
  open,
  onOpenChange,
  property,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  property?: Property | null;
}) {
  const isEdit = !!property;
  const create = useCreateProperty();
  const update = useUpdateProperty();

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<PropertyInput, unknown, PropertyValues>({
    resolver: zodResolver(propertySchema),
    defaultValues: { name: "", city: "", country: "", phone: "", email: "", star_rating: 0 },
  });

  useEffect(() => {
    if (open) {
      reset({
        name: property?.name ?? "",
        city: property?.city ?? "",
        country: property?.country ?? "",
        phone: property?.phone ?? "",
        email: property?.email ?? "",
        star_rating: property?.star_rating ?? 0,
      });
    }
  }, [open, property, reset]);

  async function onSubmit(values: PropertyValues) {
    if (isEdit) {
      await update.mutateAsync({ id: property!.id, body: values });
    } else {
      await create.mutateAsync(values);
    }
    onOpenChange(false);
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{isEdit ? "Edit property" : "New property"}</DialogTitle>
          <DialogDescription>
            {isEdit ? "Update this property's details." : "Add a new property to your organization."}
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
          <div className="flex flex-col gap-2">
            <Label htmlFor="name">Name</Label>
            <Input id="name" {...register("name")} />
            {errors.name && <p className="text-sm text-destructive">{errors.name.message}</p>}
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-2">
              <Label htmlFor="city">City</Label>
              <Input id="city" {...register("city")} />
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="country">Country</Label>
              <Input id="country" {...register("country")} />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-2">
              <Label htmlFor="phone">Phone</Label>
              <Input id="phone" {...register("phone")} />
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="star_rating">Star rating</Label>
              <Input id="star_rating" type="number" min={0} max={5} {...register("star_rating")} />
            </div>
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="email">Email</Label>
            <Input id="email" type="email" {...register("email")} />
            {errors.email && <p className="text-sm text-destructive">{errors.email.message}</p>}
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Saving…" : isEdit ? "Save changes" : "Create property"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
