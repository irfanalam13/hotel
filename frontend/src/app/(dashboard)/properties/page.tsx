"use client";

import { Building2, MoreHorizontal, Pencil, Plus, Trash2 } from "lucide-react";
import { useState } from "react";

import { useOpenOnNew } from "@/lib/use-open-on-new";

import { PageHeader } from "@/components/shared/page-header";
import { ConfirmDialog } from "@/components/shared/confirm-dialog";
import { EmptyState, ErrorState } from "@/components/shared/states";
import { TableSkeleton } from "@/components/shared/table-skeleton";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { PropertyFormDialog } from "@/features/properties/property-form";
import { useDeleteProperty, useProperties } from "@/features/properties/hooks";
import type { Property } from "@/types";

export default function PropertiesPage() {
  const { data, isLoading, isError, refetch } = useProperties();
  const del = useDeleteProperty();

  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<Property | null>(null);
  const [toDelete, setToDelete] = useState<Property | null>(null);
  useOpenOnNew(setFormOpen);

  const openCreate = () => {
    setEditing(null);
    setFormOpen(true);
  };
  const openEdit = (p: Property) => {
    setEditing(p);
    setFormOpen(true);
  };

  const properties = data?.results ?? [];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Properties"
        description="Hotels and branches in your organization."
        actions={
          <Button onClick={openCreate}>
            <Plus className="size-4" /> New property
          </Button>
        }
      />

      {isLoading ? (
        <TableSkeleton cols={5} />
      ) : isError ? (
        <ErrorState description="Could not load properties." onRetry={() => refetch()} />
      ) : properties.length === 0 ? (
        <EmptyState
          icon={Building2}
          title="No properties yet"
          description="Create your first property to start managing rooms and reservations."
          action={
            <Button onClick={openCreate}>
              <Plus className="size-4" /> New property
            </Button>
          }
        />
      ) : (
        <Card className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Location</TableHead>
                <TableHead>Rating</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="w-10" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {properties.map((p) => (
                <TableRow key={p.id}>
                  <TableCell className="font-medium">{p.name}</TableCell>
                  <TableCell className="text-muted-foreground">
                    {[p.city, p.country].filter(Boolean).join(", ") || "—"}
                  </TableCell>
                  <TableCell>{p.star_rating ? `${p.star_rating}★` : "—"}</TableCell>
                  <TableCell>
                    <Badge variant={p.is_active ? "success" : "secondary"}>
                      {p.is_active ? "Active" : "Inactive"}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon">
                          <MoreHorizontal className="size-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={() => openEdit(p)}>
                          <Pencil className="size-4" /> Edit
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          className="text-destructive focus:text-destructive"
                          onClick={() => setToDelete(p)}
                        >
                          <Trash2 className="size-4" /> Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Card>
      )}

      <PropertyFormDialog open={formOpen} onOpenChange={setFormOpen} property={editing} />
      <ConfirmDialog
        open={!!toDelete}
        onOpenChange={(o) => !o && setToDelete(null)}
        title={`Delete ${toDelete?.name}?`}
        description="This archives the property. You can recreate it later if needed."
        confirmLabel="Delete"
        destructive
        loading={del.isPending}
        onConfirm={() => {
          if (toDelete) del.mutate(toDelete.id);
          setToDelete(null);
        }}
      />
    </div>
  );
}
